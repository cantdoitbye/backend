#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings')

# Setup Django
django.setup()

from django.apps import apps
from django.conf import settings

print('\n=== Django Configuration Debug ===')
print(f'Settings configured: {settings.configured}')
print(f'INSTALLED_APPS count: {len(settings.INSTALLED_APPS)}')
print('\nAll installed apps:')
for i, app in enumerate(settings.INSTALLED_APPS):
    print(f'  {i+1:2d}. {app}')

print('\nApp configs:')
for app in apps.get_app_configs():
    print(f'  - {app.label} ({app.name})')

print('\nOur local apps:')
local_apps = ['feed_algorithm', 'feed_content_types', 'scoring_engines', 'caching', 'analytics']
for app_name in local_apps:
    try:
        app = apps.get_app_config(app_name)
        print(f'  ✓ {app_name} - loaded successfully')
        print(f'    Path: {app.path}')
        # Try to load models
        try:
            models = app.get_models()
            print(f'    Models: {len(models)} found')
            for model in models[:3]:  # Show first 3 models
                print(f'      - {model.__name__}')
        except Exception as e:
            print(f'    Models: Error loading - {e}')
    except Exception as e:
        print(f'  ✗ {app_name} - Error: {e}')

print('\n=== End Debug ===')
