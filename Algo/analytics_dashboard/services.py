from django.core.cache import cache
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q, Max, Min
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import numpy as np
from scipy import stats
from .models import (
    ABTestExperiment, ExperimentParticipant, ExperimentMetric,
    RealTimeMetric, UserBehaviorInsight
)


class AnalyticsService:
    """
    Core service for analytics processing and A/B testing
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def record_metric(self, metric_name, value, category='general', unit='', metadata=None):
        """
        Record a real-time metric and broadcast to connected clients
        """
        metric = RealTimeMetric.objects.create(
            metric_name=metric_name,
            metric_category=category,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        
        # Broadcast to WebSocket clients
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                f'metric_{metric_name}',
                {
                    'type': 'metric_update',
                    'metric_name': metric_name,
                    'value': value,
                    'unit': unit,
                    'timestamp': metric.timestamp.isoformat()
                }
            )
        
        return metric
    
    def get_dashboard_metrics(self, timerange='1h'):
        """
        Get aggregated metrics for dashboard display
        """
        cache_key = f'dashboard_metrics_{timerange}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Calculate time delta
        timerange_map = {
            '1h': timezone.timedelta(hours=1),
            '6h': timezone.timedelta(hours=6),
            '24h': timezone.timedelta(hours=24),
            '7d': timezone.timedelta(days=7)
        }
        
        delta = timerange_map.get(timerange, timezone.timedelta(hours=1))
        since = timezone.now() - delta
        
        # Aggregate metrics by category
        metrics = RealTimeMetric.objects.filter(
            timestamp__gte=since
        ).values(
            'metric_category', 'metric_name'
        ).annotate(
            avg_value=Avg('value'),
            max_value=Max('value'),
            min_value=Min('value'),
            count=Count('id')
        )
        
        # Organize by category
        dashboard_data = {}
        for metric in metrics:
            category = metric['metric_category']
            if category not in dashboard_data:
                dashboard_data[category] = {}
            
            dashboard_data[category][metric['metric_name']] = {
                'avg': metric['avg_value'],
                'max': metric['max_value'],
                'min': metric['min_value'],
                'count': metric['count']
            }
        
        # Cache for 5 minutes
        cache.set(cache_key, dashboard_data, 300)
        
        return dashboard_data
    
    def create_ab_test(self, name, description, control_config, treatment_config, 
                      traffic_allocation=10.0, duration_days=14, created_by_user=None):
        """
        Create a new A/B test experiment
        """
        experiment = ABTestExperiment.objects.create(
            name=name,
            description=description,
            control_config=control_config,
            treatment_config=treatment_config,
            traffic_allocation=traffic_allocation,
            duration_days=duration_days,
            created_by=created_by_user
        )
        
        return experiment
    
    def assign_user_to_experiment(self, experiment, user):
        """
        Assign a user to an A/B test experiment
        """
        # Check if user is already in experiment
        try:
            participant = ExperimentParticipant.objects.get(
                experiment=experiment,
                user=user
            )
            return participant
        except ExperimentParticipant.DoesNotExist:
            pass
        
        # Random assignment with traffic allocation
        import random
        
        # Check if user should be included based on traffic allocation
        if random.random() * 100 > experiment.traffic_allocation:
            return None  # User not included in experiment
        
        # Assign to control or treatment group (50/50 split)
        group = 'control' if random.random() < 0.5 else 'treatment'
        
        participant = ExperimentParticipant.objects.create(
            experiment=experiment,
            user=user,
            group=group
        )
        
        return participant
    
    def record_experiment_metric(self, experiment, participant, metric_name, 
                                metric_value, metric_type='count', session_id=None, metadata=None):
        """
        Record a metric for an experiment participant
        """
        metric = ExperimentMetric.objects.create(
            experiment=experiment,
            participant=participant,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            session_id=session_id or '',
            metadata=metadata or {}
        )
        
        # Update participant activity
        participant.last_activity = timezone.now()
        if not participant.first_exposure:
            participant.first_exposure = timezone.now()
        participant.save()
        
        return metric
    
    def get_experiment_results(self, experiment_id):
        """
        Calculate A/B test experiment results with statistical significance
        """
        try:
            experiment = ABTestExperiment.objects.get(id=experiment_id)
        except ABTestExperiment.DoesNotExist:
            return None
        
        cache_key = f'experiment_results_{experiment_id}'
        cached_results = cache.get(cache_key)
        
        if cached_results:
            return cached_results
        
        # Get participants by group
        control_participants = experiment.participants.filter(group='control')
        treatment_participants = experiment.participants.filter(group='treatment')
        
        # Calculate primary metric for each group
        control_metrics = ExperimentMetric.objects.filter(
            experiment=experiment,
            participant__in=control_participants,
            metric_name=experiment.primary_metric
        )
        
        treatment_metrics = ExperimentMetric.objects.filter(
            experiment=experiment,
            participant__in=treatment_participants,
            metric_name=experiment.primary_metric
        )
        
        # Calculate statistics
        control_values = list(control_metrics.values_list('metric_value', flat=True))
        treatment_values = list(treatment_metrics.values_list('metric_value', flat=True))
        
        if len(control_values) == 0 or len(treatment_values) == 0:
            return {
                'error': 'Insufficient data for analysis',
                'control_count': len(control_values),
                'treatment_count': len(treatment_values)
            }
        
        # Statistical analysis
        control_mean = np.mean(control_values)
        treatment_mean = np.mean(treatment_values)
        control_std = np.std(control_values)
        treatment_std = np.std(treatment_values)
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(treatment_values, control_values)
        
        # Calculate confidence interval
        confidence_level = experiment.confidence_level / 100
        alpha = 1 - confidence_level
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(control_values) - 1) * control_std**2 + 
                             (len(treatment_values) - 1) * treatment_std**2) / 
                            (len(control_values) + len(treatment_values) - 2))
        
        effect_size = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0
        
        # Determine significance
        is_significant = p_value < alpha
        
        # Determine winner
        if is_significant:
            if treatment_mean > control_mean:
                winner = 'treatment'
            else:
                winner = 'control'
        else:
            winner = 'inconclusive'
        
        results = {
            'control': {
                'participants': len(control_values),
                'mean': control_mean,
                'std': control_std
            },
            'treatment': {
                'participants': len(treatment_values),
                'mean': treatment_mean,
                'std': treatment_std
            },
            'statistics': {
                't_statistic': t_stat,
                'p_value': p_value,
                'effect_size': effect_size,
                'is_significant': is_significant,
                'confidence_level': confidence_level,
                'winner': winner
            },
            'improvement': {
                'absolute': treatment_mean - control_mean,
                'relative_percent': ((treatment_mean - control_mean) / control_mean * 100) if control_mean > 0 else 0
            }
        }
        
        # Update experiment with results
        experiment.is_statistically_significant = is_significant
        experiment.winner = winner
        experiment.results_summary = results
        experiment.save()
        
        # Cache results for 10 minutes
        cache.set(cache_key, results, 600)
        
        return results
    
    def calculate_user_insights(self, user):
        """
        Calculate behavioral insights for a user
        """
        # This would analyze user interaction data
        # For now, we'll return mock insights
        
        insight, created = UserBehaviorInsight.objects.get_or_create(
            user=user,
            defaults={
                'session_duration_avg': 15.5,  # minutes
                'daily_active_hours': [9, 12, 15, 18, 21],  # peak hours
                'preferred_content_types': {
                    'posts': 0.6,
                    'communities': 0.3,
                    'products': 0.1
                },
                'engagement_patterns': {
                    'likes_per_session': 12,
                    'comments_per_session': 3,
                    'shares_per_session': 1
                },
                'optimal_feed_composition': {
                    'personal_connections': 0.45,
                    'interest_based': 0.30,
                    'trending_content': 0.25
                },
                'engagement_score': 0.75,
                'retention_score': 0.82
            }
        )
        
        return insight
    
    def send_system_alert(self, level, message):
        """
        Send system alert to connected dashboard clients
        """
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                'analytics_dashboard',
                {
                    'type': 'system_alert',
                    'level': level,
                    'message': message,
                    'timestamp': timezone.now().isoformat()
                }
            )


class RealtimeMetricsCollector:
    """
    Service for collecting and processing real-time metrics
    """
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def collect_feed_metrics(self, user_id, generation_time_ms, cache_hit, item_count):
        """
        Collect feed generation metrics
        """
        self.analytics_service.record_metric(
            'feed_generation_time',
            generation_time_ms,
            'feed_performance',
            'ms',
            {'user_id': user_id, 'cache_hit': cache_hit, 'item_count': item_count}
        )
        
        if cache_hit:
            self.analytics_service.record_metric(
                'feed_cache_hits',
                1,
                'cache_performance',
                'count'
            )
        else:
            self.analytics_service.record_metric(
                'feed_cache_misses',
                1,
                'cache_performance',
                'count'
            )
    
    def collect_engagement_metrics(self, user_id, content_id, action, session_duration=None):
        """
        Collect user engagement metrics
        """
        self.analytics_service.record_metric(
            f'user_engagement_{action}',
            1,
            'user_engagement',
            'count',
            {'user_id': user_id, 'content_id': content_id}
        )
        
        if session_duration:
            self.analytics_service.record_metric(
                'session_duration',
                session_duration,
                'user_engagement',
                'seconds',
                {'user_id': user_id}
            )
    
    def collect_system_metrics(self, metric_name, value, unit=''):
        """
        Collect system performance metrics
        """
        self.analytics_service.record_metric(
            metric_name,
            value,
            'system_health',
            unit
        )
