# Agent GraphQL Input Types
# This module defines GraphQL input types for the agentic community management system.

import graphene
from graphene import InputObjectType, String, List, Boolean, Int, Enum


class AgentTypeEnum(Enum):
    """
    Enum for agent types.
    """
    COMMUNITY_LEADER = "COMMUNITY_LEADER"
    MODERATOR = "MODERATOR"
    ASSISTANT = "ASSISTANT"


class CreateAgentInput(InputObjectType):
    """
    Input type for creating a new agent.
    """
    name = String(required=True, description="Human-readable name for the agent")
    description = String(description="Detailed description of the agent's purpose")
    agent_type = AgentTypeEnum(required=True, description="Type of agent")
    capabilities = List(String, required=True, description="List of capabilities this agent should have. Available capabilities: edit_community, moderate_users, send_messages, view_analytics, manage_events, handle_reports")
    icon_id = String(description="Optional reference to agent's avatar/icon")


class UpdateAgentInput(InputObjectType):
    """
    Input type for updating an existing agent.
    """
    uid = String(required=True, description="UID of the agent to update")
    name = String(description="New name for the agent")
    description = String(description="New description for the agent")
    capabilities = List(String, description="New capabilities list. Available capabilities: edit_community, moderate_users, send_messages, view_analytics, manage_events, handle_reports")
    status = String(description="New status for the agent (ACTIVE, INACTIVE, SUSPENDED)")
    icon_id = String(description="New icon reference")


class AgentCapabilityInput(InputObjectType):
    """
    Input type for managing agent capabilities.
    """
    agent_uid = String(required=True, description="Unique identifier of the agent")
    capabilities = List(String, required=True, description="List of capabilities to manage. Available capabilities: edit_community, moderate_users, send_messages, view_analytics, manage_events, handle_reports")
    operation = String(required=True, description="Operation to perform: 'add', 'remove', or 'replace'")
    community_uid = String(description="Community context for capability management")


class AgentPermissionInput(InputObjectType):
    """
    Input type for managing agent permissions.
    """
    assignment_uid = String(required=True, description="Unique identifier of the assignment")
    permissions = List(String, required=True, description="List of permissions to manage")
    operation = String(required=True, description="Operation to perform: 'add', 'remove', or 'replace'")
    reason = String(description="Reason for permission change")


class BulkAgentOperationInput(InputObjectType):
    """
    Input type for bulk agent operations.
    """
    agent_uids = List(String, required=True, description="List of agent UIDs to operate on")
    operation = String(required=True, description="Operation to perform: 'activate', 'deactivate', 'suspend'")
    reason = String(description="Reason for bulk operation")
    community_uid = String(description="Community context for operation")


class BulkAssignmentOperationInput(InputObjectType):
    """
    Input type for bulk assignment operations.
    """
    assignment_uids = List(String, required=True, description="List of assignment UIDs to operate on")
    operation = String(required=True, description="Operation to perform: 'activate', 'deactivate', 'transfer'")
    target_community_uid = String(description="Target community for transfer operations")
    reason = String(description="Reason for bulk operation")


class AssignAgentToCommunityInput(InputObjectType):
    """
    Input type for assigning an agent to a community.
    """
    agent_uid = String(required=True, description="UID of the agent to assign")
    community_uid = String(required=True, description="UID of the community to assign to")
    permissions = List(String, description="Optional additional permissions for this assignment")
    allow_multiple_leaders = Boolean(default_value=False, description="Whether to allow multiple active leader assignments")


class UpdateAgentAssignmentInput(InputObjectType):
    """
    Input type for updating an agent-community assignment.
    """
    assignment_uid = String(required=True, description="UID of the assignment to update")
    status = String(description="New status for the assignment (ACTIVE, INACTIVE, SUSPENDED)")
    permissions = List(String, description="New permissions list for the assignment")


class DeactivateAgentAssignmentInput(InputObjectType):
    """
    Input type for deactivating an agent assignment.
    """
    assignment_uid = String(required=True, description="UID of the assignment to deactivate")


class StoreAgentContextInput(InputObjectType):
    """
    Input type for storing agent context.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")
    context = graphene.JSONString(required=True, description="Context data to store")
    expires_in_hours = Int(description="Optional expiration time in hours")
    priority = Int(default_value=0, description="Priority for memory cleanup (higher = more important)")


class UpdateConversationHistoryInput(InputObjectType):
    """
    Input type for updating agent conversation history.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")
    conversation_data = graphene.JSONString(required=True, description="New conversation data to add")
    max_history_items = Int(default_value=100, description="Maximum number of history items to keep")


class StoreAgentKnowledgeInput(InputObjectType):
    """
    Input type for storing agent knowledge.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")
    knowledge_data = graphene.JSONString(required=True, description="Knowledge data to store")
    knowledge_key = String(description="Optional key to organize knowledge by topic")


class StoreAgentPreferencesInput(InputObjectType):
    """
    Input type for storing agent preferences.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")
    preferences = graphene.JSONString(required=True, description="Preferences data to store")


class ClearAgentMemoryInput(InputObjectType):
    """
    Input type for clearing agent memory.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")
    memory_type = String(description="Optional specific memory type to clear (context, conversation, knowledge, preferences)")


class LogAgentActionInput(InputObjectType):
    """
    Input type for logging agent actions.
    """
    agent_uid = String(required=True, description="UID of the agent that performed the action")
    community_uid = String(required=True, description="UID of the community where action was performed")
    action_type = String(required=True, description="Type of action performed")
    details = graphene.JSONString(required=True, description="Detailed information about the action")
    success = Boolean(required=True, description="Whether the action succeeded")
    error_message = String(description="Error details if action failed")
    execution_time_ms = Int(description="How long the action took to execute")
    user_context = graphene.JSONString(description="Additional context information")


class GetAgentActionHistoryInput(InputObjectType):
    """
    Input type for retrieving agent action history.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(description="Optional community UID to filter by")
    action_type = String(description="Optional action type to filter by")
    limit = Int(default_value=100, description="Maximum number of log entries to return")


class ValidateAgentActionInput(InputObjectType):
    """
    Input type for validating agent action permissions.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")
    action_type = String(required=True, description="Type of action to validate")


class GetConversationHistoryInput(InputObjectType):
    """
    Input type for retrieving conversation history.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")
    limit = Int(description="Optional limit on number of entries to return")


class GetCommunityKnowledgeInput(InputObjectType):
    """
    Input type for retrieving community knowledge.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")
    knowledge_key = String(description="Optional specific key to retrieve")


class GetAgentPreferencesInput(InputObjectType):
    """
    Input type for retrieving agent preferences.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")


class GetMemoryStatsInput(InputObjectType):
    """
    Input type for retrieving memory statistics.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(description="Optional community UID to filter by")


class GenerateAuditReportInput(InputObjectType):
    """
    Input type for generating agent audit reports.
    """
    agent_uid = String(required=True, description="UID of the agent")
    community_uid = String(required=True, description="UID of the community")


# Filter and pagination inputs
class AgentFilterInput(InputObjectType):
    """
    Input type for filtering agents.
    """
    agent_type = AgentTypeEnum(description="Filter by agent type")
    status = String(description="Filter by agent status")
    has_capability = String(description="Filter by specific capability")
    created_after = graphene.DateTime(description="Filter by creation date (after)")
    created_before = graphene.DateTime(description="Filter by creation date (before)")


class AgentAssignmentFilterInput(InputObjectType):
    """
    Input type for filtering agent assignments.
    """
    agent_uid = String(description="Filter by agent UID")
    community_uid = String(description="Filter by community UID")
    status = String(description="Filter by assignment status")
    assigned_after = graphene.DateTime(description="Filter by assignment date (after)")
    assigned_before = graphene.DateTime(description="Filter by assignment date (before)")


class PaginationInput(InputObjectType):
    """
    Input type for pagination.
    """
    page = Int(default_value=1, description="Page number (1-based)")
    page_size = Int(default_value=20, description="Number of items per page")
    order_by = String(description="Field to order by")
    order_direction = String(default_value="ASC", description="Order direction (ASC or DESC)")


# Bulk operation inputs
class BulkAssignAgentsInput(InputObjectType):
    """
    Input type for bulk agent assignments.
    """
    agent_uids = List(String, required=True, description="List of agent UIDs to assign")
    community_uid = String(required=True, description="UID of the community to assign to")
    permissions = List(String, description="Optional permissions for all assignments")


class BulkUpdateAgentStatusInput(InputObjectType):
    """
    Input type for bulk agent status updates.
    """
    agent_uids = List(String, required=True, description="List of agent UIDs to update")
    status = String(required=True, description="New status for all agents")


class BulkDeactivateAssignmentsInput(InputObjectType):
    """
    Input type for bulk assignment deactivation.
    """
    assignment_uids = List(String, required=True, description="List of assignment UIDs to deactivate")


# Search inputs
class AgentSearchInput(InputObjectType):
    """
    Input type for searching agents.
    """
    query = String(required=True, description="Search query")
    search_fields = List(String, description="Fields to search in (name, description, capabilities)")
    filters = graphene.Field(AgentFilterInput, description="Additional filters to apply")
    pagination = graphene.Field(PaginationInput, description="Pagination options")


class CommunityAgentSearchInput(InputObjectType):
    """
    Input type for searching agents within a community.
    """
    community_uid = String(required=True, description="UID of the community")
    query = String(description="Optional search query")
    include_inactive = Boolean(default_value=False, description="Whether to include inactive assignments")
    pagination = graphene.Field(PaginationInput, description="Pagination options")