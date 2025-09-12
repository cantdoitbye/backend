# Simple Django test script to check if basic functionality works
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings.development')

# Configure Django
try:
    django.setup()
    print("✓ Django setup successful")
    
    # Test basic Django functionality
    from django.conf import settings
    print(f"✓ Settings loaded: {settings.DEBUG=}")
    
    # Test database connection
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✓ Database connection: {result}")
    
    # Test apps
    from django.apps import apps
    app_configs = apps.get_app_configs()
    print(f"✓ Apps loaded: {len(app_configs)} apps")
    
    # Check specific apps
    try:
        analytics_app = apps.get_app_config('analytics_dashboard')
        print(f"✓ Analytics dashboard app: {analytics_app.name}")
    except Exception as e:
        print(f"✗ Analytics dashboard app error: {e}")
    
    print("\n✓ Basic Django test completed successfully!")
    
except Exception as e:
    print(f"✗ Django test failed: {e}")
    import traceback
    traceback.print_exc()
