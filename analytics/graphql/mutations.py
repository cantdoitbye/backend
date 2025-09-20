"""Analytics GraphQL Mutations

This module contains GraphQL mutations for tracking user interactions
and analytics events in real-time.
"""

import graphene
from graphene import Mutation, String, Float, Boolean, Int
from graphql_jwt.decorators import login_required
from django.utils import timezone

from user_activity.services.activity_service import ActivityService
from analytics.services.analytics_aggregation_service import AnalyticsAggregationService


class TrackScrollDepthInput(graphene.InputObjectType):
    """Input for tracking scroll depth."""
    page_url = String(required=True, description="URL of the page")
    max_scroll_depth = Float(required=True, description="Maximum scroll depth percentage (0-100)")
    time_on_page = Float(required=True, description="Time spent on page in seconds")
    session_id = String(description="Session identifier")


class TrackContentInteractionInput(graphene.InputObjectType):
    """Input for tracking content interactions."""
    content_type = String(required=True, description="Type of content (post, community, etc.)")
    content_id = String(required=True, description="Identifier of the content")
    interaction_type = String(required=True, description="Type of interaction (view, like, share, etc.)")
    metadata = String(description="Additional metadata as JSON string")


class TrackUserSessionInput(graphene.InputObjectType):
    """Input for tracking user session data."""
    session_id = String(required=True, description="Session identifier")
    session_start = String(description="Session start timestamp")
    session_end = String(description="Session end timestamp")
    pages_visited = Int(description="Number of pages visited in session")
    device_type = String(description="Device type (mobile, desktop, tablet)")
    user_agent = String(description="User agent string")


class TrackScrollDepth(Mutation):
    """Track user scroll depth on pages."""
    success = Boolean()
    message = String()
    
    class Arguments:
        input = TrackScrollDepthInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        """Track scroll depth for analytics."""
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            # Track scroll depth using activity service
            ActivityService.track_content_interaction_by_id(
                user_id=user_id,
                content_type="page",
                content_id=input.page_url,
                interaction_type="scroll",
                metadata={
                    "max_scroll_depth": input.max_scroll_depth,
                    "time_on_page": input.time_on_page,
                    "session_id": input.session_id or "",
                    "timestamp": timezone.now().isoformat()
                }
            )
            
            return TrackScrollDepth(
                success=True,
                message="Scroll depth tracked successfully"
            )
        except Exception as e:
            print(f"Error tracking scroll depth: {e}")
            return TrackScrollDepth(
                success=False,
                message=f"Failed to track scroll depth: {str(e)}"
            )


class TrackContentInteraction(Mutation):
    """Track user content interactions."""
    success = Boolean()
    message = String()
    
    class Arguments:
        input = TrackContentInteractionInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        """Track content interaction for analytics."""
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            # Parse metadata if provided
            metadata = {}
            if input.metadata:
                try:
                    import json
                    metadata = json.loads(input.metadata)
                except json.JSONDecodeError:
                    metadata = {"raw_metadata": input.metadata}
            
            # Track interaction using activity service
            ActivityService.track_content_interaction_by_id(
                user_id=user_id,
                content_type=input.content_type,
                content_id=input.content_id,
                interaction_type=input.interaction_type,
                metadata=metadata
            )
            
            return TrackContentInteraction(
                success=True,
                message="Content interaction tracked successfully"
            )
        except Exception as e:
            print(f"Error tracking content interaction: {e}")
            return TrackContentInteraction(
                success=False,
                message=f"Failed to track content interaction: {str(e)}"
            )


class TrackUserSession(Mutation):
    """Track user session data."""
    success = Boolean()
    message = String()
    
    class Arguments:
        input = TrackUserSessionInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        """Track user session for analytics."""
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            # Track session using activity service
            ActivityService.track_content_interaction_by_id(
                user_id=user_id,
                content_type="session",
                content_id=input.session_id,
                interaction_type="session_data",
                metadata={
                    "session_start": input.session_start,
                    "session_end": input.session_end,
                    "pages_visited": input.pages_visited,
                    "device_type": input.device_type,
                    "user_agent": input.user_agent,
                    "timestamp": timezone.now().isoformat()
                }
            )
            
            return TrackUserSession(
                success=True,
                message="User session tracked successfully"
            )
        except Exception as e:
            print(f"Error tracking user session: {e}")
            return TrackUserSession(
                success=False,
                message=f"Failed to track user session: {str(e)}"
            )


class AnalyticsMutation(graphene.ObjectType):
    """Analytics mutation endpoints."""
    track_scroll_depth = TrackScrollDepth.Field()
    track_content_interaction = TrackContentInteraction.Field()
    track_user_session = TrackUserSession.Field()