import time
import logging

logger = logging.getLogger(__name__)

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