"""Celery tasks for scoring engines and metric calculations."""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import CreatorMetric, TrendingMetric, ContentScore
from .utils import (
    calculate_creator_metrics, calculate_trending_metrics,
    cleanup_expired_scores, bulk_calculate_trending_metrics
)
from analytics.utils import log_scoring_event
import structlog

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def recalculate_creator_metrics(self, creator_id=None):
    """Recalculate creator metrics for one or all creators."""
    from users.models import UserProfile
    
    try:
        if creator_id:
            # Recalculate for specific creator
            try:
                creator = UserProfile.objects.get(id=creator_id)
                metrics_data = calculate_creator_metrics(creator)
                
                metric, created = CreatorMetric.objects.get_or_create(
                    creator=creator
                )
                
                # Update all fields
                for field, value in metrics_data.items():
                    setattr(metric, field, value)
                
                metric.save()
                
                log_scoring_event(
                    event_type='creator_metrics_recalculated',
                    user_id=creator_id,
                    metadata={
                        'reputation_score': metric.reputation_score,
                        'authority_score': metric.authority_score,
                        'total_content': metric.total_content_created
                    }
                )
                
                logger.info(
                    "Creator metrics recalculated",
                    creator_id=creator_id,
                    reputation_score=metric.reputation_score
                )
                
                return {
                    'success': True,
                    'creator_id': creator_id,
                    'reputation_score': metric.reputation_score
                }
                
            except UserProfile.DoesNotExist:
                logger.error(
                    "Creator not found for metrics calculation",
                    creator_id=creator_id
                )
                return {'success': False, 'error': 'Creator not found'}
        
        else:
            # Recalculate for all creators who have created content
            from content_types.registry import registry as content_registry
            
            # Get creators who have created content
            creator_ids = set()
            
            for content_type_name, model_class in content_registry.get_all_content_types().items():
                content_creator_ids = model_class.objects.filter(
                    is_active=True
                ).values_list('creator_id', flat=True).distinct()
                creator_ids.update(content_creator_ids)
            
            updated_count = 0
            
            for creator_id in creator_ids:
                try:
                    creator = UserProfile.objects.get(id=creator_id)
                    metrics_data = calculate_creator_metrics(creator)
                    
                    metric, created = CreatorMetric.objects.get_or_create(
                        creator=creator
                    )
                    
                    for field, value in metrics_data.items():
                        setattr(metric, field, value)
                    
                    metric.save()
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(
                        "Error updating creator metrics",
                        creator_id=creator_id,
                        error=str(e)
                    )
            
            logger.info(
                "Bulk creator metrics recalculation completed",
                updated_count=updated_count,
                total_creators=len(creator_ids)
            )
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_creators': len(creator_ids)
            }
    
    except Exception as e:
        logger.error(
            "Error in creator metrics recalculation task",
            creator_id=creator_id,
            error=str(e),
            retry_count=self.request.retries
        )
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'success': False,
            'error': str(e),
            'max_retries_exceeded': True
        }


@shared_task(bind=True, max_retries=3)
def update_trending_metrics(self, content_type=None, content_id=None):
    """Update trending metrics for content."""
    try:
        if content_type and content_id:
            # Update specific content
            metrics = calculate_trending_metrics(content_type, content_id)
            
            if metrics:
                trending_metric, created = TrendingMetric.objects.get_or_create(
                    metric_type='content',
                    metric_id=f"{content_type}:{content_id}"
                )
                
                # Update fields
                trending_metric.velocity_score = metrics.get('velocity_score', 0.0)
                trending_metric.viral_coefficient = metrics.get('viral_coefficient', 0.0)
                trending_metric.engagement_volume = metrics.get('engagement_volume', 0)
                trending_metric.trending_score = metrics.get('trending_score', 0.0)
                
                # Update time windows
                trending_metric.window_1h = metrics.get('window_1h', {})
                trending_metric.window_24h = metrics.get('window_24h', {})
                trending_metric.window_7d = metrics.get('window_7d', {})
                
                trending_metric.save()
                
                logger.info(
                    "Trending metrics updated",
                    content_type=content_type,
                    content_id=content_id,
                    trending_score=trending_metric.trending_score
                )
                
                return {
                    'success': True,
                    'content_type': content_type,
                    'content_id': content_id,
                    'trending_score': trending_metric.trending_score
                }
        
        else:
            # Update trending metrics for recent content
            from content_types.registry import registry as content_registry
            
            # Get content from last 7 days
            since = timezone.now() - timedelta(days=7)
            content_items = []
            
            for content_type_name, model_class in content_registry.get_all_content_types().items():
                recent_content = model_class.objects.filter(
                    created_at__gte=since,
                    is_active=True
                ).values_list('id', flat=True)[:100]  # Limit for performance
                
                for content_id in recent_content:
                    content_items.append((content_type_name, str(content_id)))
            
            # Bulk calculate trending metrics
            results = bulk_calculate_trending_metrics(content_items)
            updated_count = 0
            
            for content_key, metrics in results.items():
                try:
                    content_type_name, content_id = content_key.split(':', 1)
                    
                    trending_metric, created = TrendingMetric.objects.get_or_create(
                        metric_type='content',
                        metric_id=content_key
                    )
                    
                    # Update fields
                    trending_metric.velocity_score = metrics.get('velocity_score', 0.0)
                    trending_metric.viral_coefficient = metrics.get('viral_coefficient', 0.0)
                    trending_metric.engagement_volume = metrics.get('engagement_volume', 0)
                    trending_metric.trending_score = metrics.get('trending_score', 0.0)
                    
                    # Update time windows
                    trending_metric.window_1h = metrics.get('window_1h', {})
                    trending_metric.window_24h = metrics.get('window_24h', {})
                    trending_metric.window_7d = metrics.get('window_7d', {})
                    
                    trending_metric.save()
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(
                        "Error updating trending metric",
                        content_key=content_key,
                        error=str(e)
                    )
            
            logger.info(
                "Bulk trending metrics update completed",
                updated_count=updated_count,
                total_items=len(content_items)
            )
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_items': len(content_items)
            }
    
    except Exception as e:
        logger.error(
            "Error in trending metrics update task",
            content_type=content_type,
            content_id=content_id,
            error=str(e),
            retry_count=self.request.retries
        )
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            'success': False,
            'error': str(e),
            'max_retries_exceeded': True
        }


@shared_task
def cleanup_expired_content_scores():
    """Clean up expired content scores."""
    try:
        deleted_count = cleanup_expired_scores()
        
        logger.info(
            "Expired content scores cleanup completed",
            deleted_count=deleted_count
        )
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
    
    except Exception as e:
        logger.error(
            "Error in cleanup expired scores task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def cleanup_old_trending_metrics():
    """Clean up old trending metrics."""
    try:
        # Delete trending metrics older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_count = TrendingMetric.objects.filter(
            last_updated__lt=cutoff_date
        ).delete()[0]
        
        logger.info(
            "Old trending metrics cleanup completed",
            deleted_count=deleted_count,
            cutoff_date=cutoff_date
        )
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
    
    except Exception as e:
        logger.error(
            "Error in cleanup old trending metrics task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def recalculate_low_performing_scores():
    """Recalculate scores for content with very low engagement."""
    try:
        from content_types.registry import registry as content_registry
        from .utils import calculate_content_score
        
        # Find content with very low scores that might need recalculation
        low_scores = ContentScore.objects.filter(
            final_score__lt=0.1,
            computed_at__lt=timezone.now() - timedelta(hours=6)
        )[:100]  # Limit for performance
        
        recalculated_count = 0
        
        for score_obj in low_scores:
            try:
                # Get the content object
                model_class = content_registry.get_content_type(score_obj.content_type)
                if not model_class:
                    continue
                
                content = model_class.objects.get(id=score_obj.content_id)
                
                # Recalculate score
                result = calculate_content_score(
                    content=content,
                    user=score_obj.user,
                    force_recalculate=True
                )
                
                # If the new score is significantly different, log it
                if abs(result['final_score'] - score_obj.final_score) > 0.1:
                    logger.info(
                        "Low performing content score updated",
                        content_type=score_obj.content_type,
                        content_id=str(score_obj.content_id),
                        old_score=score_obj.final_score,
                        new_score=result['final_score']
                    )
                
                recalculated_count += 1
                
            except Exception as e:
                logger.error(
                    "Error recalculating low performing score",
                    score_id=score_obj.id,
                    error=str(e)
                )
        
        logger.info(
            "Low performing scores recalculation completed",
            recalculated_count=recalculated_count,
            total_checked=len(low_scores)
        )
        
        return {
            'success': True,
            'recalculated_count': recalculated_count,
            'total_checked': len(low_scores)
        }
    
    except Exception as e:
        logger.error(
            "Error in recalculate low performing scores task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def update_algorithm_performance_metrics():
    """Update performance metrics for the algorithm."""
    try:
        from .models import FeedDebugEvent
        from django.db.models import Avg, Count
        
        # Calculate performance metrics for the last 24 hours
        since = timezone.now() - timedelta(hours=24)
        
        performance_stats = FeedDebugEvent.objects.filter(
            created_at__gte=since
        ).aggregate(
            avg_execution_time=Avg('execution_time_ms'),
            total_events=Count('id'),
            feed_generations=Count('id', filter=Q(event_type='feed_generation')),
            score_computations=Count('id', filter=Q(event_type='score_computation'))
        )
        
        # Log the performance metrics
        log_scoring_event(
            event_type='algorithm_performance_metrics',
            metadata={
                'time_window': '24h',
                'avg_execution_time_ms': performance_stats['avg_execution_time'],
                'total_events': performance_stats['total_events'],
                'feed_generations': performance_stats['feed_generations'],
                'score_computations': performance_stats['score_computations']
            }
        )
        
        logger.info(
            "Algorithm performance metrics updated",
            **performance_stats
        )
        
        return {
            'success': True,
            'metrics': performance_stats
        }
    
    except Exception as e:
        logger.error(
            "Error in update algorithm performance metrics task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }