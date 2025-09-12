#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings')

print('=== Testing settings import ===')

try:
    from django.conf import settings
    print('✓ django.conf.settings imported successfully')
    
    # Try to access INSTALLED_APPS
    installed_apps = settings.INSTALLED_APPS
    print(f'✓ INSTALLED_APPS accessed: {len(installed_apps)} apps')
    
    # Print each app
    for app in installed_apps:
        print(f'  - {app}')
        
except Exception as e:
    print(f'✗ Error importing settings: {e}')
    import traceback
    traceback.print_exc()

print('\n=== Testing direct settings module import ===')
try:
    import ooumph_feed.settings as settings_module
    print('✓ Settings module imported successfully')
    print(f'DJANGO_APPS: {len(settings_module.DJANGO_APPS)}')
    print(f'THIRD_PARTY_APPS: {len(settings_module.THIRD_PARTY_APPS)}')
    print(f'LOCAL_APPS: {len(settings_module.LOCAL_APPS)}')
    print(f'INSTALLED_APPS: {len(settings_module.INSTALLED_APPS)}')
except Exception as e:
    print(f'✗ Error importing settings module: {e}')
    import traceback
    traceback.print_exc()
