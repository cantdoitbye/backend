"""
Simple test to verify notification sending and storage
"""
from django.core.management.base import BaseCommand
from notification.global_service import GlobalNotificationService
from notification.models import UserNotification


class Command(BaseCommand):
    help = 'Test sending a single notification to verify it works and stores in DB'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Testing Notification Service ===\n'))
        
        # Test data
        test_recipient = {
            'device_id': 'test_device_token_12345',
            'uid': 'test_user_uid_67890'
        }
        
        self.stdout.write('📤 Sending test notification...')
        self.stdout.write(f'   Event: new_comment_on_post')
        self.stdout.write(f'   Recipient UID: {test_recipient["uid"]}')
        self.stdout.write(f'   Device ID: {test_recipient["device_id"]}\n')
        
        # Send notification
        service = GlobalNotificationService()
        
        try:
            results = service.send(
                event_type="new_comment_on_post",
                recipients=[test_recipient],
                username="Test User",
                comment_text="This is a test comment!",
                post_id="test_post_123"
            )
            
            self.stdout.write(self.style.SUCCESS('✅ Notification sent!\n'))
            
            # Check database
            self.stdout.write('📊 Checking PostgreSQL...')
            
            notifications = UserNotification.objects.filter(
                user_uid=test_recipient['uid']
            ).order_by('-created_at')
            
            if notifications.exists():
                latest = notifications.first()
                self.stdout.write(self.style.SUCCESS(f'✅ Found {notifications.count()} notification(s) in database\n'))
                
                self.stdout.write('📋 Latest Notification Details:')
                self.stdout.write(f'   ID: {latest.id}')
                self.stdout.write(f'   Type: {latest.notification_type}')
                self.stdout.write(f'   Title: {latest.title}')
                self.stdout.write(f'   Body: {latest.body}')
                self.stdout.write(f'   Status: {latest.status}')
                self.stdout.write(f'   Priority: {latest.priority}')
                self.stdout.write(f'   Click Action: {latest.click_action}')
                self.stdout.write(f'   Created: {latest.created_at}')
                self.stdout.write(f'   Sent: {latest.sent_at}')
                self.stdout.write(f'   Is Read: {latest.is_read}\n')
                
                if latest.status == 'sent':
                    self.stdout.write(self.style.SUCCESS('🎉 SUCCESS! Notification was sent and stored correctly!\n'))
                elif latest.status == 'failed':
                    self.stdout.write(self.style.ERROR(f'❌ Notification failed: {latest.error_message}\n'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️  Notification status: {latest.status}\n'))
                
                # Show send results
                if results:
                    result = results[0]
                    if result.get('success'):
                        self.stdout.write(self.style.SUCCESS(f'✅ Send Result: Success'))
                        self.stdout.write(f'   Notification ID: {result.get("notification_id")}')
                    else:
                        self.stdout.write(self.style.ERROR(f'❌ Send Result: Failed'))
                        self.stdout.write(f'   Error: {result.get("error")}')
            else:
                self.stdout.write(self.style.ERROR('❌ No notifications found in database!\n'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}\n'))
            import traceback
            self.stdout.write(traceback.format_exc())
        
        self.stdout.write('\n=== Test Complete ===\n')
