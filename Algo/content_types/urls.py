"""
URL configuration for the Content Types app.

Defines API endpoints for content type management and registration.
"""

from django.urls import path, include
from . import views

# Note: ViewSets will be implemented later
# For now, using individual API views

app_name = 'content_types'

urlpatterns = [
    # Content type registry
    path('registry/', views.ContentTypeRegistryView.as_view(), name='content-type-registry'),
    path('registry/register/', views.RegisterContentTypeView.as_view(), name='register-content-type'),
    
    # Content discovery and search
    path('search/', views.ContentSearchView.as_view(), name='content-search'),
    path('trending/', views.TrendingContentView.as_view(), name='trending-content'),
    path('featured/', views.FeaturedContentView.as_view(), name='featured-content'),
    
    # Content analytics
    path('analytics/engagement/', views.EngagementAnalyticsView.as_view(), name='engagement-analytics'),
    path('analytics/performance/', views.ContentPerformanceView.as_view(), name='content-performance'),
    
    # Bulk operations
    path('bulk/import/', views.BulkContentImportView.as_view(), name='bulk-content-import'),
    path('bulk/update/', views.BulkContentUpdateView.as_view(), name='bulk-content-update'),
    
    # ViewSet URLs will be added when ViewSets are implemented
    # path('posts/', views.PostViewSet.as_view({'get': 'list'})),
    # path('communities/', views.CommunityViewSet.as_view({'get': 'list'})),
    # path('products/', views.ProductViewSet.as_view({'get': 'list'})),
    # path('engagements/', views.EngagementViewSet.as_view({'get': 'list'})),
]
