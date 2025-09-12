from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from . import views, api_views

# API v1 Router (current version)
api_v1_router = DefaultRouter()
api_v1_router.register(r'activities', views.UserActivityViewSet, basename='activity')
api_v1_router.register(r'engagement', views.UserEngagementViewSet, basename='engagement')
api_v1_router.register(r'stats', views.ActivityStatsViewSet, basename='activity-stats')

# New API v2 Router
api_v2_router = SimpleRouter()
api_v2_router.register(r'feed', api_views.ActivityFeedViewSet, basename='activity-feed')
api_v2_router.register(
    r'content/(?P<content_type>\w+)/(?P<object_id>\d+)/activities',
    api_views.ContentActivityViewSet,
    basename='content-activities'
)

# Include versioned API URLs
api_urlpatterns = [
    path('v1/', include(api_v1_router.urls)),
    path('v2/', include(api_v2_router.urls)),
]

urlpatterns = [
    # API endpoints
    path('api/', include(api_urlpatterns)),
    
    # Backward compatibility
    path('', include(api_v1_router.urls)),
]
