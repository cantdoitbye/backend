"""Utility functions for scoring engines and feed algorithm."""

from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from .models import CreatorMetric, TrendingMetric, ContentScore
from .registry import registry
import math
import structlog

logger = structlog.get_logger(__name__)


def calculate_user_engagement(user) -> float:
    """Calculate overall engagement score for a user."""
    from content_types.models import Engagement
    from django.contrib.contenttypes.models import ContentType
    
    try:
        # Get user's content
        user_content = []
        from content_types.registry import registry as content_registry
        
        for content_type_name, model_class in content_registry.get_all_content_types().items():
            content_items = model_class.objects.filter(
                creator=user,
                is_active=True
            ).values_list('id', flat=True)
            user_content.extend([(ContentType.objects.get_for_model(model_class), cid) for cid in content_items])
        
        if not user_content:
            return 0.0
        
        # Calculate engagement metrics
        total_engagements = 0
        total_score = 0.0
        
        for content_type, content_id in user_content:
            engagements = Engagement.objects.filter(
                content_type=content_type,
                object_id=content_id
            ).aggregate(
                count=Count('id'),
                avg_score=Avg('score'),
                total_score=Sum('score')
            )
            
            if engagements['count']:
                total_engagements += engagements['count']
                total_score += engagements['total_score'] or 0.0
        
        if total_engagements == 0:
            return 0.0
        
        # Normalize engagement score
        avg_engagement_per_content = total_engagements / len(user_content)
        avg_score_per_engagement = total_score / total_engagements
        
        # Logarithmic scaling to prevent outliers
        engagement_score = math.log10(avg_engagement_per_content + 1) * avg_score_per_engagement
        
        return min(10.0, engagement_score)
        
    except Exception as e:
        logger.error(
            "Error calculating user engagement",
            user_id=user.id,
            error=str(e)
        )
        return 0.0


def calculate_creator_metrics(creator) -> Dict[str, float]:
    """Calculate comprehensive creator metrics."""
    from content_types.models import Engagement
    from content_types.registry import registry as content_registry
    from django.contrib.contenttypes.models import ContentType
    
    try:
        metrics = {
            'reputation_score': 0.5,
            'authority_score': 0.0,
            'consistency_score': 0.5,
            'total_engagements': 0,
            'avg_engagement_rate': 0.0,
            'total_content_created': 0,
            'content_quality_avg': 0.5,
            'follower_growth_rate': 0.0,
            'connection_influence': 0.0,
            'recent_activity_score': 0.5
        }
        
        # Get all creator's content
        all_content = []
        total_content_count = 0
        total_quality_score = 0.0
        
        for content_type_name, model_class in content_registry.get_all_content_types().items():
            content_items = model_class.objects.filter(
                creator=creator,
                is_active=True
            )
            
            for content in content_items:
                all_content.append(content)
                total_content_count += 1
                total_quality_score += getattr(content, 'quality_score', 0.5)
        
        metrics['total_content_created'] = total_content_count
        
        if total_content_count > 0:
            metrics['content_quality_avg'] = total_quality_score / total_content_count
        
        # Calculate engagement metrics
        if all_content:
            total_engagements = 0
            engagement_scores = []
            
            for content in all_content:
                content_type = ContentType.objects.get_for_model(content)
                content_engagements = Engagement.objects.filter(
                    content_type=content_type,
                    object_id=content.id
                ).aggregate(
                    count=Count('id'),
                    avg_score=Avg('score')
                )
                
                eng_count = content_engagements['count'] or 0
                avg_score = content_engagements['avg_score'] or 0.0
                
                total_engagements += eng_count
                if eng_count > 0:
                    engagement_scores.append(avg_score)
            
            metrics['total_engagements'] = total_engagements
            
            if total_content_count > 0:
                metrics['avg_engagement_rate'] = total_engagements / total_content_count
            
            # Consistency score based on engagement variance
            if engagement_scores:
                avg_engagement = sum(engagement_scores) / len(engagement_scores)
                variance = sum((x - avg_engagement) ** 2 for x in engagement_scores) / len(engagement_scores)
                std_dev = math.sqrt(variance)
                
                # Lower variance = higher consistency
                if avg_engagement > 0:
                    consistency = max(0.0, 1.0 - (std_dev / avg_engagement))
                    metrics['consistency_score'] = consistency
        
        # Calculate reputation based on multiple factors
        quality_factor = metrics['content_quality_avg']
        engagement_factor = min(1.0, metrics['avg_engagement_rate'] / 10.0)
        consistency_factor = metrics['consistency_score']
        volume_factor = min(1.0, total_content_count / 50.0)
        
        reputation = (
            quality_factor * 0.3 +
            engagement_factor * 0.3 +
            consistency_factor * 0.2 +
            volume_factor * 0.2
        )
        
        metrics['reputation_score'] = min(1.0, reputation)
        
        # Authority score based on follower count and engagement
        from users.models import Connection
        follower_count = Connection.objects.filter(
            to_user=creator,
            status='accepted'
        ).count()
        
        # Logarithmic scaling for authority
        if follower_count > 0:
            authority = math.log10(follower_count + 1) / 4.0  # Max log10(10000) = 4
            metrics['authority_score'] = min(1.0, authority)
        
        # Recent activity score
        now = timezone.now()
        recent_content = [c for c in all_content if (now - c.created_at).days <= 30]
        
        if recent_content:
            activity_score = min(1.0, len(recent_content) / 10.0)  # 10 posts per month = max
            metrics['recent_activity_score'] = activity_score
        
        return metrics
        
    except Exception as e:
        logger.error(
            "Error calculating creator metrics",
            creator_id=creator.id,
            error=str(e)
        )
        return metrics


def calculate_trending_metrics(content_type: str, content_id: str) -> Dict[str, float]:
    """Calculate trending metrics for a piece of content."""
    from content_types.models import Engagement
    from content_types.registry import registry as content_registry
    from django.contrib.contenttypes.models import ContentType
    
    try:
        # Get the content object
        model_class = content_registry.get_content_type(content_type)
        if not model_class:
            return {}
        
        try:
            content = model_class.objects.get(id=content_id)
        except model_class.DoesNotExist:
            return {}
        
        django_content_type = ContentType.objects.get_for_model(model_class)
        now = timezone.now()
        
        # Define time windows
        windows = {
            'window_1h': now - timedelta(hours=1),
            'window_24h': now - timedelta(hours=24),
            'window_7d': now - timedelta(days=7)
        }
        
        metrics = {
            'velocity_score': 0.0,
            'viral_coefficient': 0.0,
            'engagement_volume': 0,
            'trending_score': 0.0
        }
        
        window_data = {}
        
        # Calculate metrics for each time window
        for window_name, start_time in windows.items():
            engagements = Engagement.objects.filter(
                content_type=django_content_type,
                object_id=content_id,
                created_at__gte=start_time
            ).values('engagement_type').annotate(
                count=Count('id'),
                avg_score=Avg('score')
            )
            
            window_stats = {}
            total_count = 0
            
            for eng in engagements:
                eng_type = eng['engagement_type']
                count = eng['count']
                avg_score = eng['avg_score'] or 1.0
                
                window_stats[eng_type] = {
                    'count': count,
                    'avg_score': avg_score
                }
                total_count += count
            
            window_stats['total'] = total_count
            window_data[window_name] = window_stats
        
        # Calculate velocity (engagements per hour)
        recent_engagements = window_data['window_1h']['total']
        daily_engagements = window_data['window_24h']['total']
        
        if daily_engagements > 0:
            velocity = recent_engagements / max(1, daily_engagements) * 24
            metrics['velocity_score'] = min(100.0, velocity * 10)
        
        # Calculate viral coefficient
        shares_1h = window_data['window_1h'].get('share', {}).get('count', 0)
        shares_24h = window_data['window_24h'].get('share', {}).get('count', 0)
        
        if shares_24h > 0 and shares_1h > 0:
            viral_coeff = shares_1h / max(1, shares_24h) * 24
            metrics['viral_coefficient'] = min(10.0, viral_coeff)
        
        metrics['engagement_volume'] = daily_engagements
        
        # Calculate final trending score
        velocity_norm = min(1.0, metrics['velocity_score'] / 100.0)
        volume_norm = min(1.0, metrics['engagement_volume'] / 1000.0)
        viral_norm = min(1.0, metrics['viral_coefficient'] / 5.0)
        
        trending_score = (
            velocity_norm * 0.5 +
            volume_norm * 0.3 +
            viral_norm * 0.2
        )
        
        metrics['trending_score'] = trending_score
        
        # Store window data
        for window_name, data in window_data.items():
            metrics[window_name] = data
        
        return metrics
        
    except Exception as e:
        logger.error(
            "Error calculating trending metrics",
            content_type=content_type,
            content_id=content_id,
            error=str(e)
        )
        return {}


def calculate_content_score(
    content,
    user=None,
    force_recalculate=False,
    engine_configs=None
) -> Dict[str, Any]:
    """Calculate comprehensive score for content."""
    try:
        content_type = content.__class__.__name__.lower()
        content_id = str(content.id)
        
        # Check for cached score
        if not force_recalculate:
            cached_score = ContentScore.objects.filter(
                content_type=content_type,
                content_id=content_id,
                user=user
            ).first()
            
            if cached_score and not cached_score.is_expired():
                return {
                    'final_score': cached_score.final_score,
                    'breakdown': cached_score.factor_scores,
                    'cached': True,
                    'computed_at': cached_score.computed_at
                }
        
        # Use default engine configuration if not provided
        if not engine_configs:
            from django.conf import settings
            feed_config = settings.FEED_CONFIG
            
            engine_configs = {
                'personal_connections': {'weight': 1.0},
                'interest_based': {'weight': 0.8},
                'trending': {'weight': 0.9},
                'engagement': {'weight': 1.0},
                'quality': {'weight': 0.8},
                'freshness': {'weight': 0.6},
                'diversity': {'weight': 0.5},
                'discovery': {'weight': 0.7}
            }
        
        # Create composite scorer
        scorer = registry.create_composite_scorer(engine_configs)
        
        # Calculate score
        result = scorer.calculate_score(content, user)
        
        # Cache the result
        expires_at = timezone.now() + timedelta(hours=1)  # Cache for 1 hour
        
        ContentScore.objects.update_or_create(
            content_type=content_type,
            content_id=content_id,
            user=user,
            defaults={
                'final_score': result['final_score'],
                'factor_scores': result['breakdown'],
                'algorithm_version': '1.0',
                'expires_at': expires_at
            }
        )
        
        result['cached'] = False
        result['computed_at'] = timezone.now()
        
        return result
        
    except Exception as e:
        logger.error(
            "Error calculating content score",
            content_id=getattr(content, 'id', None),
            user_id=getattr(user, 'id', None) if user else None,
            error=str(e)
        )
        return {
            'final_score': 0.5,
            'breakdown': {},
            'error': str(e),
            'cached': False
        }


def get_personalized_weights(user) -> Dict[str, float]:
    """Get personalized scoring weights for a user."""
    try:
        from .models import UserScoringPreference
        
        prefs = UserScoringPreference.objects.filter(user=user).first()
        if not prefs:
            # Return default weights
            return {
                'personal_connections': 1.0,
                'interest_based': 0.8,
                'trending': 0.9,
                'engagement': 1.0,
                'quality': 0.8,
                'freshness': 0.6,
                'diversity': 0.5,
                'discovery': 0.7
            }
        
        # Merge custom weights with defaults
        default_weights = {
            'personal_connections': 1.0,
            'interest_based': 0.8,
            'trending': 0.9,
            'engagement': 1.0,
            'quality': 0.8,
            'freshness': 0.6,
            'diversity': 0.5,
            'discovery': 0.7
        }
        
        custom_weights = prefs.custom_weights
        
        for engine_name in default_weights:
            if engine_name in custom_weights:
                default_weights[engine_name] = custom_weights[engine_name]
        
        return default_weights
        
    except Exception as e:
        logger.error(
            "Error getting personalized weights",
            user_id=getattr(user, 'id', None) if user else None,
            error=str(e)
        )
        return {}


def cleanup_expired_scores():
    """Clean up expired content scores."""
    try:
        expired_count = ContentScore.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        logger.info(
            "Cleaned up expired content scores",
            count=expired_count
        )
        
        return expired_count
        
    except Exception as e:
        logger.error(
            "Error cleaning up expired scores",
            error=str(e)
        )
        return 0


def bulk_calculate_trending_metrics(content_items: List[Tuple[str, str]]) -> Dict[str, Dict[str, float]]:
    """Calculate trending metrics for multiple content items efficiently."""
    results = {}
    
    for content_type, content_id in content_items:
        try:
            metrics = calculate_trending_metrics(content_type, content_id)
            if metrics:
                results[f"{content_type}:{content_id}"] = metrics
        except Exception as e:
            logger.error(
                "Error in bulk trending calculation",
                content_type=content_type,
                content_id=content_id,
                error=str(e)
            )
    
    return results