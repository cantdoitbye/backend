from django.apps import AppConfig


class FeedAlgorithmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feed_algorithm'
    verbose_name = 'Feed Algorithm'
    
    def ready(self):
        # Import signal handlers if needed
        pass
