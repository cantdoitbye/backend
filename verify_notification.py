import os
import sys
import django

# Setup Django
sys.path.insert(0, '/code')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from notification.models import UserNotification

def check_notifications():
    recipient_uid = "5be2fe92c9804e93a685a3aaf3469f8a"
    print(f"Checking notifications for recipient: {recipient_uid}")
    
    notifications = UserNotification.objects.filter(
        user_uid=recipient_uid
    ).order_by('-created_at')[:5]
    
    print(f"Found {notifications.count()} recent notifications:")
    for n in notifications:
        print(f"ID: {n.id}")
        print(f"Type: {n.notification_type}")
        print(f"Status: {n.status}")
        print(f"Created: {n.created_at}")
        print(f"Error: {n.error_message}")
        print("-" * 30)

if __name__ == "__main__":
    check_notifications()
