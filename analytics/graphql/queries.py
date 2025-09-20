"""Analytics GraphQL Queries

This module contains GraphQL queries for analytics data aggregation.
It provides endpoints for user activity summaries, engagement trends,
and other analytics insights.
"""

import graphene
from graphene import ObjectType, String, Int, List, DateTime, Float, Boolean
from graphql_jwt.decorators import login_required
from datetime import datetime, timedelta
from django.utils import timezone

from .types import (
    ActivitySummaryType,
    EngagementTrendType,
    ContentInteractionType,
    ScrollDepthType,
    PopularContentType,
    UserEngagementMetricsType
)
from user_activity.services.activity_service import ActivityService
from analytics.services.analytics_aggregation_service import AnalyticsAggregationService


class AnalyticsQuery(ObjectType):
    """Analytics GraphQL query endpoints."""
    
    # User Activity Summary
    user_activity_summary = graphene.Field(
        ActivitySummaryType,
        user_id=String(description="User ID to get activity summary for"),
        days=Int(default_value=30, description="Number of days to look back"),
        description="Get user activity summary for a specified period"
    )
    
    # User Engagement Trends
    user_engagement_trends = graphene.List(
        EngagementTrendType,
        user_id=String(description="User ID to get engagement trends for"),
        days=Int(default_value=30, description="Number of days to look back"),
        description="Get user engagement trends over time"
    )
    
    # Content Interactions
    content_interactions = graphene.List(
        ContentInteractionType,
        user_id=String(description="Filter by user ID"),
        content_type=String(description="Filter by content type"),
        content_id=String(description="Filter by content ID"),
        interaction_type=String(description="Filter by interaction type"),
        limit=Int(default_value=100, description="Maximum number of results"),
        description="Get content interaction history"
    )
    
    # Popular Content
    popular_content = graphene.List(
        PopularContentType,
        content_type=String(description="Filter by content type"),
        days=Int(default_value=7, description="Number of days to look back"),
        limit=Int(default_value=50, description="Maximum number of results"),
        description="Get popular content based on interactions"
    )
    
    # User Engagement Metrics
    user_engagement_metrics = graphene.Field(
        UserEngagementMetricsType,
        user_id=String(description="User ID to get metrics for"),
        description="Get comprehensive user engagement metrics"
    )
    
    @login_required
    def resolve_user_activity_summary(self, info, user_id=None, days=30):
        """Resolve user activity summary."""
        try:
            # Use current user if no user_id provided
            if not user_id:
                payload = info.context.payload
                user_id = payload.get('user_id')
            
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            summary = AnalyticsAggregationService.get_user_activity_summary(
                user_id=user_id,
                days=days
            )
            
            return ActivitySummaryType(
                user_id=user_id,
                total_interactions=summary.get('total_interactions', 0),
                posts_created=summary.get('posts_created', 0),
                communities_joined=summary.get('communities_joined', 0),
                connections_made=summary.get('connections_made', 0),
                likes_given=summary.get('likes_given', 0),
                comments_made=summary.get('comments_made', 0),
                period_start=start_date,
                period_end=end_date
            )
        except Exception as e:
            print(f"Error resolving user activity summary: {e}")
            return None
    
    @login_required
    def resolve_user_engagement_trends(self, info, user_id=None, days=30):
        """Resolve user engagement trends."""
        try:
            # Use current user if no user_id provided
            if not user_id:
                payload = info.context.payload
                user_id = payload.get('user_id')
            
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            trends = AnalyticsAggregationService.get_user_engagement_trends(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return [
                EngagementTrendType(
                    user_id=user_id,
                    date=trend['date'],
                    daily_interactions=trend['daily_interactions'],
                    engagement_score=trend['engagement_score'],
                    active_hours=trend['active_hours']
                )
                for trend in trends
            ]
        except Exception as e:
            print(f"Error resolving user engagement trends: {e}")
            return []
    
    @login_required
    def resolve_content_interactions(self, info, user_id=None, content_type=None, 
                                   content_id=None, interaction_type=None, limit=100):
        """Resolve content interactions."""
        try:
            interactions = AnalyticsAggregationService.get_content_interactions(
                user_id=user_id,
                content_type=content_type,
                content_id=content_id,
                interaction_type=interaction_type,
                limit=limit
            )
            
            return [
                ContentInteractionType(
                    interaction_id=interaction['id'],
                    user_id=interaction['user_id'],
                    content_type=interaction['content_type'],
                    content_id=interaction['content_id'],
                    interaction_type=interaction['interaction_type'],
                    timestamp=interaction['timestamp'],
                    metadata=str(interaction.get('metadata', {}))
                )
                for interaction in interactions
            ]
        except Exception as e:
            print(f"Error resolving content interactions: {e}")
            return []
    
    @login_required
    def resolve_popular_content(self, info, content_type=None, days=7, limit=50):
        """Resolve popular content."""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            popular_content = AnalyticsAggregationService.get_popular_content(
                content_type=content_type,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            return [
                PopularContentType(
                    content_id=content['content_id'],
                    content_type=content['content_type'],
                    title=content.get('title', ''),
                    interaction_count=content['interaction_count'],
                    unique_users=content['unique_users'],
                    trending_score=content['trending_score'],
                    period_start=start_date,
                    period_end=end_date
                )
                for content in popular_content
            ]
        except Exception as e:
            print(f"Error resolving popular content: {e}")
            return []
    
    @login_required
    def resolve_user_engagement_metrics(self, info, user_id=None):
        """Resolve user engagement metrics."""
        try:
            # Use current user if no user_id provided
            if not user_id:
                payload = info.context.payload
                user_id = payload.get('user_id')
            
            metrics = AnalyticsAggregationService.get_user_engagement_metrics(user_id)
            
            return UserEngagementMetricsType(
                user_id=user_id,
                avg_session_duration=metrics.get('avg_session_duration', 0.0),
                total_sessions=metrics.get('total_sessions', 0),
                bounce_rate=metrics.get('bounce_rate', 0.0),
                pages_per_session=metrics.get('pages_per_session', 0.0),
                return_visitor_rate=metrics.get('return_visitor_rate', 0.0),
                last_activity=metrics.get('last_activity')
            )
        except Exception as e:
            print(f"Error resolving user engagement metrics: {e}")
            return None