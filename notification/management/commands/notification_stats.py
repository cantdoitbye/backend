"""
Show notification statistics
"""
from django.core.management.base import BaseCommand
from notification.models import UserNotification, NotificationLog
from django.db.models import Count


class Command(BaseCommand):
    help = 'Show notification statistics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Notification Statistics ===\n'))
        
        # Total notifications
        total = UserNotification.objects.count()
        self.stdout.write(f'📊 Total Notifications: {total}')
        
        # By status
        self.stdout.write('\n📈 By Status:')
        status_counts = UserNotification.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for item in status_counts:
            self.stdout.write(f'   {item["status"]}: {item["count"]}')
        
        # By type
        self.stdout.write('\n📋 By Type (Top 10):')
        type_counts = UserNotification.objects.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        for item in type_counts:
            self.stdout.write(f'   {item["notification_type"]}: {item["count"]}')
        
        # Recent notifications
        self.stdout.write('\n🕐 Recent Notifications (Last 5):')
        recent = UserNotification.objects.order_by('-created_at')[:5]
        
        for notif in recent:
            self.stdout.write(f'   [{notif.created_at}] {notif.notification_type} → {notif.user_uid} ({notif.status})')
        
        # Batch logs
        self.stdout.write('\n📦 Batch Logs:')
        logs = NotificationLog.objects.order_by('-created_at')[:5]
        
        for log in logs:
            self.stdout.write(
                f'   [{log.created_at}] {log.notification_type}: '
                f'{log.successful_count}/{log.recipient_count} sent ({log.status})'
            )
        
        self.stdout.write('\n')
