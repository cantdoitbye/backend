from django.apps import AppConfig


class ActivityTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity_tracker'
    verbose_name = 'Activity Tracker'
    
    def ready(self):
        # Import signal handlers
        import activity_tracker.signals  # noqa
