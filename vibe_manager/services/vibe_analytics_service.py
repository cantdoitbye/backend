from django.db.models import Count, Q, Avg, Sum, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
try:
    from user_activity.models import VibeActivity
except Exception:
    VibeActivity = None
from auth_manager.models import Users
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class VibeAnalyticsService:
    """
    Service for aggregating and analyzing vibe-related activities.
    Provides comprehensive insights into vibe creation, sending, and engagement patterns.
    """
    
    @staticmethod
    def get_vibe_activity_summary(user: Users = None, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive vibe activity summary for a user or globally.
        
        Args:
            user: Specific user to analyze (None for global stats)
            days: Number of days to look back (default: 30)
            
        Returns:
            Dictionary containing activity summary
        """
        try:
            if VibeActivity is None:
                return {
                    'period': {
                        'start_date': None,
                        'end_date': None,
                        'days': days
                    },
                    'overview': {
                        'total_activities': 0,
                        'successful_activities': 0,
                        'failed_activities': 0,
                        'success_rate': 0
                    },
                    'activity_breakdown': [],
                    'vibe_type_breakdown': [],
                    'daily_trends': [],
                    'most_active_users': [],
                    'popular_vibes': [],
                    'score_impact': {
                        'avg_score_impact': None,
                        'max_score_impact': None,
                        'min_score_impact': None,
                        'total_score_impact': None
                    }
                }
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Base queryset
            queryset = VibeActivity.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )
            
            if user:
                queryset = queryset.filter(user=user)
            
            # Activity type breakdown
            activity_breakdown = queryset.values('activity_type').annotate(
                count=Count('id'),
                success_rate=Avg('success')
            ).order_by('-count')
            
            # Vibe type breakdown
            vibe_type_breakdown = queryset.values('vibe_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Daily activity trends
            daily_trends = queryset.extra(
                select={'day': 'date(timestamp)'}
            ).values('day').annotate(
                total_activities=Count('id'),
                creations=Count('id', filter=Q(activity_type='creation')),
                sendings=Count('id', filter=Q(activity_type='sending')),
                viewings=Count('id', filter=Q(activity_type='viewing')),
                searches=Count('id', filter=Q(activity_type='search'))
            ).order_by('day')
            
            # Success/failure rates
            success_stats = queryset.aggregate(
                total_activities=Count('id'),
                successful_activities=Count('id', filter=Q(success=True)),
                failed_activities=Count('id', filter=Q(success=False))
            )
            
            success_rate = 0
            if success_stats['total_activities'] > 0:
                success_rate = (success_stats['successful_activities'] / success_stats['total_activities']) * 100
            
            # Most active users (if global analysis)
            most_active_users = []
            if not user:
                most_active_users = queryset.values(
                    'user__user_id', 'user__username'
                ).annotate(
                    activity_count=Count('id')
                ).order_by('-activity_count')[:10]
            
            # Popular vibes
            popular_vibes = queryset.filter(
                activity_type__in=['creation', 'sending', 'viewing']
            ).values('vibe_name').annotate(
                interaction_count=Count('id')
            ).order_by('-interaction_count')[:10]
            
            # Score impact analysis
            score_impact = queryset.filter(
                score_impact__isnull=False
            ).aggregate(
                avg_score_impact=Avg('score_impact'),
                max_score_impact=Max('score_impact'),
                min_score_impact=Min('score_impact'),
                total_score_impact=Sum('score_impact')
            )
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'overview': {
                    'total_activities': success_stats['total_activities'],
                    'successful_activities': success_stats['successful_activities'],
                    'failed_activities': success_stats['failed_activities'],
                    'success_rate': round(success_rate, 2)
                },
                'activity_breakdown': list(activity_breakdown),
                'vibe_type_breakdown': list(vibe_type_breakdown),
                'daily_trends': list(daily_trends),
                'most_active_users': list(most_active_users),
                'popular_vibes': list(popular_vibes),
                'score_impact': score_impact
            }
            
        except Exception as e:
            logger.error(f"Error generating vibe activity summary: {str(e)}")
            return {
                'error': 'Failed to generate activity summary',
                'message': str(e)
            }
    
    @staticmethod
    def get_vibe_creation_analytics(user: Users = None, days: int = 30) -> Dict[str, Any]:
        """
        Get detailed analytics for vibe creation activities.
        
        Args:
            user: Specific user to analyze (None for global stats)
            days: Number of days to look back
            
        Returns:
            Dictionary containing creation analytics
        """
        try:
            if VibeActivity is None:
                return {
                    'period': {
                        'start_date': None,
                        'end_date': None,
                        'days': days
                    },
                    'creation_overview': {
                        'total_attempts': 0,
                        'successful_creations': 0,
                        'failed_creations': 0,
                        'success_rate': 0
                    },
                    'category_breakdown': [],
                    'quality_analysis': {
                        'avg_iq': None,
                        'avg_aq': None,
                        'avg_sq': None,
                        'avg_hq': None
                    },
                    'hourly_patterns': []
                }
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            queryset = VibeActivity.objects.filter(
                activity_type='creation',
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )
            
            if user:
                queryset = queryset.filter(user=user)
            
            # Creation success rate
            creation_stats = queryset.aggregate(
                total_attempts=Count('id'),
                successful_creations=Count('id', filter=Q(success=True)),
                failed_creations=Count('id', filter=Q(success=False))
            )
            
            # Category breakdown
            category_breakdown = queryset.filter(
                success=True
            ).values('additional_context__category').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Quality score analysis
            quality_analysis = queryset.filter(
                success=True
            ).aggregate(
                avg_iq=Avg('additional_context__iq'),
                avg_aq=Avg('additional_context__aq'),
                avg_sq=Avg('additional_context__sq'),
                avg_hq=Avg('additional_context__hq')
            )
            
            # Hourly creation patterns
            hourly_patterns = queryset.extra(
                select={'hour': 'extract(hour from timestamp)'}
            ).values('hour').annotate(
                creation_count=Count('id')
            ).order_by('hour')
            
            success_rate = 0
            if creation_stats['total_attempts'] > 0:
                success_rate = (creation_stats['successful_creations'] / creation_stats['total_attempts']) * 100
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'creation_overview': {
                    'total_attempts': creation_stats['total_attempts'],
                    'successful_creations': creation_stats['successful_creations'],
                    'failed_creations': creation_stats['failed_creations'],
                    'success_rate': round(success_rate, 2)
                },
                'category_breakdown': list(category_breakdown),
                'quality_analysis': quality_analysis,
                'hourly_patterns': list(hourly_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error generating vibe creation analytics: {str(e)}")
            return {
                'error': 'Failed to generate creation analytics',
                'message': str(e)
            }
    
    @staticmethod
    def get_vibe_engagement_metrics(user: Users = None, days: int = 30) -> Dict[str, Any]:
        """
        Get engagement metrics for vibe-related activities.
        
        Args:
            user: Specific user to analyze (None for global stats)
            days: Number of days to look back
            
        Returns:
            Dictionary containing engagement metrics
        """
        try:
            if VibeActivity is None:
                return {
                    'period': {
                        'start_date': None,
                        'end_date': None,
                        'days': days
                    },
                    'engagement_overview': {
                        'total_activities': 0,
                        'unique_users': 0,
                        'unique_vibes': 0
                    },
                    'engagement_breakdown': [],
                    'user_engagement_levels': {
                        'high_engagement': 0,
                        'medium_engagement': 0,
                        'low_engagement': 0
                    },
                    'top_interactions': []
                }
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            queryset = VibeActivity.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )
            
            if user:
                queryset = queryset.filter(user=user)
            
            # Engagement by activity type
            engagement_breakdown = queryset.values('activity_type').annotate(
                count=Count('id'),
                unique_users=Count('user', distinct=True),
                unique_vibes=Count('vibe_name', distinct=True)
            ).order_by('-count')
            
            # User engagement levels
            user_engagement = queryset.values('user').annotate(
                activity_count=Count('id'),
                activity_types=Count('activity_type', distinct=True)
            ).order_by('-activity_count')
            
            # Calculate engagement scores
            high_engagement = user_engagement.filter(activity_count__gte=10).count()
            medium_engagement = user_engagement.filter(
                activity_count__gte=5, activity_count__lt=10
            ).count()
            low_engagement = user_engagement.filter(activity_count__lt=5).count()
            
            # Vibe interaction patterns
            interaction_patterns = queryset.filter(
                activity_type__in=['sending', 'viewing']
            ).values('vibe_name').annotate(
                total_interactions=Count('id'),
                unique_users=Count('user', distinct=True)
            ).order_by('-total_interactions')[:20]
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'engagement_overview': {
                    'total_activities': queryset.count(),
                    'unique_users': queryset.values('user').distinct().count(),
                    'unique_vibes': queryset.values('vibe_name').distinct().count()
                },
                'engagement_breakdown': list(engagement_breakdown),
                'user_engagement_levels': {
                    'high_engagement': high_engagement,
                    'medium_engagement': medium_engagement,
                    'low_engagement': low_engagement
                },
                'top_interactions': list(interaction_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error generating vibe engagement metrics: {str(e)}")
            return {
                'error': 'Failed to generate engagement metrics',
                'message': str(e)
            }
    
    @staticmethod
    def get_real_time_vibe_stats() -> Dict[str, Any]:
        """
        Get real-time vibe activity statistics for the last 24 hours.
        
        Returns:
            Dictionary containing real-time stats
        """
        try:
            if VibeActivity is None:
                return {
                    'timestamp': timezone.now().isoformat(),
                    'last_24_hours': {
                        'total_activities': 0,
                        'creations': 0,
                        'sendings': 0,
                        'viewings': 0,
                        'searches': 0,
                        'unique_users': 0
                    },
                    'last_1_hour': {
                        'total_activities': 0,
                        'creations': 0,
                        'sendings': 0,
                        'viewings': 0,
                        'searches': 0,
                        'unique_users': 0
                    },
                    'recent_activities': []
                }
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_1h = now - timedelta(hours=1)
            
            # Last 24 hours stats
            last_24h_stats = VibeActivity.objects.filter(
                timestamp__gte=last_24h
            ).aggregate(
                total_activities=Count('id'),
                creations=Count('id', filter=Q(activity_type='creation')),
                sendings=Count('id', filter=Q(activity_type='sending')),
                viewings=Count('id', filter=Q(activity_type='viewing')),
                searches=Count('id', filter=Q(activity_type='search')),
                unique_users=Count('user', distinct=True)
            )
            
            # Last 1 hour stats
            last_1h_stats = VibeActivity.objects.filter(
                timestamp__gte=last_1h
            ).aggregate(
                total_activities=Count('id'),
                creations=Count('id', filter=Q(activity_type='creation')),
                sendings=Count('id', filter=Q(activity_type='sending')),
                viewings=Count('id', filter=Q(activity_type='viewing')),
                searches=Count('id', filter=Q(activity_type='search')),
                unique_users=Count('user', distinct=True)
            )
            
            # Recent activities
            recent_activities = VibeActivity.objects.filter(
                timestamp__gte=last_1h
            ).order_by('-timestamp')[:10].values(
                'activity_type', 'vibe_name', 'success', 'timestamp', 'user__username'
            )
            
            return {
                'timestamp': now.isoformat(),
                'last_24_hours': last_24h_stats,
                'last_1_hour': last_1h_stats,
                'recent_activities': list(recent_activities)
            }
            
        except Exception as e:
            logger.error(f"Error generating real-time vibe stats: {str(e)}")
            return {
                'error': 'Failed to generate real-time stats',
                'message': str(e)
            }
