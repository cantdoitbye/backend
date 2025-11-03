from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification'
    verbose_name = 'Unified Notification Service'
    
    def ready(self):
        """
        Import notification signals when the app is ready
        """
        pass


