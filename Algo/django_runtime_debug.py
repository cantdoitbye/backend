#!/usr/bin/env python
import os
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings')
    
    # Setup Django
    django.setup()
    
    from django.conf import settings
    from django.apps import apps
    
    print('\n=== Django Runtime Debug ===')
    print(f'INSTALLED_APPS count: {len(settings.INSTALLED_APPS)}')
    print('Local apps in settings:')
    for app in settings.INSTALLED_APPS:
        if not app.startswith('django'):
            print(f'  - {app}')
    
    print(f'\nApp configs loaded: {len(list(apps.get_app_configs()))}')
    print('Available app labels:')
    for app in apps.get_app_configs():
        print(f'  - {app.label} ({app.name})')
    
    # Try to load our models specifically
    print('\nTesting model imports:')
    local_apps = ['feed_algorithm', 'feed_content_types', 'scoring_engines', 'caching', 'analytics']
    for app_name in local_apps:
        try:
            app_config = apps.get_app_config(app_name)
            models = app_config.get_models()
            print(f'  ✓ {app_name}: {len(models)} models')
        except Exception as e:
            print(f'  ✗ {app_name}: {e}')
