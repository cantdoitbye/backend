from django.apps import AppConfig


class AuthManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_manager'

    def ready(self):
        import auth_manager.signals
        import auth_manager.management.commands.createadmin
