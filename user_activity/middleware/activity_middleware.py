import time
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from user_activity.models import UserActivity, SessionActivity
from user_activity.services.activity_service import ActivityService
import logging

logger = logging.getLogger(__name__)


class ActivityTrackingMiddleware(MiddlewareMixin):
    """Middleware to track user activities at the request level."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.activity_service = ActivityService()
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming request and set up activity tracking."""
        request.activity_start_time = time.time()
        request.activity_data = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
        }
        
        # Track session activity for authenticated users
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            self.track_session_activity(request)
    
    def process_response(self, request, response):
        """Process response and log activity data."""
        if hasattr(request, 'activity_start_time'):
            duration = time.time() - request.activity_start_time
            
            # Add response data to activity tracking
            request.activity_data.update({
                'response_status': response.status_code,
                'duration_ms': int(duration * 1000),
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
            })
            
            # Track navigation activity for authenticated users
            if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
                self.track_navigation_activity(request, response)
        
        return response
    
    def process_exception(self, request, exception):
        """Process exceptions and log error activities."""
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            try:
                self.activity_service.track_activity_async(
                    user=request.user,
                    activity_type='error',
                    description=f"Exception: {str(exception)}",
                    success=False,
                    ip_address=request.activity_data.get('ip_address'),
                    user_agent=request.activity_data.get('user_agent'),
                    metadata={
                        'exception_type': type(exception).__name__,
                        'path': request.path,
                        'method': request.method,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to track error activity: {e}")
    
    def track_session_activity(self, request):
        """Track or update session activity."""
        try:
            session_id = request.session.session_key
            if not session_id:
                # Create session if it doesn't exist
                request.session.create()
                session_id = request.session.session_key
            
            # Get or create session activity
            session_activity, created = SessionActivity.objects.get_or_create(
                user=request.user,
                session_id=session_id,
                end_time__isnull=True,  # Active session
                defaults={
                    'session_type': self.detect_session_type(request),
                    'ip_address': request.activity_data['ip_address'],
                    'user_agent': request.activity_data['user_agent'],
                    'referrer': request.activity_data.get('referer'),
                    'device_info': self.extract_device_info(request),
                }
            )
            
            if not created:
                # Update existing session
                session_activity.pages_visited += 1
                session_activity.save(update_fields=['pages_visited', 'updated_at'])
            
            request.session_activity = session_activity
            
        except Exception as e:
            logger.error(f"Failed to track session activity: {e}")
    
    def track_navigation_activity(self, request, response):
        """Track navigation patterns."""
        try:
            # Only track successful page loads
            if 200 <= response.status_code < 400:
                self.activity_service.track_activity_async(
                    user=request.user,
                    activity_type='navigation',
                    description=f"Visited {request.path}",
                    ip_address=request.activity_data['ip_address'],
                    user_agent=request.activity_data['user_agent'],
                    metadata={
                        'path': request.path,
                        'method': request.method,
                        'duration_ms': request.activity_data.get('duration_ms'),
                        'referer': request.activity_data.get('referer'),
                        'query_params': request.activity_data.get('query_params'),
                    }
                )
                
                # Update session activity with current page
                if hasattr(request, 'session_activity'):
                    request.session_activity.actions_performed += 1
                    request.session_activity.save(update_fields=['actions_performed', 'updated_at'])
        
        except Exception as e:
            logger.error(f"Failed to track navigation activity: {e}")
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def detect_session_type(self, request):
        """Detect session type based on user agent and other factors."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif request.path.startswith('/admin/'):
            return 'admin'
        elif 'api' in request.path or request.content_type == 'application/json':
            return 'api'
        else:
            return 'web'
    
    def extract_device_info(self, request):
        """Extract device information from user agent."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        device_info = {
            'user_agent': user_agent,
            'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
        }
        
        # Basic device detection
        user_agent_lower = user_agent.lower()
        if 'mobile' in user_agent_lower:
            device_info['device_type'] = 'mobile'
        elif 'tablet' in user_agent_lower:
            device_info['device_type'] = 'tablet'
        else:
            device_info['device_type'] = 'desktop'
        
        # Browser detection
        if 'chrome' in user_agent_lower:
            device_info['browser'] = 'chrome'
        elif 'firefox' in user_agent_lower:
            device_info['browser'] = 'firefox'
        elif 'safari' in user_agent_lower:
            device_info['browser'] = 'safari'
        elif 'edge' in user_agent_lower:
            device_info['browser'] = 'edge'
        else:
            device_info['browser'] = 'unknown'
        
        return device_info


class SessionCleanupMiddleware(MiddlewareMixin):
    """Middleware to handle session cleanup and end time tracking."""
    
    def process_request(self, request):
        """Mark session end time for logout requests."""
        if (request.path.endswith('/logout/') or 
            (request.method == 'POST' and 'logout' in request.path)):
            
            if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
                try:
                    # Mark current session as ended
                    session_id = request.session.session_key
                    if session_id:
                        SessionActivity.objects.filter(
                            user=request.user,
                            session_id=session_id,
                            end_time__isnull=True
                        ).update(
                            end_time=timezone.now(),
                            exit_page=request.META.get('HTTP_REFERER', request.path)
                        )
                except Exception as e:
                    logger.error(f"Failed to cleanup session: {e}")