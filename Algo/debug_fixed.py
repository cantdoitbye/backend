#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

print('=== Testing settings with proper __file__ context ===')

try:
    # Set the environment variable that Django expects
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings')
    
    # Try to read the settings file content directly
    settings_path = project_dir / 'ooumph_feed' / 'settings.py'
    print(f'Reading settings from: {settings_path}')
    
    # Execute the settings file in a controlled way with proper context
    settings_globals = {
        '__file__': str(settings_path),
        '__name__': 'ooumph_feed.settings',
        '__package__': 'ooumph_feed',
    }
    settings_locals = {}
    
    with open(settings_path, 'r') as f:
        settings_content = f.read()
    
    exec(settings_content, settings_globals, settings_locals)
    
    print('\n✓ Settings executed successfully!')
    print(f'DJANGO_APPS: {len(settings_locals.get("DJANGO_APPS", []))}')
    print(f'THIRD_PARTY_APPS: {len(settings_locals.get("THIRD_PARTY_APPS", []))}')
    print(f'LOCAL_APPS: {len(settings_locals.get("LOCAL_APPS", []))}')
    print(f'INSTALLED_APPS: {len(settings_locals.get("INSTALLED_APPS", []))}')
    
    if 'INSTALLED_APPS' in settings_locals:
        print('\nInstalled apps:')
        for i, app in enumerate(settings_locals['INSTALLED_APPS']):
            print(f'  {i+1:2d}. {app}')
    
except Exception as e:
    print(f'✗ Error executing settings: {e}')
    import traceback
    traceback.print_exc()

print('\n=== Testing Django setup with proper context ===')
try:
    import django
    django.setup()
    
    from django.apps import apps
    print(f'Django apps loaded: {len(list(apps.get_app_configs()))}')
    
    for app in apps.get_app_configs():
        print(f'  - {app.label}')
        
except Exception as e:
    print(f'✗ Error with Django setup: {e}')
    import traceback
    traceback.print_exc()
