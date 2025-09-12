from django.db import models
from django.utils.functional import cached_property

class TrackChangesMixin:
    """
    A model mixin that tracks changes to model fields.
    """
    _state = None  # Will be set by Django
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial = self._get_field_values()
    
    def _get_field_values(self):
        """Get a dictionary of field names to values."""
        field_values = {}
        for field in self._meta.fields:
            field_values[field.name] = getattr(self, field.attname)
        return field_values
    
    @cached_property
    def _changed_fields(self):
        ""
        Return a list of field names that have changed since initialization.
        """
        if self._state.adding:
            return []
            
        changed_fields = []
        for field_name, initial_value in self._initial.items():
            current_value = getattr(self, field_name)
            if current_value != initial_value:
                changed_fields.append(field_name)
        
        return changed_fields
    
    def has_changed(self, field_name):
        ""Check if the specified field has changed."""
        return field_name in self._changed_fields
    
    def get_field_diff(self, field_name):
        ""
        Get the difference between the initial and current value of a field.
        Returns a tuple of (old_value, new_value).
        """
        if field_name not in self._initial:
            return None, None
            
        return self._initial[field_name], getattr(self, field_name)
    
    def save(self, *args, **kwargs):
        ""Save the model and reset the initial state."""
        super().save(*args, **kwargs)
        self._initial = self._get_field_values()
    
    def refresh_from_db(self, *args, **kwargs):
        ""Refresh the model from the database and reset the initial state."""
        super().refresh_from_db(*args, **kwargs)
        self._initial = self._get_field_values()


def track_field_changes(*field_names):
    ""
    A decorator to track changes to specific fields on a model.
    
    Usage:
        @track_field_changes('status', 'priority')
        class MyModel(models.Model):
            status = models.CharField(max_length=20)
            priority = models.IntegerField()
            
            def save(self, *args, **kwargs):
                if self.has_status_changed:
                    print(f"Status changed from {self.old_status} to {self.status}")
                super().save(*args, **kwargs)
    """
    def decorator(cls):
        # Create properties for each tracked field
        for field_name in field_names:
            # Add a property to check if the field has changed
            def make_has_changed_property(field):
                def has_changed_property(self):
                    return self.has_changed(field)
                return property(has_changed_property)
            
            # Add a property to get the old value of the field
            def make_old_value_property(field):
                def old_value_property(self):
                    old, _ = self.get_field_diff(field)
                    return old
                return property(old_value_property)
            
            # Add the properties to the class
            setattr(cls, f'has_{field_name}_changed', make_has_changed_property(field_name))
            setattr(cls, f'old_{field_name}', make_old_value_property(field_name))
        
        return cls
    
    return decorator


def track_related_changes(related_field_name, *fields):
    ""
    A decorator to track changes to related model fields.
    
    Usage:
        @track_related_changes('profile', 'bio', 'avatar')
        class User(models.Model):
            username = models.CharField(max_length=100)
            profile = models.OneToOneField('Profile', on_delete=models.CASCADE)
    ""
    def decorator(cls):
        original_save = cls.save
        
        def save(self, *args, **kwargs):
            if hasattr(self, related_field_name):
                related = getattr(self, related_field_name)
                if related and related.pk:
                    # Get the current state of the related object
                    related_class = related.__class__
                    try:
                        old_related = related_class.objects.get(pk=related.pk)
                        for field in fields:
                            old_value = getattr(old_related, field, None)
                            new_value = getattr(related, field, None)
                            if old_value != new_value:
                                # Field has changed, do something
                                pass
                    except related_class.DoesNotExist:
                        pass
            
            return original_save(self, *args, **kwargs)
        
        cls.save = save
        return cls
    
    return decorator


def track_m2m_changes(*m2m_field_names):
    ""
    A decorator to track changes to many-to-many fields.
    
    Usage:
        @track_m2m_changes('tags', 'categories')
        class Post(models.Model):
            title = models.CharField(max_length=200)
            tags = models.ManyToManyField('Tag')
            categories = models.ManyToManyField('Category')
    ""
    def decorator(cls):
        original_save = cls.save
        
        def save(self, *args, **kwargs):
            if not self.pk:
                # New instance, no M2M changes to track yet
                return original_save(self, *args, **kwargs)
            
            # Get the current state of M2M fields
            old_m2m = {}
            for field_name in m2m_field_names:
                if hasattr(self, field_name):
                    m2m_field = getattr(self, field_name)
                    try:
                        old_m2m[field_name] = set(m2m_field.all().values_list('pk', flat=True))
                    except (ValueError, AttributeError):
                        old_m2m[field_name] = set()
            
            # Save the instance
            result = original_save(self, *args, **kwargs)
            
            # Check for changes in M2M fields
            for field_name in m2m_field_names:
                if field_name in old_m2m and hasattr(self, field_name):
                    m2m_field = getattr(self, field_name)
                    try:
                        current_pks = set(m2m_field.all().values_list('pk', flat=True))
                        added = current_pks - old_m2m[field_name]
                        removed = old_m2m[field_name] - current_pks
                        
                        if added or removed:
                            # M2M field has changed, do something
                            pass
                            
                    except (ValueError, AttributeError):
                        pass
            
            return result
        
        cls.save = save
        return cls
    
    return decorator
