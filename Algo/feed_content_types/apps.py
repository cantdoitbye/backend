from django.apps import AppConfig


class FeedContentTypesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feed_content_types'
    verbose_name = 'Feed Content Types'
    
    def ready(self):
        # Import signal handlers if needed
        pass
