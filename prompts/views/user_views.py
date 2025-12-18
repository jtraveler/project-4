from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
import logging

from prompts.models import Prompt, Comment, UserProfile
from prompts.forms import CommentForm

logger = logging.getLogger(__name__)


def user_profile(request, username, active_tab=None):
    """
    Display public user profile page with user's prompts.

    Shows user information, stats, and a paginated masonry grid of their
    published prompts. Supports media filtering (all/photos/videos) and
    trash tab for profile owners.

    Args:
        request: HTTP request object
        username (str): Username of the profile to display
        active_tab (str): Optional active tab ('trash' for trash view)

    URL:
        /users/<username>/ - Public profile page
        /users/<username>/?media=photos - Show only images
        /users/<username>/?media=videos - Show only videos
        /users/<username>/trash/ - Trash bin (owner only)

    Template:
        prompts/user_profile.html

    Context:
        profile_user (User): The user whose profile is being viewed
        profile (UserProfile): The user's profile model instance
        prompts (QuerySet): Published prompts by this user (filtered by media type)
        page_obj (Page): Paginated prompts for current page
        total_prompts (int): Total count of user's published prompts
        total_likes (int): Sum of likes across all user's prompts
        media_filter (str): Current media filter ('all', 'photos', or 'videos')
        is_owner (bool): True if viewing user is the profile owner
        active_tab (str): Currently active tab ('gallery' or 'trash')
        trash_items (QuerySet): Trashed prompts (only for owner viewing trash tab)
        trash_count (int): Count of items in trash

    Example:
        # View john's profile
        /users/john/

        # View john's photos only
        /users/john/?media=photos

        # View john's videos only
        /users/john/?media=videos

        # View john's trash (owner only)
        /users/john/trash/

    Raises:
        Http404: If user with given username doesn't exist
    """
    # Get the user (404 if not found)
    profile_user = get_object_or_404(User, username=username)

    # Get user's profile (should always exist due to signals)
    profile = profile_user.userprofile

    # Get media filter from query params (default: 'all')
    media_filter = request.GET.get('media', 'all')

    # Get sort order from query params (default: 'recency')
    sort_order = request.GET.get('sort', 'recency')

    # Check if viewing user is the profile owner
    is_owner = request.user.is_authenticated and request.user == profile_user

    # PERFORMANCE OPTIMIZATION: Prefetch all relations to avoid N+1 queries
    # Same pattern as PromptList (homepage) - proven to reduce queries from 55 to 7
    from django.db.models import Count

    base_queryset = Prompt.objects.select_related(
        'author'  # ForeignKey - join User table (avoids N queries for prompt.author)
    ).prefetch_related(
        'tags',   # ManyToMany - separate query fetches all tags (avoids N queries)
        'likes',  # ManyToMany - separate query fetches all likes (avoids N queries)
        Prefetch(
            'comments',  # Reverse FK - fetch only approved comments
            queryset=Comment.objects.filter(approved=True)
        )
    )

    # Base queryset: Show drafts ONLY to owner, published to everyone else
    # Note: Staff/admins should NOT see drafts on other users' profiles
    # (they would get 404 on detail view anyway - keep UI consistent)
    if is_owner:
        # Owner sees all their prompts (published and draft, exclude deleted)
        prompts = base_queryset.filter(
            author=profile_user,
            deleted_at__isnull=True  # Not in trash
        )
    else:
        # Everyone else (including staff) sees published prompts only
        prompts = base_queryset.filter(
            author=profile_user,
            status=1,  # Published only
            deleted_at__isnull=True  # Not in trash
        )

    # Apply media filtering
    if media_filter == 'photos':
        # Filter for items with featured_image only
        prompts = prompts.filter(featured_image__isnull=False)
    elif media_filter == 'videos':
        # Filter for items with featured_video only
        prompts = prompts.filter(featured_video__isnull=False)
    # 'all' shows everything (no additional filtering)

    # Apply sorting
    if sort_order == 'views':
        # Sort by view count (most views first)
        from prompts.models import PromptView
        prompts = prompts.annotate(
            views_count=Count('views')
        ).order_by('-views_count', '-created_on')
    else:
        # Default: sort by recency
        prompts = prompts.order_by('-created_on')

    # Calculate stats
    total_prompts = Prompt.objects.filter(
        author=profile_user,
        status=1,
        deleted_at__isnull=True
    ).count()

    total_likes = profile.get_total_likes()

    # Calculate profile metrics (Phase G enhancement)
    # Uses 5-minute caching to improve performance (same TTL as leaderboard)
    from django.core.cache import cache
    from prompts.models import PromptView
    from prompts.services.leaderboard import LeaderboardService

    # Cache key validation function (security hardening)
    # Prevents cache poisoning by validating user_id before key generation
    def _get_profile_stats_cache_key(user_id):
        """
        Generate a validated cache key for profile stats.

        Security measures:
        1. Validates user_id is a positive integer
        2. Uses versioned prefix (allows cache invalidation on schema changes)
        3. Returns None if validation fails (triggers fresh calculation)
        """
        if not isinstance(user_id, int) or user_id <= 0:
            return None
        return f'pf_profile_stats_v1_{user_id}'

    # Get validated cache key
    cache_key = _get_profile_stats_cache_key(profile_user.id)

    # Only use cache if key is valid
    cached_stats = cache.get(cache_key) if cache_key else None

    if cached_stats:
        # Validate cached data structure before using (prevents corrupted cache data)
        if isinstance(cached_stats, dict) and 'total_views' in cached_stats:
            total_views = cached_stats.get('total_views', 0)
            all_time_rank = cached_stats.get('all_time_rank')
            thirty_day_rank = cached_stats.get('thirty_day_rank')
        else:
            # Invalid cache data structure - recalculate
            cached_stats = None

    if not cached_stats:
        # Compute stats with error handling for each metric
        # Total Views: Sum of all unique views across user's prompts
        try:
            total_views = PromptView.objects.filter(prompt__author=profile_user).count()
        except Exception as e:
            logger.error(f"Failed to get total views for user {profile_user.id}: {e}")
            total_views = 0

        # All-time Rank: Position on Most Viewed leaderboard (all time)
        try:
            all_time_rank = LeaderboardService.get_user_rank(
                user=profile_user,
                metric='views',
                period='all'
            )
        except Exception as e:
            logger.error(f"Failed to get all-time rank for user {profile_user.id}: {e}")
            all_time_rank = None

        # 30-day Rank: Position on Most Active leaderboard (past 30 days)
        try:
            thirty_day_rank = LeaderboardService.get_user_rank(
                user=profile_user,
                metric='active',
                period='month'
            )
        except Exception as e:
            logger.error(f"Failed to get 30-day rank for user {profile_user.id}: {e}")
            thirty_day_rank = None

        # Cache results for 5 minutes (300 seconds) - aligns with leaderboard cache TTL
        # Only cache if we have a valid key (security: prevents cache pollution)
        if cache_key:
            cache.set(cache_key, {
                'total_views': total_views,
                'all_time_rank': all_time_rank,
                'thirty_day_rank': thirty_day_rank,
            }, 300)

    # Trash tab data (only for owner)
    trash_items = []
    trash_count = 0
    if is_owner:
        trash_items_qs = Prompt.all_objects.filter(
            author=profile_user,
            deleted_at__isnull=False
        ).order_by('-deleted_at')
        trash_count = trash_items_qs.count()

        # Only load full data if trash tab is active
        if active_tab == 'trash':
            trash_items = list(trash_items_qs)

    # Redirect non-owners away from trash tab
    if active_tab == 'trash' and not is_owner:
        return redirect('prompts:user_profile', username=username)

    # Pagination (18 prompts per page, same as homepage)
    paginator = Paginator(prompts, 18)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'prompts': page_obj.object_list,  # Prompts for current page
        'page_obj': page_obj,  # Paginator object for load more
        'total_prompts': total_prompts,
        'total_likes': total_likes,
        'total_views': total_views,  # Phase G: Total views across all prompts
        'all_time_rank': all_time_rank,  # Phase G: Most Viewed leaderboard position
        'thirty_day_rank': thirty_day_rank,  # Phase G: Most Active leaderboard position (30 days)
        'media_filter': media_filter,
        'sort_order': sort_order,  # Sort order for profile prompts
        'is_own_profile': is_owner,
        'active_tab': active_tab or 'gallery',
        'trash_items': trash_items,
        'trash_count': trash_count,
        'show_statistics_tab': False,  # Phase G: Hidden for future implementation
    }

    response = render(request, 'prompts/user_profile.html', context)

    # Prevent caching when viewing trash tab (same fix as standalone trash page)
    # Uses 'private' to ensure shared caches (CDN, proxies) don't cache user-specific data
    # Vary: Cookie ensures cache key depends on user session
    if active_tab == 'trash':
        response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
        response['Vary'] = 'Cookie'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    return response


@login_required


def edit_profile(request):
    """
    View for editing user profile information.

    Features:
    - Only allows users to edit their own profile
    - Handles avatar upload with Cloudinary
    - Validates form data with UserProfileForm
    - Success message with redirect to profile
    - Error handling for form validation and database issues

    Security:
    - @login_required ensures authentication
    - Uses get_or_create for backward compatibility
    - transaction.atomic for database safety
    - Form validation in UserProfileForm

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Rendered edit_profile.html template
    """
    from django.db import transaction
    from prompts.forms import UserProfileForm

    # Get or create user profile (backward compatibility)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save profile with Cloudinary upload handled automatically
                    profile = form.save(commit=False)
                    profile.user = request.user  # Ensure ownership
                    profile.save()

                    messages.success(
                        request,
                        'Profile updated successfully! '
                        f'<a href="{reverse("prompts:user_profile", args=[request.user.username])}">View your profile</a>',
                        extra_tags='safe'
                    )

                    return redirect('prompts:user_profile', username=request.user.username)

            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Profile update failed for {request.user.username}: {e}", exc_info=True)

                messages.error(
                    request,
                    'An error occurred while updating your profile. Please try again. '
                    'If the problem persists, contact support.'
                )
        else:
            # Form validation errors - Django will display them in template
            messages.error(
                request,
                'Please correct the errors below and try again.'
            )
    else:
        # GET request - display form with current profile data
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
    }

    return render(request, 'prompts/edit_profile.html', context)


@login_required


def email_preferences(request):
    """
    Display and handle email notification preferences.

    GET: Display current preferences with toggle switches
    POST: Save updated preferences and show success message

    Users can toggle individual notification types on/off.

    Security:
    - @login_required ensures authentication
    - Uses get_or_create for backward compatibility
    - Form validation in EmailPreferencesForm

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Rendered settings_notifications.html template
    """
    from prompts.forms import EmailPreferencesForm
    from prompts.models import EmailPreferences

    # Get or create preferences for current user (signal should have created it)
    prefs, created = EmailPreferences.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = EmailPreferencesForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your email preferences have been updated.')
            return redirect('prompts:email_preferences')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmailPreferencesForm(instance=prefs)

    context = {
        'form': form,
        'preferences': prefs,
    }

    return render(request, 'prompts/settings_notifications.html', context)


@login_required
@require_POST


def report_prompt(request, slug):
    """
    View for reporting inappropriate prompts.

    Features:
    - Allows authenticated users to report prompts
    - Prevents duplicate reports (unique constraint)
    - Sends email notification to admins
    - AJAX-compatible (returns JSON for modal submission)
    - Graceful error handling

    Security:
    - @login_required ensures authentication
    - UniqueConstraint prevents spam
    - Email sent via fail_silently=True (no user-facing errors)
    - CSRF protection via Django forms

    Args:
        request: HttpRequest object
        slug: Prompt slug to report

    Returns:
        - On success: JSON response with success message
        - On duplicate: JSON response with error message
        - On error: JSON response with error details
    """
    from django.http import JsonResponse
    from django.core.mail import EmailMessage
    from django.conf import settings
    from prompts.forms import PromptReportForm
    from prompts.models import PromptReport
    import logging

    logger = logging.getLogger(__name__)

    # Get the prompt being reported
    prompt = get_object_or_404(Prompt, slug=slug, status=1)

    # Prevent users from reporting their own prompts
    if prompt.author == request.user:
        return JsonResponse({
            'success': False,
            'error': 'You cannot report your own prompt.'
        }, status=403)

    # Process the report form
    form = PromptReportForm(request.POST)

    if form.is_valid():
        try:
            # Create the report
            report = form.save(commit=False)
            report.prompt = prompt
            report.reported_by = request.user
            report.save()

            # Send email notification to admins
            try:
                admin_emails = [admin[1] for admin in settings.ADMINS] if hasattr(settings, 'ADMINS') else []

                if admin_emails:
                    # Sanitize subject line (prevent email header injection)
                    safe_title = prompt.title.replace('\r', '').replace('\n', ' ')[:100]
                    subject = f'New Prompt Report: {safe_title}'

                    message = f"""
A new prompt has been reported on PromptFinder.

**Report Details:**
- Prompt: {prompt.title}
- Reported By: {request.user.username} ({request.user.email})
- Reason: {report.get_reason_display()}
- Comment: {report.comment or '(No additional details provided)'}
- Report ID: #{report.id}

**Actions:**
- View prompt on site: {request.build_absolute_uri(prompt.get_absolute_url())}
- Log in to admin panel to review this report

Please review this report at your earliest convenience.

---
This is an automated notification from PromptFinder.
                    """

                    email = EmailMessage(
                        subject=subject,
                        body=message,
                        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@promptfinder.net',
                        to=admin_emails,
                    )
                    email.send(fail_silently=True)
                    logger.info(f"Report email sent for prompt '{prompt.slug}' by user '{request.user.username}'")

            except Exception as e:
                # Log email error but don't fail the request
                logger.error(f"Failed to send report email for prompt '{prompt.slug}': {e}", exc_info=True)

            # Return success response
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your report. Our team will review it shortly.'
            })

        except Exception as e:
            # Handle duplicate report or other database errors
            if 'unique_user_prompt_report' in str(e).lower() or 'duplicate' in str(e).lower():
                return JsonResponse({
                    'success': False,
                    'error': 'You have already reported this prompt. Our team is reviewing your previous report.'
                }, status=400)
            else:
                logger.error(f"Error creating report for prompt '{prompt.slug}': {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': 'An error occurred while submitting your report. Please try again.'
                }, status=500)

    else:
        # Form validation errors
        errors = form.errors.as_json()
        return JsonResponse({
            'success': False,
            'error': 'Please correct the errors in your report.',
            'form_errors': errors
        }, status=400)


