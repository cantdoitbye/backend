# Agent GraphQL Queries
# This module defines GraphQL queries for the agentic community management system.

import graphene
from graphene import ObjectType, String, List, Boolean, Int
from graphql_jwt.decorators import login_required
import logging

from .types import (
    AgentType, AgentSummaryType, AgentAssignmentType, CommunityAgentSummaryType,
    AgentActionLogType, AgentMemoryType, AgentStatsType, AgentMemoryStatsType,
    AgentAuditReportType
)
from .inputs import (
    AgentFilterInput, AgentAssignmentFilterInput, PaginationInput,
    GetAgentActionHistoryInput, GetConversationHistoryInput,
    GetCommunityKnowledgeInput, GetAgentPreferencesInput,
    GetMemoryStatsInput, GenerateAuditReportInput,
    AgentSearchInput, CommunityAgentSearchInput
)
from ..services.agent_service import AgentService, AgentServiceError
from ..services.auth_service import AgentAuthService, AgentAuthError
from ..services.memory_service import AgentMemoryService, AgentMemoryError
from ..models import Agent, AgentCommunityAssignment, AgentActionLog, AgentMemory


logger = logging.getLogger(__name__)


class AgentQueries(ObjectType):
    """
    GraphQL queries for agent management.
    
    This class provides all query operations for retrieving agent information,
    assignments, memory, and audit data.
    """
    
    # Basic agent queries
    get_agent = graphene.Field(
        AgentType,
        agent_uid=String(required=True),
        description="Get a specific agent by UID"
    )
    
    get_agents = graphene.List(
        AgentType,
        filters=graphene.Argument(AgentFilterInput),
        pagination=graphene.Argument(PaginationInput),
        description="Get list of agents with optional filtering and pagination"
    )
    
    get_agents_summary = graphene.List(
        AgentSummaryType,
        filters=graphene.Argument(AgentFilterInput),
        pagination=graphene.Argument(PaginationInput),
        description="Get summarized list of agents for performance"
    )
    
    search_agents = graphene.List(
        AgentType,
        input=graphene.Argument(AgentSearchInput, required=True),
        description="Search agents by query with filters"
    )
    
    # Community-agent relationship queries
    get_community_leader = graphene.Field(
        AgentType,
        community_uid=String(required=True),
        description="Get the current leader agent for a community"
    )
    
    get_community_agents = graphene.List(
        CommunityAgentSummaryType,
        community_uid=String(required=True),
        include_inactive=Boolean(default_value=False),
        description="Get all agents assigned to a specific community"
    )
    
    get_agent_assignments = graphene.List(
        AgentAssignmentType,
        agent_uid=String(required=True),
        filters=graphene.Argument(AgentAssignmentFilterInput),
        description="Get all assignments for a specific agent"
    )
    
    get_agent_assignment = graphene.Field(
        AgentAssignmentType,
        assignment_uid=String(required=True),
        description="Get a specific agent assignment by UID"
    )
    
    # Agent memory and context queries
    get_agent_context = graphene.JSONString(
        agent_uid=String(required=True),
        community_uid=String(required=True),
        description="Get stored context for agent in community"
    )
    
    get_conversation_history = graphene.List(
        graphene.JSONString,
        input=graphene.Argument(GetConversationHistoryInput, required=True),
        description="Get conversation history for agent in community"
    )
    
    get_community_knowledge = graphene.JSONString(
        input=graphene.Argument(GetCommunityKnowledgeInput, required=True),
        description="Get community-specific knowledge for agent"
    )
    
    get_agent_preferences = graphene.JSONString(
        input=graphene.Argument(GetAgentPreferencesInput, required=True),
        description="Get agent preferences for a community"
    )
    
    get_agent_memory = graphene.List(
        AgentMemoryType,
        agent_uid=String(required=True),
        community_uid=String(),
        memory_type=String(),
        description="Get agent memory records with optional filtering"
    )
    
    # Agent action and audit queries
    get_agent_action_history = graphene.List(
        AgentActionLogType,
        input=graphene.Argument(GetAgentActionHistoryInput, required=True),
        description="Get action history for an agent"
    )
    
    get_community_action_history = graphene.List(
        AgentActionLogType,
        community_uid=String(required=True),
        action_type=String(),
        limit=Int(default_value=100),
        description="Get action history for a community"
    )
    
    generate_agent_audit_report = graphene.Field(
        AgentAuditReportType,
        input=graphene.Argument(GenerateAuditReportInput, required=True),
        description="Generate comprehensive audit report for agent access"
    )
    
    # Statistics and analytics queries
    get_agent_stats = graphene.Field(
        AgentStatsType,
        description="Get overall agent statistics"
    )
    
    get_agent_memory_stats = graphene.Field(
        AgentMemoryStatsType,
        input=graphene.Argument(GetMemoryStatsInput, required=True),
        description="Get memory usage statistics for an agent"
    )
    
    # Permission and capability queries
    get_agent_permissions = graphene.List(
        String,
        agent_uid=String(required=True),
        community_uid=String(required=True),
        description="Get permissions for agent in specific community"
    )
    
    get_available_actions = graphene.List(
        String,
        agent_uid=String(required=True),
        community_uid=String(required=True),
        description="Get available actions for agent in community"
    )
    
    validate_agent_permission = graphene.Boolean(
        agent_uid=String(required=True),
        community_uid=String(required=True),
        permission=String(required=True),
        description="Check if agent has specific permission in community"
    )
    
    # Implementation methods
    
    @login_required
    def resolve_get_agent(self, info, agent_uid):
        """Get a specific agent by UID."""
        try:
            logger.debug(f"Getting agent: {agent_uid}")
            
            agent_service = AgentService()
            agent = agent_service.get_agent_by_uid(agent_uid)
            
            return AgentType.from_neomodel(agent)
            
        except Exception as e:
            logger.error(f"Error getting agent {agent_uid}: {str(e)}")
            return None
    
    @login_required
    def resolve_get_agents(self, info, filters=None, pagination=None):
        """Get list of agents with optional filtering and pagination."""
        try:
            logger.debug("Getting agents list")
            
            # Build query filters
            query_filters = {}
            if filters:
                if filters.agent_type:
                    query_filters['agent_type'] = filters.agent_type
                if filters.status:
                    query_filters['status'] = filters.status
            
            # Get agents from database
            agents = Agent.nodes.filter(**query_filters)
            
            # Apply capability filter if specified
            if filters and filters.has_capability:
                agents = [agent for agent in agents if agent.has_capability(filters.has_capability)]
            
            # Apply date filters
            if filters:
                if filters.created_after:
                    agents = [agent for agent in agents if agent.created_date >= filters.created_after]
                if filters.created_before:
                    agents = [agent for agent in agents if agent.created_date <= filters.created_before]
            
            # Apply pagination
            if pagination:
                page = pagination.page or 1
                page_size = pagination.page_size or 20
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                agents = list(agents)[start_idx:end_idx]
            
            # Convert to GraphQL types
            return [AgentType.from_neomodel(agent) for agent in agents if agent]
            
        except Exception as e:
            logger.error(f"Error getting agents: {str(e)}")
            return []
    
    @login_required
    def resolve_get_agents_summary(self, info, filters=None, pagination=None):
        """Get summarized list of agents for performance."""
        try:
            logger.debug("Getting agents summary")
            
            # Use similar logic as get_agents but return summary types
            query_filters = {}
            if filters:
                if filters.agent_type:
                    query_filters['agent_type'] = filters.agent_type
                if filters.status:
                    query_filters['status'] = filters.status
            
            agents = Agent.nodes.filter(**query_filters)
            
            # Apply filters and pagination (same as get_agents)
            if filters and filters.has_capability:
                agents = [agent for agent in agents if agent.has_capability(filters.has_capability)]
            
            if pagination:
                page = pagination.page or 1
                page_size = pagination.page_size or 20
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                agents = list(agents)[start_idx:end_idx]
            
            return [AgentSummaryType.from_neomodel(agent) for agent in agents if agent]
            
        except Exception as e:
            logger.error(f"Error getting agents summary: {str(e)}")
            return []
    
    @login_required
    def resolve_search_agents(self, info, input):
        """Search agents by query with filters."""
        try:
            logger.debug(f"Searching agents with query: {input.query}")
            
            # Get all agents first
            agents = list(Agent.nodes.all())
            
            # Apply text search
            if input.query:
                query_lower = input.query.lower()
                search_fields = input.search_fields or ['name', 'description', 'capabilities']
                
                filtered_agents = []
                for agent in agents:
                    match = False
                    
                    if 'name' in search_fields and agent.name and query_lower in agent.name.lower():
                        match = True
                    elif 'description' in search_fields and agent.description and query_lower in agent.description.lower():
                        match = True
                    elif 'capabilities' in search_fields and agent.capabilities:
                        for capability in agent.capabilities:
                            if query_lower in capability.lower():
                                match = True
                                break
                    
                    if match:
                        filtered_agents.append(agent)
                
                agents = filtered_agents
            
            # Apply additional filters
            if input.filters:
                if input.filters.agent_type:
                    agents = [a for a in agents if a.agent_type == input.filters.agent_type]
                if input.filters.status:
                    agents = [a for a in agents if a.status == input.filters.status]
            
            # Apply pagination
            if input.pagination:
                page = input.pagination.page or 1
                page_size = input.pagination.page_size or 20
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                agents = agents[start_idx:end_idx]
            
            return [AgentType.from_neomodel(agent) for agent in agents if agent]
            
        except Exception as e:
            logger.error(f"Error searching agents: {str(e)}")
            return []
    
    @login_required
    def resolve_get_community_leader(self, info, community_uid):
        """Get the current leader agent for a community."""
        try:
            logger.debug(f"Getting community leader for: {community_uid}")
            
            agent_service = AgentService()
            leader = agent_service.get_community_leader(community_uid)
            
            if leader:
                return AgentType.from_neomodel(leader)
            return None
            
        except Exception as e:
            logger.error(f"Error getting community leader for {community_uid}: {str(e)}")
            return None
    
    @login_required
    def resolve_get_community_agents(self, info, community_uid, include_inactive=False):
        """Get all agents assigned to a specific community."""
        try:
            logger.debug(f"Getting agents for community: {community_uid}")
            
            agent_service = AgentService()
            agents = agent_service.get_community_agents(community_uid)
            
            # Get assignments for these agents
            all_assignments = AgentCommunityAssignment.nodes.all()
            community_assignments = []
            
            for assignment in all_assignments:
                assignment_community = assignment.community.single()
                if (assignment_community and 
                    assignment_community.uid == community_uid and 
                    (include_inactive or assignment.is_active())):
                    community_assignments.append(assignment)
            
            return [CommunityAgentSummaryType.from_assignment(assignment) 
                   for assignment in community_assignments if assignment]
            
        except Exception as e:
            logger.error(f"Error getting community agents for {community_uid}: {str(e)}")
            return []
    
    @login_required
    def resolve_get_agent_assignments(self, info, agent_uid, filters=None):
        """Get all assignments for a specific agent."""
        try:
            logger.debug(f"Getting assignments for agent: {agent_uid}")
            
            agent_service = AgentService()
            assignments = agent_service.get_agent_assignments(agent_uid)
            
            # Apply filters
            if filters:
                if filters.community_uid:
                    assignments = [a for a in assignments 
                                 if a.community.single() and a.community.single().uid == filters.community_uid]
                if filters.status:
                    assignments = [a for a in assignments if a.status == filters.status]
                if filters.assigned_after:
                    assignments = [a for a in assignments if a.assignment_date >= filters.assigned_after]
                if filters.assigned_before:
                    assignments = [a for a in assignments if a.assignment_date <= filters.assigned_before]
            
            return [AgentAssignmentType.from_neomodel(assignment) for assignment in assignments if assignment]
            
        except Exception as e:
            logger.error(f"Error getting agent assignments for {agent_uid}: {str(e)}")
            return []
    
    @login_required
    def resolve_get_agent_assignment(self, info, assignment_uid):
        """Get a specific agent assignment by UID."""
        try:
            logger.debug(f"Getting assignment: {assignment_uid}")
            
            assignment = AgentCommunityAssignment.nodes.get(uid=assignment_uid)
            return AgentAssignmentType.from_neomodel(assignment)
            
        except AgentCommunityAssignment.DoesNotExist:
            logger.warning(f"Assignment not found: {assignment_uid}")
            return None
        except Exception as e:
            logger.error(f"Error getting assignment {assignment_uid}: {str(e)}")
            return None
    
    @login_required
    def resolve_get_agent_context(self, info, agent_uid, community_uid):
        """Get stored context for agent in community."""
        try:
            logger.debug(f"Getting context for agent {agent_uid} in community {community_uid}")
            
            memory_service = AgentMemoryService()
            context = memory_service.retrieve_context(agent_uid, community_uid)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting agent context: {str(e)}")
            return {}
    
    @login_required
    def resolve_get_conversation_history(self, info, input):
        """Get conversation history for agent in community."""
        try:
            logger.debug(f"Getting conversation history for agent {input.agent_uid}")
            
            memory_service = AgentMemoryService()
            history = memory_service.get_conversation_history(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                limit=input.limit
            )
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    @login_required
    def resolve_get_community_knowledge(self, info, input):
        """Get community-specific knowledge for agent."""
        try:
            logger.debug(f"Getting knowledge for agent {input.agent_uid}")
            
            memory_service = AgentMemoryService()
            knowledge = memory_service.get_community_knowledge(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                knowledge_key=input.knowledge_key
            )
            
            return knowledge
            
        except Exception as e:
            logger.error(f"Error getting community knowledge: {str(e)}")
            return {}
    
    @login_required
    def resolve_get_agent_preferences(self, info, input):
        """Get agent preferences for a community."""
        try:
            logger.debug(f"Getting preferences for agent {input.agent_uid}")
            
            memory_service = AgentMemoryService()
            preferences = memory_service.get_preferences(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid
            )
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting agent preferences: {str(e)}")
            return {}
    
    @login_required
    def resolve_get_agent_memory(self, info, agent_uid, community_uid=None, memory_type=None):
        """Get agent memory records with optional filtering."""
        try:
            logger.debug(f"Getting memory for agent {agent_uid}")
            
            # Build query filters
            filters = {'agent_uid': agent_uid}
            if community_uid:
                filters['community_uid'] = community_uid
            if memory_type:
                filters['memory_type'] = memory_type
            
            # Get memory records
            memories = AgentMemory.objects.filter(**filters).order_by('-updated_date')
            
            return [AgentMemoryType.from_django_model(memory) for memory in memories]
            
        except Exception as e:
            logger.error(f"Error getting agent memory: {str(e)}")
            return []
    
    @login_required
    def resolve_get_agent_action_history(self, info, input):
        """Get action history for an agent."""
        try:
            logger.debug(f"Getting action history for agent {input.agent_uid}")
            
            auth_service = AgentAuthService()
            logs = auth_service.get_agent_action_history(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                action_type=input.action_type,
                limit=input.limit
            )
            
            return [AgentActionLogType.from_django_model(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Error getting agent action history: {str(e)}")
            return []
    
    @login_required
    def resolve_get_community_action_history(self, info, community_uid, action_type=None, limit=100):
        """Get action history for a community."""
        try:
            logger.debug(f"Getting action history for community {community_uid}")
            
            # Build query filters
            filters = {'community_uid': community_uid}
            if action_type:
                filters['action_type'] = action_type
            
            # Get action logs
            logs = AgentActionLog.objects.filter(**filters).order_by('-timestamp')[:limit]
            
            return [AgentActionLogType.from_django_model(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Error getting community action history: {str(e)}")
            return []
    
    @login_required
    def resolve_generate_agent_audit_report(self, info, input):
        """Generate comprehensive audit report for agent access."""
        try:
            logger.debug(f"Generating audit report for agent {input.agent_uid}")
            
            auth_service = AgentAuthService()
            audit_data = auth_service.audit_agent_access(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid
            )
            
            return AgentAuditReportType.from_audit_dict(audit_data)
            
        except Exception as e:
            logger.error(f"Error generating audit report: {str(e)}")
            return AgentAuditReportType.from_audit_dict({
                'agent_uid': input.agent_uid,
                'community_uid': input.community_uid,
                'error': str(e)
            })
    
    @login_required
    def resolve_get_agent_stats(self, info):
        """Get overall agent statistics."""
        try:
            logger.debug("Getting agent statistics")
            
            # Calculate statistics
            all_agents = list(Agent.nodes.all())
            all_assignments = list(AgentCommunityAssignment.nodes.all())
            
            stats = {
                'total_agents': len(all_agents),
                'active_agents': len([a for a in all_agents if a.status == 'ACTIVE']),
                'inactive_agents': len([a for a in all_agents if a.status == 'INACTIVE']),
                'suspended_agents': len([a for a in all_agents if a.status == 'SUSPENDED']),
                'total_assignments': len(all_assignments),
                'active_assignments': len([a for a in all_assignments if a.is_active()]),
                'agents_by_type': {},
                'assignments_by_community': {}
            }
            
            # Calculate agents by type
            for agent in all_agents:
                agent_type = agent.agent_type
                stats['agents_by_type'][agent_type] = stats['agents_by_type'].get(agent_type, 0) + 1
            
            # Calculate assignments by community
            for assignment in all_assignments:
                community = assignment.community.single()
                if community:
                    community_uid = community.uid
                    stats['assignments_by_community'][community_uid] = stats['assignments_by_community'].get(community_uid, 0) + 1
            
            return AgentStatsType.from_stats_dict(stats)
            
        except Exception as e:
            logger.error(f"Error getting agent stats: {str(e)}")
            return AgentStatsType.from_stats_dict({})
    
    @login_required
    def resolve_get_agent_memory_stats(self, info, input):
        """Get memory usage statistics for an agent."""
        try:
            logger.debug(f"Getting memory stats for agent {input.agent_uid}")
            
            memory_service = AgentMemoryService()
            stats = memory_service.get_memory_stats(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid
            )
            
            return AgentMemoryStatsType.from_stats_dict(stats)
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return AgentMemoryStatsType.from_stats_dict({})
    
    @login_required
    def resolve_get_agent_permissions(self, info, agent_uid, community_uid):
        """Get permissions for agent in specific community."""
        try:
            logger.debug(f"Getting permissions for agent {agent_uid} in community {community_uid}")
            
            auth_service = AgentAuthService()
            permissions = auth_service.get_agent_permissions(agent_uid, community_uid)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting agent permissions: {str(e)}")
            return []
    
    @login_required
    def resolve_get_available_actions(self, info, agent_uid, community_uid):
        """Get available actions for agent in community."""
        try:
            logger.debug(f"Getting available actions for agent {agent_uid} in community {community_uid}")
            
            auth_service = AgentAuthService()
            actions = auth_service.get_available_actions(agent_uid, community_uid)
            
            return actions
            
        except Exception as e:
            logger.error(f"Error getting available actions: {str(e)}")
            return []
    
    @login_required
    def resolve_validate_agent_permission(self, info, agent_uid, community_uid, permission):
        """Check if agent has specific permission in community."""
        try:
            logger.debug(f"Validating permission '{permission}' for agent {agent_uid}")
            
            auth_service = AgentAuthService()
            has_permission = auth_service.check_permission(agent_uid, community_uid, permission)
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Error validating agent permission: {str(e)}")
            return False