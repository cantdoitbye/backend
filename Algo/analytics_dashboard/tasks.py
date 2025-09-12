from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q, Avg, Max, Min
from datetime import timedelta
import logging
from .models import (
    ABTestExperiment, ExperimentParticipant, RealTimeMetric,
    UserBehaviorInsight
)
from .services import AnalyticsService, RealtimeMetricsCollector

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def calculate_experiment_results(self, experiment_id):
    """
    Background task to calculate A/B test experiment results
    """
    try:
        logger.info(f"Calculating results for experiment {experiment_id}")
        
        service = AnalyticsService()
        results = service.get_experiment_results(experiment_id)
        
        if results and not results.get('error'):
            # Update experiment with latest results
            experiment = ABTestExperiment.objects.get(id=experiment_id)
            experiment.results_summary = results
            experiment.save()
            
            logger.info(f"Successfully calculated results for experiment {experiment_id}")
            return {'status': 'success', 'experiment_id': experiment_id}
        else:
            logger.warning(f"Insufficient data for experiment {experiment_id}")
            return {'status': 'insufficient_data', 'experiment_id': experiment_id}
            
    except ABTestExperiment.DoesNotExist:
        logger.error(f"Experiment {experiment_id} not found")
        return {'status': 'error', 'message': 'Experiment not found'}
    except Exception as e:
        logger.error(f"Error calculating experiment results: {str(e)}")
        self.retry(countdown=60, max_retries=3)


@shared_task
def process_user_behavior_insights():
    """
    Background task to process user behavior insights for all users
    """
    try:
        logger.info("Starting user behavior insights processing")
        
        # Get users who need insight updates (haven't been updated in last 24 hours)
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        users_needing_update = User.objects.filter(
            Q(behavior_insights__isnull=True) |
            Q(behavior_insights__last_calculated__lt=cutoff_time)
        )[:100]  # Process in batches of 100
        
        service = AnalyticsService()
        updated_count = 0
        
        for user in users_needing_update:
            try:
                service.calculate_user_insights(user)
                updated_count += 1
            except Exception as e:
                logger.error(f"Error processing insights for user {user.id}: {str(e)}")
                continue
        
        logger.info(f"Processed insights for {updated_count} users")
        return {'status': 'success', 'updated_count': updated_count}
        
    except Exception as e:
        logger.error(f"Error in user behavior insights processing: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def aggregate_realtime_metrics():
    """
    Background task to aggregate real-time metrics for better performance
    """
    try:
        logger.info("Starting real-time metrics aggregation")
        
        # Aggregate metrics from the last hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Get unique metric names and categories
        metric_groups = RealTimeMetric.objects.filter(
            timestamp__gte=one_hour_ago
        ).values('metric_name', 'metric_category').distinct()
        
        aggregated_count = 0
        collector = RealtimeMetricsCollector()
        
        for group in metric_groups:
            metric_name = group['metric_name']
            category = group['metric_category']
            
            # Calculate aggregations
            metrics = RealTimeMetric.objects.filter(
                metric_name=metric_name,
                metric_category=category,
                timestamp__gte=one_hour_ago
            )
            
            if metrics.exists():
                avg_value = metrics.aggregate(Avg('value'))['value__avg']
                max_value = metrics.aggregate(Max('value'))['value__max']
                min_value = metrics.aggregate(Min('value'))['value__min']
                count = metrics.count()
                
                # Store aggregated metrics
                cache_key = f"aggregated_metric_{metric_name}_{category}_1h"
                cache.set(cache_key, {
                    'avg': avg_value,
                    'max': max_value,
                    'min': min_value,
                    'count': count,
                    'last_updated': timezone.now().isoformat()
                }, 3600)  # Cache for 1 hour
                
                aggregated_count += 1
        
        logger.info(f"Aggregated {aggregated_count} metric groups")
        return {'status': 'success', 'aggregated_count': aggregated_count}
        
    except Exception as e:
        logger.error(f"Error in metrics aggregation: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_metrics():
    """
    Background task to clean up old real-time metrics
    """
    try:
        logger.info("Starting cleanup of old metrics")
        
        # Delete metrics older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        
        deleted_count, _ = RealTimeMetric.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        logger.info(f"Deleted {deleted_count} old metrics")
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f"Error in metrics cleanup: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def monitor_experiment_completion():
    """
    Background task to monitor and complete experiments that have reached their end date
    """
    try:
        logger.info("Monitoring experiment completion")
        
        # Get running experiments that have passed their end date
        now = timezone.now()
        expired_experiments = ABTestExperiment.objects.filter(
            status='running',
            end_date__lt=now
        )
        
        completed_count = 0
        service = AnalyticsService()
        
        for experiment in expired_experiments:
            try:
                # Calculate final results
                results = service.get_experiment_results(str(experiment.id))
                
                # Update experiment status
                experiment.status = 'completed'
                experiment.results_summary = results
                experiment.save()
                
                # Send notification (you would implement actual notification logic)
                logger.info(f"Experiment {experiment.name} completed automatically")
                
                completed_count += 1
                
            except Exception as e:
                logger.error(f"Error completing experiment {experiment.id}: {str(e)}")
                continue
        
        logger.info(f"Completed {completed_count} experiments")
        return {'status': 'success', 'completed_count': completed_count}
        
    except Exception as e:
        logger.error(f"Error in experiment completion monitoring: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def generate_performance_alerts():
    """
    Background task to generate performance alerts based on metrics
    """
    try:
        logger.info("Generating performance alerts")
        
        # Check recent metrics for anomalies
        recent_metrics = RealTimeMetric.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=10)
        )
        
        alerts = []
        service = AnalyticsService()
        
        # Check for high response times
        response_time_metrics = recent_metrics.filter(
            metric_name='feed_generation_time'
        )
        
        if response_time_metrics.exists():
            avg_response_time = response_time_metrics.aggregate(
                Avg('value')
            )['value__avg']
            
            if avg_response_time > 500:  # 500ms threshold
                alert_message = f"High average response time: {avg_response_time:.1f}ms"
                alerts.append({
                    'level': 'warning',
                    'metric': 'response_time',
                    'message': alert_message,
                    'value': avg_response_time
                })
                
                # Send real-time alert
                service.send_system_alert('warning', alert_message)
        
        # Check for low cache hit rate
        cache_hits = recent_metrics.filter(metric_name='feed_cache_hits').count()
        cache_misses = recent_metrics.filter(metric_name='feed_cache_misses').count()
        
        if cache_hits + cache_misses > 0:
            hit_rate = cache_hits / (cache_hits + cache_misses)
            
            if hit_rate < 0.7:  # 70% threshold
                alert_message = f"Low cache hit rate: {hit_rate:.1%}"
                alerts.append({
                    'level': 'warning',
                    'metric': 'cache_hit_rate',
                    'message': alert_message,
                    'value': hit_rate
                })
                
                service.send_system_alert('warning', alert_message)
        
        logger.info(f"Generated {len(alerts)} performance alerts")
        return {'status': 'success', 'alerts_count': len(alerts), 'alerts': alerts}
        
    except Exception as e:
        logger.error(f"Error generating performance alerts: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def warm_feed_cache():
    """
    Background task to warm up feed cache for active users
    """
    try:
        logger.info("Starting feed cache warming")
        
        # Get active users (logged in within last 24 hours)
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        # This would need to be integrated with your user activity tracking
        # For now, we'll use a simple approach
        active_users = User.objects.filter(
            last_login__gte=cutoff_time
        )[:50]  # Warm cache for top 50 active users
        
        warmed_count = 0
        
        for user in active_users:
            try:
                # This would trigger feed generation and caching
                # You would call your feed generation service here
                logger.debug(f"Warming cache for user {user.id}")
                warmed_count += 1
                
            except Exception as e:
                logger.error(f"Error warming cache for user {user.id}: {str(e)}")
                continue
        
        logger.info(f"Warmed cache for {warmed_count} users")
        return {'status': 'success', 'warmed_count': warmed_count}
        
    except Exception as e:
        logger.error(f"Error in cache warming: {str(e)}")
        return {'status': 'error', 'message': str(e)}
