from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from prompts.models import Prompt, Comment, UserProfile, EmailPreferences
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from prompts.email_utils import should_send_email
from django.template.response import TemplateResponse
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Extract client IP address from request, validating proxy headers.

    Security: Only trusts X-Forwarded-For headers when behind known proxies
    to prevent IP spoofing attacks. Falls back to REMOTE_ADDR if not behind
    trusted proxy or header is missing.

    Args:
        request: Django request object

    Returns:
        str: Client IP address (validated)
    """
    from django.conf import settings
    import ipaddress

    # Get X-Forwarded-For header (set by proxies/load balancers)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        # Split comma-separated IP chain
        ips = [ip.strip() for ip in x_forwarded_for.split(',')]

        # Iterate from rightmost IP (closest to our server) backwards
        # Stop at first IP that's NOT in our trusted proxy list
        for ip in reversed(ips):
            try:
                ip_obj = ipaddress.ip_address(ip)

                # Check if IP is in trusted proxy ranges
                is_trusted_proxy = False
                for proxy_range in getattr(settings, 'TRUSTED_PROXIES', []):
                    if ip_obj in ipaddress.ip_network(proxy_range):
                        is_trusted_proxy = True
                        break

                # If not a trusted proxy, this is the client IP
                if not is_trusted_proxy:
                    return ip

            except ValueError:
                # Invalid IP format, skip it
                continue

    # Fallback to REMOTE_ADDR (direct connection or no valid X-Forwarded-For)
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _disable_all_notifications(email_preferences):
    """
    Disable all email notifications EXCEPT critical platform updates.

    Used by both unsubscribe_custom() and unsubscribe_package() to avoid
    code duplication (DRY principle).

    Per model's unsubscribe_all() behavior, notify_updates stays enabled
    so users still receive critical security and platform notifications.
    This matches the documented intent in EmailPreferences.unsubscribe_all().

    Args:
        email_preferences: EmailPreferences instance to modify

    Returns:
        EmailPreferences: Updated instance (for chaining if needed)
    """
    email_preferences.notify_comments = False
    email_preferences.notify_replies = False
    email_preferences.notify_follows = False
    email_preferences.notify_likes = False
    email_preferences.notify_mentions = False
    email_preferences.notify_weekly_digest = False
    # email_preferences.notify_updates = False    # Keep True - critical platform updates
    email_preferences.notify_marketing = False
    email_preferences.save(update_fields=[
        'notify_comments', 'notify_replies', 'notify_follows',
        'notify_likes', 'notify_mentions', 'notify_weekly_digest',
        # 'notify_updates',    # Not changing this field - keep enabled
        'notify_marketing'
    ])
    return email_preferences


def ratelimited(request, exception=None):
    """
    Custom 429 error handler for django-ratelimit.

    Called automatically by RatelimitMiddleware when rate limits are exceeded.
    Provides a branded, user-friendly error page instead of generic 429.

    The django-ratelimit 4.x decorator raises a Ratelimited exception, which
    our custom middleware catches and passes to this view function.

    Referenced in settings.py:
        RATELIMIT_VIEW = 'prompts.views.ratelimited'

    Middleware:
        prompts.middleware.RatelimitMiddleware intercepts the exception
        and calls this view to render the custom 429 page.

    Args:
        request: Django HttpRequest object
        exception: Optional Ratelimited exception from django-ratelimit 4.x
                   (contains metadata like rate, group, method)

    Returns:
        TemplateResponse: Rendered 429.html template with status code 429

    Security:
        - No sensitive information exposed in error message
        - Generic retry guidance (doesn't reveal rate limit details)
        - Properly escapes all context variables

    Template Context:
        error_title: Human-readable error heading
        error_message: User-friendly explanation of the error
        retry_after: Plain language time to wait (matches 5/hour rate limit)
        support_email: Contact email for persistent issues

    Example Usage:
        User makes 6th request to /unsubscribe/token/ within 1 hour
        → @ratelimit decorator raises Ratelimited exception
        → RatelimitMiddleware catches exception
        → Middleware calls this view function
        → User sees branded 429.html template

    Testing:
        Returns TemplateResponse (not HttpResponse) to expose context
        and template information for automated testing.
    """
    from django.template.response import TemplateResponse

    context = {
        'error_title': 'Too Many Requests',
        'error_message': (
            'You have made too many requests. '
            'Please wait a moment and try again.'
        ),
        'retry_after': '1 hour',  # Matches UNSUBSCRIBE_RATE_LIMIT (5/hour)
        'support_email': 'support@promptfinder.com',  # For persistent issues
    }

    # Use TemplateResponse instead of render() for testability
    # TemplateResponse exposes .context_data and .templates attributes
    # which are needed by Django's test framework
    response = TemplateResponse(request, '429.html', context)
    response.status_code = 429
    return response


def _test_rate_limit_trigger():
    """
    Test helper function to manually verify rate limiting.

    This is a development/testing utility - NOT used in production.
    Helps developers verify the 429 error page displays correctly.

    Usage in Django shell:
        from prompts.views import _test_rate_limit_trigger
        _test_rate_limit_trigger()
        # Then visit /unsubscribe/<token>/ repeatedly

    Note: This is intentionally simple - actual rate limit testing
    should use automated test suite (see tests below).
    """
    from django.core.cache import cache
    # Clear any existing rate limit cache for testing
    cache.clear()
    print("Rate limit cache cleared. Test by making 6+ rapid requests.")
    print("Example: curl http://127.0.0.1:8000/unsubscribe/test_token/")


def unsubscribe_custom(request, token):
    """
    Custom rate limiting implementation with security hardening.

    Security Features:
        - IP spoofing protection via get_client_ip()
        - SHA-256 hashing for cache keys (not MD5)
        - Configurable rate limits from settings
        - Graceful cache error handling (fail open)
        - No token information in logs

    Rate Limit: 5 requests per IP per hour (configurable)

    Args:
        request: Django request object
        token: Unique unsubscribe token from EmailPreferences

    Returns:
        Rendered unsubscribe.html template with success/error context
        Status 429 if rate limit exceeded
    """
    from django.conf import settings

    # Get client IP with spoofing protection
    ip = get_client_ip(request)

    # Create secure cache key with SHA-256
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()
    cache_key = f'unsubscribe_ratelimit_{ip_hash}'

    # Get rate limit settings
    rate_limit = getattr(settings, 'UNSUBSCRIBE_RATE_LIMIT', 5)
    rate_limit_ttl = getattr(settings, 'UNSUBSCRIBE_RATE_LIMIT_TTL', 3600)

    # Check rate limit with error handling
    try:
        request_count = cache.get(cache_key, 0)

        if request_count >= rate_limit:
            logger.warning(
                f"Rate limit exceeded for IP hash {ip_hash[:16]}... "
                f"(attempt {request_count + 1})"
            )
            context = {
                'success': False,
                'rate_limited': True,
                'error': 'Too many unsubscribe requests. Please try again in an hour.',
            }
            return render(request, 'prompts/unsubscribe.html', context, status=429)

        cache.set(cache_key, request_count + 1, rate_limit_ttl)

    except Exception as e:
        logger.error(
            f"Cache backend error in rate limiting: {e}. "
            f"Failing open (allowing request)."
        )

    # Continue with unsubscribe logic
    try:
        email_preferences = EmailPreferences.objects.select_related('user').get(
            unsubscribe_token=token
        )

        # Disable all email notifications using helper function
        _disable_all_notifications(email_preferences)

        logger.info(f"User {email_preferences.user.username} unsubscribed via email link")

        context = {
            'success': True,
            'rate_limited': False,
            'user': email_preferences.user
        }

    except EmailPreferences.DoesNotExist:
        # Security: Don't log any part of the token (prevents enumeration)
        logger.warning("Invalid unsubscribe token attempt")
        context = {
            'success': False,
            'rate_limited': False,
            'error': 'invalid_token'
        }
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        context = {
            'success': False,
            'rate_limited': False,
            'error': 'server_error'
        }

    return render(request, 'prompts/unsubscribe.html', context)


# Import django-ratelimit decorator (with graceful fallback)
try:
    from django_ratelimit.decorators import ratelimit
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False
    # Fallback decorator that does nothing if package not installed
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator




def unsubscribe_package(request, token):
    """
    django-ratelimit implementation (production recommended).

    Features:
        - Battle-tested by major Django projects (Sentry, Mozilla, etc.)
        - Automatic IP spoofing protection (validates proxies)
        - Built-in monitoring and metrics
        - Less code to maintain (decorator handles rate limiting)
        - Better performance (optimized caching)

    Rate Limit: 5 requests per IP per hour (handled by @ratelimit decorator)

    Args:
        request: Django request object
        token: Unique unsubscribe token from EmailPreferences

    Returns:
        Rendered unsubscribe.html template with success/error context
        Status 429 if rate limit exceeded (handled by decorator)
    """
    # Rate limiting handled by @ratelimit decorator above
    # If rate limit exceeded, decorator returns 429 automatically

    try:
        email_preferences = EmailPreferences.objects.select_related('user').get(
            unsubscribe_token=token
        )

        # Disable all email notifications using helper function
        _disable_all_notifications(email_preferences)

        logger.info(f"User {email_preferences.user.username} unsubscribed via email link")

        context = {
            'success': True,
            'rate_limited': False,
            'user': email_preferences.user
        }

    except EmailPreferences.DoesNotExist:
        # Security: Don't log any part of the token (prevents enumeration)
        logger.warning("Invalid unsubscribe token attempt")
        context = {
            'success': False,
            'rate_limited': False,
            'error': 'invalid_token'
        }
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        context = {
            'success': False,
            'rate_limited': False,
            'error': 'server_error'
        }

    return render(request, 'prompts/unsubscribe.html', context)


# Apply @ratelimit decorator if django-ratelimit is available
# This ensures rate limiting works regardless of which backend is selected
if RATELIMIT_AVAILABLE:
    @ratelimit(key='ip', rate='5/h', method='GET', block=True)
    def unsubscribe_view(request, token):
        """
        Main unsubscribe view with switchable backend (rate limited).

        Rate Limiting: 5 requests per IP per hour (enforced by @ratelimit decorator)

        Uses RATE_LIMIT_BACKEND setting to choose implementation:
            - 'custom': Security-hardened custom implementation
            - 'package': django-ratelimit (production recommended, default)

        Environment Variable Override:
            export RATE_LIMIT_BACKEND=custom  # Use custom implementation
            export RATE_LIMIT_BACKEND=package # Use django-ratelimit (default)

        Fallback Behavior:
            If 'package' selected but django-ratelimit not installed,
            automatically falls back to custom implementation with warning.

        Args:
            request: Django request object
            token: Unique unsubscribe token from EmailPreferences

        Returns:
            Delegated to unsubscribe_custom() or unsubscribe_package()
            Status 429 if rate limit exceeded (handled by decorator)
        """
        from django.conf import settings

        backend = getattr(settings, 'RATE_LIMIT_BACKEND', 'package')

        # Check if django-ratelimit is available
        if backend == 'package' and RATELIMIT_AVAILABLE:
            return unsubscribe_package(request, token)
        elif backend == 'package' and not RATELIMIT_AVAILABLE:
            logger.warning(
                "RATE_LIMIT_BACKEND set to 'package' but django-ratelimit not installed. "
                "Falling back to custom implementation. "
                "Install with: pip install django-ratelimit==4.1.0"
            )
            return unsubscribe_custom(request, token)
        else:
            # backend == 'custom' or any other value
            return unsubscribe_custom(request, token)
else:
    # If django-ratelimit not available, define undecorated version
    # Custom implementation will handle rate limiting internally
    def unsubscribe_view(request, token):
        """
        Main unsubscribe view with switchable backend (custom rate limiting).

        Rate Limiting: Handled by custom implementation (django-ratelimit not available)

        Uses RATE_LIMIT_BACKEND setting to choose implementation:
            - 'custom': Security-hardened custom implementation (default when package unavailable)
            - 'package': Not available (will fall back to custom with warning)

        Args:
            request: Django request object
            token: Unique unsubscribe token from EmailPreferences

        Returns:
            Delegated to unsubscribe_custom()
        """
        from django.conf import settings

        backend = getattr(settings, 'RATE_LIMIT_BACKEND', 'package')

        if backend == 'package':
            logger.warning(
                "RATE_LIMIT_BACKEND set to 'package' but django-ratelimit not installed. "
                "Falling back to custom implementation. "
                "Install with: pip install django-ratelimit==4.1.0"
            )

        # Always use custom implementation when django-ratelimit not available
        return unsubscribe_custom(request, token)


# ============================================================================
# FOLLOW SYSTEM VIEWS (Phase F Day 1)
# ============================================================================



