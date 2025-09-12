"""
URL configuration for the Analytics app.

Defines API endpoints for analytics, monitoring, and logging.
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Feed analytics
    path('feed/', views.FeedAnalyticsView.as_view(), name='feed-analytics'),
    path('feed/performance/', views.FeedPerformanceAnalyticsView.as_view(), name='feed-performance-analytics'),
    path('feed/composition/', views.FeedCompositionAnalyticsView.as_view(), name='feed-composition-analytics'),
    
    # User behavior analytics
    path('users/behavior/', views.UserBehaviorAnalyticsView.as_view(), name='user-behavior-analytics'),
    path('users/engagement/', views.UserEngagementAnalyticsView.as_view(), name='user-engagement-analytics'),
    path('users/retention/', views.UserRetentionAnalyticsView.as_view(), name='user-retention-analytics'),
    
    # Content analytics
    path('content/performance/', views.ContentPerformanceAnalyticsView.as_view(), name='content-performance-analytics'),
    path('content/trending/', views.ContentTrendingAnalyticsView.as_view(), name='content-trending-analytics'),
    path('content/discovery/', views.ContentDiscoveryAnalyticsView.as_view(), name='content-discovery-analytics'),
    
    # Algorithm analytics
    path('algorithm/effectiveness/', views.AlgorithmEffectivenessView.as_view(), name='algorithm-effectiveness'),
    path('algorithm/ab-testing/', views.ABTestingAnalyticsView.as_view(), name='ab-testing-analytics'),
    path('algorithm/scoring/', views.ScoringEngineAnalyticsView.as_view(), name='scoring-engine-analytics'),
    
    # System monitoring
    path('system/health/', views.SystemHealthView.as_view(), name='system-health'),
    path('system/performance/', views.SystemPerformanceView.as_view(), name='system-performance'),
    path('system/errors/', views.SystemErrorsView.as_view(), name='system-errors'),
    
    # Real-time metrics
    path('realtime/dashboard/', views.RealtimeDashboardView.as_view(), name='realtime-dashboard'),
    path('realtime/feed-generation/', views.RealtimeFeedGenerationView.as_view(), name='realtime-feed-generation'),
    path('realtime/user-activity/', views.RealtimeUserActivityView.as_view(), name='realtime-user-activity'),
    
    # Reports and exports
    path('reports/', views.AnalyticsReportsView.as_view(), name='analytics-reports'),
    path('reports/generate/', views.GenerateAnalyticsReportView.as_view(), name='generate-analytics-report'),
    path('reports/export/', views.ExportAnalyticsDataView.as_view(), name='export-analytics-data'),
    
    # Logging and debugging
    path('logs/', views.SystemLogsView.as_view(), name='system-logs'),
    path('logs/feed/', views.FeedLogsView.as_view(), name='feed-logs'),
    path('logs/errors/', views.ErrorLogsView.as_view(), name='error-logs'),
]
