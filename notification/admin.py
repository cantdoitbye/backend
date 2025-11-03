from django.contrib import admin
from .models import UserNotification, NotificationLog, NotificationPreference


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_uid', 'notification_type', 'title', 'status', 'is_read', 'created_at')
    list_filter = ('notification_type', 'status', 'is_read', 'priority', 'created_at')
    search_fields = ('user_uid', 'notification_type', 'title', 'body')
    readonly_fields = ('created_at', 'sent_at', 'read_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Recipient', {
            'fields': ('user_uid', 'device_id')
        }),
        ('Notification Details', {
            'fields': ('notification_type', 'title', 'body', 'priority')
        }),
        ('Actions & Links', {
            'fields': ('click_action', 'image_url', 'data')
        }),
        ('Status', {
            'fields': ('status', 'is_read', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'read_at')
        }),
    )
    
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f"{queryset.count()} notifications marked as read")
    mark_as_read.short_description = "Mark selected as read"


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'notification_type', 'recipient_count', 'successful_count', 'failed_count', 'status', 'created_at')
    list_filter = ('notification_type', 'status', 'created_at')
    search_fields = ('notification_type', 'metadata')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'notification_type', 'is_enabled', 'updated_at')
    list_filter = ('is_enabled', 'notification_type', 'updated_at')
    search_fields = ('user__username', 'notification_type')
    ordering = ('-updated_at',)


