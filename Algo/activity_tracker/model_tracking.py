from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import UserActivity, ActivityType
from .handlers import ActivityTracker
import inspect

User = get_user_model()

def track_activity_for_model(model_class, activity_type, fields=None, exclude=None, 
                           created_only=False, updated_only=False, deleted_only=False):
    """
    Decorator to register a model for automatic activity tracking.
    
    Args:
        model_class: The model class to track
        activity_type: The activity type to record
        fields: List of fields to track (None for all fields)
        exclude: List of fields to exclude from tracking
        created_only: Only track object creation
        updated_only: Only track object updates
        deleted_only: Only track object deletion
    """
    def decorator(func):
        @receiver(post_save, sender=model_class, weak=False)
        def handle_save(sender, instance, created, **kwargs):
            if created and created_only and not updated_only and not deleted_only:
                # Track creation
                func(instance, created=True)
            elif not created and updated_only and not created_only and not deleted_only:
                # Track update
                func(instance, created=False)
            elif not deleted_only:
                # Track both create and update
                func(instance, created=created)
        
        @receiver(post_delete, sender=model_class, weak=False)
        def handle_delete(sender, instance, **kwargs):
            if deleted_only or (not created_only and not updated_only):
                func(instance, deleted=True)
        
        # Handle M2M field changes
        if fields:
            for field in fields:
                field_obj = model_class._meta.get_field(field)
                if field_obj.many_to_many or field_obj.one_to_many:
                    @receiver(m2m_changed, sender=getattr(model_class, field).through, weak=False)
                    def handle_m2m_change(sender, instance, action, reverse, model, pk_set, **kwargs):
                        if action in ['post_add', 'post_remove', 'post_clear']:
                            func(instance, m2m_action=action, m2m_field=field, m2m_pks=pk_set)
        
        return func
    return decorator

class ModelTracker:
    """
    Class-based approach to track model changes as activities.
    """
    def __init__(self, model_class, activity_type, fields=None, exclude=None, 
                 created_only=False, updated_only=False, deleted_only=False):
        self.model_class = model_class
        self.activity_type = activity_type
        self.fields = fields
        self.exclude = exclude or []
        self.created_only = created_only
        self.updated_only = updated_only
        self.deleted_only = deleted_only
        
        # Register signals
        post_save.connect(self.handle_save, sender=model_class, weak=False)
        post_delete.connect(self.handle_delete, sender=model_class, weak=False)
        
        # Register M2M signals for tracked fields
        if self.fields:
            for field in self.fields:
                try:
                    field_obj = model_class._meta.get_field(field)
                    if field_obj.many_to_many or field_obj.one_to_many:
                        m2m_through = getattr(model_class, field).through
                        m2m_changed.connect(
                            self.handle_m2m_change,
                            sender=m2m_through,
                            weak=False
                        )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not set up M2M tracking for {field}: {e}")
    
    def handle_save(self, sender, instance, created, **kwargs):
        """Handle model save events."""
        if created and self.created_only and not self.updated_only and not self.deleted_only:
            self.track_activity(instance, created=True)
        elif not created and self.updated_only and not self.created_only and not self.deleted_only:
            self.track_activity(instance, created=False)
        elif not self.deleted_only:
            self.track_activity(instance, created=created)
    
    def handle_delete(self, sender, instance, **kwargs):
        """Handle model delete events."""
        if self.deleted_only or (not self.created_only and not self.updated_only):
            self.track_activity(instance, deleted=True)
    
    def handle_m2m_change(self, sender, instance, action, reverse, model, pk_set, **kwargs):
        """Handle M2M field changes."""
        if action in ['post_add', 'post_remove', 'post_clear']:
            field = None
            # Find which field triggered this signal
            for f in self.fields or []:
                try:
                    field_obj = self.model_class._meta.get_field(f)
                    if field_obj.many_to_many and getattr(instance, f).through == sender:
                        field = f
                        break
                except:
                    continue
            
            if field:
                self.track_activity(
                    instance, 
                    m2m_action=action,
                    m2m_field=field,
                    m2m_pks=pk_set
                )
    
    def track_activity(self, instance, created=None, deleted=False, **kwargs):
        """Track the activity."""
        # Determine the user who performed the action
        user = self.get_user(instance, **kwargs)
        if not user or not user.is_authenticated:
            return
        
        # Prepare metadata
        metadata = self.get_metadata(instance, created=created, deleted=deleted, **kwargs)
        
        # Track the activity
        ActivityTracker.track_activity(
            user=user,
            activity_type=self.activity_type,
            content_object=instance,
            metadata=metadata
        )
    
    def get_user(self, instance, **kwargs):
        """Get the user who performed the action."""
        # Try to get user from request
        from django.utils.functional import SimpleLazyObject
        from django.contrib.auth.models import AnonymousUser
        
        user = None
        
        # Check if user is passed in the signal
        if 'user' in kwargs:
            user = kwargs['user']
        # Check for request in thread local
        elif hasattr(instance, '_request') and hasattr(instance._request, 'user'):
            user = instance._request.user
        # Try to get user from common field names
        else:
            for field in ['user', 'author', 'created_by', 'modified_by', 'owner']:
                if hasattr(instance, field):
                    user = getattr(instance, field)
                    if user and hasattr(user, 'is_authenticated'):
                        break
        
        # Handle lazy objects
        if isinstance(user, SimpleLazyObject):
            try:
                user = user._wrapped
            except:
                user = None
        
        return user if user and hasattr(user, 'is_authenticated') else None
    
    def get_metadata(self, instance, created=None, deleted=False, **kwargs):
        """Get metadata for the activity."""
        metadata = {
            'action': 'created' if created else ('deleted' if deleted else 'updated'),
            'model': f"{instance._meta.app_label}.{instance._meta.model_name}",
            'object_id': str(instance.pk)
        }
        
        # Add M2M change info if available
        if 'm2m_action' in kwargs and 'm2m_field' in kwargs:
            metadata.update({
                'm2m_action': kwargs['m2m_action'],
                'm2m_field': kwargs['m2m_field'],
                'm2m_pks': list(kwargs.get('m2m_pks', [])),
            })
        
        # Add field changes if this is an update
        if not created and not deleted and hasattr(instance, '_changed_fields'):
            changed_fields = {}
            for field in instance._changed_fields:
                if self.fields and field not in self.fields:
                    continue
                if field in self.exclude:
                    continue
                
                # Get field value safely
                try:
                    value = getattr(instance, field)
                    # Handle models, dates, and other non-serializable types
                    if hasattr(value, 'pk'):
                        value = str(value.pk)
                    elif hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    changed_fields[field] = value
                except:
                    pass
            
            if changed_fields:
                metadata['changed_fields'] = changed_fields
        
        return metadata
