from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile, FeedComposition

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile and FeedComposition when a new User is created."""
    if created:
        # Create UserProfile
        UserProfile.objects.create(user=instance)
        
        # Create FeedComposition with default values
        FeedComposition.objects.create(user=instance)

@receiver(pre_save, sender=UserProfile)
def update_user_profile(sender, instance, **kwargs):
    """Update UserProfile when related User is updated."""
    # Ensure the user's last_active is updated when the profile is saved
    if not instance.pk:
        return
    
    try:
        old_instance = UserProfile.objects.get(pk=instance.pk)
        if old_instance.last_active != instance.last_active:
            # Update the user's last_login to match last_active
            user = instance.user
            user.last_login = instance.last_active
            user.save(update_fields=['last_login'])
    except UserProfile.DoesNotExist:
        pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the user profile when the user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    
    if hasattr(instance, 'feed_composition'):
        instance.feed_composition.save()
