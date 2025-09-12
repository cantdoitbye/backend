from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings

from .models import UserActivity, ActivityType

class ActivityTracker:
    """Helper class for tracking user activities."""
    
    @classmethod
    def track_activity(cls, user, activity_type, content_object=None, metadata=None):
        """
        Track a user activity.
        
        Args:
            user: The user performing the activity
            activity_type: Type of activity (from ActivityType)
            content_object: Optional related content object
            metadata: Additional metadata for the activity
        """
        if not settings.ACTIVITY_TRACKING.get('AUTO_TRACK', True):
            return None
            
        if not user or not user.is_authenticated:
            return None
            
        content_type = None
        object_id = None
        
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.pk
        
        return UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            content_type=content_type,
            object_id=object_id,
            metadata=metadata or {}
        )

# Example signal handlers for common activities

def register_model_activity(model_class, activity_type):
    ""
    Register signal handlers to track model activities.
    
    Args:
        model_class: The model class to track
        activity_type: Type of activity (from ActivityType)
    ""
    def save_handler(sender, instance, created, **kwargs):
        if created:
            ActivityTracker.track_activity(
                user=getattr(instance, 'user', None) or getattr(instance, 'creator', None),
                activity_type=activity_type,
                content_object=instance
            )
    
    post_save.connect(save_handler, sender=model_class, weak=False)
    
    return save_handler


def register_action_activity(model_class, action_name, activity_type):
    """
    Register a custom action to track as an activity.
    
    Args:
        model_class: The model class the action is performed on
        action_name: Name of the action method
        activity_type: Type of activity (from ActivityType)
    ""
    original_method = getattr(model_class, action_name, None)
    
    if not original_method:
        return None
    
    def wrapped_method(self, user, **kwargs):
        # Call the original method
        result = original_method(self, user=user, **kwargs)
        
        # Track the activity
        ActivityTracker.track_activity(
            user=user,
            activity_type=activity_type,
            content_object=self,
            metadata=kwargs.get('metadata')
        )
        
        return result
    
    # Replace the original method
    setattr(model_class, action_name, wrapped_method)
    return wrapped_method


# Example usage in your models.py:
# from activity_tracker.handlers import register_model_activity, register_action_activity
# 
# # Track model creation
# register_model_activity(Post, ActivityType.POST_CREATE)
# 
# # Track a custom action
# class Post(models.Model):
#     def like(self, user):
#         # Like logic here
#         pass
# 
# register_action_activity(Post, 'like', ActivityType.VIBE)
