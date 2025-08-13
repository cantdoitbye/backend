# Agentic Models Module
# This module defines all the data models for the agentic community management system.
# It handles AI agents, agent-community assignments, and related functionality.
# The system uses both Neo4j graph database through neomodel for complex relationship management
# and traditional Django models for audit logging and memory storage.

from neomodel import (
    StructuredNode, StringProperty, ArrayProperty, DateTimeProperty, 
    BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom
)
from django_neomodel import DjangoNode
from django.db import models
from datetime import datetime
from auth_manager.models import Users
from community.models import Community


class Agent(DjangoNode, StructuredNode):
    """
    Agent Model - Represents an AI agent that can be assigned as a community leader.
    
    This model manages AI agents within the platform, supporting:
    - Agent identification and metadata
    - Agent capabilities and permissions
    - Agent status and lifecycle management
    - Version tracking for agent schema evolution
    - Integration with community assignment system
    
    Business Logic:
    - Agents can be assigned to multiple communities
    - Each agent has specific capabilities that determine what actions they can perform
    - Agent status controls whether they can be assigned to new communities
    - Version tracking enables schema evolution and compatibility management
    
    Agent Types:
    - COMMUNITY_LEADER: Full community management capabilities
    - MODERATOR: Content moderation and user management
    - ASSISTANT: Limited helper functions and information provision
    
    Use Cases:
    - Autonomous community management
    - Content moderation and user engagement
    - Community analytics and reporting
    - Automated community assistance and support
    """
    
    # Agent type choices for different roles and capabilities
    AGENT_TYPE_CHOICES = {
        'COMMUNITY_LEADER': 'community_leader',    # Full community management
        'MODERATOR': 'moderator',                  # Content and user moderation
        'ASSISTANT': 'assistant'                   # Helper and information functions
    }
    
    # Agent status choices for lifecycle management
    STATUS_CHOICES = {
        'ACTIVE': 'active',        # Agent is active and can be assigned
        'INACTIVE': 'inactive',    # Agent is inactive but can be reactivated
        'SUSPENDED': 'suspended'   # Agent is suspended and cannot be used
    }
    
    # Core identification and metadata fields
    uid = UniqueIdProperty()                                    # Unique identifier for the agent
    name = StringProperty(required=True)                        # Human-readable agent name
    description = StringProperty()                              # Detailed description of agent purpose and capabilities
    agent_type = StringProperty(choices=AGENT_TYPE_CHOICES.items(), required=True)  # Type of agent and its role
    
    # Visual and branding elements
    icon_id = StringProperty()                                  # Reference to agent avatar/icon image
    
    # Agent state and lifecycle management
    status = StringProperty(choices=STATUS_CHOICES.items(), default='ACTIVE')  # Current agent status
    capabilities = ArrayProperty(StringProperty())              # List of specific capabilities this agent has
    
    # Timestamp tracking for audit and lifecycle management
    created_date = DateTimeProperty(default_now=True)          # When the agent was created
    updated_date = DateTimeProperty(default_now=True)          # Last modification timestamp
    
    # Version tracking for schema evolution and compatibility
    version = StringProperty(default='1.0')                    # Agent schema version for compatibility
    
    # Core relationships - define how agents connect to other entities
    assigned_communities = RelationshipTo('AgentCommunityAssignment', 'ASSIGNED_TO')  # Communities this agent is assigned to
    created_by = RelationshipTo('Users', 'CREATED_BY')         # User who created this agent (typically admin)
    
    def save(self, *args, **kwargs):
        """
        Override the default save method to automatically update the modification timestamp.
        
        This ensures that every time an agent is modified, we track when the change occurred.
        This is crucial for:
        - Audit trails and change tracking
        - Version management and compatibility
        - Agent lifecycle monitoring
        - Performance optimization
        """
        self.updated_date = datetime.now()
        super().save(*args, **kwargs)
    
    def is_active(self):
        """
        Check if the agent is currently active and available for assignment.
        
        Returns:
            bool: True if agent is active, False otherwise
        """
        return self.status == 'ACTIVE'
    
    def has_capability(self, capability):
        """
        Check if the agent has a specific capability.
        
        Args:
            capability (str): The capability to check for
            
        Returns:
            bool: True if agent has the capability, False otherwise
        """
        return capability in (self.capabilities or [])
    
    class Meta:
        app_label = 'agentic'  # Django app label for proper model registration

    def __str__(self):
        """
        String representation of the agent for admin interfaces and debugging.
        Returns the agent name and type as it's the most user-friendly identifier.
        """
        return f"{self.name} ({self.agent_type})"


class AgentCommunityAssignment(DjangoNode, StructuredNode):
    """
    AgentCommunityAssignment Model - Junction model linking agents to communities.
    
    This model manages the relationship between agents and communities, supporting:
    - Agent assignment to specific communities
    - Assignment status and lifecycle management
    - Permission overrides for specific assignments
    - Assignment metadata and audit trail
    - Flexible assignment management
    
    Business Logic:
    - Each assignment represents one agent's role in one community
    - Assignments can be active, inactive, or suspended independently of agent status
    - Permissions can be customized per assignment beyond agent's base capabilities
    - Assignment history is preserved for audit and analytics
    - Only one active leader assignment per community is allowed
    
    Assignment Lifecycle:
    1. Assignment created when agent is assigned to community
    2. Assignment becomes active and agent can perform actions
    3. Assignment can be suspended temporarily or deactivated permanently
    4. Assignment history is maintained for audit purposes
    
    Use Cases:
    - Community leadership assignment and management
    - Agent permission customization per community
    - Assignment audit trail and history
    - Community-specific agent configuration
    """
    
    # Assignment status choices for lifecycle management
    STATUS_CHOICES = {
        'ACTIVE': 'active',        # Assignment is active and agent can perform actions
        'INACTIVE': 'inactive',    # Assignment is inactive but can be reactivated
        'SUSPENDED': 'suspended'   # Assignment is suspended temporarily
    }
    
    # Core identification and relationships
    uid = UniqueIdProperty()                                    # Unique assignment identifier
    agent = RelationshipTo('Agent', 'AGENT')                   # The agent being assigned
    community = RelationshipTo('Community', 'COMMUNITY')       # The community being assigned to
    assigned_by = RelationshipTo('Users', 'ASSIGNED_BY')       # User who made this assignment
    
    # Assignment lifecycle and status
    assignment_date = DateTimeProperty(default_now=True)       # When the assignment was made
    status = StringProperty(choices=STATUS_CHOICES.items(), default='ACTIVE')  # Current assignment status
    
    # Permission customization for this specific assignment
    permissions = ArrayProperty(StringProperty())              # Specific permissions for this assignment (overrides/additions to agent capabilities)
    
    # Metadata and audit trail
    created_date = DateTimeProperty(default_now=True)          # When the assignment record was created
    updated_date = DateTimeProperty(default_now=True)          # Last modification timestamp
    
    def save(self, *args, **kwargs):
        """
        Override the default save method to automatically update the modification timestamp.
        
        This ensures that every time an assignment is modified, we track when the change occurred.
        This is crucial for:
        - Assignment audit trails
        - Status change tracking
        - Permission modification history
        - System monitoring and analytics
        """
        self.updated_date = datetime.now()
        super().save(*args, **kwargs)
    
    def is_active(self):
        """
        Check if the assignment is currently active.
        
        Returns:
            bool: True if assignment is active, False otherwise
        """
        return self.status == 'ACTIVE'
    
    def get_effective_permissions(self):
        """
        Get the effective permissions for this assignment.
        
        Combines agent capabilities with assignment-specific permissions.
        
        Returns:
            list: List of effective permissions for this assignment
        """
        agent_capabilities = self.agent.single().capabilities or []
        assignment_permissions = self.permissions or []
        
        # Combine and deduplicate permissions
        return list(set(agent_capabilities + assignment_permissions))
    
    def has_permission(self, permission):
        """
        Check if this assignment has a specific permission.
        
        Args:
            permission (str): The permission to check for
            
        Returns:
            bool: True if assignment has the permission, False otherwise
        """
        return permission in self.get_effective_permissions()
    
    class Meta:
        app_label = 'agentic'  # Django app registration

    def __str__(self):
        """
        String representation of the assignment for admin and debugging.
        Shows the relationship between agent and community.
        """
        agent_name = self.agent.single().name if self.agent.single() else "Unknown Agent"
        community_name = self.community.single().name if self.community.single() else "Unknown Community"
        return f"{agent_name} -> {community_name} ({self.status})"


# PostgreSQL models for audit logging and memory storage
class AgentActionLog(models.Model):
    """
    AgentActionLog Model - Logs all actions performed by agents for audit and debugging.
    
    This model provides comprehensive audit logging for agent actions, supporting:
    - Complete action history and audit trail
    - Debugging and troubleshooting capabilities
    - Performance monitoring and analytics
    - Security and compliance tracking
    - Error tracking and resolution
    
    Business Logic:
    - Every agent action is logged with full context
    - Logs include success/failure status and error details
    - Logs are immutable once created for audit integrity
    - Log retention policies can be applied for storage management
    - Logs support both automated and manual analysis
    
    Use Cases:
    - Security audit and compliance reporting
    - Debugging agent behavior and issues
    - Performance monitoring and optimization
    - User activity tracking and analytics
    - System health monitoring
    """
    
    # Core identification and context
    agent_uid = models.CharField(max_length=255, db_index=True)     # Agent that performed the action
    community_uid = models.CharField(max_length=255, db_index=True) # Community where action was performed
    
    # Action details and metadata
    action_type = models.CharField(max_length=100, db_index=True)   # Type of action performed
    action_details = models.JSONField()                             # Detailed action parameters and context
    
    # Execution results and status
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)  # When the action was performed
    success = models.BooleanField()                                 # Whether the action succeeded
    error_message = models.TextField(null=True, blank=True)        # Error details if action failed
    
    # Additional metadata
    execution_time_ms = models.IntegerField(null=True, blank=True)  # How long the action took to execute
    user_context = models.JSONField(null=True, blank=True)         # Additional user/context information
    
    class Meta:
        app_label = 'agentic'
        db_table = 'agentic_agentactionlog'
        indexes = [
            models.Index(fields=['agent_uid', 'timestamp']),
            models.Index(fields=['community_uid', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]
        ordering = ['-timestamp']  # Most recent actions first
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.action_type} by {self.agent_uid} in {self.community_uid} - {status}"


class AgentMemory(models.Model):
    """
    AgentMemory Model - Stores persistent memory and context for agents.
    
    This model provides persistent memory capabilities for agents, supporting:
    - Agent context storage across interactions
    - Conversation history and continuity
    - Community-specific knowledge and preferences
    - Learning and adaptation capabilities
    - Cross-session state persistence
    
    Business Logic:
    - Memory is scoped to agent-community pairs for isolation
    - Different memory types serve different purposes (context, conversation, knowledge)
    - Memory can be updated and evolved over time
    - Memory supports both structured and unstructured data
    - Memory access is controlled by agent authorization
    
    Memory Types:
    - context: Current session context and state
    - conversation: Chat history and conversation flow
    - knowledge: Learned information and community insights
    - preferences: Agent preferences and configuration
    
    Use Cases:
    - Maintaining conversation continuity across sessions
    - Storing community-specific knowledge and insights
    - Personalizing agent behavior per community
    - Learning from interactions and improving responses
    - Preserving agent state across system restarts
    """
    
    # Memory type choices for different kinds of stored information
    MEMORY_TYPE_CHOICES = [
        ('context', 'Context'),           # Current session context and state
        ('conversation', 'Conversation'), # Chat history and conversation flow
        ('knowledge', 'Knowledge'),       # Learned information and insights
        ('preferences', 'Preferences'),   # Agent preferences and settings
    ]
    
    # Core identification and scope
    agent_uid = models.CharField(max_length=255, db_index=True)     # Agent this memory belongs to
    community_uid = models.CharField(max_length=255, db_index=True) # Community this memory is scoped to
    memory_type = models.CharField(max_length=50, choices=MEMORY_TYPE_CHOICES, db_index=True)  # Type of memory stored
    
    # Memory content and metadata
    content = models.JSONField()                                    # The actual memory content (flexible JSON structure)
    
    # Timestamp tracking
    created_date = models.DateTimeField(auto_now_add=True)         # When the memory was first created
    updated_date = models.DateTimeField(auto_now=True)             # Last time the memory was updated
    
    # Memory management
    expires_at = models.DateTimeField(null=True, blank=True)       # Optional expiration time for temporary memory
    priority = models.IntegerField(default=0)                      # Priority for memory cleanup (higher = more important)
    
    class Meta:
        app_label = 'agentic'
        db_table = 'agentic_agentmemory'
        unique_together = ['agent_uid', 'community_uid', 'memory_type']  # One memory record per type per agent-community pair
        indexes = [
            models.Index(fields=['agent_uid', 'community_uid']),
            models.Index(fields=['memory_type', 'updated_date']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-updated_date']  # Most recently updated first
    
    def is_expired(self):
        """
        Check if this memory record has expired.
        
        Returns:
            bool: True if memory has expired, False otherwise
        """
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def __str__(self):
        return f"{self.memory_type} memory for {self.agent_uid} in {self.community_uid}"