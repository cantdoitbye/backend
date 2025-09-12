import os

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings')

try:
    from django.conf import settings
    print("Settings imported successfully")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"SECRET_KEY length: {len(settings.SECRET_KEY)}")
    print(f"INSTALLED_APPS count: {len(settings.INSTALLED_APPS)}")
    print("INSTALLED_APPS:")
    for app in settings.INSTALLED_APPS:
        print(f"  - {app}")
except Exception as e:
    print(f"Failed to import settings: {e}")
    import traceback
    traceback.print_exc()
