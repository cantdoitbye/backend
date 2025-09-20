"""Analytics Aggregation Service

This service handles aggregation and analysis of user activity data
for analytics reporting and insights.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone

from user_activity.models import UserActivity, ContentInteraction, ProfileActivity, MediaInteraction, SocialInteraction, SessionActivity


class AnalyticsAggregationService:
    """Service for aggregating and analyzing user activity data."""
    
    @staticmethod
    def get_comprehensive_user_activity_summary(user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive activity summary for a user across all activity models."""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Aggregate from all activity models
            user_activities = UserActivity.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            content_interactions = ContentInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            profile_activities = ProfileActivity.objects.filter(
                visitor_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            media_interactions = MediaInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            social_interactions = SocialInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            session_activities = SessionActivity.objects.filter(
                user_id=user_id,
                start_time__gte=start_date,
                start_time__lte=end_date
            )
            
            # Calculate totals
            total_activities = (
                user_activities.count() +
                content_interactions.count() +
                profile_activities.count() +
                media_interactions.count() +
                social_interactions.count() +
                session_activities.count()
            )
            
            # Activity breakdown by model
            activity_breakdown = {
                'user_activities': user_activities.count(),
                'content_interactions': content_interactions.count(),
                'profile_activities': profile_activities.count(),
                'media_interactions': media_interactions.count(),
                'social_interactions': social_interactions.count(),
                'session_activities': session_activities.count()
            }
            
            # Content interaction breakdown
            content_by_type = content_interactions.values('content_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            interaction_by_type = content_interactions.values('interaction_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_activities': total_activities,
                'activity_breakdown': activity_breakdown,
                'content_by_type': list(content_by_type),
                'interaction_by_type': list(interaction_by_type),
                'average_daily_activities': total_activities / days if days > 0 else 0
            }
        except Exception as e:
            print(f"Error getting comprehensive user activity summary: {e}")
            return {
                'user_id': user_id,
                'error': str(e)
            }
    
    @staticmethod
    def get_user_engagement_trends(user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get user engagement trends over time with daily breakdown."""
        try:
            from user_activity.models import ContentInteraction, SocialInteraction, SessionActivity
            
            trends = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
                day_end = day_start + timedelta(days=1)
                
                # Get activities for this day
                daily_activities = UserActivity.objects.filter(
                    user_id=user_id,
                    created_at__gte=day_start,
                    created_at__lt=day_end
                )
                
                # Get content interactions for this day
                daily_content_interactions = ContentInteraction.objects.filter(
                    user_id=user_id,
                    created_at__gte=day_start,
                    created_at__lt=day_end
                )
                
                # Get social interactions for this day
                daily_social_interactions = SocialInteraction.objects.filter(
                    user_id=user_id,
                    created_at__gte=day_start,
                    created_at__lt=day_end
                )
                
                # Calculate daily interactions
                daily_interactions = (
                    daily_activities.count() + 
                    daily_content_interactions.count() + 
                    daily_social_interactions.count()
                )
                
                # Calculate active hours (estimate based on activity spread)
                active_hours = 0.0
                if daily_interactions > 0:
                    # Get unique hours when activities occurred
                    activity_hours = set()
                    
                    for activity in daily_activities:
                        activity_hours.add(activity.created_at.hour)
                    
                    for interaction in daily_content_interactions:
                        activity_hours.add(interaction.created_at.hour)
                    
                    for interaction in daily_social_interactions:
                        activity_hours.add(interaction.created_at.hour)
                    
                    active_hours = float(len(activity_hours))
                
                # Calculate engagement score (simple algorithm)
                engagement_score = 0.0
                if daily_interactions > 0:
                    # Base score from interactions (normalized to 0-5)
                    interaction_score = min(daily_interactions / 10.0, 5.0)
                    
                    # Bonus for active hours (normalized to 0-3)
                    hours_score = min(active_hours / 8.0, 3.0)
                    
                    # Bonus for variety of interaction types
                    variety_score = 0.0
                    interaction_types = set()
                    
                    for activity in daily_activities:
                        interaction_types.add(activity.activity_type)
                    
                    for interaction in daily_content_interactions:
                        interaction_types.add(interaction.interaction_type)
                    
                    for interaction in daily_social_interactions:
                        interaction_types.add(interaction.interaction_type)
                    
                    variety_score = min(len(interaction_types) / 5.0, 2.0)
                    
                    engagement_score = interaction_score + hours_score + variety_score
                
                trends.append({
                    'date': day_start,
                    'daily_interactions': daily_interactions,
                    'engagement_score': round(engagement_score, 2),
                    'active_hours': round(active_hours, 2)
                })
                
                current_date += timedelta(days=1)
            
            return trends
            
        except Exception as e:
            print(f"Error getting user engagement trends: {e}")
            return []
    
    @staticmethod
    def get_user_activity_summary(user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get activity summary for a user over specified days with GraphQL-compatible fields."""
        try:
            from django.contrib.auth.models import User
            from user_activity.models import ContentInteraction, SocialInteraction
            
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Get all user activities in the period
            activities = UserActivity.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Get content interactions
            content_interactions = ContentInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Get social interactions
            social_interactions = SocialInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Calculate specific metrics for GraphQL
            total_interactions = activities.count() + content_interactions.count() + social_interactions.count()
            
            # Posts created (from content interactions or activities)
            posts_created = content_interactions.filter(
                content_type='post',
                interaction_type='view'  # Assuming view indicates creation context
            ).count()
            
            # Communities joined (from social interactions)
            communities_joined = social_interactions.filter(
                interaction_type='group_join'
            ).count()
            
            # Connections made (from social interactions)
            connections_made = social_interactions.filter(
                interaction_type='connection_accept'
            ).count()
            
            # Likes given (from content interactions)
            likes_given = content_interactions.filter(
                interaction_type='like'
            ).count()
            
            # Comments made (from content interactions)
            comments_made = content_interactions.filter(
                interaction_type='comment'
            ).count()
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_interactions': total_interactions,
                'posts_created': posts_created,
                'communities_joined': communities_joined,
                'connections_made': connections_made,
                'likes_given': likes_given,
                'comments_made': comments_made,
                'total_activities': activities.count(),
                'unique_activity_types': activities.values('activity_type').distinct().count(),
                'average_daily_activities': total_interactions / days if days > 0 else 0
            }
        except Exception as e:
            print(f"Error getting user activity summary: {e}")
            return {
                'user_id': user_id,
                'total_interactions': 0,
                'posts_created': 0,
                'communities_joined': 0,
                'connections_made': 0,
                'likes_given': 0,
                'comments_made': 0,
                'error': str(e)
            }
    
    @staticmethod
    def get_engagement_trends(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user engagement trends over time."""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            activities = UserActivity.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Weekly engagement trends
            weekly_trends = []
            weeks = days // 7
            for i in range(weeks):
                week_start = start_date + timedelta(weeks=i)
                week_end = week_start + timedelta(weeks=1)
                
                week_activities = activities.filter(
                    created_at__gte=week_start,
                    created_at__lt=week_end
                )
                
                # Calculate engagement metrics
                total_count = week_activities.count()
                unique_sessions = week_activities.values('metadata__session_id').distinct().count()
                
                # Scroll depth analysis for pages
                scroll_activities = week_activities.filter(
                    content_type='page',
                    interaction_type='scroll'
                )
                avg_scroll_depth = 0
                if scroll_activities.exists():
                    scroll_depths = []
                    for activity in scroll_activities:
                        if activity.metadata and 'max_scroll_depth' in activity.metadata:
                            try:
                                depth = float(activity.metadata['max_scroll_depth'])
                                scroll_depths.append(depth)
                            except (ValueError, TypeError):
                                continue
                    if scroll_depths:
                        avg_scroll_depth = sum(scroll_depths) / len(scroll_depths)
                
                weekly_trends.append({
                    'week_start': week_start.strftime('%Y-%m-%d'),
                    'week_end': week_end.strftime('%Y-%m-%d'),
                    'total_activities': total_count,
                    'unique_sessions': unique_sessions,
                    'avg_scroll_depth': round(avg_scroll_depth, 2)
                })
            
            return {
                'user_id': user_id,
                'period_days': days,
                'weekly_trends': weekly_trends
            }
        except Exception as e:
            print(f"Error getting engagement trends: {e}")
            return {
                'user_id': user_id,
                'error': str(e)
            }
    
    @staticmethod
    def get_content_interactions(user_id: Optional[str] = None, content_type: Optional[str] = None, 
                               content_id: Optional[str] = None, interaction_type: Optional[str] = None, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get content interaction records for GraphQL query."""
        try:
            from user_activity.models import ContentInteraction
            
            # Start with all content interactions
            queryset = ContentInteraction.objects.all()
            
            # Apply filters
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            if content_type:
                queryset = queryset.filter(content_type=content_type)
            if content_id:
                queryset = queryset.filter(content_id=content_id)
            if interaction_type:
                queryset = queryset.filter(interaction_type=interaction_type)
            
            # Order by most recent and limit results
            interactions = queryset.order_by('-created_at')[:limit]
            
            # Convert to list of dictionaries for GraphQL
            result = []
            for interaction in interactions:
                result.append({
                    'id': str(interaction.id),
                    'user_id': str(interaction.user_id),
                    'content_type': interaction.content_type,
                    'content_id': interaction.content_id,
                    'interaction_type': interaction.interaction_type,
                    'timestamp': interaction.created_at,
                    'metadata': interaction.metadata or {}
                })
            
            return result
        except Exception as e:
            print(f"Error getting content interactions: {e}")
            return []
    
    @staticmethod
    def get_popular_content(
        content_type: Optional[str] = None, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get popular content across all users."""
        try:
            from user_activity.models import ContentInteraction
            
            # Set default date range if not provided
            if not end_date:
                end_date = timezone.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            interactions = ContentInteraction.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )
            
            if content_type:
                interactions = interactions.filter(content_type=content_type)
            
            # Popular content by interaction count
            popular_content = interactions.values('content_id', 'content_type').annotate(
                interaction_count=Count('id'),
                unique_users=Count('user_id', distinct=True)
            ).order_by('-interaction_count')[:limit]
            
            # Calculate trending score and format results
            results = []
            for content in popular_content:
                # Simple trending score calculation
                trending_score = (
                    content['interaction_count'] * 0.7 + 
                    content['unique_users'] * 0.3
                )
                
                results.append({
                    'content_id': content['content_id'],
                    'content_type': content['content_type'],
                    'title': f"Content {content['content_id']}",  # Default title
                    'interaction_count': content['interaction_count'],
                    'unique_users': content['unique_users'],
                    'trending_score': round(trending_score, 2)
                })
            
            return results
            
        except Exception as e:
            print(f"Error getting popular content: {e}")
            return []
    
    @staticmethod
    def get_user_engagement_metrics(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive engagement metrics for a user."""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            activities = UserActivity.objects.filter(
                user_id=user_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Basic metrics
            total_activities = activities.count()
            active_days = activities.values('created_at__date').distinct().count()
            
            # Session analysis - filter by activity_type instead
            session_activities = activities.filter(
                activity_type='session_data'
            )
            total_sessions = session_activities.count()
            
            # Calculate average session duration
            avg_session_duration = 0
            session_durations = []
            for session in session_activities:
                if session.metadata and 'session_start' in session.metadata and 'session_end' in session.metadata:
                    try:
                        start = datetime.fromisoformat(session.metadata['session_start'].replace('Z', '+00:00'))
                        end = datetime.fromisoformat(session.metadata['session_end'].replace('Z', '+00:00'))
                        duration = (end - start).total_seconds() / 60  # Convert to minutes
                        session_durations.append(duration)
                    except (ValueError, TypeError):
                        continue
            
            if session_durations:
                avg_session_duration = sum(session_durations) / len(session_durations)
            
            # Scroll depth analysis - filter by activity_type instead
            scroll_activities = activities.filter(
                activity_type='scroll'
            )
            avg_scroll_depth = 0
            if scroll_activities.exists():
                scroll_depths = []
                for activity in scroll_activities:
                    if activity.metadata and 'max_scroll_depth' in activity.metadata:
                        try:
                            depth = float(activity.metadata['max_scroll_depth'])
                            scroll_depths.append(depth)
                        except (ValueError, TypeError):
                            continue
                if scroll_depths:
                    avg_scroll_depth = sum(scroll_depths) / len(scroll_depths)
            
            # Engagement score calculation (simple algorithm)
            engagement_score = 0
            if days > 0:
                daily_activity_rate = total_activities / days
                session_frequency = total_sessions / days if days > 0 else 0
                engagement_score = (
                    daily_activity_rate * 0.4 +
                    session_frequency * 0.3 +
                    (avg_scroll_depth / 100) * 0.2 +
                    (avg_session_duration / 30) * 0.1  # Normalize to 30 min sessions
                )
                engagement_score = min(engagement_score, 10)  # Cap at 10
            
            # Calculate bounce rate (sessions with only 1 activity)
            bounce_rate = 0.0
            if total_sessions > 0:
                single_activity_sessions = 0
                for session in session_activities:
                    session_activity_count = activities.filter(
                        metadata__session_id=session.metadata.get('session_id') if session.metadata else None
                    ).count()
                    if session_activity_count <= 1:
                        single_activity_sessions += 1
                bounce_rate = (single_activity_sessions / total_sessions) * 100
            
            # Calculate pages per session
            pages_per_session = 0.0
            if total_sessions > 0:
                page_views = activities.filter(activity_type='page_view').count()
                pages_per_session = page_views / total_sessions
            
            # Calculate return visitor rate (users with activities in multiple days)
            return_visitor_rate = 0.0
            if active_days > 1:
                return_visitor_rate = ((active_days - 1) / active_days) * 100
            
            # Get last activity timestamp
            last_activity = None
            latest_activity = activities.order_by('-created_at').first()
            if latest_activity:
                last_activity = latest_activity.created_at

            return {
                'user_id': user_id,
                'period_days': days,
                'total_activities': total_activities,
                'active_days': active_days,
                'total_sessions': total_sessions,
                'avg_session_duration': round(avg_session_duration, 2),
                'avg_scroll_depth_percent': round(avg_scroll_depth, 2),
                'engagement_score': round(engagement_score, 2),
                'activity_rate_per_day': round(total_activities / days if days > 0 else 0, 2),
                'bounce_rate': round(bounce_rate, 2),
                'pages_per_session': round(pages_per_session, 2),
                'return_visitor_rate': round(return_visitor_rate, 2),
                'last_activity': last_activity
            }
        except Exception as e:
            print(f"Error getting user engagement metrics: {e}")
            return {
                'user_id': user_id,
                'error': str(e)
            }