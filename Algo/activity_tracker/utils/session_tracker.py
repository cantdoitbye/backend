import time
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, F, Q, Sum, Case, When, IntegerField
from django.db.models.functions import TruncDay, TruncHour, ExtractHour, ExtractDayOfWeek

from activity_tracker.models import UserActivity, UserEngagementScore

User = get_user_model()

class SessionTracker:
    """
    Tracks user sessions and engagement over time.
    
    A session is defined as a period of user activity with no more than
    SESSION_TIMEOUT seconds of inactivity.
    """
    SESSION_TIMEOUT = getattr(settings, 'SESSION_TIMEOUT', 30 * 60)  # 30 minutes
    SESSION_KEY_PREFIX = 'user_session_'
    
    @classmethod
    def update_session(cls, user):
        """
        Update or create a user session.
        
        Args:
            user: The user whose session to update
            
        Returns:
            dict: Session data including session_id, start_time, last_activity, etc.
        """
        if not user or not user.is_authenticated:
            return None
            
        now = timezone.now()
        cache_key = f"{cls.SESSION_KEY_PREFIX}{user.id}"
        
        # Get existing session or create a new one
        session = cache.get(cache_key)
        
        if session:
            # Update last activity time
            session['last_activity'] = now.isoformat()
            session['duration'] = (now - datetime.fromisoformat(session['start_time'])).total_seconds()
            session['activity_count'] = session.get('activity_count', 0) + 1
            
            # Extend session expiry
            cache.set(cache_key, session, cls.SESSION_TIMEOUT)
        else:
            # Create new session
            session = {
                'session_id': f"{user.id}_{int(time.time())}",
                'user_id': user.id,
                'start_time': now.isoformat(),
                'last_activity': now.isoformat(),
                'duration': 0,
                'activity_count': 1,
                'device_info': getattr(user, 'device_info', {}),
                'ip_address': getattr(user, 'ip_address', None)
            }
            cache.set(cache_key, session, cls.SESSION_TIMEOUT)
            
            # Record session start
            cls._record_session_event(user, 'session_start', session)
        
        return session
    
    @classmethod
    def end_session(cls, user):
        """
        End a user session.
        
        Args:
            user: The user whose session to end
            
        Returns:
            dict: The ended session data, or None if no session was active
        """
        if not user or not user.is_authenticated:
            return None
            
        cache_key = f"{cls.SESSION_KEY_PREFIX}{user.id}"
        session = cache.get(cache_key)
        
        if session:
            # Update session end time and duration
            now = timezone.now()
            start_time = datetime.fromisoformat(session['start_time'])
            session['end_time'] = now.isoformat()
            session['duration'] = (now - start_time).total_seconds()
            
            # Record session end
            cls._record_session_event(user, 'session_end', session)
            
            # Clear the session from cache
            cache.delete(cache_key)
            
            return session
        
        return None
    
    @classmethod
    def get_active_sessions(cls, user_ids=None):
        """
        Get all active sessions.
        
        Args:
            user_ids: Optional list of user IDs to filter by
            
        Returns:
            list: List of active session dictionaries
        """
        if user_ids and not isinstance(user_ids, (list, tuple, set)):
            user_ids = [user_ids]
        
        # In a production environment, you'd use a more efficient method to get all sessions
        # This is a simplified version that works with Django's cache backend
        active_sessions = []
        
        if user_ids:
            for user_id in user_ids:
                cache_key = f"{cls.SESSION_KEY_PREFIX}{user_id}"
                session = cache.get(cache_key)
                if session:
                    active_sessions.append(session)
        
        return active_sessions
    
    @classmethod
    def get_user_session_stats(cls, user):
        """
        Get session statistics for a user.
        
        Args:
            user: The user to get stats for
            
        Returns:
            dict: Session statistics
        """
        if not user or not user.is_authenticated:
            return {}
        
        # Get recent sessions (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_sessions = (
            UserActivity.objects
            .filter(
                user=user,
                activity_type='session_end',
                created_at__gte=thirty_days_ago
            )
            .order_by('-created_at')
        )
        
        # Calculate stats
        total_sessions = recent_sessions.count()
        
        if total_sessions == 0:
            return {
                'total_sessions': 0,
                'avg_session_duration': 0,
                'sessions_last_30_days': 0,
                'avg_sessions_per_day': 0,
                'preferred_session_times': {},
                'activity_by_day': {}
            }
        
        # Calculate average session duration
        avg_duration = recent_sessions.aggregate(
            avg_duration=Avg('metadata__duration')
        )['avg_duration'] or 0
        
        # Calculate sessions per day
        sessions_by_day = (
            recent_sessions
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        
        # Calculate preferred session times
        preferred_times = (
            recent_sessions
            .annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Calculate activity by day of week
        activity_by_day = (
            recent_sessions
            .annotate(day_of_week=ExtractDayOfWeek('created_at'))
            .values('day_of_week')
            .annotate(count=Count('id'))
            .order_by('day_of_week')
        )
        
        # Format results
        return {
            'total_sessions': total_sessions,
            'avg_session_duration': avg_duration,
            'sessions_last_30_days': total_sessions,
            'avg_sessions_per_day': total_sessions / 30,  # Last 30 days
            'preferred_session_times': {
                f"{item['hour']:02d}:00": item['count'] 
                for item in preferred_times[:5]  # Top 5 hours
            },
            'activity_by_day': {
                item['day_of_week']: item['count'] 
                for item in activity_by_day
            }
        }
    
    @classmethod
    def _record_session_event(cls, user, event_type, session_data):
        """Record a session event in the database."""
        from activity_tracker.handlers import ActivityTracker
        
        metadata = {
            'event_type': event_type,
            'session_id': session_data.get('session_id'),
            'duration': session_data.get('duration', 0),
            'activity_count': session_data.get('activity_count', 1),
            'device_info': session_data.get('device_info', {}),
            'ip_address': session_data.get('ip_address')
        }
        
        # Add start/end times if available
        if 'start_time' in session_data:
            metadata['start_time'] = session_data['start_time']
        if 'end_time' in session_data:
            metadata['end_time'] = session_data['end_time']
        
        # Record the event
        ActivityTracker.track_activity(
            user=user,
            activity_type=event_type.upper(),
            metadata=metadata
        )


class EngagementAnalyzer:
    """
    Analyzes user engagement patterns and provides insights.
    """
    @classmethod
    def get_engagement_trends(cls, user, days=30):
        """
        Get engagement trends for a user over time.
        
        Args:
            user: The user to analyze
            days: Number of days to look back
            
        Returns:
            dict: Engagement trends data
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get daily activity counts
        daily_activity = (
            UserActivity.objects
            .filter(
                user=user,
                created_at__range=(start_date, end_date)
            )
            .annotate(day=TruncDay('created_at'))
            .values('day', 'activity_type')
            .annotate(count=Count('id'))
            .order_by('day', 'activity_type')
        )
        
        # Format data for charts
        activity_by_day = {}
        activity_types = set()
        
        for item in daily_activity:
            day = item['day'].strftime('%Y-%m-%d')
            activity_type = item['activity_type']
            count = item['count']
            
            if day not in activity_by_day:
                activity_by_day[day] = {}
            
            activity_by_day[day][activity_type] = count
            activity_types.add(activity_type)
        
        # Fill in missing days
        all_days = [
            (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range((end_date - start_date).days + 1)
        ]
        
        # Prepare datasets for charting
        datasets = []
        for activity_type in sorted(activity_types):
            data = []
            for day in all_days:
                data.append(activity_by_day.get(day, {}).get(activity_type, 0))
            
            datasets.append({
                'label': activity_type.replace('_', ' ').title(),
                'data': data
            })
        
        return {
            'labels': all_days,
            'datasets': datasets,
            'activity_types': sorted(activity_types),
            'total_activities': sum(sum(day.values()) for day in activity_by_day.values()),
            'most_active_day': max(activity_by_day.items(), 
                                 key=lambda x: sum(x[1].values()),
                                 default=(None, {}))[0]
        }
    
    @classmethod
    def get_engagement_score_history(cls, user, days=30):
        """
        Get historical engagement scores for a user.
        
        Args:
            user: The user to analyze
            days: Number of days to look back
            
        Returns:
            dict: Engagement score history
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get daily engagement scores
        scores = (
            UserEngagementScore.history
            .filter(
                user=user,
                history_date__range=(start_date, end_date)
            )
            .annotate(day=TruncDay('history_date'))
            .values('day')
            .annotate(
                engagement_score=Avg('engagement_score'),
                content_score=Avg('content_score'),
                social_score=Avg('social_score')
            )
            .order_by('day')
        )
        
        # Format data for charts
        days = []
        engagement_scores = []
        content_scores = []
        social_scores = []
        
        for item in scores:
            days.append(item['day'].strftime('%Y-%m-%d'))
            engagement_scores.append(round(item['engagement_score'], 2))
            content_scores.append(round(item['content_score'], 2))
            social_scores.append(round(item['social_score'], 2))
        
        return {
            'labels': days,
            'datasets': [
                {
                    'label': 'Engagement Score',
                    'data': engagement_scores,
                    'borderColor': '#4e73df',
                    'fill': False
                },
                {
                    'label': 'Content Score',
                    'data': content_scores,
                    'borderColor': '#1cc88a',
                    'fill': False
                },
                {
                    'label': 'Social Score',
                    'data': social_scores,
                    'borderColor': '#f6c23e',
                    'fill': False
                }
            ]
        }
