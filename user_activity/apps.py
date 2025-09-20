from django.apps import AppConfig


class UserActivityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_activity'
    verbose_name = 'User Activity Tracking'

    def ready(self):
        """Import signals when the app is ready."""
        import user_activity.signals  # noqa