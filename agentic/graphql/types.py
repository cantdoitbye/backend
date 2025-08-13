# Agent GraphQL Types
# This module defines GraphQL types for the agentic community management system.

import graphene
from graphene import ObjectType, String, List, Boolean, DateTime, Int, Float, Enum
from datetime import datetime
import threading

from auth_manager.Utils import generate_presigned_url
from community.graphql.types import CommunityType, UserType, FileDetailType
from ..models import Agent, AgentCommunityAssignment, AgentActionLog, AgentMemory


class AgentTypeEnum(Enum):
    """
    Enum for agent types.
    """
    COMMUNITY_LEADER = "COMMUNITY_LEADER"
    MODERATOR = "MODERATOR"
    ASSISTANT = "ASSISTANT"

# Thread-local storage to prevent infinite recursion
_local = threading.local()


class AgentType(ObjectType):
    """
    GraphQL type for Agent model.
    
    Represents an AI agent that can be assigned as a community leader.
    """
    uid = String()
    name = String()
    description = String()
    agent_type = AgentTypeEnum()
    icon_id = String()
    icon_url = graphene.Field(FileDetailType)
    status = String()
    capabilities = List(String)
    created_date = DateTime()
    updated_date = DateTime()
    version = String()
    
    # Relationships
    created_by = graphene.Field(UserType)
    assigned_communities = List(lambda: AgentAssignmentType)
    
    @classmethod
    def from_neomodel(cls, agent, include_assignments=True):
        """
        Convert neomodel Agent instance to GraphQL type.
        
        Args:
            agent: Agent neomodel instance
            include_assignments: Whether to include assignment relationships (default: True)
            
        Returns:
            AgentType: GraphQL representation of the agent
        """
        if not agent:
            return None
            
        # Prevent infinite recursion using thread-local storage
        if not hasattr(_local, 'converting_agents'):
            _local.converting_agents = set()
        
        agent_uid = getattr(agent, 'uid', None)
        if agent_uid in _local.converting_agents:
            # Return a minimal version to break recursion
            return cls(
                uid=agent_uid,
                name=getattr(agent, 'name', 'Unknown'),
                description=getattr(agent, 'description', ''),
                agent_type=getattr(agent, 'agent_type', 'UNKNOWN'),
                icon_id=getattr(agent, 'icon_id', None),
                icon_url=None,
                status=getattr(agent, 'status', 'UNKNOWN'),
                capabilities=getattr(agent, 'capabilities', []) or [],
                created_date=getattr(agent, 'created_date', None),
                updated_date=getattr(agent, 'updated_date', None),
                version=getattr(agent, 'version', '1.0'),
                created_by=None,
                assigned_communities=[]
            )
        
        _local.converting_agents.add(agent_uid)
        
        try:
            # Safely generate icon URL - handle errors gracefully
            icon_url = None
            try:
                if agent.icon_id and str(agent.icon_id).strip():
                    file_info = generate_presigned_url.generate_file_info(agent.icon_id)
                    if file_info and isinstance(file_info, dict) and file_info.get('url'):
                        icon_url = FileDetailType(**file_info)
            except Exception as e:
                print(f"Error generating agent icon URL: {e}")
                icon_url = None
            
            # Get assigned communities only if requested to avoid circular references
            assigned_communities = []
            if include_assignments:
                try:
                    assigned_communities = [
                        AgentAssignmentType.from_neomodel(assignment, include_agent=False, include_community=False) 
                        for assignment in agent.assigned_communities.all()
                    ]
                except Exception as e:
                    print(f"Error loading agent assignments: {e}")
                    assigned_communities = []
            
            result = cls(
                uid=agent.uid,
                name=agent.name,
                description=agent.description,
                agent_type=agent.agent_type,
                icon_id=agent.icon_id,
                icon_url=icon_url,
                status=agent.status,
                capabilities=agent.capabilities or [],
                created_date=agent.created_date,
                updated_date=agent.updated_date,
                version=agent.version,
                created_by=UserType.from_neomodel(agent.created_by.single()) if agent.created_by.single() else None,
                assigned_communities=assigned_communities
            )
            
            return result
            
        except Exception as e:
            print(f"Error converting Agent to GraphQL type: {e}")
            return None
        finally:
            # Clean up thread-local storage
            if agent_uid in _local.converting_agents:
                _local.converting_agents.remove(agent_uid)


class AgentAssignmentType(ObjectType):
    """
    GraphQL type for AgentCommunityAssignment model.
    
    Represents the assignment relationship between an agent and a community.
    """
    uid = String()
    agent = graphene.Field(AgentType)
    community = graphene.Field(CommunityType)
    assigned_by = graphene.Field(UserType)
    assignment_date = DateTime()
    status = String()
    permissions = List(String)
    created_date = DateTime()
    updated_date = DateTime()
    
    # Computed fields
    is_active = Boolean()
    effective_permissions = List(String)
    
    @classmethod
    def from_neomodel(cls, assignment, include_agent=True, include_community=True):
        """
        Convert neomodel AgentCommunityAssignment instance to GraphQL type.
        
        Args:
            assignment: AgentCommunityAssignment neomodel instance
            include_agent: Whether to include agent relationship (default: True)
            include_community: Whether to include community relationship (default: True)
            
        Returns:
            AgentAssignmentType: GraphQL representation of the assignment
        """
        if not assignment:
            return None
        
        # Prevent infinite recursion using thread-local storage
        if not hasattr(_local, 'converting_assignments'):
            _local.converting_assignments = set()
        
        assignment_uid = getattr(assignment, 'uid', None)
        if assignment_uid in _local.converting_assignments:
            # Return a minimal version to break recursion
            return cls(
                uid=assignment_uid,
                agent=None,
                community=None,
                assigned_by=None,
                assignment_date=getattr(assignment, 'assignment_date', None),
                status=getattr(assignment, 'status', 'UNKNOWN'),
                permissions=getattr(assignment, 'permissions', []) or [],
                created_date=getattr(assignment, 'created_date', None),
                updated_date=getattr(assignment, 'updated_date', None),
                is_active=False,
                effective_permissions=[]
            )
        
        _local.converting_assignments.add(assignment_uid)
            
        try:
            # Basic assignment data that should always be safe to access
            uid = getattr(assignment, 'uid', None)
            assignment_date = getattr(assignment, 'assignment_date', None)
            status = getattr(assignment, 'status', 'UNKNOWN')
            permissions = getattr(assignment, 'permissions', []) or []
            created_date = getattr(assignment, 'created_date', None)
            updated_date = getattr(assignment, 'updated_date', None)
            
            # Get agent only if requested to avoid circular references
            agent = None
            if include_agent:
                try:
                    agent_node = assignment.agent.single()
                    if agent_node:
                        agent = AgentType.from_neomodel(agent_node, include_assignments=False)
                except Exception as e:
                    print(f"Error loading assignment agent: {e}")
                    agent = None
            
            # Get community only if requested to avoid circular references
            community = None
            if include_community:
                try:
                    community_node = assignment.community.single()
                    if community_node:
                        # Import here to avoid circular imports
                        from community.graphql.types import CommunityType
                        community = CommunityType.from_neomodel(community_node, include_agent_assignments=False)
                except Exception as e:
                    print(f"Error loading assignment community: {e}")
                    community = None
            
            # Get assigned_by safely
            assigned_by = None
            try:
                assigned_by_node = assignment.assigned_by.single()
                if assigned_by_node:
                    assigned_by = UserType.from_neomodel(assigned_by_node)
            except Exception as e:
                print(f"Error loading assignment assigned_by: {e}")
                assigned_by = None
            
            # Get effective permissions safely
            effective_permissions = []
            try:
                if hasattr(assignment, 'get_effective_permissions'):
                    effective_permissions = assignment.get_effective_permissions()
                else:
                    effective_permissions = permissions
            except Exception as e:
                print(f"Error getting effective permissions: {e}")
                effective_permissions = permissions
            
            # Get is_active status safely
            is_active = False
            try:
                if hasattr(assignment, 'is_active'):
                    is_active = assignment.is_active()
                else:
                    is_active = status == 'ACTIVE'
            except Exception as e:
                print(f"Error getting assignment active status: {e}")
                is_active = status == 'ACTIVE'
            
            result = cls(
                uid=uid,
                agent=agent,
                community=community,
                assigned_by=assigned_by,
                assignment_date=assignment_date,
                status=status,
                permissions=permissions,
                created_date=created_date,
                updated_date=updated_date,
                is_active=is_active,
                effective_permissions=effective_permissions
            )
            
            return result
            
        except Exception as e:
            print(f"Error converting AgentCommunityAssignment to GraphQL type: {e}")
            # Return a minimal object to prevent complete failure
            result = cls(
                uid=getattr(assignment, 'uid', 'unknown'),
                agent=None,
                community=None,
                assigned_by=None,
                assignment_date=None,
                status='ERROR',
                permissions=[],
                created_date=None,
                updated_date=None,
                is_active=False,
                effective_permissions=[]
            )
            return result
        finally:
            # Clean up thread-local storage
            if assignment_uid in _local.converting_assignments:
                _local.converting_assignments.remove(assignment_uid)


class AgentActionLogType(ObjectType):
    """
    GraphQL type for AgentActionLog model.
    
    Represents a logged action performed by an agent.
    """
    id = Int()
    agent_uid = String()
    community_uid = String()
    action_type = String()
    action_details = graphene.JSONString()
    timestamp = DateTime()
    success = Boolean()
    error_message = String()
    execution_time_ms = Int()
    user_context = graphene.JSONString()
    
    @classmethod
    def from_django_model(cls, log):
        """
        Convert Django AgentActionLog instance to GraphQL type.
        
        Args:
            log: AgentActionLog Django model instance
            
        Returns:
            AgentActionLogType: GraphQL representation of the action log
        """
        return cls(
            id=log.id,
            agent_uid=log.agent_uid,
            community_uid=log.community_uid,
            action_type=log.action_type,
            action_details=log.action_details,
            timestamp=log.timestamp,
            success=log.success,
            error_message=log.error_message,
            execution_time_ms=log.execution_time_ms,
            user_context=log.user_context
        )


class AgentMemoryType(ObjectType):
    """
    GraphQL type for AgentMemory model.
    
    Represents stored memory/context for an agent.
    """
    id = Int()
    agent_uid = String()
    community_uid = String()
    memory_type = String()
    content = graphene.JSONString()
    created_date = DateTime()
    updated_date = DateTime()
    expires_at = DateTime()
    priority = Int()
    
    # Computed fields
    is_expired = Boolean()
    
    @classmethod
    def from_django_model(cls, memory):
        """
        Convert Django AgentMemory instance to GraphQL type.
        
        Args:
            memory: AgentMemory Django model instance
            
        Returns:
            AgentMemoryType: GraphQL representation of the memory
        """
        return cls(
            id=memory.id,
            agent_uid=memory.agent_uid,
            community_uid=memory.community_uid,
            memory_type=memory.memory_type,
            content=memory.content,
            created_date=memory.created_date,
            updated_date=memory.updated_date,
            expires_at=memory.expires_at,
            priority=memory.priority,
            is_expired=memory.is_expired()
        )


class AgentStatsType(ObjectType):
    """
    GraphQL type for agent statistics and metrics.
    """
    total_agents = Int()
    active_agents = Int()
    inactive_agents = Int()
    suspended_agents = Int()
    total_assignments = Int()
    active_assignments = Int()
    agents_by_type = graphene.JSONString()
    assignments_by_community = graphene.JSONString()
    
    @classmethod
    def from_stats_dict(cls, stats):
        """
        Convert statistics dictionary to GraphQL type.
        
        Args:
            stats: Dictionary containing agent statistics
            
        Returns:
            AgentStatsType: GraphQL representation of the statistics
        """
        return cls(
            total_agents=stats.get('total_agents', 0),
            active_agents=stats.get('active_agents', 0),
            inactive_agents=stats.get('inactive_agents', 0),
            suspended_agents=stats.get('suspended_agents', 0),
            total_assignments=stats.get('total_assignments', 0),
            active_assignments=stats.get('active_assignments', 0),
            agents_by_type=stats.get('agents_by_type', {}),
            assignments_by_community=stats.get('assignments_by_community', {})
        )


class AgentMemoryStatsType(ObjectType):
    """
    GraphQL type for agent memory statistics.
    """
    total_records = Int()
    by_type = graphene.JSONString()
    by_community = graphene.JSONString()
    expired_count = Int()
    total_size_estimate = Int()
    
    @classmethod
    def from_stats_dict(cls, stats):
        """
        Convert memory statistics dictionary to GraphQL type.
        
        Args:
            stats: Dictionary containing memory statistics
            
        Returns:
            AgentMemoryStatsType: GraphQL representation of the memory statistics
        """
        return cls(
            total_records=stats.get('total_records', 0),
            by_type=stats.get('by_type', {}),
            by_community=stats.get('by_community', {}),
            expired_count=stats.get('expired_count', 0),
            total_size_estimate=stats.get('total_size_estimate', 0)
        )


class AgentAuditReportType(ObjectType):
    """
    GraphQL type for agent audit reports.
    """
    agent_uid = String()
    community_uid = String()
    authenticated = Boolean()
    permissions = List(String)
    permission_descriptions = graphene.JSONString()
    available_actions = List(String)
    is_admin = Boolean()
    recent_actions = List(AgentActionLogType)
    audit_timestamp = String()
    error = String()
    
    @classmethod
    def from_audit_dict(cls, audit_data):
        """
        Convert audit dictionary to GraphQL type.
        
        Args:
            audit_data: Dictionary containing audit information
            
        Returns:
            AgentAuditReportType: GraphQL representation of the audit report
        """
        # Convert recent actions if present
        recent_actions = []
        if 'recent_actions' in audit_data:
            for action_data in audit_data['recent_actions']:
                # Create a mock object with the action data for conversion
                mock_log = type('MockLog', (), action_data)()
                recent_actions.append(AgentActionLogType.from_django_model(mock_log))
        
        return cls(
            agent_uid=audit_data.get('agent_uid'),
            community_uid=audit_data.get('community_uid'),
            authenticated=audit_data.get('authenticated', False),
            permissions=audit_data.get('permissions', []),
            permission_descriptions=audit_data.get('permission_descriptions', {}),
            available_actions=audit_data.get('available_actions', []),
            is_admin=audit_data.get('is_admin', False),
            recent_actions=recent_actions,
            audit_timestamp=audit_data.get('audit_timestamp'),
            error=audit_data.get('error')
        )


# Response types for mutations
class AgentMutationResponse(ObjectType):
    """Base response type for agent mutations."""
    success = Boolean()
    message = String()
    agent = graphene.Field(AgentType)


class AgentAssignmentMutationResponse(ObjectType):
    """Response type for agent assignment mutations."""
    success = Boolean()
    message = String()
    assignment = graphene.Field(AgentAssignmentType)


class AgentMemoryMutationResponse(ObjectType):
    """Response type for agent memory mutations."""
    success = Boolean()
    message = String()
    memory = graphene.Field(AgentMemoryType)


class AgentActionResponse(ObjectType):
    """Response type for agent actions."""
    success = Boolean()
    message = String()
    action_log = graphene.Field(AgentActionLogType)
    result_data = graphene.JSONString()


# Simplified types for lists and summaries
class AgentSummaryType(ObjectType):
    """
    Simplified agent type for lists and summaries.
    """
    uid = String()
    name = String()
    agent_type = AgentTypeEnum()
    status = String()
    capabilities_count = Int()
    assignments_count = Int()
    icon_url = graphene.Field(FileDetailType)
    
    @classmethod
    def from_neomodel(cls, agent):
        """
        Convert neomodel Agent instance to summary GraphQL type.
        
        Args:
            agent: Agent neomodel instance
            
        Returns:
            AgentSummaryType: Simplified GraphQL representation of the agent
        """
        try:
            # Safely generate icon URL
            icon_url = None
            try:
                if agent.icon_id and str(agent.icon_id).strip():
                    file_info = generate_presigned_url.generate_file_info(agent.icon_id)
                    if file_info and isinstance(file_info, dict) and file_info.get('url'):
                        icon_url = FileDetailType(**file_info)
            except Exception:
                icon_url = None
            
            return cls(
                uid=agent.uid,
                name=agent.name,
                agent_type=agent.agent_type,
                status=agent.status,
                capabilities_count=len(agent.capabilities or []),
                assignments_count=len(list(agent.assigned_communities.all())),
                icon_url=icon_url
            )
        except Exception as e:
            print(f"Error converting Agent to summary GraphQL type: {e}")
            return None


class CommunityAgentSummaryType(ObjectType):
    """
    Summary type for agents in a community context.
    """
    agent = graphene.Field(AgentSummaryType)
    assignment = graphene.Field(AgentAssignmentType)
    is_leader = Boolean()
    assignment_date = DateTime()
    
    @classmethod
    def from_assignment(cls, assignment):
        """
        Convert assignment to community agent summary.
        
        Args:
            assignment: AgentCommunityAssignment instance
            
        Returns:
            CommunityAgentSummaryType: Summary representation
        """
        try:
            agent = assignment.agent.single()
            return cls(
                agent=AgentSummaryType.from_neomodel(agent) if agent else None,
                assignment=AgentAssignmentType.from_neomodel(assignment, include_agent=False, include_community=False),
                is_leader=assignment.is_active() and agent and agent.agent_type == 'COMMUNITY_LEADER',
                assignment_date=assignment.assignment_date
            )
        except Exception as e:
            print(f"Error converting assignment to community agent summary: {e}")
            return None