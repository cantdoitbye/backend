# truststream/apps.py

from django.apps import AppConfig


class TruststreamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'truststream'
    verbose_name = 'TrustStream AI Governance Platform'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        This is called after all models are loaded.
        """
        pass