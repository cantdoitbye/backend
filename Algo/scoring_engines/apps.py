from django.apps import AppConfig


class ScoringEnginesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scoring_engines'
    verbose_name = 'Scoring Engines'
    
    def ready(self):
        # Import signal handlers if needed
        pass
