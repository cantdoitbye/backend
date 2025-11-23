"""
GraphQL Types for Notification Module
"""
import graphene
from graphene_django import DjangoObjectType
from notification.models import UserNotification, NotificationLog, NotificationPreference


class UserNotificationType(DjangoObjectType):
    """
    GraphQL type for UserNotification model.
    
    Represents individual user notifications with all fields
    including status, read state, and notification content.
    """
    class Meta:
        model = UserNotification
        fields = (
            'id',
            'user_uid',
            'notification_type',
            'title',
            'body',
            'device_id',
            'status',
            'priority',
            'click_action',
            'deep_link',
            'web_link',
            'image_url',
            'data',
            'error_message',
            'is_read',
            'read_at',
            'sent_at',
            'created_at',
        )


class NotificationLogType(DjangoObjectType):
    """
    GraphQL type for NotificationLog model.
    
    Represents batch notification logs for tracking and debugging.
    """
    class Meta:
        model = NotificationLog
        fields = (
            'id',
            'notification_type',
            'recipient_count',
            'successful_count',
            'failed_count',
            'status',
            'metadata',
            'error_message',
            'created_at',
        )


class NotificationPreferenceType(DjangoObjectType):
    """
    GraphQL type for NotificationPreference model.
    
    Represents user preferences for different notification types.
    """
    class Meta:
        model = NotificationPreference
        fields = (
            'id',
            'user',
            'notification_type',
            'is_enabled',
            'created_at',
            'updated_at',
        )


class NotificationStatsType(graphene.ObjectType):
    """
    Statistics about user notifications.
    """
    total_count = graphene.Int(description="Total number of notifications")
    unread_count = graphene.Int(description="Number of unread notifications")
    read_count = graphene.Int(description="Number of read notifications")
    pending_count = graphene.Int(description="Number of pending notifications")
    sent_count = graphene.Int(description="Number of sent notifications")
    failed_count = graphene.Int(description="Number of failed notifications")


class PaginatedNotificationsType(graphene.ObjectType):
    """
    Paginated notifications response with metadata.
    """
    notifications = graphene.List(UserNotificationType, description="List of notifications")
    total_count = graphene.Int(description="Total number of notifications")
    page = graphene.Int(description="Current page number")
    page_size = graphene.Int(description="Number of items per page")
    total_pages = graphene.Int(description="Total number of pages")
    has_next = graphene.Boolean(description="Whether there is a next page")
    has_previous = graphene.Boolean(description="Whether there is a previous page")
    unread_count = graphene.Int(description="Number of unread notifications")
