from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, F
from django.core.cache import cache
from .models import UserProfile, Connection, Interest, UserInterest, InterestCollection
from .serializers import (
    UserProfileSerializer, UserProfileUpdateSerializer,
    ConnectionSerializer, ConnectionCreateSerializer,
    InterestSerializer, UserInterestSerializer, UserInterestCreateSerializer,
    InterestCollectionSerializer
)
from analytics.utils import log_user_event
import structlog

logger = structlog.get_logger(__name__)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profile management."""
    
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_private', 'allow_recommendations', 'ab_test_group']
    search_fields = ['username', 'first_name', 'last_name', 'bio']
    ordering_fields = ['engagement_score', 'total_connections', 'last_active']
    
    def get_queryset(self):
        if self.action == 'list':
            # Only show public profiles in list view (except own profile)
            return self.queryset.filter(
                Q(is_private=False) | Q(id=self.request.user.id)
            )
        return self.queryset
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer
    
    def get_permissions(self):
        """Allow profile creation without authentication."""
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated]
        return super().get_permissions()
    
    def perform_update(self, serializer):
        """Ensure users can only update their own profile."""
        if serializer.instance.id != self.request.user.id:
            raise PermissionError("Cannot update another user's profile")
        
        serializer.save()
        log_user_event(
            user_id=self.request.user.id,
            event_type='profile_updated',
            metadata={'updated_fields': list(serializer.validated_data.keys())}
        )
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_feed_composition(self, request):
        """Update user's feed composition preferences."""
        user = request.user
        composition = request.data.get('feed_composition')
        
        if not composition:
            return Response(
                {'error': 'feed_composition is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate composition ratios
        total = sum(composition.values())
        if not (0.95 <= total <= 1.05):
            return Response(
                {'error': 'Feed composition ratios must sum to approximately 1.0'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.feed_composition = composition
        user.save(update_fields=['feed_composition'])
        
        # Clear user's feed cache
        cache.delete(f'user_feed:{user.id}')
        
        log_user_event(
            user_id=user.id,
            event_type='feed_composition_updated',
            metadata={'new_composition': composition}
        )
        
        return Response({'message': 'Feed composition updated successfully'})
    
    @action(detail=True, methods=['get'])
    def connections(self, request, pk=None):
        """Get user's connections."""
        user = self.get_object()
        
        # Check if user can view these connections
        if user.is_private and user.id != request.user.id:
            return Response(
                {'error': 'User profile is private'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        connections = Connection.objects.filter(
            from_user=user,
            status='accepted'
        ).select_related('to_user')
        
        serializer = ConnectionSerializer(connections, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def interests(self, request, pk=None):
        """Get user's interests."""
        user = self.get_object()
        
        interests = UserInterest.objects.filter(
            user=user
        ).select_related('interest').order_by('-strength')
        
        serializer = UserInterestSerializer(interests, many=True)
        return Response(serializer.data)


class ConnectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user connections."""
    
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['circle_type', 'status']
    ordering_fields = ['created_at', 'last_interaction', 'interaction_count']
    
    def get_queryset(self):
        """Only show user's own connections."""
        return self.queryset.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        ).select_related('from_user', 'to_user')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConnectionCreateSerializer
        return ConnectionSerializer
    
    @action(detail=False, methods=['get'])
    def circles(self, request):
        """Get connections organized by circle type."""
        cache_key = f'user_connections:{request.user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        connections = Connection.objects.filter(
            from_user=request.user,
            status='accepted'
        ).values('circle_type').annotate(
            count=Count('id')
        ).order_by('circle_type')
        
        # Format response
        circles_data = {
            circle['circle_type']: circle['count']
            for circle in connections
        }
        
        # Add circle weights for reference
        from django.conf import settings
        response_data = {
            'circles': circles_data,
            'weights': settings.FEED_CONFIG['CIRCLE_WEIGHTS']
        }
        
        # Cache for 1 hour
        cache.set(cache_key, response_data, 3600)
        
        return Response(response_data)
    
    @action(detail=True, methods=['patch'])
    def update_circle(self, request, pk=None):
        """Update connection's circle type."""
        connection = self.get_object()
        
        # Only connection creator can update circle
        if connection.from_user != request.user:
            return Response(
                {'error': 'Can only update your own connections'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        circle_type = request.data.get('circle_type')
        if circle_type not in ['inner', 'outer', 'universe']:
            return Response(
                {'error': 'Invalid circle type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        connection.circle_type = circle_type
        connection.save(update_fields=['circle_type'])
        
        log_user_event(
            user_id=request.user.id,
            event_type='connection_circle_updated',
            metadata={
                'connection_id': connection.id,
                'new_circle_type': circle_type
            }
        )
        
        serializer = self.get_serializer(connection)
        return Response(serializer.data)


class InterestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing available interests."""
    
    queryset = Interest.objects.filter(is_active=True)
    serializer_class = InterestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'follower_count', 'trending_score']
    ordering = ['-trending_score', '-follower_count']
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending interests."""
        trending_interests = self.get_queryset().filter(
            trending_score__gte=0.5
        ).order_by('-trending_score')[:20]
        
        serializer = self.get_serializer(trending_interests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get interest categories."""
        categories = Interest.objects.filter(
            is_active=True
        ).values('category').annotate(
            count=Count('id')
        ).order_by('category')
        
        return Response({
            'categories': [
                {
                    'name': cat['category'],
                    'count': cat['count']
                }
                for cat in categories
            ]
        })


class UserInterestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user interests."""
    
    queryset = UserInterest.objects.all()
    serializer_class = UserInterestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['interest_type']
    ordering_fields = ['strength', 'engagement_count', 'created_at']
    ordering = ['-strength']
    
    def get_queryset(self):
        """Only show user's own interests."""
        return self.queryset.filter(
            user=self.request.user
        ).select_related('interest')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserInterestCreateSerializer
        return UserInterestSerializer
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get interest recommendations for user."""
        from scoring_engines.recommendation import InterestRecommendationEngine
        
        engine = InterestRecommendationEngine()
        recommended_interests = engine.get_recommendations(
            user=request.user,
            limit=20
        )
        
        serializer = InterestSerializer(recommended_interests, many=True)
        return Response(serializer.data)


class InterestCollectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing interest collections."""
    
    queryset = InterestCollection.objects.all()
    serializer_class = InterestCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_system']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        return self.queryset.prefetch_related('interests').select_related('creator')