"""
Django app configuration for the Diary module.
"""

from django.apps import AppConfig


class DiaryConfig(AppConfig):
    """
    Configuration class for the Diary Django application.
    
    This app manages diary folders, notes, documents, and todos for users.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diary'
    verbose_name = 'Diary Management'
    
    def ready(self):
        """
        Perform initialization when Django starts.
        Can be used to register signals or perform other setup tasks.
        """
        pass
