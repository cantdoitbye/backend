# Agent Service Module
# This module provides core business logic for agent management operations.
# It handles agent creation, assignment, and community relationship management.

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..models import Agent, AgentCommunityAssignment
from ..matrix_utils import create_agent_matrix_profile, MatrixRegistrationError, MatrixLoginError, MatrixProfileUpdateError, join_agent_to_community_matrix_room
from auth_manager.models import Users
from community.models import Community
from neomodel import DoesNotExist


logger = logging.getLogger(__name__)


class AgentServiceError(Exception):
    """Base exception for agent service errors."""
    pass


class AgentNotFoundError(AgentServiceError):
    """Raised when agent is not found."""
    pass


class CommunityNotFoundError(AgentServiceError):
    """Raised when community is not found."""
    pass


class UserNotFoundError(AgentServiceError):
    """Raised when user is not found."""
    pass


class CommunityAlreadyHasLeaderError(AgentServiceError):
    """Raised when trying to assign agent to community that already has a leader."""
    pass


class AgentService:
    """
    Core service for agent management operations.
    
    This service provides high-level business logic for:
    - Agent creation and lifecycle management
    - Agent-community assignment operations
    - Agent capability and permission management
    - Agent status and availability tracking
    
    The service acts as a facade over the data models and provides
    transaction management, validation, and business rule enforcement.
    """
    
    def create_agent(
        self, 
        name: str, 
        agent_type: str, 
        capabilities: List[str],
        description: str = None,
        icon_id: str = None,
        created_by_uid: str = None
    ) -> Agent:
        """
        Create a new agent with specified capabilities.
        
        Args:
            name: Human-readable name for the agent
            agent_type: Type of agent (COMMUNITY_LEADER, MODERATOR, ASSISTANT)
            capabilities: List of capabilities this agent should have
            description: Optional description of the agent's purpose
            icon_id: Optional reference to agent's avatar/icon
            created_by_uid: UID of user creating the agent
            
        Returns:
            Agent: The newly created agent instance
            
        Raises:
            AgentServiceError: If agent creation fails
            UserNotFoundError: If created_by_uid is invalid
        """
        try:
            logger.info(f"Creating new agent: {name} ({agent_type})")
            
            # Convert enum to string if needed
            if hasattr(agent_type, 'value'):
                agent_type_str = agent_type.value
            elif hasattr(agent_type, 'name'):
                agent_type_str = agent_type.name
            else:
                agent_type_str = str(agent_type)
            
            # Validate agent type
            valid_types = ['COMMUNITY_LEADER', 'MODERATOR', 'ASSISTANT']
            if agent_type_str not in valid_types:
                raise AgentServiceError(f"Invalid agent type: {agent_type_str}. Must be one of {valid_types}")
            
            # Validate capabilities
            if not capabilities or not isinstance(capabilities, list):
                raise AgentServiceError("Agent must have at least one capability")
            
            # Create the agent
            agent = Agent(
                name=name,
                description=description or f"AI {agent_type_str.lower().replace('_', ' ')} agent",
                agent_type=agent_type_str,
                icon_id=icon_id,
                capabilities=capabilities,
                status='ACTIVE'
            )
            agent.save()
            
            # Connect to creator if provided
            if created_by_uid:
                try:
                    creator = Users.nodes.get(user_id=created_by_uid)
                    agent.created_by.connect(creator)
                    logger.info(f"Connected agent {agent.uid} to creator {created_by_uid}")
                except DoesNotExist:
                    logger.warning(f"Creator user {created_by_uid} not found, agent created without creator link")
                    # Don't fail agent creation if creator link fails
            
            # Create Matrix profile for the agent
            try:
                matrix_success = create_agent_matrix_profile(agent)
                if matrix_success:
                    logger.info(f"Successfully created Matrix profile for agent {agent.uid}")
                else:
                    logger.warning(f"Matrix profile creation failed for agent {agent.uid}, marked as pending")
            except MatrixRegistrationError as e:
                logger.error(f"Matrix registration error for agent {agent.uid}: {str(e)}")
                # Agent is already marked as pending in matrix_utils
            except MatrixLoginError as e:
                logger.error(f"Matrix login error for agent {agent.uid}: {str(e)}")
                # Agent is already marked as pending in matrix_utils
            except MatrixProfileUpdateError as e:
                logger.error(f"Matrix profile update error for agent {agent.uid}: {str(e)}")
                # Agent is already marked as pending in matrix_utils
            except Exception as e:
                logger.error(f"Unexpected error during Matrix profile creation for agent {agent.uid}: {str(e)}")
                # Don't fail agent creation if Matrix profile creation fails
            
            logger.info(f"Successfully created agent {agent.uid}: {name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {str(e)}")
            if isinstance(e, AgentServiceError):
                raise
            raise AgentServiceError(f"Failed to create agent: {str(e)}")
    
    def assign_agent_to_community(
        self, 
        agent_uid: str, 
        community_uid: str, 
        assigned_by_uid: str,
        permissions: List[str] = None,
        allow_multiple_leaders: bool = False
    ) -> AgentCommunityAssignment:
        """
        Assign an agent as leader to a community.
        
        Args:
            agent_uid: UID of the agent to assign
            community_uid: UID of the community to assign to
            assigned_by_uid: UID of user making the assignment
            permissions: Optional additional permissions for this assignment
            allow_multiple_leaders: Whether to allow multiple active leader assignments
            
        Returns:
            AgentCommunityAssignment: The created assignment
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
            CommunityNotFoundError: If community doesn't exist
            UserNotFoundError: If assigning user doesn't exist
            CommunityAlreadyHasLeaderError: If community already has a leader and allow_multiple_leaders is False
        """
        try:
            logger.info(f"Assigning agent {agent_uid} to community {community_uid}")
            
            # Validate agent exists and is active
            try:
                agent = Agent.nodes.get(uid=agent_uid)
            except DoesNotExist:
                raise AgentNotFoundError(f"Agent {agent_uid} not found")
            
            if not agent.is_active():
                raise AgentServiceError(f"Agent {agent_uid} is not active (status: {agent.status})")
            
            # Validate community exists
            try:
                community = Community.nodes.get(uid=community_uid)
            except DoesNotExist:
                raise CommunityNotFoundError(f"Community {community_uid} not found")
            
            # Validate assigning user exists
            try:
                assigned_by = Users.nodes.get(user_id=assigned_by_uid)
            except DoesNotExist:
                raise UserNotFoundError(f"User {assigned_by_uid} not found")
            
            # Check if community already has an active leader (if not allowing multiple)
            if not allow_multiple_leaders:
                existing_leader = self.get_community_leader(community_uid)
                if existing_leader:
                    raise CommunityAlreadyHasLeaderError(
                        f"Community {community_uid} already has an active leader: {existing_leader.uid}"
                    )
            
            # Create the assignment
            assignment = AgentCommunityAssignment(
                permissions=permissions or [],
                status='ACTIVE'
            )
            assignment.save()
            
            # Connect relationships
            assignment.agent.connect(agent)
            assignment.community.connect(community)
            assignment.assigned_by.connect(assigned_by)
            
            # Connect assignment to agent's assigned communities
            agent.assigned_communities.connect(assignment)
            
            # Connect assignment to community's leader_agent relationship
            community.leader_agent.connect(assignment)
            
            # Automatically join agent to Matrix room and grant admin rights (power level 100)
            try:
                if agent.matrix_user_id and community.room_id:
                    logger.info(f"Joining agent {agent_uid} to Matrix room and granting admin rights in community {community_uid}")
                    success = join_agent_to_community_matrix_room(
                        agent=agent,
                        community=community
                    )
                    if success:
                        logger.info(f"Successfully joined agent {agent_uid} to Matrix room with admin rights")
                    else:
                        logger.warning(f"Failed to join agent {agent_uid} to Matrix room or grant admin rights, but assignment was successful")
                else:
                    logger.info(f"Skipping Matrix room join - agent has no Matrix profile or community has no Matrix room")
            except Exception as matrix_error:
                # Don't fail the assignment if Matrix operations fail
                logger.warning(f"Failed to join agent to Matrix room or set power level for agent {agent_uid}: {matrix_error}")
            
            logger.info(f"Successfully assigned agent {agent_uid} to community {community_uid}")
            return assignment
            
        except (AgentNotFoundError, CommunityNotFoundError, UserNotFoundError, CommunityAlreadyHasLeaderError):
            # Re-raise specific errors
            raise
        except Exception as e:
            logger.error(f"Failed to assign agent {agent_uid} to community {community_uid}: {str(e)}")
            raise AgentServiceError(f"Failed to assign agent to community: {str(e)}")
    
    def get_community_leader(self, community_uid: str) -> Optional[Agent]:
        """
        Retrieve the current leader agent for a community.
        
        Args:
            community_uid: UID of the community to check
            
        Returns:
            Agent: The current leader agent, or None if no active leader
            
        Raises:
            CommunityNotFoundError: If community doesn't exist
        """
        try:
            logger.debug(f"Getting leader for community {community_uid}")
            
            # Validate community exists
            try:
                community = Community.nodes.get(uid=community_uid)
            except DoesNotExist:
                raise CommunityNotFoundError(f"Community {community_uid} not found")
            
            # Find active assignments for this community
            # Note: This is a simplified approach - in a real implementation,
            # you might want to add a direct relationship from Community to AgentCommunityAssignment
            all_assignments = AgentCommunityAssignment.nodes.all()
            
            for assignment in all_assignments:
                assignment_community = assignment.community.single()
                if (assignment_community and 
                    assignment_community.uid == community_uid and 
                    assignment.is_active()):
                    
                    agent = assignment.agent.single()
                    if agent and agent.is_active():
                        logger.debug(f"Found active leader {agent.uid} for community {community_uid}")
                        return agent
            
            logger.debug(f"No active leader found for community {community_uid}")
            return None
            
        except CommunityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get community leader for {community_uid}: {str(e)}")
            raise AgentServiceError(f"Failed to get community leader: {str(e)}")
    
    def update_agent_assignment(
        self, 
        assignment_uid: str, 
        status: str = None,
        permissions: List[str] = None,
        **kwargs
    ) -> AgentCommunityAssignment:
        """
        Update an existing agent-community assignment.
        
        Args:
            assignment_uid: UID of the assignment to update
            status: New status for the assignment (ACTIVE, INACTIVE, SUSPENDED)
            permissions: New permissions list for the assignment
            **kwargs: Additional fields to update
            
        Returns:
            AgentCommunityAssignment: The updated assignment
            
        Raises:
            AgentServiceError: If assignment not found or update fails
        """
        try:
            logger.info(f"Updating assignment {assignment_uid}")
            
            # Find the assignment
            try:
                assignment = AgentCommunityAssignment.nodes.get(uid=assignment_uid)
            except DoesNotExist:
                raise AgentServiceError(f"Assignment {assignment_uid} not found")
            
            # Update fields
            if status is not None:
                valid_statuses = ['ACTIVE', 'INACTIVE', 'SUSPENDED']
                if status not in valid_statuses:
                    raise AgentServiceError(f"Invalid status: {status}. Must be one of {valid_statuses}")
                assignment.status = status
            
            if permissions is not None:
                assignment.permissions = permissions
            
            # Update any additional fields
            for key, value in kwargs.items():
                if hasattr(assignment, key):
                    setattr(assignment, key, value)
            
            assignment.save()
            
            logger.info(f"Successfully updated assignment {assignment_uid}")
            return assignment
            
        except Exception as e:
            logger.error(f"Failed to update assignment {assignment_uid}: {str(e)}")
            if isinstance(e, AgentServiceError):
                raise
            raise AgentServiceError(f"Failed to update assignment: {str(e)}")
    
    def deactivate_agent_assignment(self, assignment_uid: str) -> bool:
        """
        Deactivate an agent's assignment to a community.
        
        Args:
            assignment_uid: UID of the assignment to deactivate
            
        Returns:
            bool: True if successfully deactivated
            
        Raises:
            AgentServiceError: If assignment not found or deactivation fails
        """
        try:
            logger.info(f"Deactivating assignment {assignment_uid}")
            
            assignment = self.update_agent_assignment(assignment_uid, status='INACTIVE')
            
            logger.info(f"Successfully deactivated assignment {assignment_uid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate assignment {assignment_uid}: {str(e)}")
            if isinstance(e, AgentServiceError):
                raise
            raise AgentServiceError(f"Failed to deactivate assignment: {str(e)}")
    
    def get_agent_assignments(self, agent_uid: str) -> List[AgentCommunityAssignment]:
        """
        Get all assignments for a specific agent.
        
        Args:
            agent_uid: UID of the agent
            
        Returns:
            List[AgentCommunityAssignment]: List of assignments for the agent
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        try:
            logger.debug(f"Getting assignments for agent {agent_uid}")
            
            # Validate agent exists
            try:
                agent = Agent.nodes.get(uid=agent_uid)
            except DoesNotExist:
                raise AgentNotFoundError(f"Agent {agent_uid} not found")
            
            # Get all assignments for this agent
            assignments = list(agent.assigned_communities.all())
            
            logger.debug(f"Found {len(assignments)} assignments for agent {agent_uid}")
            return assignments
            
        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get assignments for agent {agent_uid}: {str(e)}")
            raise AgentServiceError(f"Failed to get agent assignments: {str(e)}")
    
    def get_community_agents(self, community_uid: str) -> List[Agent]:
        """
        Get all agents assigned to a specific community.
        
        Args:
            community_uid: UID of the community
            
        Returns:
            List[Agent]: List of agents assigned to the community
            
        Raises:
            CommunityNotFoundError: If community doesn't exist
        """
        try:
            logger.debug(f"Getting agents for community {community_uid}")
            
            # Validate community exists
            try:
                community = Community.nodes.get(uid=community_uid)
            except DoesNotExist:
                raise CommunityNotFoundError(f"Community {community_uid} not found")
            
            # Find all active assignments for this community
            agents = []
            all_assignments = AgentCommunityAssignment.nodes.all()
            
            for assignment in all_assignments:
                assignment_community = assignment.community.single()
                if (assignment_community and 
                    assignment_community.uid == community_uid and 
                    assignment.is_active()):
                    
                    agent = assignment.agent.single()
                    if agent:
                        agents.append(agent)
            
            logger.debug(f"Found {len(agents)} agents for community {community_uid}")
            return agents
            
        except CommunityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get agents for community {community_uid}: {str(e)}")
            raise AgentServiceError(f"Failed to get community agents: {str(e)}")
    
    def get_default_community_agent(self) -> Optional[Agent]:
        """
        Get the default agent to assign to new communities.
        
        This method implements the business logic for selecting which agent
        should be automatically assigned to new communities.
        
        Returns:
            Agent: The default agent, or None if no suitable agent found
        """
        try:
            logger.debug("Getting default community agent")
            
            # Look for active community leader agents
            agents = Agent.nodes.filter(
                agent_type='COMMUNITY_LEADER',
                status='ACTIVE'
            )
            
            # For now, return the first available agent
            # In a more sophisticated implementation, this could consider:
            # - Agent workload (number of current assignments)
            # - Agent specialization or preferences
            # - Community type matching
            for agent in agents:
                if agent.has_capability('edit_community'):
                    logger.debug(f"Selected default agent: {agent.uid}")
                    return agent
            
            logger.warning("No suitable default community agent found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get default community agent: {str(e)}")
            return None
    
    def get_agent_by_uid(self, agent_uid: str) -> Agent:
        """
        Get an agent by its UID.
        
        Args:
            agent_uid: UID of the agent to retrieve
            
        Returns:
            Agent: The agent instance
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        try:
            return Agent.nodes.get(uid=agent_uid)
        except DoesNotExist:
            raise AgentNotFoundError(f"Agent {agent_uid} not found")
    
    def update_agent(
        self, 
        agent_uid: str, 
        name: str = None,
        description: str = None,
        capabilities: List[str] = None,
        status: str = None,
        **kwargs
    ) -> Agent:
        """
        Update an existing agent.
        
        Args:
            agent_uid: UID of the agent to update
            name: New name for the agent
            description: New description for the agent
            capabilities: New capabilities list
            status: New status for the agent
            **kwargs: Additional fields to update
            
        Returns:
            Agent: The updated agent
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
            AgentServiceError: If update fails
        """
        try:
            logger.info(f"Updating agent {agent_uid}")
            
            agent = self.get_agent_by_uid(agent_uid)
            
            # Update fields
            if name is not None:
                agent.name = name
            if description is not None:
                agent.description = description
            if capabilities is not None:
                agent.capabilities = capabilities
            if status is not None:
                valid_statuses = ['ACTIVE', 'INACTIVE', 'SUSPENDED']
                if status not in valid_statuses:
                    raise AgentServiceError(f"Invalid status: {status}. Must be one of {valid_statuses}")
                agent.status = status
            
            # Update any additional fields
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            
            agent.save()
            
            logger.info(f"Successfully updated agent {agent_uid}")
            return agent
            
        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent {agent_uid}: {str(e)}")
            raise AgentServiceError(f"Failed to update agent: {str(e)}")