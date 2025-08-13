# Agent GraphQL Mutations
# This module defines GraphQL mutations for the agentic community management system.

import graphene
from graphene import Mutation, Boolean, String, List, Field
from graphql_jwt.decorators import login_required, superuser_required
import logging

from .types import (
    AgentType, AgentAssignmentType, AgentMemoryType, AgentActionLogType,
    AgentMutationResponse, AgentAssignmentMutationResponse, 
    AgentMemoryMutationResponse, AgentActionResponse
)
from .inputs import (
    CreateAgentInput, UpdateAgentInput, AgentCapabilityInput, AgentPermissionInput, 
    BulkAgentOperationInput, BulkAssignmentOperationInput, AssignAgentToCommunityInput,
    UpdateAgentAssignmentInput, DeactivateAgentAssignmentInput,
    StoreAgentContextInput, UpdateConversationHistoryInput,
    StoreAgentKnowledgeInput, StoreAgentPreferencesInput,
    ClearAgentMemoryInput, LogAgentActionInput
)
from ..utils.agent_decorator import handle_agent_errors, require_authentication
from ..services.agent_service import AgentService, AgentServiceError
from ..services.auth_service import AgentAuthService, AgentAuthError
from ..services.memory_service import AgentMemoryService, AgentMemoryError
from ..utils.agent_decorator import handle_agent_errors


logger = logging.getLogger(__name__)


class CreateAgent(Mutation):
    """
    Create a new agent with specified capabilities.
    
    This mutation allows authorized users (typically admins) to create new AI agents
    that can be assigned to communities for autonomous management.
    """
    
    class Arguments:
        input = CreateAgentInput(required=True)
    
    Output = AgentMutationResponse
    
    @handle_agent_errors
    @login_required
    # @superuser_required
    def mutate(self, info, input):
        try:
            logger.info(f"Creating new agent: {input.name}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            # Create agent using service
            agent_service = AgentService()
            agent = agent_service.create_agent(
                name=input.name,
                agent_type=input.agent_type,
                capabilities=input.capabilities,
                description=input.description,
                icon_id=input.icon_id,
                created_by_uid=user_id
            )
            
            logger.info(f"Successfully created agent {agent.uid}: {agent.name}")
            
            return AgentMutationResponse(
                success=True,
                message=f"Agent '{agent.name}' created successfully",
                agent=AgentType.from_neomodel(agent)
            )
            
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            return AgentMutationResponse(
                success=False,
                message=f"Failed to create agent: {str(e)}",
                agent=None
            )


class UpdateAgent(Mutation):
    """
    Update an existing agent's information.
    
    This mutation allows authorized users to modify agent properties
    such as name, description, capabilities, and status.
    """
    
    class Arguments:
        input = UpdateAgentInput(required=True)
    
    Output = AgentMutationResponse
    
    @handle_agent_errors
    @login_required
    # @superuser_required
    def mutate(self, info, input):
        try:
            logger.info(f"Updating agent: {input.uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Update agent using service
            agent_service = AgentService()
            agent = agent_service.update_agent(
                agent_uid=input.uid,
                name=input.name,
                description=input.description,
                capabilities=input.capabilities,
                status=input.status,
                icon_id=input.icon_id
            )
            
            logger.info(f"Successfully updated agent {agent.uid}")
            
            return AgentMutationResponse(
                success=True,
                message=f"Agent '{agent.name}' updated successfully",
                agent=AgentType.from_neomodel(agent)
            )
            
        except Exception as e:
            logger.error(f"Failed to update agent: {str(e)}")
            return AgentMutationResponse(
                success=False,
                message=f"Failed to update agent: {str(e)}",
                agent=None
            )


class AssignAgentToCommunity(Mutation):
    """
    Assign an agent as leader to a community.
    
    This mutation creates an assignment relationship between an agent and a community,
    allowing the agent to perform management actions within that community.
    """
    
    class Arguments:
        input = AssignAgentToCommunityInput(required=True)
    
    Output = AgentAssignmentMutationResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Assigning agent {input.agent_uid} to community {input.community_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            # Create assignment using service
            agent_service = AgentService()
            assignment = agent_service.assign_agent_to_community(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                assigned_by_uid=user_id,
                permissions=input.permissions,
                allow_multiple_leaders=input.allow_multiple_leaders
            )
            
            logger.info(f"Successfully assigned agent {input.agent_uid} to community {input.community_uid}")
            
            return AgentAssignmentMutationResponse(
                success=True,
                message="Agent assigned to community successfully",
                assignment=AgentAssignmentType.from_neomodel(assignment)
            )
            
        except Exception as e:
            logger.error(f"Failed to assign agent to community: {str(e)}")
            return AgentAssignmentMutationResponse(
                success=False,
                message=f"Failed to assign agent to community: {str(e)}",
                assignment=None
            )


class UpdateAgentAssignment(Mutation):
    """
    Update an existing agent-community assignment.
    
    This mutation allows modification of assignment properties such as
    status and permissions.
    """
    
    class Arguments:
        input = UpdateAgentAssignmentInput(required=True)
    
    Output = AgentAssignmentMutationResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Updating assignment: {input.assignment_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Update assignment using service
            agent_service = AgentService()
            assignment = agent_service.update_agent_assignment(
                assignment_uid=input.assignment_uid,
                status=input.status,
                permissions=input.permissions
            )
            
            logger.info(f"Successfully updated assignment {input.assignment_uid}")
            
            return AgentAssignmentMutationResponse(
                success=True,
                message="Agent assignment updated successfully",
                assignment=AgentAssignmentType.from_neomodel(assignment)
            )
            
        except Exception as e:
            logger.error(f"Failed to update assignment: {str(e)}")
            return AgentAssignmentMutationResponse(
                success=False,
                message=f"Failed to update assignment: {str(e)}",
                assignment=None
            )


class DeactivateAgentAssignment(Mutation):
    """
    Deactivate an agent's assignment to a community.
    
    This mutation sets the assignment status to inactive, effectively
    removing the agent's access to the community.
    """
    
    class Arguments:
        input = DeactivateAgentAssignmentInput(required=True)
    
    Output = AgentAssignmentMutationResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Deactivating assignment: {input.assignment_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Deactivate assignment using service
            agent_service = AgentService()
            success = agent_service.deactivate_agent_assignment(input.assignment_uid)
            
            if success:
                # Get updated assignment for response
                from ..models import AgentCommunityAssignment
                assignment = AgentCommunityAssignment.nodes.get(uid=input.assignment_uid)
                
                logger.info(f"Successfully deactivated assignment {input.assignment_uid}")
                
                return AgentAssignmentMutationResponse(
                    success=True,
                    message="Agent assignment deactivated successfully",
                    assignment=AgentAssignmentType.from_neomodel(assignment)
                )
            else:
                return AgentAssignmentMutationResponse(
                    success=False,
                    message="Failed to deactivate assignment",
                    assignment=None
                )
            
        except Exception as e:
            logger.error(f"Failed to deactivate assignment: {str(e)}")
            return AgentAssignmentMutationResponse(
                success=False,
                message=f"Failed to deactivate assignment: {str(e)}",
                assignment=None
            )


class StoreAgentContext(Mutation):
    """
    Store agent context for a community.
    
    This mutation allows storing persistent context data that agents
    can access across sessions.
    """
    
    class Arguments:
        input = StoreAgentContextInput(required=True)
    
    Output = AgentMemoryMutationResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Storing context for agent {input.agent_uid} in community {input.community_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Store context using memory service
            memory_service = AgentMemoryService()
            memory = memory_service.store_context(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                context=input.context,
                expires_in_hours=input.expires_in_hours,
                priority=input.priority
            )
            
            logger.info(f"Successfully stored context for agent {input.agent_uid}")
            
            return AgentMemoryMutationResponse(
                success=True,
                message="Agent context stored successfully",
                memory=AgentMemoryType.from_django_model(memory)
            )
            
        except Exception as e:
            logger.error(f"Failed to store agent context: {str(e)}")
            return AgentMemoryMutationResponse(
                success=False,
                message=f"Failed to store agent context: {str(e)}",
                memory=None
            )


class UpdateConversationHistory(Mutation):
    """
    Update agent conversation history.
    
    This mutation adds new conversation data to the agent's history
    for maintaining context continuity.
    """
    
    class Arguments:
        input = UpdateConversationHistoryInput(required=True)
    
    Output = AgentMemoryMutationResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Updating conversation history for agent {input.agent_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Update conversation history using memory service
            memory_service = AgentMemoryService()
            memory = memory_service.update_conversation_history(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                conversation_data=input.conversation_data,
                max_history_items=input.max_history_items
            )
            
            logger.info(f"Successfully updated conversation history for agent {input.agent_uid}")
            
            return AgentMemoryMutationResponse(
                success=True,
                message="Conversation history updated successfully",
                memory=AgentMemoryType.from_django_model(memory)
            )
            
        except Exception as e:
            logger.error(f"Failed to update conversation history: {str(e)}")
            return AgentMemoryMutationResponse(
                success=False,
                message=f"Failed to update conversation history: {str(e)}",
                memory=None
            )


class StoreAgentKnowledge(Mutation):
    """
    Store community-specific knowledge for agent.
    
    This mutation allows storing learned information and insights
    that the agent can use for better community management.
    """
    
    class Arguments:
        input = StoreAgentKnowledgeInput(required=True)
    
    Output = AgentMemoryMutationResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Storing knowledge for agent {input.agent_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Store knowledge using memory service
            memory_service = AgentMemoryService()
            memory = memory_service.store_knowledge(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                knowledge_data=input.knowledge_data,
                knowledge_key=input.knowledge_key
            )
            
            logger.info(f"Successfully stored knowledge for agent {input.agent_uid}")
            
            return AgentMemoryMutationResponse(
                success=True,
                message="Agent knowledge stored successfully",
                memory=AgentMemoryType.from_django_model(memory)
            )
            
        except Exception as e:
            logger.error(f"Failed to store agent knowledge: {str(e)}")
            return AgentMemoryMutationResponse(
                success=False,
                message=f"Failed to store agent knowledge: {str(e)}",
                memory=None
            )


class StoreAgentPreferences(Mutation):
    """
    Store agent preferences for a community.
    
    This mutation allows storing agent configuration and behavior
    settings specific to a community.
    """
    
    class Arguments:
        input = StoreAgentPreferencesInput(required=True)
    
    Output = AgentMemoryMutationResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Storing preferences for agent {input.agent_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Store preferences using memory service
            memory_service = AgentMemoryService()
            memory = memory_service.store_preferences(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                preferences=input.preferences
            )
            
            logger.info(f"Successfully stored preferences for agent {input.agent_uid}")
            
            return AgentMemoryMutationResponse(
                success=True,
                message="Agent preferences stored successfully",
                memory=AgentMemoryType.from_django_model(memory)
            )
            
        except Exception as e:
            logger.error(f"Failed to store agent preferences: {str(e)}")
            return AgentMemoryMutationResponse(
                success=False,
                message=f"Failed to store agent preferences: {str(e)}",
                memory=None
            )


class ClearAgentMemory(Mutation):
    """
    Clear memory for agent in community.
    
    This mutation allows clearing specific types of memory or all memory
    for an agent in a particular community.
    """
    
    class Arguments:
        input = ClearAgentMemoryInput(required=True)
    
    Output = AgentActionResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Clearing memory for agent {input.agent_uid} in community {input.community_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Clear memory using memory service
            memory_service = AgentMemoryService()
            deleted_count = memory_service.clear_memory(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                memory_type=input.memory_type
            )
            
            memory_type_desc = input.memory_type or "all types"
            logger.info(f"Successfully cleared {deleted_count} memory records ({memory_type_desc}) for agent {input.agent_uid}")
            
            return AgentActionResponse(
                success=True,
                message=f"Cleared {deleted_count} memory records ({memory_type_desc})",
                action_log=None,
                result_data={'deleted_count': deleted_count, 'memory_type': input.memory_type}
            )
            
        except Exception as e:
            logger.error(f"Failed to clear agent memory: {str(e)}")
            return AgentActionResponse(
                success=False,
                message=f"Failed to clear agent memory: {str(e)}",
                action_log=None,
                result_data=None
            )


class LogAgentAction(Mutation):
    """
    Log an action performed by an agent.
    
    This mutation creates an audit log entry for agent actions,
    supporting compliance and debugging requirements.
    """
    
    class Arguments:
        input = LogAgentActionInput(required=True)
    
    Output = AgentActionResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, input):
        try:
            logger.info(f"Logging action '{input.action_type}' for agent {input.agent_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Log action using auth service
            auth_service = AgentAuthService()
            log_entry = auth_service.log_agent_action(
                agent_uid=input.agent_uid,
                community_uid=input.community_uid,
                action_type=input.action_type,
                details=input.details,
                success=input.success,
                error_message=input.error_message,
                execution_time_ms=input.execution_time_ms,
                user_context=input.user_context
            )
            
            if log_entry:
                logger.info(f"Successfully logged action '{input.action_type}' for agent {input.agent_uid}")
                
                return AgentActionResponse(
                    success=True,
                    message="Agent action logged successfully",
                    action_log=AgentActionLogType.from_django_model(log_entry),
                    result_data={'log_id': log_entry.id}
                )
            else:
                return AgentActionResponse(
                    success=False,
                    message="Failed to create action log entry",
                    action_log=None,
                    result_data=None
                )
            
        except Exception as e:
            logger.error(f"Failed to log agent action: {str(e)}")
            return AgentActionResponse(
                success=False,
                message=f"Failed to log agent action: {str(e)}",
                action_log=None,
                result_data=None
            )


# Bulk operations
class BulkAssignAgents(Mutation):
    """
    Assign multiple agents to a community in bulk.
    
    This mutation allows efficient assignment of multiple agents
    to the same community with the same permissions.
    """
    
    class Arguments:
        agent_uids = graphene.List(graphene.String, required=True)
        community_uid = graphene.String(required=True)
        permissions = graphene.List(graphene.String)
    
    Output = AgentActionResponse
    
    @handle_agent_errors
    @login_required
    def mutate(self, info, agent_uids, community_uid, permissions=None):
        try:
            logger.info(f"Bulk assigning {len(agent_uids)} agents to community {community_uid}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            # Assign agents using service
            agent_service = AgentService()
            successful_assignments = []
            failed_assignments = []
            
            for agent_uid in agent_uids:
                try:
                    assignment = agent_service.assign_agent_to_community(
                        agent_uid=agent_uid,
                        community_uid=community_uid,
                        assigned_by_uid=user_id,
                        permissions=permissions or [],
                        allow_multiple_leaders=True  # Allow multiple for bulk operations
                    )
                    successful_assignments.append(agent_uid)
                except Exception as e:
                    failed_assignments.append({'agent_uid': agent_uid, 'error': str(e)})
            
            logger.info(f"Bulk assignment completed: {len(successful_assignments)} successful, {len(failed_assignments)} failed")
            
            return AgentActionResponse(
                success=len(successful_assignments) > 0,
                message=f"Assigned {len(successful_assignments)} agents successfully, {len(failed_assignments)} failed",
                action_log=None,
                result_data={
                    'successful_assignments': successful_assignments,
                    'failed_assignments': failed_assignments,
                    'total_attempted': len(agent_uids)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed bulk agent assignment: {str(e)}")
            return AgentActionResponse(
                success=False,
                message=f"Failed bulk agent assignment: {str(e)}",
                action_log=None,
                result_data=None
            )


class BulkUpdateAgentStatus(Mutation):
    """
    Update status of multiple agents in bulk.
    
    This mutation allows efficient status updates for multiple agents
    simultaneously.
    """
    
    class Arguments:
        agent_uids = graphene.List(graphene.String, required=True)
        status = graphene.String(required=True)
    
    Output = AgentActionResponse
    
    @handle_agent_errors
    @login_required
    # @superuser_required
    def mutate(self, info, agent_uids, status):
        try:
            logger.info(f"Bulk updating status of {len(agent_uids)} agents to {status}")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Update agents using service
            agent_service = AgentService()
            successful_updates = []
            failed_updates = []
            
            for agent_uid in agent_uids:
                try:
                    agent = agent_service.update_agent(
                        agent_uid=agent_uid,
                        status=status
                    )
                    successful_updates.append(agent_uid)
                except Exception as e:
                    failed_updates.append({'agent_uid': agent_uid, 'error': str(e)})
            
            logger.info(f"Bulk status update completed: {len(successful_updates)} successful, {len(failed_updates)} failed")
            
            return AgentActionResponse(
                success=len(successful_updates) > 0,
                message=f"Updated {len(successful_updates)} agents successfully, {len(failed_updates)} failed",
                action_log=None,
                result_data={
                    'successful_updates': successful_updates,
                    'failed_updates': failed_updates,
                    'total_attempted': len(agent_uids),
                    'new_status': status
                }
            )
            
        except Exception as e:
            logger.error(f"Failed bulk agent status update: {str(e)}")
            return AgentActionResponse(
                success=False,
                message=f"Failed bulk agent status update: {str(e)}",
                action_log=None,
                result_data=None
            )


# Cleanup operations
class CleanupExpiredMemory(Mutation):
    """
    Clean up expired memory records across all agents.
    
    This mutation performs system maintenance by removing expired
    memory records to free up storage space.
    """
    
    Output = AgentActionResponse
    
    @handle_agent_errors
    @login_required
    # @superuser_required
    def mutate(self, info):
        try:
            logger.info("Starting expired memory cleanup")
            
            # Get current user
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication required")
            
            # Cleanup expired memory using memory service
            memory_service = AgentMemoryService()
            deleted_count = memory_service.cleanup_expired_memory()
            
            logger.info(f"Expired memory cleanup completed: {deleted_count} records deleted")
            
            return AgentActionResponse(
                success=True,
                message=f"Cleaned up {deleted_count} expired memory records",
                action_log=None,
                result_data={'deleted_count': deleted_count}
            )
            
        except Exception as e:
            logger.error(f"Failed expired memory cleanup: {str(e)}")
            return AgentActionResponse(
                success=False,
                message=f"Failed expired memory cleanup: {str(e)}",
                action_log=None,
                result_data=None
            )
        
        except Exception as e:
            logger.error(f"Failed to cleanup expired memory: {str(e)}")
            return CleanupExpiredMemory(
                success=False,
                message=str(e),
                errors=[str(e)],
                cleared_count=0
            )
        except Exception as e:
            logger.error(f"Unexpected error clearing memory: {str(e)}")
            return ClearAgentMemory(
                success=False,
                message="An unexpected error occurred while clearing memory",
                errors=[str(e)],
                cleared_count=0
            )


class ManageAgentCapabilities(Mutation):
    """
    Mutation to manage agent capabilities.
    
    Allows adding, removing, or replacing capabilities for an agent.
    """
    
    class Arguments:
        input = AgentCapabilityInput(required=True, description="Capability management parameters")
    
    success = Boolean()
    message = String()
    errors = List(String)
    agent = Field(AgentType)
    
    @staticmethod
    @handle_agent_errors
    @require_authentication
    def mutate(root, info, input):
        """Manage agent capabilities."""
        try:
            logger.info(f"Managing capabilities for agent {input.agent_uid}: {input.operation}")
            
            # Initialize agent service
            agent_service = AgentService()
            
            # Get the agent
            agent = agent_service.get_agent_by_uid(input.agent_uid)
            
            # Perform the capability operation
            if input.operation == "add":
                updated_agent = agent_service.add_agent_capabilities(
                    agent_uid=input.agent_uid,
                    capabilities=input.capabilities
                )
            elif input.operation == "remove":
                updated_agent = agent_service.remove_agent_capabilities(
                    agent_uid=input.agent_uid,
                    capabilities=input.capabilities
                )
            elif input.operation == "replace":
                updated_agent = agent_service.update_agent(
                    agent_uid=input.agent_uid,
                    capabilities=input.capabilities
                )
            else:
                raise AgentServiceError(f"Invalid operation: {input.operation}. Must be 'add', 'remove', or 'replace'")
            
            logger.info(f"Successfully managed capabilities for agent {input.agent_uid}")
            
            return ManageAgentCapabilities(
                success=True,
                message=f"Agent capabilities {input.operation}d successfully",
                agent=updated_agent
            )
            
        except AgentServiceError as e:
            logger.error(f"Failed to manage capabilities: {str(e)}")
            return ManageAgentCapabilities(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
        except Exception as e:
            logger.error(f"Unexpected error managing capabilities: {str(e)}")
            return ManageAgentCapabilities(
                success=False,
                message="An unexpected error occurred while managing capabilities",
                errors=[str(e)]
            )


class ManageAssignmentPermissions(Mutation):
    """
    Mutation to manage assignment-specific permissions.
    
    Allows adding, removing, or replacing permissions for an agent assignment.
    """
    
    class Arguments:
        input = AgentPermissionInput(required=True, description="Permission management parameters")
    
    success = Boolean()
    message = String()
    errors = List(String)
    assignment = Field(AgentAssignmentType)
    
    @staticmethod
    @handle_agent_errors
    @require_authentication
    def mutate(root, info, input):
        """Manage assignment permissions."""
        try:
            logger.info(f"Managing permissions for assignment {input.assignment_uid}: {input.operation}")
            
            # Initialize agent service
            agent_service = AgentService()
            
            # Get the assignment
            assignment = agent_service.get_assignment_by_uid(input.assignment_uid)
            
            # Perform the permission operation
            if input.operation == "add":
                updated_assignment = agent_service.add_assignment_permissions(
                    assignment_uid=input.assignment_uid,
                    permissions=input.permissions
                )
            elif input.operation == "remove":
                updated_assignment = agent_service.remove_assignment_permissions(
                    assignment_uid=input.assignment_uid,
                    permissions=input.permissions
                )
            elif input.operation == "replace":
                updated_assignment = agent_service.update_agent_assignment(
                    assignment_uid=input.assignment_uid,
                    permissions=input.permissions
                )
            else:
                raise AgentServiceError(f"Invalid operation: {input.operation}")
            
            logger.info(f"Successfully managed permissions for assignment {input.assignment_uid}")
            
            return ManageAssignmentPermissions(
                success=True,
                message=f"Assignment permissions {input.operation}d successfully",
                assignment=updated_assignment
            )
            
        except AgentServiceError as e:
            logger.error(f"Failed to manage permissions: {str(e)}")
            return ManageAssignmentPermissions(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
        except Exception as e:
            logger.error(f"Unexpected error managing permissions: {str(e)}")
            return ManageAssignmentPermissions(
                success=False,
                message="An unexpected error occurred while managing permissions",
                errors=[str(e)]
            )


class BulkAgentOperation(Mutation):
    """
    Mutation for bulk operations on agents.
    
    Allows performing operations on multiple agents at once.
    """
    
    class Arguments:
        input = BulkAgentOperationInput(required=True, description="Bulk operation parameters")
    
    success = Boolean()
    message = String()
    errors = List(String)
    processed_count = graphene.Int()
    failed_count = graphene.Int()
    
    @staticmethod
    @handle_agent_errors
    @require_authentication
    def mutate(root, info, input):
        """Perform bulk operation on agents."""
        try:
            logger.info(f"Performing bulk {input.operation} on {len(input.agent_uids)} agents")
            
            # Initialize agent service
            agent_service = AgentService()
            
            processed_count = 0
            failed_count = 0
            errors = []
            
            # Process each agent
            for agent_uid in input.agent_uids:
                try:
                    if input.operation == "activate":
                        agent_service.update_agent(agent_uid=agent_uid, status="ACTIVE")
                    elif input.operation == "deactivate":
                        agent_service.update_agent(agent_uid=agent_uid, status="INACTIVE")
                    elif input.operation == "suspend":
                        agent_service.update_agent(agent_uid=agent_uid, status="SUSPENDED")
                    else:
                        raise AgentServiceError(f"Invalid operation: {input.operation}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Agent {agent_uid}: {str(e)}")
                    logger.warning(f"Failed to {input.operation} agent {agent_uid}: {str(e)}")
            
            success = failed_count == 0
            message = f"Bulk operation completed. Processed: {processed_count}, Failed: {failed_count}"
            
            logger.info(f"Bulk operation completed: {message}")
            
            return BulkAgentOperation(
                success=success,
                message=message,
                errors=errors,
                processed_count=processed_count,
                failed_count=failed_count
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in bulk operation: {str(e)}")
            return BulkAgentOperation(
                success=False,
                message="An unexpected error occurred during bulk operation",
                errors=[str(e)],
                processed_count=0,
                failed_count=len(input.agent_uids)
            )


class BulkAssignmentOperation(Mutation):
    """
    Mutation for bulk operations on assignments.
    
    Allows performing operations on multiple assignments at once.
    """
    
    class Arguments:
        input = BulkAssignmentOperationInput(required=True, description="Bulk assignment operation parameters")
    
    success = Boolean()
    message = String()
    errors = List(String)
    processed_count = graphene.Int()
    failed_count = graphene.Int()
    
    @staticmethod
    @handle_agent_errors
    @require_authentication
    def mutate(root, info, input):
        """Perform bulk operation on assignments."""
        try:
            logger.info(f"Performing bulk {input.operation} on {len(input.assignment_uids)} assignments")
            
            # Initialize agent service
            agent_service = AgentService()
            
            processed_count = 0
            failed_count = 0
            errors = []
            
            # Process each assignment
            for assignment_uid in input.assignment_uids:
                try:
                    if input.operation == "activate":
                        agent_service.update_agent_assignment(assignment_uid=assignment_uid, status="ACTIVE")
                    elif input.operation == "deactivate":
                        agent_service.deactivate_agent_assignment(assignment_uid=assignment_uid)
                    elif input.operation == "suspend":
                        agent_service.update_agent_assignment(assignment_uid=assignment_uid, status="SUSPENDED")
                    else:
                        raise AgentServiceError(f"Invalid operation: {input.operation}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Assignment {assignment_uid}: {str(e)}")
                    logger.warning(f"Failed to {input.operation} assignment {assignment_uid}: {str(e)}")
            
            success = failed_count == 0
            message = f"Bulk assignment operation completed. Processed: {processed_count}, Failed: {failed_count}"
            
            logger.info(f"Bulk assignment operation completed: {message}")
            
            return BulkAssignmentOperation(
                success=success,
                message=message,
                errors=errors,
                processed_count=processed_count,
                failed_count=failed_count
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in bulk assignment operation: {str(e)}")
            return BulkAssignmentOperation(
                success=False,
                message="An unexpected error occurred during bulk assignment operation",
                errors=[str(e)],
                processed_count=0,
                failed_count=len(input.assignment_uids)
            )


# Mutation class that groups all agent mutations
class AgentMutations(graphene.ObjectType):
    """
    Root mutation class for all agent-related mutations.
    
    This class groups all agent mutations for easy inclusion in the main schema.
    """
    
    # Agent management mutations
    create_agent = CreateAgent.Field()
    update_agent = UpdateAgent.Field()
    
    # Assignment management mutations
    assign_agent_to_community = AssignAgentToCommunity.Field()
    update_agent_assignment = UpdateAgentAssignment.Field()
    deactivate_agent_assignment = DeactivateAgentAssignment.Field()
    
    # Memory management mutations
    store_agent_context = StoreAgentContext.Field()
    update_agent_conversation_history = UpdateConversationHistory.Field()
    store_agent_knowledge = StoreAgentKnowledge.Field()
    store_agent_preferences = StoreAgentPreferences.Field()
    clear_agent_memory = ClearAgentMemory.Field()
    
    # Capability and permission management
    manage_agent_capabilities = ManageAgentCapabilities.Field()
    manage_assignment_permissions = ManageAssignmentPermissions.Field()
    
    # Bulk operations
    bulk_agent_operation = BulkAgentOperation.Field()
    bulk_assignment_operation = BulkAssignmentOperation.Field()