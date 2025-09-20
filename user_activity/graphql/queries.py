import graphene
from graphene import String, Int, Float, Boolean, List, DateTime
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
from user_activity.models import (
    UserActivity,
    ContentInteraction,
    ProfileActivity,
    MediaInteraction,
    SocialInteraction,
    SessionActivity,
    ActivityAggregation
)
from user_activity.graphql.types import (
    UserActivityType,
    ContentInteractionType,
    ProfileActivityType,
    MediaInteractionType,
    SocialInteractionType,
    SessionActivityType,
    UserActivitySummaryType,
    EngagementTrendsType,
    ActivityAnalyticsType,
    TimeRangeInput,
    ContentTypeEnum
)
from user_activity.services.activity_service import ActivityService
import logging

logger = logging.getLogger(__name__)


class Query(graphene.ObjectType):
    # Basic activity queries
    user_activities = List(
        UserActivityType,
        user_id=String(),
        activity_type=String(),
        limit=Int(default_value=50),
        offset=Int(default_value=0)
    )
    
    content_interactions = List(
        ContentInteractionType,
        user_id=String(),
        content_type=ContentTypeEnum(),
        content_id=String(),
        limit=Int(default_value=50),
        offset=Int(default_value=0)
    )
    
    profile_activities = List(
        ProfileActivityType,
        visitor_id=String(),
        profile_owner_id=String(),
        limit=Int(default_value=50),
        offset=Int(default_value=0)
    )
    
    media_interactions = List(
        MediaInteractionType,
        user_id=String(),
        media_type=String(),
        limit=Int(default_value=50),
        offset=Int(default_value=0)
    )
    
    social_interactions = List(
        SocialInteractionType,
        user_id=String(),
        target_user_id=String(),
        interaction_type=String(),
        limit=Int(default_value=50),
        offset=Int(default_value=0)
    )
    
    session_activities = List(
        SessionActivityType,
        user_id=String(),
        limit=Int(default_value=50),
        offset=Int(default_value=0)
    )
    
    # Analytics queries
    user_activity_summary = graphene.Field(
        UserActivitySummaryType,
        user_id=String(),
        time_range=graphene.Argument(TimeRangeInput)
    )
    
    user_engagement_trends = graphene.Field(
        EngagementTrendsType,
        user_id=String(required=True),
        period=String(required=True)
    )
    
    activity_analytics = graphene.Field(
        ActivityAnalyticsType,
        time_range=graphene.Argument(TimeRangeInput)
    )
    
    # Content performance queries
    popular_content = List(
        graphene.JSONString,
        content_type=ContentTypeEnum(),
        time_range=graphene.Argument(TimeRangeInput),
        limit=Int(default_value=10)
    )
    
    user_engagement_score = Float(
        user_id=String(required=True),
        time_range=graphene.Argument(TimeRangeInput)
    )
    
    # Resolvers
    def resolve_user_activities(self, info, user_id=None, activity_type=None, limit=50, offset=0):
        try:
            queryset = UserActivity.objects.all()
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            if activity_type:
                queryset = queryset.filter(activity_type=activity_type)
            
            return queryset.order_by('-timestamp')[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Error resolving user activities: {e}")
            return []
    
    def resolve_content_interactions(self, info, user_id=None, content_type=None, 
                                   content_id=None, limit=50, offset=0):
        try:
            queryset = ContentInteraction.objects.all()
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            if content_type:
                queryset = queryset.filter(content_type=content_type)
            
            if content_id:
                queryset = queryset.filter(content_id=content_id)
            
            return queryset.order_by('-timestamp')[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Error resolving content interactions: {e}")
            return []
    
    def resolve_profile_activities(self, info, visitor_id=None, profile_owner_id=None, 
                                 limit=50, offset=0):
        try:
            queryset = ProfileActivity.objects.all()
            
            if visitor_id:
                queryset = queryset.filter(visitor_id=visitor_id)
            
            if profile_owner_id:
                queryset = queryset.filter(profile_owner_id=profile_owner_id)
            
            return queryset.order_by('-timestamp')[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Error resolving profile activities: {e}")
            return []
    
    def resolve_media_interactions(self, info, user_id=None, media_type=None, 
                                 limit=50, offset=0):
        try:
            queryset = MediaInteraction.objects.all()
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            if media_type:
                queryset = queryset.filter(media_type=media_type)
            
            return queryset.order_by('-timestamp')[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Error resolving media interactions: {e}")
            return []
    
    def resolve_social_interactions(self, info, user_id=None, target_user_id=None, 
                                  interaction_type=None, limit=50, offset=0):
        try:
            queryset = SocialInteraction.objects.all()
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            if target_user_id:
                queryset = queryset.filter(target_user_id=target_user_id)
            
            if interaction_type:
                queryset = queryset.filter(interaction_type=interaction_type)
            
            return queryset.order_by('-timestamp')[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Error resolving social interactions: {e}")
            return []
    
    def resolve_session_activities(self, info, user_id=None, limit=50, offset=0):
        try:
            queryset = SessionActivity.objects.all()
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            return queryset.order_by('-start_time')[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Error resolving session activities: {e}")
            return []
    
    def resolve_user_activity_summary(self, info, user_id=None, time_range=None):
        try:
            # Use current user if no user_id provided
            if not user_id:
                user = info.context.user
                if not user.is_authenticated:
                    return None
                user_id = user.id
            
            # Set default time range if not provided
            if not time_range:
                end_date = timezone.now()
                start_date = end_date - timedelta(days=30)
            else:
                start_date = time_range.start_date
                end_date = time_range.end_date
            
            activity_service = ActivityService()
            summary = activity_service.get_activity_summary(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return summary
        
        except Exception as e:
            logger.error(f"Error resolving user activity summary: {e}")
            return None
    
    def resolve_user_engagement_trends(self, info, user_id, period):
        try:
            activity_service = ActivityService()
            trends = activity_service.get_engagement_trends(
                user_id=user_id,
                period=period
            )
            
            return trends
        
        except Exception as e:
            logger.error(f"Error resolving user engagement trends: {e}")
            return None
    
    def resolve_activity_analytics(self, info, time_range=None):
        try:
            # Set default time range if not provided
            if not time_range:
                end_date = timezone.now()
                start_date = end_date - timedelta(days=30)
            else:
                start_date = time_range.start_date
                end_date = time_range.end_date
            
            # Calculate various analytics
            total_users = User.objects.filter(
                useractivity__timestamp__range=[start_date, end_date]
            ).distinct().count()
            
            total_activities = UserActivity.objects.filter(
                timestamp__range=[start_date, end_date]
            ).count()
            
            total_content_interactions = ContentInteraction.objects.filter(
                timestamp__range=[start_date, end_date]
            ).count()
            
            total_social_interactions = SocialInteraction.objects.filter(
                timestamp__range=[start_date, end_date]
            ).count()
            
            avg_session_duration = SessionActivity.objects.filter(
                start_time__range=[start_date, end_date],
                end_time__isnull=False
            ).aggregate(
                avg_duration=Avg('duration_seconds')
            )['avg_duration'] or 0
            
            # Most active users
            most_active_users = User.objects.filter(
                useractivity__timestamp__range=[start_date, end_date]
            ).annotate(
                activity_count=Count('useractivity')
            ).order_by('-activity_count')[:10]
            
            # Popular content types
            popular_content_types = ContentInteraction.objects.filter(
                timestamp__range=[start_date, end_date]
            ).values('content_type').annotate(
                interaction_count=Count('id')
            ).order_by('-interaction_count')
            
            return {
                'total_users': total_users,
                'total_activities': total_activities,
                'total_content_interactions': total_content_interactions,
                'total_social_interactions': total_social_interactions,
                'avg_session_duration': avg_session_duration,
                'most_active_users': [{
                    'user_id': str(user.id),
                    'username': user.username,
                    'activity_count': user.activity_count
                } for user in most_active_users],
                'popular_content_types': list(popular_content_types)
            }
        
        except Exception as e:
            logger.error(f"Error resolving activity analytics: {e}")
            return None
    
    def resolve_popular_content(self, info, content_type=None, time_range=None, limit=10):
        try:
            # Set default time range if not provided
            if not time_range:
                end_date = timezone.now()
                start_date = end_date - timedelta(days=7)
            else:
                start_date = time_range.start_date
                end_date = time_range.end_date
            
            queryset = ContentInteraction.objects.filter(
                timestamp__range=[start_date, end_date]
            )
            
            if content_type:
                queryset = queryset.filter(content_type=content_type)
            
            popular_content = queryset.values(
                'content_id', 'content_type'
            ).annotate(
                interaction_count=Count('id'),
                unique_users=Count('user', distinct=True),
                avg_duration=Avg('duration_seconds'),
                avg_scroll_depth=Avg('scroll_depth_percentage')
            ).order_by('-interaction_count')[:limit]
            
            return [{
                'content_id': item['content_id'],
                'content_type': item['content_type'],
                'interaction_count': item['interaction_count'],
                'unique_users': item['unique_users'],
                'avg_duration': item['avg_duration'] or 0,
                'avg_scroll_depth': item['avg_scroll_depth'] or 0
            } for item in popular_content]
        
        except Exception as e:
            logger.error(f"Error resolving popular content: {e}")
            return []
    
    def resolve_user_engagement_score(self, info, user_id, time_range=None):
        try:
            # Set default time range if not provided
            if not time_range:
                end_date = timezone.now()
                start_date = end_date - timedelta(days=30)
            else:
                start_date = time_range.start_date
                end_date = time_range.end_date
            
            activity_service = ActivityService()
            engagement_score = activity_service.calculate_engagement_score(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return engagement_score
        
        except Exception as e:
            logger.error(f"Error resolving user engagement score: {e}")
            return 0.0