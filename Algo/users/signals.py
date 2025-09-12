# Simplified signals for users app
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    """Handle user creation."""
    if created:
        try:
            # Log user creation event
            from analytics.utils import log_user_event
            log_user_event('user_created', user_id=instance.id)
            logger.info(f"User created: {instance.username}")
        except Exception as e:
            logger.error(f"Error handling user creation: {e}")


@receiver(post_save, sender=User)
def user_updated(sender, instance, created, **kwargs):
    """Handle user updates."""
    if not created:
        try:
            # Log user update event
            from analytics.utils import log_user_event
            log_user_event('user_updated', user_id=instance.id)
            logger.debug(f"User updated: {instance.username}")
        except Exception as e:
            logger.error(f"Error handling user update: {e}")
