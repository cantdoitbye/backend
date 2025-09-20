"""Analytics GraphQL Types

This module defines GraphQL types for analytics data structures.
It provides types for user activity summaries, engagement trends,
and other analytics-related data.
"""

import graphene
from graphene import ObjectType, String, Int, Float, List, DateTime


class ActivitySummaryType(ObjectType):
    """User activity summary data type."""
    user_id = String(description="User identifier")
    total_interactions = Int(description="Total number of interactions")
    posts_created = Int(description="Number of posts created")
    communities_joined = Int(description="Number of communities joined")
    connections_made = Int(description="Number of connections made")
    likes_given = Int(description="Number of likes given")
    comments_made = Int(description="Number of comments made")
    period_start = DateTime(description="Start of the activity period")
    period_end = DateTime(description="End of the activity period")


class EngagementTrendType(ObjectType):
    """User engagement trend data type."""
    user_id = String(description="User identifier")
    date = DateTime(description="Date of the engagement data")
    daily_interactions = Int(description="Number of interactions on this date")
    engagement_score = Float(description="Calculated engagement score")
    active_hours = Float(description="Hours of activity on this date")


class ContentInteractionType(ObjectType):
    """Content interaction data type."""
    interaction_id = String(description="Unique interaction identifier")
    user_id = String(description="User who performed the interaction")
    content_type = String(description="Type of content (post, community, etc.)")
    content_id = String(description="Identifier of the content")
    interaction_type = String(description="Type of interaction (like, comment, etc.)")
    timestamp = DateTime(description="When the interaction occurred")
    metadata = String(description="Additional interaction metadata as JSON")


class ScrollDepthType(ObjectType):
    """Scroll depth tracking data type."""
    session_id = String(description="User session identifier")
    user_id = String(description="User identifier")
    page_url = String(description="URL of the page")
    max_scroll_depth = Float(description="Maximum scroll depth percentage")
    time_on_page = Float(description="Time spent on page in seconds")
    timestamp = DateTime(description="When the scroll tracking occurred")


class PopularContentType(ObjectType):
    """Popular content data type."""
    content_id = String(description="Content identifier")
    content_type = String(description="Type of content")
    title = String(description="Content title")
    interaction_count = Int(description="Total number of interactions")
    unique_users = Int(description="Number of unique users who interacted")
    trending_score = Float(description="Calculated trending score")
    period_start = DateTime(description="Start of the trending period")
    period_end = DateTime(description="End of the trending period")


class UserEngagementMetricsType(ObjectType):
    """Comprehensive user engagement metrics."""
    user_id = String(description="User identifier")
    avg_session_duration = Float(description="Average session duration in minutes")
    total_sessions = Int(description="Total number of sessions")
    bounce_rate = Float(description="Bounce rate percentage")
    pages_per_session = Float(description="Average pages per session")
    return_visitor_rate = Float(description="Return visitor rate percentage")
    last_activity = DateTime(description="Last recorded activity timestamp")