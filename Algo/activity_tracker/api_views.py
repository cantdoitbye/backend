from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, F, Count, Case, When, Value, IntegerField
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import UserActivity, UserEngagementScore, ActivityType
from .serializers import UserActivitySerializer, UserEngagementScoreSerializer
from .pagination import ActivityPagination

class ActivityFeedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for retrieving a user's activity feed.
    """
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ActivityPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at', 'activity_type']
    search_fields = ['activity_type', 'metadata']
    
    def get_queryset(self):
        """Return activities for the current user and their network."""
        queryset = UserActivity.objects.filter(
            Q(user=self.request.user) |  # User's own activities
            Q(content_type=ContentType.objects.get_for_model(self.request.user),
              object_id=self.request.user.id)  # Activities targeting the user
        ).select_related('user', 'content_type').order_by('-created_at')
        
        # Filter by activity type if provided
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # Filter by content type if provided
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(
                content_type__model=content_type.lower()
            )
        
        # Filter by date range if provided
        days = self.request.query_params.get('days')
        if days and days.isdigit():
            since_date = timezone.now() - timezone.timedelta(days=int(days))
            queryset = queryset.filter(created_at__gte=since_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get a summary of the user's recent activities."""
        days = int(request.query_params.get('days', 30))
        since_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get activity counts by type
        activity_counts = (
            UserActivity.objects
            .filter(user=request.user, created_at__gte=since_date)
            .values('activity_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Get most active day
        most_active_day = (
            UserActivity.objects
            .filter(user=request.user, created_at__gte=since_date)
            .extra({'date': "date(created_at)"})
            .values('date')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        
        # Get most common activity
        most_common_activity = activity_counts.first()
        
        return Response({
            'total_activities': sum(item['count'] for item in activity_counts),
            'activity_counts': activity_counts,
            'most_active_day': most_active_day,
            'most_common_activity': most_common_activity,
        })
    
    @action(detail=False, methods=['get'])
    def engagement_metrics(self, request):
        """Get engagement metrics for the current user."""
        try:
            score = UserEngagementScore.objects.get(user=request.user)
            serializer = UserEngagementScoreSerializer(score)
            return Response(serializer.data)
        except UserEngagementScore.DoesNotExist:
            return Response(
                {'detail': 'Engagement score not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ContentActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for retrieving activities related to specific content.
    """
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ActivityPagination
    
    def get_queryset(self):
        """Return activities related to a specific content object."""
        content_type = self.kwargs.get('content_type')
        object_id = self.kwargs.get('object_id')
        
        if not (content_type and object_id):
            return UserActivity.objects.none()
        
        try:
            content_type = ContentType.objects.get(model=content_type.lower())
        except ContentType.DoesNotExist:
            return UserActivity.objects.none()
        
        return UserActivity.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).select_related('user').order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def engagement_stats(self, request, content_type=None, object_id=None):
        """Get engagement statistics for a content object."""
        try:
            content_type = ContentType.objects.get(model=content_type.lower())
        except ContentType.DoesNotExist:
            return Response(
                {'detail': 'Invalid content type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get activity counts by type
        activity_counts = (
            UserActivity.objects
            .filter(content_type=content_type, object_id=object_id)
            .values('activity_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Get unique users
        unique_users = (
            UserActivity.objects
            .filter(content_type=content_type, object_id=object_id)
            .values('user')
            .distinct()
            .count()
        )
        
        # Get most recent activity
        most_recent = (
            UserActivity.objects
            .filter(content_type=content_type, object_id=object_id)
            .order_by('-created_at')
            .first()
        )
        
        return Response({
            'total_activities': sum(item['count'] for item in activity_counts),
            'unique_users': unique_users,
            'activity_breakdown': activity_counts,
            'most_recent_activity': (
                UserActivitySerializer(most_recent).data 
                if most_recent else None
            ),
        })
