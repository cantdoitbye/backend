# truststream/graphql/types.py

"""
TrustStream GraphQL Types

This module defines all GraphQL types for the TrustStream API endpoints
that the admin interface expects.
"""

import graphene
from graphene import ObjectType, String, Float, Int, Boolean, List, Field
from graphene_django import DjangoObjectType
from ..models import TrustScoreCache, ModerationLog, AgentPerformanceMetrics


class TrustScoreType(ObjectType):
    """Trust score information for a user"""
    user_id = String(required=True)
    trust_score = Float(required=True)
    risk_level = String(required=True)
    last_updated = String(required=True)
    factors = Field(lambda: TrustFactorsType)


class TrustFactorsType(ObjectType):
    """Detailed trust factors breakdown"""
    engagement = Float()
    reputation = Float()
    consistency = Float()


class CommunityTrustMetricsType(ObjectType):
    """Community-level trust metrics"""
    community_id = String(required=True)
    trust_score = Float(required=True)
    risk_level = String(required=True)
    active_members = Int(required=True)
    moderation_actions = Int(required=True)
    ai_confidence = Float(required=True)
    engagement_quality = Float(required=True)
    positive_ratio = Float(required=True)


class TrustMetricsType(ObjectType):
    """General trust metrics"""
    trust_score = Float(required=True)
    risk_level = String(required=True)
    active_members = Int(required=True)
    moderation_actions = Int(required=True)
    ai_confidence = Float(required=True)
    engagement_quality = Float(required=True)
    positive_ratio = Float(required=True)


class CommunityInsightType(ObjectType):
    """Community insight information"""
    id = String(required=True)
    timestamp = String(required=True)
    type = String(required=True)
    risk_level = String(required=True)
    message = String(required=True)
    details = String(required=True)


class MessageAnalysisType(ObjectType):
    """AI message analysis results"""
    message_id = String(required=True)
    trust_score = Float(required=True)
    risk_level = String(required=True)
    sentiment = String(required=True)
    confidence = Float(required=True)
    flags = List(String)


class DecisionAuditTrailType(ObjectType):
    """Audit trail for moderation decisions"""
    timestamp = String(required=True)
    action = String(required=True)
    agent = String(required=True)
    details = String(required=True)


class MatrixRoomType(ObjectType):
    """Matrix room information"""
    room_id = String(required=True)
    name = String(required=True)
    member_count = Int(required=True)
    encrypted = Boolean(required=True)


class MatrixUserType(ObjectType):
    """Matrix user information"""
    user_id = String(required=True)
    display_name = String()
    avatar_url = String()
    power_level = Int()


class AgentEcosystemStatusType(ObjectType):
    """Agent ecosystem status"""
    total_agents = Int(required=True)
    active_agents = Int(required=True)
    avg_response_time = Float(required=True)
    success_rate = Float(required=True)


class AgentPerformanceType(ObjectType):
    """Individual agent performance metrics"""
    agent_id = String(required=True)
    accuracy_rate = Float(required=True)
    processing_time = Float(required=True)
    decisions_made = Int(required=True)


class SystemHealthType(ObjectType):
    """System health status"""
    status = String(required=True)
    uptime = Float(required=True)
    response_time = Float(required=True)
    error_rate = Float(required=True)


class SystemAlertType(ObjectType):
    """System alert information"""
    id = String(required=True)
    severity = String(required=True)
    message = String(required=True)
    timestamp = String(required=True)


class PerformanceMetricsType(ObjectType):
    """Performance metrics"""
    cpu_usage = Float(required=True)
    memory_usage = Float(required=True)
    response_time = Float(required=True)
    throughput = Float(required=True)


class AIProviderStatsType(ObjectType):
    """AI provider statistics"""
    provider = String(required=True)
    requests = Int(required=True)
    success_rate = Float(required=True)
    avg_response_time = Float(required=True)


class AIProviderCostsType(ObjectType):
    """AI provider cost information"""
    provider = String(required=True)
    total_cost = Float(required=True)
    tokens_used = Int(required=True)
    cost_per_token = Float(required=True)