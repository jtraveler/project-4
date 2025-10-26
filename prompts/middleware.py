import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RatelimitMiddleware(MiddlewareMixin):
    """
    Middleware to catch django-ratelimit exceptions and show custom 429 page.

    In django-ratelimit 4.x, the @ratelimit decorator raises a Ratelimited
    exception when the rate limit is exceeded. By default, Django converts
    this to a 403 Forbidden response.

    This middleware intercepts the exception and calls our custom ratelimited()
    view function to return a branded 429 Too Many Requests page instead.

    Installation:
        Add to MIDDLEWARE in settings.py:
            'prompts.middleware.RatelimitMiddleware',

    Configuration:
        RATELIMIT_VIEW setting is respected (defaults to 'prompts.views.ratelimited')
    """

    def process_exception(self, request, exception):
        """
        Catch Ratelimited exceptions and return custom 429 response.

        Args:
            request: Django HttpRequest object
            exception: Exception raised during view processing

        Returns:
            HttpResponse with status 429 if Ratelimited exception,
            None otherwise (let Django handle other exceptions)
        """
        try:
            from django_ratelimit.exceptions import Ratelimited
        except ImportError:
            # django-ratelimit not installed, let Django handle exception
            return None

        # Check if this is a rate limit exception
        if isinstance(exception, Ratelimited):
            from django.conf import settings
            from django.utils.module_loading import import_string

            # Get custom ratelimited view from settings
            view_path = getattr(settings, 'RATELIMIT_VIEW', 'prompts.views.ratelimited')

            try:
                # Import and call the custom ratelimited view
                ratelimited_view = import_string(view_path)
                return ratelimited_view(request, exception)
            except (ImportError, AttributeError) as e:
                # If custom view not found, return simple 429 response
                from django.http import HttpResponse
                return HttpResponse(
                    '<h1>429 Too Many Requests</h1>'
                    '<p>You have made too many requests. Please try again later.</p>',
                    status=429
                )

        # Not a rate limit exception, let Django handle it normally
        return None


class InfrastructureDebugMiddleware:
    """
    Debug middleware to measure infrastructure performance
    Following Sentry Django Performance Guide debugging approach
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip debug for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)
            
        # DEBUG: Measure request processing time
        start_time = time.time()
        
        response = self.get_response(request)
        
        # DEBUG: Calculate response time
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # DEBUG: Check response compression
        content_encoding = response.get('Content-Encoding', 'none')
        content_length = len(response.content) if hasattr(response, 'content') else 0
        
        # DEBUG: Log infrastructure metrics (only for main pages)
        if request.path in ['/', '/about/', '/collaborate/'] or request.path.startswith('/prompts/'):
            logger.warning(
                f"INFRA DEBUG: {request.path} | "
                f"Time: {response_time:.1f}ms | "
                f"Size: {content_length} bytes | "
                f"Compression: {content_encoding} | "
                f"Status: {response.status_code}"
            )
        
        return response