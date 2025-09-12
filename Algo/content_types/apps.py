from django.apps import AppConfig


class ContentTypesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content_types'
    verbose_name = 'Content Types'
    
    def ready(self):
        # Import signal handlers if needed
        pass
