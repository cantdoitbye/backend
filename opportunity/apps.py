# opportunity/apps.py

from django.apps import AppConfig


class OpportunityConfig(AppConfig):
    """
    Django app configuration for the Opportunity module.
    
    This module handles job opportunity creation, management, and display.
    It integrates with the feed algorithm to show opportunities alongside
    posts and debates in the user's feed.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opportunity'
    verbose_name = 'Job Opportunities'
    
    def ready(self):
        """
        Run initialization code when Django starts.
        Import signals, register custom checks, etc.
        """
        # Import signals when app is ready
        # import opportunity.signals
        pass
