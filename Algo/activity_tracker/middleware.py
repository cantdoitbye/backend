from django.utils import timezone
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from .models import UserActivity, ActivityType
from .handlers import ActivityTracker
import re

class ActivityTrackingMiddleware:
    """
    Middleware to automatically track user activities like page views.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.ignored_paths = [
            r'^/admin/',
            r'^/static/',
            r'^/media/',
            r'^/__debug__/',
            r'^/health/',
        ]
        self.ignored_methods = ['OPTIONS', 'HEAD']
    
    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        
        # Skip tracking for certain conditions
        if not self.should_track(request, response):
            return response
        
        # Track the page view
        self.track_page_view(request)
        
        return response
    
    def should_track(self, request, response):
        """Determine if we should track this request."""
        # Skip if not authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Skip ignored HTTP methods
        if request.method in self.ignored_methods:
            return False
        
        # Skip ignored paths
        path = request.path
        if any(re.match(pattern, path) for pattern in self.ignored_paths):
            return False
        
        # Only track successful responses
        if not (200 <= response.status_code < 300):
            return False
        
        # Skip AJAX/API requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return False
            
        return True
    
    def track_page_view(self, request):
        """Track a page view activity."""
        try:
            # Get the view name if available
            view_name = None
            if hasattr(request, 'resolver_match') and request.resolver_match:
                view_name = (
                    request.resolver_match.view_name
                    or request.resolver_match.url_name
                    or request.resolver_match._func_path
                )
            
            # Get the referring page
            referrer = request.META.get('HTTP_REFERER')
            
            # Track the activity
            ActivityTracker.track_activity(
                user=request.user,
                activity_type=ActivityType.PAGE_VIEW,
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'view': view_name,
                    'referrer': referrer,
                    'query_params': dict(request.GET),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'ip_address': self.get_client_ip(request),
                }
            )
            
        except Exception as e:
            # Don't let tracking failures affect the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error tracking page view: {e}", exc_info=True)
    
    @staticmethod
    def get_client_ip(request):
        ""Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
