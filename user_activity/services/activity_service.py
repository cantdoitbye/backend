from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from user_activity.models import (
    UserActivity,
    ContentInteraction,
    ProfileActivity,
    MediaInteraction,
    SocialInteraction,
    SessionActivity,
    ActivityAggregation,
    VibeActivity
)
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for handling activity tracking and analytics."""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    @staticmethod
    def track_content_interaction_by_id(user_id: str, content_type: str, 
                                      interaction_type: str, content_id: str = None,
                                      metadata: Dict[str, Any] = None) -> bool:
        """Static method to track content interaction by user_id."""
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            service = ActivityService()
            return service._track_content_interaction_instance(
                user=user,
                content_type=content_type,
                content_id=content_id or f"{content_type}_{user_id}",
                interaction_type=interaction_type,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Failed to track content interaction for user {user_id}: {e}")
            return False
    
    def track_activity_async(self, user: User, activity_type: str, 
                           description: str = None, success: bool = True,
                           ip_address: str = None, user_agent: str = None,
                           metadata: Dict[str, Any] = None) -> bool:
        """Track user activity asynchronously."""
        try:
            # Use Celery task if available, otherwise execute synchronously
            if self._is_celery_available():
                from user_activity.tasks import track_user_activity_task
                track_user_activity_task.delay(
                    user_id=user.id,
                    activity_type=activity_type,
                    description=description,
                    success=success,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            else:
                self.track_activity_sync(
                    user=user,
                    activity_type=activity_type,
                    description=description,
                    success=success,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata
                )
            return True
        except Exception as e:
            logger.error(f"Failed to track activity asynchronously: {e}")
            return False
    
    def track_activity_sync(self, user: User, activity_type: str,
                          description: str = None, success: bool = True,
                          ip_address: str = None, user_agent: str = None,
                          metadata: Dict[str, Any] = None) -> Optional[UserActivity]:
        """Track user activity synchronously."""
        try:
            activity = UserActivity.objects.create(
                user=user,
                activity_type=activity_type,
                description=description,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            # Update daily aggregation
            self._update_daily_aggregation(user, activity_type)
            
            return activity
        except Exception as e:
            logger.error(f"Failed to track activity synchronously: {e}")
            return None
    
    def _track_content_interaction_instance(self, user: User, content_type: str, content_id: str,
                                          interaction_type: str, duration_seconds: int = None,
                                          scroll_depth_percentage: float = None,
                                          ip_address: str = None, user_agent: str = None,
                                          metadata: Dict[str, Any] = None) -> bool:
        """Track content interaction."""
        try:
            if self._is_celery_available():
                from user_activity.tasks import track_content_interaction_task
                track_content_interaction_task.delay(
                    user_id=user.id,
                    content_type=content_type,
                    content_id=content_id,
                    interaction_type=interaction_type,
                    duration_seconds=duration_seconds,
                    scroll_depth_percentage=scroll_depth_percentage,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            else:
                ContentInteraction.objects.create(
                    user=user,
                    content_type=content_type,
                    content_id=content_id,
                    interaction_type=interaction_type,
                    duration_seconds=duration_seconds,
                    scroll_depth_percentage=scroll_depth_percentage,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            
            # Update engagement cache
            self._update_engagement_cache(user, content_type, interaction_type)
            
            return True
        except Exception as e:
            logger.error(f"Failed to track content interaction: {e}")
            return False
    
    def track_profile_activity(self, visitor: User, profile_owner: User,
                             activity_type: str, duration_seconds: int = None,
                             ip_address: str = None, user_agent: str = None,
                             metadata: Dict[str, Any] = None) -> bool:
        """Track profile activity."""
        try:
            if self._is_celery_available():
                from user_activity.tasks import track_profile_activity_task
                track_profile_activity_task.delay(
                    visitor_id=visitor.id,
                    profile_owner_id=profile_owner.id,
                    activity_type=activity_type,
                    duration_seconds=duration_seconds,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            else:
                ProfileActivity.objects.create(
                    visitor=visitor,
                    profile_owner=profile_owner,
                    activity_type=activity_type,
                    duration_seconds=duration_seconds,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to track profile activity: {e}")
            return False
    
    def track_media_interaction(self, user: User, media_type: str, media_id: str,
                              interaction_type: str, duration_seconds: int = None,
                              position_seconds: int = None, media_url: str = None,
                              ip_address: str = None, user_agent: str = None,
                              metadata: Dict[str, Any] = None) -> bool:
        """Track media interaction."""
        try:
            if self._is_celery_available():
                from user_activity.tasks import track_media_interaction_task
                track_media_interaction_task.delay(
                    user_id=user.id,
                    media_type=media_type,
                    media_id=media_id,
                    interaction_type=interaction_type,
                    duration_seconds=duration_seconds,
                    position_seconds=position_seconds,
                    media_url=media_url,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            else:
                MediaInteraction.objects.create(
                    user=user,
                    media_type=media_type,
                    media_id=media_id,
                    interaction_type=interaction_type,
                    duration_seconds=duration_seconds,
                    position_seconds=position_seconds,
                    media_url=media_url,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to track media interaction: {e}")
            return False
    
    def track_social_interaction(self, user: User, target_user: User = None,
                               interaction_type: str = None, context_type: str = None,
                               context_id: str = None, ip_address: str = None,
                               user_agent: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Track social interaction."""
        try:
            if self._is_celery_available():
                from user_activity.tasks import track_social_interaction_task
                track_social_interaction_task.delay(
                    user_id=user.id,
                    target_user_id=target_user.id if target_user else None,
                    interaction_type=interaction_type,
                    context_type=context_type,
                    context_id=context_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            else:
                SocialInteraction.objects.create(
                    user=user,
                    target_user=target_user,
                    interaction_type=interaction_type,
                    context_type=context_type,
                    context_id=context_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata or {}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to track social interaction: {e}")
            return False
    
    def get_user_activity_summary(self, user: User, time_range: str = 'week') -> Dict[str, Any]:
        """Get user activity summary for a given time range."""
        cache_key = f"user_activity_summary_{user.id}_{time_range}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Calculate date range
            end_date = timezone.now().date()
            if time_range == 'day':
                start_date = end_date
            elif time_range == 'week':
                start_date = end_date - timedelta(days=7)
            elif time_range == 'month':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            # Get aggregated data
            aggregation = ActivityAggregation.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date
            ).first()
            
            if aggregation:
                result = {
                    'activity_counts': aggregation.activity_counts,
                    'engagement_score': aggregation.engagement_score,
                    'time_range': time_range,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            else:
                # Calculate on-the-fly if no aggregation exists
                result = self._calculate_activity_summary(user, start_date, end_date, time_range)
            
            cache.set(cache_key, result, self.cache_timeout)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user activity summary: {e}")
            return {}
    
    def get_engagement_trends(self, user: User, period: str = 'daily') -> Dict[str, Any]:
        """Get user engagement trends."""
        cache_key = f"engagement_trends_{user.id}_{period}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Get last 30 days of data
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            aggregations = ActivityAggregation.objects.filter(
                user=user,
                aggregation_type='daily',
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            
            trends = {
                'dates': [],
                'engagement_scores': [],
                'activity_counts': [],
                'period': period
            }
            
            for agg in aggregations:
                trends['dates'].append(agg.date.isoformat())
                trends['engagement_scores'].append(agg.engagement_score)
                trends['activity_counts'].append(sum(agg.activity_counts.values()))
            
            cache.set(cache_key, trends, self.cache_timeout)
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get engagement trends: {e}")
            return {}
    
    def _update_daily_aggregation(self, user: User, activity_type: str):
        """Update daily activity aggregation."""
        try:
            today = timezone.now().date()
            aggregation, created = ActivityAggregation.objects.get_or_create(
                user=user,
                aggregation_type='daily',
                date=today,
                defaults={'activity_counts': {}}
            )
            
            # Update activity count
            if activity_type in aggregation.activity_counts:
                aggregation.activity_counts[activity_type] += 1
            else:
                aggregation.activity_counts[activity_type] = 1
            
            # Recalculate engagement score
            aggregation.engagement_score = self._calculate_engagement_score(aggregation.activity_counts)
            aggregation.save()
            
        except Exception as e:
            logger.error(f"Failed to update daily aggregation: {e}")
    
    def _update_engagement_cache(self, user: User, content_type: str, interaction_type: str):
        """Update engagement cache for real-time analytics."""
        try:
            cache_key = f"user_engagement_{user.id}"
            engagement_data = cache.get(cache_key, {})
            
            # Update interaction counts
            key = f"{content_type}_{interaction_type}"
            engagement_data[key] = engagement_data.get(key, 0) + 1
            engagement_data['last_activity'] = timezone.now().isoformat()
            
            cache.set(cache_key, engagement_data, 3600)  # 1 hour
            
        except Exception as e:
            logger.error(f"Failed to update engagement cache: {e}")
    
    def _calculate_activity_summary(self, user: User, start_date, end_date, time_range: str) -> Dict[str, Any]:
        """Calculate activity summary on-the-fly."""
        activities = UserActivity.objects.filter(
            user=user,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )
        
        content_interactions = ContentInteraction.objects.filter(
            user=user,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )
        
        activity_counts = {}
        
        # Count user activities
        for activity in activities:
            activity_counts[activity.activity_type] = activity_counts.get(activity.activity_type, 0) + 1
        
        # Count content interactions
        for interaction in content_interactions:
            key = f"{interaction.content_type}_{interaction.interaction_type}"
            activity_counts[key] = activity_counts.get(key, 0) + 1
        
        engagement_score = self._calculate_engagement_score(activity_counts)
        
        return {
            'activity_counts': activity_counts,
            'engagement_score': engagement_score,
            'time_range': time_range,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    def _calculate_engagement_score(self, activity_counts: Dict[str, int]) -> float:
        """Calculate engagement score based on activity counts."""
        # Weighted scoring system
        weights = {
            'login': 1.0,
            'post_create': 5.0,
            'post_like': 2.0,
            'post_comment': 3.0,
            'post_share': 4.0,
            'story_view': 1.5,
            'story_create': 4.0,
            'profile_view': 1.0,
            'connection_request': 3.0,
            'message_send': 2.5,
        }
        
        score = 0.0
        for activity_type, count in activity_counts.items():
            weight = weights.get(activity_type, 1.0)
            score += count * weight
        
        return round(score, 2)
    
    @staticmethod
    def track_content_interaction(user, content_type, content_id, interaction_type, **kwargs):
        """
        Track content interaction activity.
        
        Args:
            user: User object who performed the interaction
            content_type: Type of content (e.g., 'post', 'story', 'comment')
            content_id: ID of the content
            interaction_type: Type of interaction (e.g., 'like', 'share', 'view')
            **kwargs: Additional metadata
            
        Returns:
            UserActivity: Created activity record or None if failed
        """
        try:
            # Handle user_id if passed instead of User object
            if isinstance(user, str):
                user = User.objects.get(id=user)
            elif hasattr(user, 'user_id'):
                user = User.objects.get(id=user.user_id)
            
            # Create metadata
            metadata = {
                'content_type': content_type,
                'content_id': str(content_id),
                'interaction_type': interaction_type
            }
            metadata.update(kwargs.get('metadata', {}))
            
            # Create content interaction record
            from user_activity.models import ContentInteraction
            activity = ContentInteraction.objects.create(
                user=user,
                content_type=content_type,
                content_id=str(content_id),
                interaction_type=interaction_type,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                metadata=metadata
            )
            
            logger.info(f"Tracked content interaction: {user.username} {interaction_type} {content_type} {content_id}")
            return activity
            
        except Exception as e:
            logger.error(f"Failed to track content interaction: {str(e)}")
            return None
    
    @staticmethod
    async def track_content_interaction_async(user, content_type, content_id, interaction_type, **kwargs):
        """
        Async version of track_content_interaction.
        
        Args:
            user: User object who performed the interaction
            content_type: Type of content (e.g., 'post', 'story', 'comment')
            content_id: ID of the content
            interaction_type: Type of interaction (e.g., 'like', 'share', 'view')
            **kwargs: Additional metadata
            
        Returns:
            UserActivity: Created activity record or None if failed
        """
        try:
            from asgiref.sync import sync_to_async
            
            # Handle user_id if passed instead of User object
            if isinstance(user, str):
                user = await sync_to_async(User.objects.get)(id=user)
            elif hasattr(user, 'user_id'):
                user = await sync_to_async(User.objects.get)(id=user.user_id)
            
            # Create metadata
            metadata = {
                'content_type': content_type,
                'content_id': str(content_id),
                'interaction_type': interaction_type
            }
            metadata.update(kwargs.get('metadata', {}))
            
            # Create activity record
            activity = await sync_to_async(UserActivity.objects.create)(
                user=user,
                activity_type=f'{content_type}_{interaction_type}',
                content_type=content_type,
                content_id=str(content_id),
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                metadata=metadata
            )
            
            logger.info(f"Tracked content interaction async: {user.username} {interaction_type} {content_type} {content_id}")
            return activity
            
        except Exception as e:
            logger.error(f"Failed to track content interaction async: {str(e)}")
            return None

    def get_comprehensive_analytics(self, user: User = None, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics including vibe activities."""
        try:
            # Import here to avoid circular imports
            from vibe_manager.services.vibe_analytics_service import VibeAnalyticsService
            
            # Get regular activity summary
            time_range = 'month' if days >= 30 else 'week'
            regular_analytics = self.get_user_activity_summary(user, time_range)
            
            # Get vibe analytics
            vibe_analytics = VibeAnalyticsService.get_vibe_activity_summary(user, days)
            vibe_engagement = VibeAnalyticsService.get_vibe_engagement_metrics(user, days)
            
            # Combine analytics
            return {
                'user_analytics': regular_analytics,
                'vibe_analytics': vibe_analytics,
                'vibe_engagement': vibe_engagement,
                'combined_summary': {
                    'total_activities': (
                        regular_analytics.get('total_activities', 0) + 
                        vibe_analytics.get('overview', {}).get('total_activities', 0)
                    ),
                    'period_days': days,
                    'analysis_timestamp': timezone.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get comprehensive analytics: {e}")
            return {
                'error': 'Failed to generate comprehensive analytics',
                'message': str(e)
            }
    
    def get_vibe_activity_insights(self, user: User = None, days: int = 30) -> Dict[str, Any]:
        """Get detailed vibe activity insights."""
        try:
            from vibe_manager.services.vibe_analytics_service import VibeAnalyticsService
            
            return {
                'activity_summary': VibeAnalyticsService.get_vibe_activity_summary(user, days),
                'creation_analytics': VibeAnalyticsService.get_vibe_creation_analytics(user, days),
                'engagement_metrics': VibeAnalyticsService.get_vibe_engagement_metrics(user, days),
                'real_time_stats': VibeAnalyticsService.get_real_time_vibe_stats() if not user else None
            }
        except Exception as e:
            logger.error(f"Failed to get vibe activity insights: {e}")
            return {
                'error': 'Failed to generate vibe insights',
                'message': str(e)
            }
    
    def track_profile_visit(self, visitor: User, profile_owner: User, 
                           duration_seconds: int = None, ip_address: str = None, 
                           user_agent: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Track profile visit as both profile activity and social interaction."""
        try:
            # Track as profile activity
            self.track_profile_activity(
                visitor=visitor,
                profile_owner=profile_owner,
                activity_type='profile_view',
                duration_seconds=duration_seconds,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata
            )
            
            # Track as social interaction
            self.track_social_interaction(
                user=visitor,
                target_user=profile_owner,
                interaction_type='profile_visit',
                context_type='profile',
                context_id=str(profile_owner.id),
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to track profile visit: {e}")
            return False
    
    def _is_celery_available(self) -> bool:
        """Check if Celery is available for async tasks."""
        try:
            from celery import current_app
            return current_app.control.inspect().stats() is not None
        except ImportError:
            return False
        except Exception:
            return False