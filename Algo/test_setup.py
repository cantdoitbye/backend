import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings')
django.setup()

from django.apps import apps

print("Installed apps:")
for app in apps.get_app_configs():
    print(f"  - {app.label}: {app.name}")

print("\nTrying to import models...")
try:
    from feed_algorithm.models import UserProfile
    print("✓ UserProfile imported successfully")
except Exception as e:
    print(f"✗ Failed to import UserProfile: {e}")

try:
    from django.contrib.auth.models import User
    print("✓ User model imported successfully")
except Exception as e:
    print(f"✗ Failed to import User: {e}")
