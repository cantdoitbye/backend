"""
URL configuration for the Caching app.

Defines API endpoints for Redis cache management and monitoring.
"""

from django.urls import path
from . import views

app_name = 'caching'

urlpatterns = [
    # Cache management
    path('status/', views.CacheStatusView.as_view(), name='cache-status'),
    path('clear/', views.ClearCacheView.as_view(), name='clear-cache'),
    path('warm/', views.WarmCacheView.as_view(), name='warm-cache'),
    
    # Feed cache operations
    path('feed/', views.FeedCacheView.as_view(), name='feed-cache'),
    path('feed/invalidate/', views.InvalidateFeedCacheView.as_view(), name='invalidate-feed-cache'),
    path('feed/preload/', views.PreloadFeedCacheView.as_view(), name='preload-feed-cache'),
    
    # Trending cache operations
    path('trending/', views.TrendingCacheView.as_view(), name='trending-cache'),
    path('trending/update/', views.UpdateTrendingCacheView.as_view(), name='update-trending-cache'),
    path('trending/metrics/', views.TrendingMetricsCacheView.as_view(), name='trending-metrics-cache'),
    
    # Connection cache operations
    path('connections/', views.ConnectionCacheView.as_view(), name='connection-cache'),
    path('connections/circles/', views.ConnectionCirclesCacheView.as_view(), name='connection-circles-cache'),
    
    # Interest cache operations
    path('interests/', views.InterestCacheView.as_view(), name='interest-cache'),
    path('interests/recommendations/', views.InterestRecommendationsCacheView.as_view(), name='interest-recommendations-cache'),
    
    # Cache analytics and monitoring
    path('analytics/', views.CacheAnalyticsView.as_view(), name='cache-analytics'),
    path('performance/', views.CachePerformanceView.as_view(), name='cache-performance'),
    path('hit-rates/', views.CacheHitRatesView.as_view(), name='cache-hit-rates'),
    
    # Redis operations
    path('redis/info/', views.RedisInfoView.as_view(), name='redis-info'),
    path('redis/memory/', views.RedisMemoryView.as_view(), name='redis-memory'),
    path('redis/keys/', views.RedisKeysView.as_view(), name='redis-keys'),
]
