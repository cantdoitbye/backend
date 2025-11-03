from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserNotification(models.Model):
    """
    Stores all user notifications in PostgreSQL
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    )
    
    user_uid = models.CharField(max_length=255, db_index=True, help_text="User UID from Neo4j")
    notification_type = models.CharField(max_length=100, db_index=True, help_text="Type of notification")
    title = models.CharField(max_length=255, help_text="Notification title")
    body = models.TextField(help_text="Notification body/message")
    device_id = models.CharField(max_length=255, help_text="FCM device token")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    priority = models.CharField(max_length=20, default='normal', help_text="Notification priority")
    click_action = models.CharField(max_length=500, null=True, blank=True, help_text="Deep link action")
    image_url = models.URLField(null=True, blank=True, help_text="Image URL for rich notification")
    data = models.JSONField(default=dict, help_text="Additional notification data")
    error_message = models.TextField(null=True, blank=True, help_text="Error message if failed")
    is_read = models.BooleanField(default=False, db_index=True, help_text="Whether notification was read")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When notification was read")
    sent_at = models.DateTimeField(null=True, blank=True, help_text="When notification was sent")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = 'User Notification'
        verbose_name_plural = 'User Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'user_uid']),
            models.Index(fields=['user_uid', 'is_read']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} → {self.user_uid} ({self.status})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        if self.status == 'sent':
            self.status = 'read'
        self.save()


class NotificationLog(models.Model):
    """
    Stores notification batch logs for tracking and debugging
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    )
    
    notification_type = models.CharField(max_length=100, db_index=True, help_text="Type of notification sent")
    recipient_count = models.IntegerField(default=0, help_text="Number of recipients")
    successful_count = models.IntegerField(default=0, help_text="Number of successful sends")
    failed_count = models.IntegerField(default=0, help_text="Number of failed sends")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    metadata = models.JSONField(default=dict, help_text="Additional notification metadata")
    error_message = models.TextField(null=True, blank=True, help_text="Error message if failed")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'notification_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.status} ({self.successful_count}/{self.recipient_count})"


class NotificationPreference(models.Model):
    """
    User preferences for different notification types
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences',
        help_text="User who owns these preferences"
    )
    notification_type = models.CharField(
        max_length=100, 
        db_index=True,
        help_text="Type of notification"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether this notification type is enabled for the user"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
        unique_together = ('user', 'notification_type')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['is_enabled']),
        ]
    
    def __str__(self):
        status = "enabled" if self.is_enabled else "disabled"
        return f"{self.user.username} - {self.notification_type} ({status})"


