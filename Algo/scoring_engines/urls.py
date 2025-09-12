"""
URL configuration for the Scoring Engines app.

Defines API endpoints for scoring engine management and testing.
"""

from django.urls import path
from . import views

app_name = 'scoring_engines'

urlpatterns = [
    # Scoring engine registry and management
    path('registry/', views.ScoringEngineRegistryView.as_view(), name='scoring-engine-registry'),
    path('register/', views.RegisterScoringEngineView.as_view(), name='register-scoring-engine'),
    
    # Individual scoring engines
    path('personal-connections/', views.PersonalConnectionsScoringView.as_view(), name='personal-connections-scoring'),
    path('interest-based/', views.InterestBasedScoringView.as_view(), name='interest-based-scoring'),
    path('trending/', views.TrendingScoringView.as_view(), name='trending-scoring'),
    path('discovery/', views.DiscoveryScoringView.as_view(), name='discovery-scoring'),
    
    # Scoring testing and analysis
    path('test/', views.ScoringEngineTestView.as_view(), name='scoring-engine-test'),
    path('benchmark/', views.ScoringBenchmarkView.as_view(), name='scoring-benchmark'),
    path('compare/', views.ScoringComparisonView.as_view(), name='scoring-comparison'),
    
    # Scoring configuration
    path('config/', views.ScoringConfigurationView.as_view(), name='scoring-configuration'),
    path('weights/', views.ScoringWeightsView.as_view(), name='scoring-weights'),
    
    # Analytics and monitoring
    path('analytics/', views.ScoringAnalyticsView.as_view(), name='scoring-analytics'),
    path('performance/', views.ScoringPerformanceView.as_view(), name='scoring-performance'),
]
