"""
GraphQL Queries for Notification Module
"""
import graphene
from graphql import GraphQLError
from graphql_jwt.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Count, Case, When, IntegerField

from notification.models import UserNotification, NotificationLog, NotificationPreference
from notification.graphql.types import (
    UserNotificationType,
    NotificationLogType,
    NotificationPreferenceType,
    NotificationStatsType,
    PaginatedNotificationsType,
)
from auth_manager.models import Users


class NotificationQueries(graphene.ObjectType):
    """
    GraphQL queries for notifications.
    """
    
    # Get paginated notifications for current user
    my_notifications = graphene.Field(
        PaginatedNotificationsType,
        page=graphene.Int(default_value=1, description="Page number (starts at 1)"),
        page_size=graphene.Int(default_value=20, description="Number of items per page (max 100)"),
        is_read=graphene.Boolean(description="Filter by read status (true/false/null for all)"),
        notification_type=graphene.String(description="Filter by notification type"),
        status=graphene.String(description="Filter by status (pending/sent/failed/read)"),
        description="Get paginated notifications for the current user"
    )
    
    # Get single notification by ID
    notification = graphene.Field(
        UserNotificationType,
        notification_id=graphene.Int(required=True, description="Notification ID"),
        description="Get a single notification by ID"
    )
    
    # Get notification statistics
    notification_stats = graphene.Field(
        NotificationStatsType,
        description="Get notification statistics for current user"
    )
    
    # Get notification preferences
    notification_preferences = graphene.List(
        NotificationPreferenceType,
        description="Get notification preferences for current user"
    )
    
    # Get notification logs (admin only)
    notification_logs = graphene.List(
        NotificationLogType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        notification_type=graphene.String(),
        description="Get notification logs (admin only)"
    )
    
    @login_required
    def resolve_my_notifications(self, info, page=1, page_size=20, is_read=None, notification_type=None, status=None):
        """
        Get paginated notifications for the current user.
        
        Args:
            page: Page number (starts at 1)
            page_size: Number of items per page (max 100)
            is_read: Filter by read status (true/false/null for all)
            notification_type: Filter by notification type
            status: Filter by status (pending/sent/failed/read)
        
        Returns:
            PaginatedNotificationsType with notifications and metadata
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            # Get user UID from Neo4j
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            user_uid = user_node.uid
            
            # Limit page size
            page_size = min(page_size, 100)
            
            # Build query
            queryset = UserNotification.objects.filter(user_uid=user_uid)
            
            # Apply filters
            if is_read is not None:
                queryset = queryset.filter(is_read=is_read)
            
            if notification_type:
                queryset = queryset.filter(notification_type=notification_type)
            
            if status:
                queryset = queryset.filter(status=status)
            
            # Order by created_at descending (newest first)
            queryset = queryset.order_by('-created_at')
            
            # Get total count and unread count
            total_count = queryset.count()
            unread_count = UserNotification.objects.filter(
                user_uid=user_uid,
                is_read=False
            ).count()
            
            # Paginate
            paginator = Paginator(queryset, page_size)
            total_pages = paginator.num_pages
            
            try:
                notifications_page = paginator.page(page)
            except EmptyPage:
                # If page is out of range, return empty list
                notifications_page = paginator.page(paginator.num_pages) if total_pages > 0 else []
                notifications = []
            else:
                notifications = list(notifications_page.object_list)
            
            # Build response
            return PaginatedNotificationsType(
                notifications=notifications,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=notifications_page.has_next() if notifications_page else False,
                has_previous=notifications_page.has_previous() if notifications_page else False,
                unread_count=unread_count,
            )
            
        except Users.DoesNotExist:
            raise GraphQLError("User not found")
        except Exception as e:
            raise GraphQLError(f"Error fetching notifications: {str(e)}")
    
    @login_required
    def resolve_notification(self, info, notification_id):
        """
        Get a single notification by ID.
        
        Args:
            notification_id: Notification ID
        
        Returns:
            UserNotificationType or None
        """
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
                raise GraphQLError("Notification not found or access denied")
            
            return notification
            
        except Users.DoesNotExist:
            raise GraphQLError("User not found")
        except Exception as e:
            raise GraphQLError(f"Error fetching notification: {str(e)}")
    
    @login_required
    def resolve_notification_stats(self, info):
        """
        Get notification statistics for current user.
        
        Returns:
            NotificationStatsType with counts
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            # Get user UID from Neo4j
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            user_uid = user_node.uid
            
            # Get statistics
            stats = UserNotification.objects.filter(user_uid=user_uid).aggregate(
                total_count=Count('id'),
                unread_count=Count(Case(When(is_read=False, then=1), output_field=IntegerField())),
                read_count=Count(Case(When(is_read=True, then=1), output_field=IntegerField())),
                pending_count=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
                sent_count=Count(Case(When(status='sent', then=1), output_field=IntegerField())),
                failed_count=Count(Case(When(status='failed', then=1), output_field=IntegerField())),
            )
            
            return NotificationStatsType(
                total_count=stats['total_count'] or 0,
                unread_count=stats['unread_count'] or 0,
                read_count=stats['read_count'] or 0,
                pending_count=stats['pending_count'] or 0,
                sent_count=stats['sent_count'] or 0,
                failed_count=stats['failed_count'] or 0,
            )
            
        except Users.DoesNotExist:
            raise GraphQLError("User not found")
        except Exception as e:
            raise GraphQLError(f"Error fetching notification stats: {str(e)}")
    
    @login_required
    def resolve_notification_preferences(self, info):
        """
        Get notification preferences for current user.
        
        Returns:
            List of NotificationPreferenceType
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            preferences = NotificationPreference.objects.filter(user=user)
            return list(preferences)
            
        except Exception as e:
            raise GraphQLError(f"Error fetching notification preferences: {str(e)}")
    
    @login_required
    def resolve_notification_logs(self, info, page=1, page_size=20, notification_type=None):
        """
        Get notification logs (admin only).
        
        Args:
            page: Page number
            page_size: Number of items per page
            notification_type: Filter by notification type
        
        Returns:
            List of NotificationLogType
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            # Check if user is admin/superuser
            if not user.is_superuser:
                raise GraphQLError("Admin access required")
            
            # Build query
            queryset = NotificationLog.objects.all()
            
            if notification_type:
                queryset = queryset.filter(notification_type=notification_type)
            
            # Order by created_at descending
            queryset = queryset.order_by('-created_at')
            
            # Paginate
            page_size = min(page_size, 100)
            paginator = Paginator(queryset, page_size)
            
            try:
                logs_page = paginator.page(page)
                return list(logs_page.object_list)
            except EmptyPage:
                return []
            
        except Exception as e:
            raise GraphQLError(f"Error fetching notification logs: {str(e)}")
