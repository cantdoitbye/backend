from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from .models import UserActivity, UserEngagementScore
from .serializers import (
    UserActivitySerializer,
    UserEngagementScoreSerializer,
    ActivityCreateSerializer
)

class UserActivityViewSet(viewsets.ModelViewSet):
    """API endpoint for user activities."""
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return activities for the current user."""
        queryset = UserActivity.objects.filter(user=self.request.user)
        
        # Filter by activity type if provided
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
            
        # Filter by content type if provided
        content_type = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')
        if content_type and object_id:
            try:
                content_type = ContentType.objects.get(model=content_type)
                queryset = queryset.filter(
                    content_type=content_type,
                    object_id=object_id
                )
            except ContentType.DoesNotExist:
                return UserActivity.objects.none()
                
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create a new activity."""
        serializer = ActivityCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        activity = serializer.save()
        
        return Response(
            UserActivitySerializer(activity).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent activities with pagination."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserEngagementViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for user engagement scores."""
    serializer_class = UserEngagementScoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return engagement score for the current user."""
        return UserEngagementScore.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """Recalculate engagement scores."""
        score, created = UserEngagementScore.objects.get_or_create(
            user=request.user
        )
        score.update_scores()
        return Response(
            UserEngagementScoreSerializer(score).data,
            status=status.HTTP_200_OK
        )


class ActivityStatsViewSet(viewsets.ViewSet):
    """API endpoint for activity statistics."""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get activity statistics for the current user."""
        from django.db.models import Count, F, Value
        from django.db.models.functions import TruncDay, TruncWeek
        
        # Time-based activity counts
        daily_activities = (
            UserActivity.objects
            .filter(user=request.user)
            .annotate(date=TruncDay('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('-date')[:30]  # Last 30 days
        )
        
        # Activity type distribution
        activity_distribution = (
            UserActivity.objects
            .filter(user=request.user)
            .values('activity_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Content type distribution
        content_distribution = (
            UserActivity.objects
            .filter(
                user=request.user,
                content_type__isnull=False
            )
            .values('content_type__model')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        return Response({
            'daily_activity': list(daily_activities),
            'activity_distribution': list(activity_distribution),
            'content_distribution': list(content_distribution),
        })
