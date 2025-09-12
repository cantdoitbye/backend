# Analytics Dashboard App
# Real-time analytics with A/B testing capabilities

from django.apps import AppConfig


class AnalyticsDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics_dashboard'
    verbose_name = 'Analytics Dashboard'
    
    def ready(self):
        try:
            import analytics_dashboard.signals
        except ImportError:
            # Signals not available yet
            pass
