import graphene
from graphene import String, Int, Float, Boolean, JSONString, DateTime
from django.contrib.auth.models import User
from user_activity.services.activity_service import ActivityService
from user_activity.graphql.types import (
    UserActivityType,
    ContentInteractionType,
    ProfileActivityType,
    MediaInteractionType,
    SocialInteractionType,
    SessionActivityType,
    ContentTypeEnum,
    InteractionTypeEnum,
    ActivityTypeEnum,
    MediaTypeEnum,
    SocialInteractionTypeEnum,
    SessionDataInput
)
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class TrackUserActivity(graphene.Mutation):
    class Arguments:
        activity_type = ActivityTypeEnum(required=True)
        description = String()
        success = Boolean(default_value=True)
        metadata = JSONString()
    
    success = Boolean()
    message = String()
    activity = graphene.Field(UserActivityType)
    
    @staticmethod
    def mutate(root, info, activity_type, description=None, success=True, metadata=None):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return TrackUserActivity(success=False, message="Authentication required")
            
            activity_service = ActivityService()
            request = info.context
            
            # Extract request metadata
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            activity = activity_service.track_activity_sync(
                user=user,
                activity_type=activity_type,
                description=description,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            if activity:
                return TrackUserActivity(
                    success=True,
                    message="Activity tracked successfully",
                    activity=activity
                )
            else:
                return TrackUserActivity(
                    success=False,
                    message="Failed to track activity"
                )
        
        except Exception as e:
            logger.error(f"Error tracking user activity: {e}")
            return TrackUserActivity(
                success=False,
                message=f"Error: {str(e)}"
            )


class TrackContentInteraction(graphene.Mutation):
    class Arguments:
        content_type = ContentTypeEnum(required=True)
        content_id = String(required=True)
        interaction_type = InteractionTypeEnum(required=True)
        duration_seconds = Int()
        scroll_depth_percentage = Float()
        metadata = JSONString()
    
    success = Boolean()
    message = String()
    
    @staticmethod
    def mutate(root, info, content_type, content_id, interaction_type, 
               duration_seconds=None, scroll_depth_percentage=None, metadata=None):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return TrackContentInteraction(success=False, message="Authentication required")
            
            activity_service = ActivityService()
            request = info.context
            
            # Extract request metadata
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            success = activity_service.track_content_interaction(
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
            
            if success:
                return TrackContentInteraction(
                    success=True,
                    message="Content interaction tracked successfully"
                )
            else:
                return TrackContentInteraction(
                    success=False,
                    message="Failed to track content interaction"
                )
        
        except Exception as e:
            logger.error(f"Error tracking content interaction: {e}")
            return TrackContentInteraction(
                success=False,
                message=f"Error: {str(e)}"
            )


class TrackProfileActivity(graphene.Mutation):
    class Arguments:
        profile_owner_id = String(required=True)
        activity_type = String(required=True)
        duration_seconds = Int()
        metadata = JSONString()
    
    success = Boolean()
    message = String()
    
    @staticmethod
    def mutate(root, info, profile_owner_id, activity_type, duration_seconds=None, metadata=None):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return TrackProfileActivity(success=False, message="Authentication required")
            
            try:
                profile_owner = User.objects.get(id=profile_owner_id)
            except User.DoesNotExist:
                return TrackProfileActivity(success=False, message="Profile owner not found")
            
            activity_service = ActivityService()
            request = info.context
            
            # Extract request metadata
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            success = activity_service.track_profile_activity(
                visitor=user,
                profile_owner=profile_owner,
                activity_type=activity_type,
                duration_seconds=duration_seconds,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            if success:
                return TrackProfileActivity(
                    success=True,
                    message="Profile activity tracked successfully"
                )
            else:
                return TrackProfileActivity(
                    success=False,
                    message="Failed to track profile activity"
                )
        
        except Exception as e:
            logger.error(f"Error tracking profile activity: {e}")
            return TrackProfileActivity(
                success=False,
                message=f"Error: {str(e)}"
            )


class TrackMediaInteraction(graphene.Mutation):
    class Arguments:
        media_type = MediaTypeEnum(required=True)
        media_id = String(required=True)
        interaction_type = String(required=True)
        duration_seconds = Int()
        position_seconds = Int()
        media_url = String()
        metadata = JSONString()
    
    success = Boolean()
    message = String()
    
    @staticmethod
    def mutate(root, info, media_type, media_id, interaction_type, 
               duration_seconds=None, position_seconds=None, media_url=None, metadata=None):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return TrackMediaInteraction(success=False, message="Authentication required")
            
            activity_service = ActivityService()
            request = info.context
            
            # Extract request metadata
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            success = activity_service.track_media_interaction(
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
            
            if success:
                return TrackMediaInteraction(
                    success=True,
                    message="Media interaction tracked successfully"
                )
            else:
                return TrackMediaInteraction(
                    success=False,
                    message="Failed to track media interaction"
                )
        
        except Exception as e:
            logger.error(f"Error tracking media interaction: {e}")
            return TrackMediaInteraction(
                success=False,
                message=f"Error: {str(e)}"
            )


class TrackSocialInteraction(graphene.Mutation):
    class Arguments:
        target_user_id = String()
        interaction_type = SocialInteractionTypeEnum(required=True)
        context_type = String()
        context_id = String()
        metadata = JSONString()
    
    success = Boolean()
    message = String()
    
    @staticmethod
    def mutate(root, info, interaction_type, target_user_id=None, 
               context_type=None, context_id=None, metadata=None):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return TrackSocialInteraction(success=False, message="Authentication required")
            
            target_user = None
            if target_user_id:
                try:
                    target_user = User.objects.get(id=target_user_id)
                except User.DoesNotExist:
                    return TrackSocialInteraction(success=False, message="Target user not found")
            
            activity_service = ActivityService()
            request = info.context
            
            # Extract request metadata
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            success = activity_service.track_social_interaction(
                user=user,
                target_user=target_user,
                interaction_type=interaction_type,
                context_type=context_type,
                context_id=context_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            if success:
                return TrackSocialInteraction(
                    success=True,
                    message="Social interaction tracked successfully"
                )
            else:
                return TrackSocialInteraction(
                    success=False,
                    message="Failed to track social interaction"
                )
        
        except Exception as e:
            logger.error(f"Error tracking social interaction: {e}")
            return TrackSocialInteraction(
                success=False,
                message=f"Error: {str(e)}"
            )


class TrackScrollDepth(graphene.Mutation):
    class Arguments:
        post_id = String(required=True)
        depth = Float(required=True)
        content_type = ContentTypeEnum(default_value='post')
    
    success = Boolean()
    message = String()
    
    @staticmethod
    def mutate(root, info, post_id, depth, content_type='post'):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return TrackScrollDepth(success=False, message="Authentication required")
            
            activity_service = ActivityService()
            request = info.context
            
            # Extract request metadata
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            success = activity_service.track_content_interaction(
                user=user,
                content_type=content_type,
                content_id=post_id,
                interaction_type='scroll_depth',
                scroll_depth_percentage=depth,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'scroll_depth': depth}
            )
            
            if success:
                return TrackScrollDepth(
                    success=True,
                    message="Scroll depth tracked successfully"
                )
            else:
                return TrackScrollDepth(
                    success=False,
                    message="Failed to track scroll depth"
                )
        
        except Exception as e:
            logger.error(f"Error tracking scroll depth: {e}")
            return TrackScrollDepth(
                success=False,
                message=f"Error: {str(e)}"
            )


class TrackTimeSpent(graphene.Mutation):
    class Arguments:
        content_id = String(required=True)
        time_ms = Int(required=True)
        content_type = ContentTypeEnum(required=True)
    
    success = Boolean()
    message = String()
    
    @staticmethod
    def mutate(root, info, content_id, time_ms, content_type):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return TrackTimeSpent(success=False, message="Authentication required")
            
            activity_service = ActivityService()
            request = info.context
            
            # Extract request metadata
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            success = activity_service.track_content_interaction(
                user=user,
                content_type=content_type,
                content_id=content_id,
                interaction_type='time_spent',
                duration_seconds=time_ms // 1000,  # Convert to seconds
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'time_ms': time_ms}
            )
            
            if success:
                return TrackTimeSpent(
                    success=True,
                    message="Time spent tracked successfully"
                )
            else:
                return TrackTimeSpent(
                    success=False,
                    message="Failed to track time spent"
                )
        
        except Exception as e:
            logger.error(f"Error tracking time spent: {e}")
            return TrackTimeSpent(
                success=False,
                message=f"Error: {str(e)}"
            )


class TrackAppSession(graphene.Mutation):
    class Arguments:
        session_data = SessionDataInput(required=True)
    
    success = Boolean()
    message = String()
    
    @staticmethod
    def mutate(root, info, session_data):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return TrackAppSession(success=False, message="Authentication required")
            
            from user_activity.models import SessionActivity
            
            # Update or create session activity
            session_activity, created = SessionActivity.objects.update_or_create(
                user=user,
                session_id=session_data.session_id,
                defaults={
                    'start_time': session_data.start_time or timezone.now(),
                    'end_time': session_data.end_time,
                    'pages_visited': session_data.pages_visited or 0,
                    'actions_performed': session_data.actions_performed or 0,
                    'device_info': session_data.device_info or {},
                    'location_data': session_data.location_data or {},
                }
            )
            
            return TrackAppSession(
                success=True,
                message="App session tracked successfully"
            )
        
        except Exception as e:
            logger.error(f"Error tracking app session: {e}")
            return TrackAppSession(
                success=False,
                message=f"Error: {str(e)}"
            )


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class Mutation(graphene.ObjectType):
    track_user_activity = TrackUserActivity.Field()
    track_content_interaction = TrackContentInteraction.Field()
    track_profile_activity = TrackProfileActivity.Field()
    track_media_interaction = TrackMediaInteraction.Field()
    track_social_interaction = TrackSocialInteraction.Field()
    track_scroll_depth = TrackScrollDepth.Field()
    track_time_spent = TrackTimeSpent.Field()
    track_app_session = TrackAppSession.Field()