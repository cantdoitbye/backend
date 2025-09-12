from django.urls import path, include
from . import views

# API URL patterns
api_urlpatterns = [
    # Dashboard metrics
    path('dashboard/metrics/', views.dashboard_metrics, name='dashboard_metrics'),
    path('realtime/metrics/', views.realtime_metrics, name='realtime_metrics'),
    path('system/health/', views.system_health, name='system_health'),
    
    # A/B Testing
    path('experiments/', views.ab_experiments, name='ab_experiments'),
    path('experiments/<uuid:experiment_id>/', views.ab_experiment_detail, name='ab_experiment_detail'),
    path('experiments/<uuid:experiment_id>/start/', views.start_experiment, name='start_experiment'),
    path('experiments/<uuid:experiment_id>/stop/', views.stop_experiment, name='stop_experiment'),
    path('experiments/<uuid:experiment_id>/participants/', views.experiment_participants, name='experiment_participants'),
    
    # User insights
    path('insights/', views.user_behavior_insights, name='user_behavior_insights'),
    path('insights/<int:user_id>/', views.user_behavior_insights, name='user_behavior_insights_detail'),
    
    # Interaction tracking
    path('interactions/', views.record_user_interaction, name='record_user_interaction'),
]

# Dashboard URL patterns
dashboard_urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('ab-testing/', views.ab_testing_dashboard, name='ab_testing_dashboard'),
    path('performance/', views.performance_monitoring, name='performance_monitoring'),
    path('user-insights/', views.user_insights_dashboard, name='user_insights_dashboard'),
]

urlpatterns = [
    path('api/analytics/', include(api_urlpatterns)),
    path('admin/analytics/', include(dashboard_urlpatterns)),
]
