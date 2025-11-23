"""
GraphQL Mutations for Notification Module
"""
import graphene
from graphql import GraphQLError
from graphql_jwt.decorators import login_required
from django.utils import timezone

from notification.models import UserNotification, NotificationPreference
from notification.graphql.types import UserNotificationType, NotificationPreferenceType
from auth_manager.models import Users


class MarkNotificationAsRead(graphene.Mutation):
    """
    Mark a single notification as read.
    """
    class Arguments:
        notification_id = graphene.Int(required=True, description="Notification ID to mark as read")
    
    success = graphene.Boolean()
    message = graphene.String()
    notification = graphene.Field(UserNotificationType)
    
    @login_required
    def mutate(self, info, notification_id):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            # Get user UID from Neo4j
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            user_uid = user_node.uid
            
            # Get notification (ensure it belongs to current user)
            notification = UserNotification.objects.filter(
                id=notification_id,
                user_uid=user_uid
            ).first()
            
            if not notification:
                return MarkNotificationAsRead(
                    success=False,
                    message="Notification not found or access denied",
                    notification=None
                )
            
            # Mark as read
            notification.mark_as_read()
            
            return MarkNotificationAsRead(
                success=True,
                message="Notification marked as read",
                notification=notification
            )
            
        except Users.DoesNotExist:
            return MarkNotificationAsRead(
                success=False,
                message="User not found",
                notification=None
            )
        except Exception as e:
            return MarkNotificationAsRead(
                success=False,
                message=f"Error marking notification as read: {str(e)}",
                notification=None
            )


class MarkAllNotificationsAsRead(graphene.Mutation):
    """
    Mark all notifications as read for the current user.
    """
    success = graphene.Boolean()
    message = graphene.String()
    updated_count = graphene.Int(description="Number of notifications marked as read")
    
    @login_required
    def mutate(self, info):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            # Get user UID from Neo4j
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            user_uid = user_node.uid
            
            # Mark all unread notifications as read
            updated_count = UserNotification.objects.filter(
                user_uid=user_uid,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now(),
                status='read'
            )
            
            return MarkAllNotificationsAsRead(
                success=True,
                message=f"Marked {updated_count} notifications as read",
                updated_count=updated_count
            )
            
        except Users.DoesNotExist:
            return MarkAllNotificationsAsRead(
                success=False,
                message="User not found",
                updated_count=0
            )
        except Exception as e:
            return MarkAllNotificationsAsRead(
                success=False,
                message=f"Error marking notifications as read: {str(e)}",
                updated_count=0
            )


class DeleteNotification(graphene.Mutation):
    """
    Delete a single notification.
    """
    class Arguments:
        notification_id = graphene.Int(required=True, description="Notification ID to delete")
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @login_required
    def mutate(self, info, notification_id):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            # Get user UID from Neo4j
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            user_uid = user_node.uid
            
            # Get notification (ensure it belongs to current user)
            notification = UserNotification.objects.filter(
                id=notification_id,
                user_uid=user_uid
            ).first()
            
            if not notification:
                return DeleteNotification(
                    success=False,
                    message="Notification not found or access denied"
                )
            
            # Delete notification
            notification.delete()
            
            return DeleteNotification(
                success=True,
                message="Notification deleted successfully"
            )
            
        except Users.DoesNotExist:
            return DeleteNotification(
                success=False,
                message="User not found"
            )
        except Exception as e:
            return DeleteNotification(
                success=False,
                message=f"Error deleting notification: {str(e)}"
            )


class DeleteAllNotifications(graphene.Mutation):
    """
    Delete all notifications for the current user.
    """
    class Arguments:
        is_read_only = graphene.Boolean(
            default_value=False,
            description="If true, only delete read notifications"
        )
    
    success = graphene.Boolean()
    message = graphene.String()
    deleted_count = graphene.Int(description="Number of notifications deleted")
    
    @login_required
    def mutate(self, info, is_read_only=False):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            # Get user UID from Neo4j
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            user_uid = user_node.uid
            
            # Build query
            queryset = UserNotification.objects.filter(user_uid=user_uid)
            
            if is_read_only:
                queryset = queryset.filter(is_read=True)
            
            # Delete notifications
            deleted_count, _ = queryset.delete()
            
            return DeleteAllNotifications(
                success=True,
                message=f"Deleted {deleted_count} notifications",
                deleted_count=deleted_count
            )
            
        except Users.DoesNotExist:
            return DeleteAllNotifications(
                success=False,
                message="User not found",
                deleted_count=0
            )
        except Exception as e:
            return DeleteAllNotifications(
                success=False,
                message=f"Error deleting notifications: {str(e)}",
                deleted_count=0
            )


class UpdateNotificationPreference(graphene.Mutation):
    """
    Update notification preference for a specific notification type.
    """
    class Arguments:
        notification_type = graphene.String(required=True, description="Notification type")
        is_enabled = graphene.Boolean(required=True, description="Enable or disable this notification type")
    
    success = graphene.Boolean()
    message = graphene.String()
    preference = graphene.Field(NotificationPreferenceType)
    
    @login_required
    def mutate(self, info, notification_type, is_enabled):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            # Get or create preference
            preference, created = NotificationPreference.objects.get_or_create(
                user=user,
                notification_type=notification_type,
                defaults={'is_enabled': is_enabled}
            )
            
            if not created:
                # Update existing preference
                preference.is_enabled = is_enabled
                preference.save()
            
            action = "enabled" if is_enabled else "disabled"
            return UpdateNotificationPreference(
                success=True,
                message=f"Notification preference {action} for {notification_type}",
                preference=preference
            )
            
        except Exception as e:
            return UpdateNotificationPreference(
                success=False,
                message=f"Error updating notification preference: {str(e)}",
                preference=None
            )


class NotificationMutations(graphene.ObjectType):
    """
    GraphQL mutations for notifications.
    """
    mark_notification_as_read = MarkNotificationAsRead.Field()
    mark_all_notifications_as_read = MarkAllNotificationsAsRead.Field()
    delete_notification = DeleteNotification.Field()
    delete_all_notifications = DeleteAllNotifications.Field()
    update_notification_preference = UpdateNotificationPreference.Field()
    pass
