"""
Collection views for Phase K: Collections Feature.

This module provides:
- API endpoints for AJAX operations (create, add, remove)
- Page views for collection management (list, detail, edit, delete)
"""

import json
import logging
import random
import string
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from django.utils.text import slugify

from ..models import Collection, CollectionItem, Prompt, UserProfile, PromptView

logger = logging.getLogger(__name__)


# =============================================================================
# API ENDPOINTS (AJAX)
# =============================================================================

@login_required
@require_GET
def api_collections_list(request):
    """
    API endpoint to get user's collections with prompt membership status.

    GET /api/collections/
    GET /api/collections/?prompt_id=123

    Query params:
        prompt_id: Optional - if provided, includes whether each collection contains this prompt

    Returns:
        JSON with collections list including item_count and thumbnail_url
    """
    try:
        prompt_id = request.GET.get('prompt_id')
        user = request.user

        # Get user's non-deleted collections with item count (limit to 50 for performance)
        collections = list(Collection.objects.filter(
            user=user,
            is_deleted=False
        ).annotate(
            items_count=Count('items')
        ).order_by('-created_at')[:50])  # Micro-Spec #9.1: Show most recently CREATED first

        # If prompt_id provided, get set of collection IDs that contain it
        collections_with_prompt = set()
        if prompt_id:
            try:
                prompt_id_int = int(prompt_id)
                collections_with_prompt = set(
                    CollectionItem.objects.filter(
                        collection__user=user,
                        collection__is_deleted=False,
                        prompt_id=prompt_id_int
                    ).values_list('collection_id', flat=True)
                )
            except (ValueError, TypeError):
                pass  # Invalid prompt_id, just skip

        # PERFORMANCE FIX: Batch fetch all thumbnails in ONE query instead of N+1
        collection_ids = [c.id for c in collections]
        all_items = CollectionItem.objects.filter(
            collection_id__in=collection_ids
        ).select_related('prompt').order_by('collection_id', '-added_at')

        # Group items by collection (max 3 per collection)
        from collections import defaultdict
        items_by_collection = defaultdict(list)
        for item in all_items:
            if len(items_by_collection[item.collection_id]) < 3:
                items_by_collection[item.collection_id].append(item)

        # Build response data
        collections_data = []
        for collection in collections:
            # Get thumbnails from pre-fetched items
            thumbnails = []
            for idx, item in enumerate(items_by_collection.get(collection.id, [])):
                if item.prompt:
                    # Micro-Spec #11.7: Use 600px for first thumb (full-width), 300px for grid items
                    thumb_width = 600 if idx == 0 else 300
                    thumb_url = item.prompt.get_thumbnail_url(width=thumb_width)
                    if thumb_url:
                        thumbnails.append(thumb_url)

            collections_data.append({
                'id': collection.id,
                'title': collection.title,
                'slug': collection.slug,
                'is_private': collection.is_private,
                'item_count': collection.items_count,
                'thumbnail_url': thumbnails[0] if thumbnails else None,  # Legacy
                'thumbnails': thumbnails,  # New: array of up to 3
                'has_prompt': collection.id in collections_with_prompt,
            })

        return JsonResponse({
            'success': True,
            'collections': collections_data,
            'count': len(collections_data),
        })

    except Exception as e:
        logger.error(f"Error in api_collections_list: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong',
        }, status=500)


@login_required
@require_POST
def api_collection_create(request):
    """
    API endpoint to create a new collection.

    POST data:
        title: Collection title (required, max 50 chars)
        is_private: Boolean (optional, default False)
        prompt_id: Optional - if provided, add this prompt to the new collection

    Returns:
        JSON with new collection data or error
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)

    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({
            'success': False,
            'error': 'Collection title is required'
        }, status=400)

    if len(title) > 50:
        return JsonResponse({
            'success': False,
            'error': 'Collection title must be 50 characters or less'
        }, status=400)

    # Get is_private from frontend (default False = public)
    is_private = data.get('is_private', False)
    # Handle string 'true'/'false' from form data
    if isinstance(is_private, str):
        is_private = is_private.lower() == 'true'
    prompt_id = data.get('prompt_id')

    # Generate unique slug from title
    base_slug = slugify(title)
    if not base_slug:
        base_slug = 'collection'

    # Add random suffix for uniqueness (5 characters)
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    slug = f"{base_slug}-{random_suffix}"

    # Ensure slug is unique (in rare collision case)
    while Collection.objects.filter(slug=slug).exists():
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        slug = f"{base_slug}-{random_suffix}"

    # Create the collection
    collection = Collection.objects.create(
        title=title,
        slug=slug,
        user=request.user,
        is_private=is_private
    )

    # Optionally add prompt to collection
    prompt_added = False
    if prompt_id:
        try:
            prompt = Prompt.objects.get(id=prompt_id)
            CollectionItem.objects.create(
                collection=collection,
                prompt=prompt,
                order=0
            )
            prompt_added = True
        except Prompt.DoesNotExist:
            pass  # Ignore if prompt doesn't exist

    logger.info(f"User {request.user.username} created collection '{title}' (ID: {collection.id})")

    return JsonResponse({
        'success': True,
        'collection': {
            'id': collection.id,
            'title': collection.title,
            'slug': collection.slug,
            'url': reverse('prompts:collection_detail', kwargs={'slug': collection.slug}),
            'item_count': 1 if prompt_added else 0,
            'is_private': collection.is_private,
        },
        'prompt_added': prompt_added
    })


@login_required
@require_POST
def api_collection_add_prompt(request, collection_id):
    """
    API endpoint to add a prompt to a collection.

    POST data:
        prompt_id: ID of prompt to add (required)

    Returns:
        JSON with success status
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)

    prompt_id = data.get('prompt_id')
    if not prompt_id:
        return JsonResponse({
            'success': False,
            'error': 'Prompt ID is required'
        }, status=400)

    # Get collection (must be owned by user, not deleted)
    collection = get_object_or_404(
        Collection, id=collection_id, user=request.user, is_deleted=False
    )

    # Get prompt
    try:
        prompt = Prompt.objects.get(id=prompt_id)
    except Prompt.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Prompt not found'
        }, status=404)

    # Check if already in collection
    if CollectionItem.objects.filter(collection=collection, prompt=prompt).exists():
        return JsonResponse({
            'success': False,
            'error': 'Prompt is already in this collection',
            'already_exists': True
        }, status=400)

    # Get next order number
    max_order = CollectionItem.objects.filter(collection=collection).count()

    # Add prompt to collection
    CollectionItem.objects.create(
        collection=collection,
        prompt=prompt,
        order=max_order
    )

    # Update collection's updated_at
    collection.save()  # This will auto-update updated_at

    logger.info(f"User {request.user.username} added prompt {prompt_id} to collection '{collection.title}'")

    # Get updated item count
    item_count = CollectionItem.objects.filter(collection=collection).count()

    return JsonResponse({
        'success': True,
        'message': f'Added to {collection.title}',
        'collection': {
            'id': collection.id,
            'title': collection.title,
            'item_count': item_count
        }
    })


@login_required
@require_POST
def api_collection_remove_prompt(request, collection_id):
    """
    API endpoint to remove a prompt from a collection.

    POST data:
        prompt_id: ID of prompt to remove (required)

    Returns:
        JSON with success status
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)

    prompt_id = data.get('prompt_id')
    if not prompt_id:
        return JsonResponse({
            'success': False,
            'error': 'Prompt ID is required'
        }, status=400)

    # Get collection (must be owned by user, not deleted)
    collection = get_object_or_404(
        Collection, id=collection_id, user=request.user, is_deleted=False
    )

    # Find and delete the collection item
    try:
        item = CollectionItem.objects.get(collection=collection, prompt_id=prompt_id)
        item.delete()

        # Update collection's updated_at
        collection.save()

        logger.info(f"User {request.user.username} removed prompt {prompt_id} from collection '{collection.title}'")

        # Get updated item count
        item_count = CollectionItem.objects.filter(collection=collection).count()

        return JsonResponse({
            'success': True,
            'message': f'Removed from {collection.title}',
            'collection': {
                'id': collection.id,
                'title': collection.title,
                'item_count': item_count
            }
        })
    except CollectionItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Prompt is not in this collection'
        }, status=404)


# =============================================================================
# PAGE VIEWS
# =============================================================================

@login_required
def collections_list(request):
    """
    Display list of user's collections.

    Shows:
        - All user's collections with prompt counts
        - Create new collection button
        - Edit/Delete actions
    """
    user = request.user

    # Get user's non-deleted collections with prompt counts
    collections = Collection.objects.filter(
        user=user,
        is_deleted=False
    ).annotate(
        items_count=Count('items')
    ).order_by('-updated_at')

    # Pagination
    paginator = Paginator(collections, 12)  # 12 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'collections': page_obj,
        'page_obj': page_obj,
        'total_collections': collections.count(),
    }

    return render(request, 'prompts/collections_list.html', context)


def collection_detail(request, slug):
    """
    Display a collection's contents.

    - Public collections: visible to everyone
    - Private collections: only visible to owner
    """
    # Try to get the collection (must not be deleted)
    collection = get_object_or_404(Collection, slug=slug, is_deleted=False)

    # Check view permission: private collections only visible to owner
    is_owner = request.user.is_authenticated and request.user == collection.user
    if collection.is_private and not is_owner:
        messages.error(request, "You don't have permission to view this collection.")
        return redirect('prompts:home')

    # Get collection items with prompts
    items = collection.items.select_related(
        'prompt', 'prompt__author', 'prompt__author__userprofile'
    ).order_by('order', '-added_at')

    # Pagination
    paginator = Paginator(items, 24)  # 24 prompts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'collection': collection,
        'items': page_obj,
        'page_obj': page_obj,
        'can_edit': is_owner,
        'is_owner': is_owner,
    }

    return render(request, 'prompts/collection_detail.html', context)


@login_required
def collection_edit(request, slug):
    """
    Edit a collection's details.

    - Only owner can edit
    - Can update: title, visibility
    """
    collection = get_object_or_404(
        Collection, slug=slug, user=request.user, is_deleted=False
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        is_private = request.POST.get('is_private') == 'on'

        # Validate
        if not title:
            messages.error(request, 'Collection title is required.')
            return render(request, 'prompts/collection_edit.html', {'collection': collection})

        if len(title) > 50:
            messages.error(request, 'Collection title must be 50 characters or less.')
            return render(request, 'prompts/collection_edit.html', {'collection': collection})

        # Update collection
        collection.title = title
        collection.is_private = is_private
        collection.save()

        messages.success(request, f'Collection "{title}" updated successfully.')
        return redirect('prompts:collection_detail', slug=collection.slug)

    context = {
        'collection': collection,
    }

    return render(request, 'prompts/collection_edit.html', context)


@login_required
def collection_delete(request, slug):
    """
    Delete a collection (soft delete).

    - Only owner can delete
    - Uses soft delete pattern
    """
    collection = get_object_or_404(
        Collection, slug=slug, user=request.user, is_deleted=False
    )

    if request.method == 'POST':
        collection_title = collection.title
        username = request.user.username
        collection.soft_delete(request.user)

        messages.success(request, f'Collection "{collection_title}" has been deleted.')
        logger.info("User %s deleted collection '%s' (ID: %s)", username, collection_title, collection.id)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'message': f'Collection "{collection_title}" deleted.'})
        return redirect('prompts:user_collections', username=username)

    # GET requests redirect to detail page (delete is handled via modal)
    return redirect('prompts:collection_detail', slug=slug)


@login_required
@require_POST
def collection_restore(request, slug):
    """
    Restore a deleted collection from trash.

    - Only owner can restore
    - Clears is_deleted, deleted_at, deleted_by fields
    """
    # Use filter to find deleted collections (not get_object_or_404 which excludes deleted)
    collection = Collection.objects.filter(
        slug=slug, user=request.user, is_deleted=True
    ).first()

    if not collection:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Collection not found.'}, status=404)
        messages.error(request, 'Collection not found.')
        return redirect('prompts:user_profile_trash', username=request.user.username)

    collection_title = collection.title
    collection.is_deleted = False
    collection.deleted_at = None
    collection.deleted_by = None
    collection.save()

    logger.info("User %s restored collection '%s' (ID: %s)", request.user.username, collection_title, collection.id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': f'Collection "{collection_title}" restored.'})

    messages.success(request, f'Collection "{collection_title}" has been restored.')
    return redirect('prompts:user_profile_trash', username=request.user.username)


@login_required
@require_POST
def collection_permanent_delete(request, slug):
    """
    Permanently delete a collection from trash.

    - Only owner can permanently delete
    - Collection must already be in trash (is_deleted=True)
    - Permanently removes the collection and all collection items
    """
    # Use filter to find deleted collections
    collection = Collection.objects.filter(
        slug=slug, user=request.user, is_deleted=True
    ).first()

    if not collection:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Collection not found.'}, status=404)
        messages.error(request, 'Collection not found.')
        return redirect('prompts:user_profile_trash', username=request.user.username)

    collection_title = collection.title
    collection_id = collection.id

    # Delete permanently (cascade will delete CollectionItems)
    collection.delete()

    logger.info("User %s permanently deleted collection '%s' (ID: %s)", request.user.username, collection_title, collection_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': f'Collection "{collection_title}" permanently deleted.'})

    messages.success(request, f'Collection "{collection_title}" has been permanently deleted.')
    return redirect('prompts:user_profile_trash', username=request.user.username)


@login_required
@require_POST
def empty_collections_trash(request):
    """
    Permanently delete all collections in trash.

    - Only deletes collections owned by the requesting user
    - Permanently removes all deleted collections and their items
    """
    deleted_collections = Collection.objects.filter(
        user=request.user, is_deleted=True
    )

    count = deleted_collections.count()

    if count == 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'message': 'No collections to delete.'})
        messages.info(request, 'No collections in trash.')
        return redirect('prompts:user_profile_trash', username=request.user.username)

    # Permanently delete all
    deleted_collections.delete()

    logger.info("User %s emptied collections trash (%d collections)", request.user.username, count)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': f'{count} collection(s) permanently deleted.'})

    messages.success(request, f'{count} collection(s) permanently deleted.')
    return redirect('prompts:user_profile_trash', username=request.user.username)


def user_collections(request, username):
    """
    Display a user's collections on their profile page (Collections tab).

    URL: /@{username}/collections/

    This view renders the Collections tab within the profile shell, showing
    all of a user's public collections (or all collections if viewing own profile).

    Args:
        request: HTTP request object
        username (str): Username of the profile to display

    Query params:
        sort: Sorting order ('recent', 'most', 'fewest') - default 'recent'
        page: Page number for pagination

    Context:
        profile_user: The user whose collections are being viewed
        profile: UserProfile instance
        collections: Paginated collection queryset
        page_obj: Paginator page object
        total_collections: Total count of visible collections
        is_own_profile: True if viewing user is the profile owner
        sort_order: Current sort order
        total_prompts: User's total published prompts count
        total_likes: User's total likes received
        total_views: User's total views received
        all_time_rank: User's all-time leaderboard rank
        thirty_day_rank: User's 30-day activity rank
        trash_count: Count of items in trash (owner only)

    Template:
        prompts/collections_profile.html
    """
    from django.core.cache import cache
    from prompts.services.leaderboard import LeaderboardService

    # Get the user (404 if not found)
    profile_user = get_object_or_404(User, username=username)

    # Get user's profile
    profile = profile_user.userprofile

    # Check if viewing user is the profile owner
    is_own_profile = request.user.is_authenticated and request.user == profile_user

    # Get sort order from query params (default: 'recent')
    sort_order = request.GET.get('sort', 'recent')

    # Base queryset: Get collections with item counts
    collections = Collection.objects.filter(
        user=profile_user,
        is_deleted=False
    ).annotate(
        items_count=Count('items')
    )

    # Visibility: Owner sees all, visitors see only public
    if not is_own_profile:
        collections = collections.filter(is_private=False)

    # Apply sorting
    if sort_order == 'most':
        # Most items first
        collections = collections.order_by('-items_count', '-updated_at')
    elif sort_order == 'fewest':
        # Fewest items first
        collections = collections.order_by('items_count', '-updated_at')
    else:
        # Recent (default): Most recently updated first
        collections = collections.order_by('-updated_at')

    # Calculate profile stats (same as user_profile view)
    total_prompts = Prompt.objects.filter(
        author=profile_user,
        status=1,
        deleted_at__isnull=True
    ).count()

    total_likes = profile.get_total_likes()

    # Cache key for profile stats
    cache_key = f'pf_profile_stats_v1_{profile_user.id}'
    cached_stats = cache.get(cache_key)

    if cached_stats and isinstance(cached_stats, dict):
        total_views = cached_stats.get('total_views', 0)
        all_time_rank = cached_stats.get('all_time_rank')
        thirty_day_rank = cached_stats.get('thirty_day_rank')
    else:
        # Compute stats
        try:
            total_views = PromptView.objects.filter(prompt__author=profile_user).count()
        except Exception:
            total_views = 0

        try:
            all_time_rank = LeaderboardService.get_user_rank(
                user=profile_user,
                metric='views',
                period='all'
            )
        except Exception:
            all_time_rank = None

        try:
            thirty_day_rank = LeaderboardService.get_user_rank(
                user=profile_user,
                metric='active',
                period='month'
            )
        except Exception:
            thirty_day_rank = None

        # Cache for 5 minutes
        cache.set(cache_key, {
            'total_views': total_views,
            'all_time_rank': all_time_rank,
            'thirty_day_rank': thirty_day_rank,
        }, 300)

    # Trash count (owner only)
    trash_count = 0
    if is_own_profile:
        trash_count = Prompt.all_objects.filter(
            author=profile_user,
            deleted_at__isnull=False
        ).count()

    # Pagination (12 collections per page) - paginate BEFORE thumbnail fetch
    paginator = Paginator(collections, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # PERFORMANCE FIX: Batch fetch thumbnails for ONLY the current page
    # This reduces N+1 queries (was 1 query per collection)
    from collections import defaultdict

    page_collections = list(page_obj.object_list)
    collection_ids = [c.id for c in page_collections]

    all_items = CollectionItem.objects.filter(
        collection_id__in=collection_ids
    ).select_related('prompt').order_by('collection_id', '-added_at')

    # Group items by collection (max 3 per collection)
    items_by_collection = defaultdict(list)
    for item in all_items:
        if len(items_by_collection[item.collection_id]) < 3:
            items_by_collection[item.collection_id].append(item)

    # Attach thumbnails to each collection
    for collection in page_collections:
        thumbnails = []
        for idx, item in enumerate(items_by_collection.get(collection.id, [])):
            if item.prompt:
                # Micro-Spec #11.7: Use 600px for first thumb (full-width), 300px for grid items
                thumb_width = 600 if idx == 0 else 300
                thumb_url = item.prompt.get_thumbnail_url(width=thumb_width)
                if thumb_url:
                    thumbnails.append(thumb_url)
        collection.thumbnails = thumbnails

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'collections': page_obj,
        'page_obj': page_obj,
        'total_collections': paginator.count,
        'is_own_profile': is_own_profile,
        'sort': sort_order,  # Bug #4 fix: Template expects 'sort' not 'sort_order'
        'active_tab': 'collections',
        # Profile stats
        'total_prompts': total_prompts,
        'total_likes': total_likes,
        'total_views': total_views,
        'all_time_rank': all_time_rank,
        'thirty_day_rank': thirty_day_rank,
        'trash_count': trash_count,
    }

    return render(request, 'prompts/collections_profile.html', context)
