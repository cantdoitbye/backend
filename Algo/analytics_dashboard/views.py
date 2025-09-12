from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
import json
from datetime import timedelta

from .models import (
    ABTestExperiment, ExperimentParticipant, ExperimentMetric,
    RealTimeMetric, AnalyticsDashboard, UserBehaviorInsight
)
from .services import AnalyticsService, RealtimeMetricsCollector
from .serializers import (
    ABTestExperimentSerializer, ExperimentParticipantSerializer,
    RealTimeMetricSerializer, UserBehaviorInsightSerializer
)


# Dashboard Views
@staff_member_required
def analytics_dashboard(request):
    """
    Main analytics dashboard view
    """
    context = {
        'title': 'Analytics Dashboard',
        'active_experiments_count': ABTestExperiment.objects.filter(status='running').count(),
        'total_users': ExperimentParticipant.objects.values('user').distinct().count(),
    }
    return render(request, 'analytics_dashboard/dashboard.html', context)


@staff_member_required
def ab_testing_dashboard(request):
    """
    A/B Testing management dashboard
    """
    experiments = ABTestExperiment.objects.all().order_by('-created_at')
    
    context = {
        'title': 'A/B Testing Dashboard',
        'experiments': experiments,
    }
    return render(request, 'analytics_dashboard/ab_testing.html', context)


@staff_member_required
def performance_monitoring(request):
    """
    Real-time performance monitoring dashboard
    """
    context = {
        'title': 'Performance Monitoring',
    }
    return render(request, 'analytics_dashboard/performance.html', context)


@staff_member_required
def user_insights_dashboard(request):
    """
    User behavior insights dashboard
    """
    recent_insights = UserBehaviorInsight.objects.select_related('user').order_by('-last_calculated')[:50]
    
    context = {
        'title': 'User Insights',
        'recent_insights': recent_insights,
    }
    return render(request, 'analytics_dashboard/user_insights.html', context)


# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def dashboard_metrics(request):
    """
    Get dashboard metrics for specified time range
    """
    timerange = request.GET.get('timerange', '1h')
    
    service = AnalyticsService()
    metrics = service.get_dashboard_metrics(timerange)
    
    return Response({
        'status': 'success',
        'data': metrics,
        'timerange': timerange,
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def realtime_metrics(request):
    """
    Get recent real-time metrics
    """
    limit = int(request.GET.get('limit', 100))
    category = request.GET.get('category')
    
    metrics_query = RealTimeMetric.objects.all()
    
    if category:
        metrics_query = metrics_query.filter(metric_category=category)
    
    metrics = metrics_query.order_by('-timestamp')[:limit]
    serializer = RealTimeMetricSerializer(metrics, many=True)
    
    return Response({
        'status': 'success',
        'data': serializer.data,
        'count': len(serializer.data)
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ab_experiments(request):
    """
    List or create A/B test experiments
    """
    if request.method == 'GET':
        experiments = ABTestExperiment.objects.all().order_by('-created_at')
        serializer = ABTestExperimentSerializer(experiments, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = ABTestExperimentSerializer(data=request.data)
        
        if serializer.is_valid():
            experiment = serializer.save(created_by=request.user)
            
            return Response({
                'status': 'success',
                'data': ABTestExperimentSerializer(experiment).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ab_experiment_detail(request, experiment_id):
    """
    Get, update, or delete a specific A/B test experiment
    """
    experiment = get_object_or_404(ABTestExperiment, id=experiment_id)
    
    if request.method == 'GET':
        serializer = ABTestExperimentSerializer(experiment)
        
        # Include results if experiment is completed
        service = AnalyticsService()
        results = service.get_experiment_results(experiment_id)
        
        data = serializer.data
        data['results'] = results
        
        return Response({
            'status': 'success',
            'data': data
        })
    
    elif request.method == 'PUT':
        serializer = ABTestExperimentSerializer(experiment, data=request.data, partial=True)
        
        if serializer.is_valid():
            experiment = serializer.save()
            
            return Response({
                'status': 'success',
                'data': ABTestExperimentSerializer(experiment).data
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        experiment.delete()
        
        return Response({
            'status': 'success',
            'message': 'Experiment deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def start_experiment(request, experiment_id):
    """
    Start an A/B test experiment
    """
    experiment = get_object_or_404(ABTestExperiment, id=experiment_id)
    
    if experiment.status != 'draft':
        return Response({
            'status': 'error',
            'message': 'Experiment must be in draft status to start'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Start the experiment
    experiment.status = 'running'
    experiment.start_date = timezone.now()
    experiment.end_date = experiment.start_date + timedelta(days=experiment.duration_days)
    experiment.save()
    
    # Broadcast experiment update
    service = AnalyticsService()
    if service.channel_layer:
        from asgiref.sync import async_to_sync
        async_to_sync(service.channel_layer.group_send)(
            'analytics_dashboard',
            {
                'type': 'experiment_update',
                'experiment_id': str(experiment.id),
                'status': experiment.status,
                'data': ABTestExperimentSerializer(experiment).data
            }
        )
    
    return Response({
        'status': 'success',
        'data': ABTestExperimentSerializer(experiment).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def stop_experiment(request, experiment_id):
    """
    Stop an A/B test experiment
    """
    experiment = get_object_or_404(ABTestExperiment, id=experiment_id)
    
    if experiment.status != 'running':
        return Response({
            'status': 'error',
            'message': 'Only running experiments can be stopped'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Stop the experiment
    experiment.status = 'completed'
    experiment.end_date = timezone.now()
    experiment.save()
    
    # Calculate final results
    service = AnalyticsService()
    results = service.get_experiment_results(experiment_id)
    
    return Response({
        'status': 'success',
        'data': ABTestExperimentSerializer(experiment).data,
        'results': results
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def experiment_participants(request, experiment_id):
    """
    Get participants for a specific experiment
    """
    experiment = get_object_or_404(ABTestExperiment, id=experiment_id)
    participants = experiment.participants.select_related('user').all()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(participants, 50)
    paginated_participants = paginator.get_page(page)
    
    serializer = ExperimentParticipantSerializer(paginated_participants, many=True)
    
    return Response({
        'status': 'success',
        'data': serializer.data,
        'pagination': {
            'page': page,
            'pages': paginator.num_pages,
            'count': paginator.count
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def user_behavior_insights(request, user_id=None):
    """
    Get user behavior insights
    """
    if user_id:
        # Get insights for specific user
        insights = get_object_or_404(UserBehaviorInsight, user_id=user_id)
        serializer = UserBehaviorInsightSerializer(insights)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    else:
        # Get insights for all users with pagination
        insights = UserBehaviorInsight.objects.select_related('user').order_by('-last_calculated')
        
        page = request.GET.get('page', 1)
        paginator = Paginator(insights, 20)
        paginated_insights = paginator.get_page(page)
        
        serializer = UserBehaviorInsightSerializer(paginated_insights, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'pagination': {
                'page': page,
                'pages': paginator.num_pages,
                'count': paginator.count
            }
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_user_interaction(request):
    """
    Record user interaction for analytics
    """
    try:
        # Extract interaction data
        interaction_type = request.data.get('type')
        content_id = request.data.get('content_id')
        session_duration = request.data.get('session_duration')
        metadata = request.data.get('metadata', {})
        
        # Record the interaction
        collector = RealtimeMetricsCollector()
        collector.collect_engagement_metrics(
            user_id=request.user.id,
            content_id=content_id,
            action=interaction_type,
            session_duration=session_duration
        )
        
        # Check if user is in any active experiments
        active_experiments = ABTestExperiment.objects.filter(
            status='running',
            participants__user=request.user
        )
        
        # Record experiment metrics
        service = AnalyticsService()
        for experiment in active_experiments:
            try:
                participant = experiment.participants.get(user=request.user)
                service.record_experiment_metric(
                    experiment=experiment,
                    participant=participant,
                    metric_name=interaction_type,
                    metric_value=1,
                    metric_type='count',
                    metadata=metadata
                )
            except ExperimentParticipant.DoesNotExist:
                continue
        
        return Response({
            'status': 'success',
            'message': 'Interaction recorded successfully'
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error recording interaction: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def system_health(request):
    """
    Get system health metrics
    """
    # This would integrate with actual health check systems
    # For now, we'll return mock data
    
    health_data = {
        'status': 'healthy',
        'services': {
            'database': {
                'status': 'healthy',
                'response_time_ms': 12.5,
                'connections': 45
            },
            'redis': {
                'status': 'healthy',
                'memory_usage': '234MB',
                'hit_rate': 0.89
            },
            'celery': {
                'status': 'healthy',
                'active_tasks': 3,
                'processed_tasks': 1247
            }
        },
        'performance': {
            'avg_response_time_ms': 87.3,
            'error_rate_percent': 0.02,
            'requests_per_minute': 156
        },
        'timestamp': timezone.now().isoformat()
    }
    
    return Response({
        'status': 'success',
        'data': health_data
    })
