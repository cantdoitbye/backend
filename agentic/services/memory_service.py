# Agent Memory Service
# This module provides persistent memory and context management for AI agents.
# It handles agent context storage, conversation history, and knowledge persistence.

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json

from ..models import AgentMemory
from .auth_service import AgentAuthService


logger = logging.getLogger(__name__)


class AgentMemoryError(Exception):
    """Base exception for agent memory errors."""
    pass


class MemoryNotFoundError(AgentMemoryError):
    """Raised when requested memory is not found."""
    pass


class MemoryExpiredError(AgentMemoryError):
    """Raised when requested memory has expired."""
    pass


class AgentMemoryService:
    """
    Manages persistent memory and context for agents.
    
    This service provides comprehensive memory management for AI agents, including:
    - Context storage and retrieval across sessions
    - Conversation history and continuity
    - Community-specific knowledge and insights
    - Learning and adaptation capabilities
    - Memory expiration and cleanup
    
    The service ensures that agents can maintain state and context across
    interactions while providing proper isolation between communities.
    """
    
    def __init__(self):
        """Initialize the memory service with auth service dependency."""
        self.auth_service = AgentAuthService()
    
    def store_context(
        self, 
        agent_uid: str, 
        community_uid: str, 
        context: Dict[str, Any],
        expires_in_hours: Optional[int] = None,
        priority: int = 0
    ) -> AgentMemory:
        """
        Store agent context for a community.
        
        Context typically includes current session state, active tasks,
        and temporary information that should persist across interactions.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            context: Context data to store
            expires_in_hours: Optional expiration time in hours
            priority: Priority for memory cleanup (higher = more important)
            
        Returns:
            AgentMemory: The stored memory record
            
        Raises:
            AgentMemoryError: If context storage fails
        """
        try:
            logger.debug(f"Storing context for agent {agent_uid} in community {community_uid}")
            
            # Validate that agent has access to community
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentMemoryError(f"Agent {agent_uid} not authorized for community {community_uid}")
            
            # Calculate expiration time if specified
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            # Store or update context memory
            memory, created = AgentMemory.objects.update_or_create(
                agent_uid=agent_uid,
                community_uid=community_uid,
                memory_type='context',
                defaults={
                    'content': context,
                    'expires_at': expires_at,
                    'priority': priority
                }
            )
            
            action = "created" if created else "updated"
            logger.info(f"Context memory {action} for agent {agent_uid} in community {community_uid}")
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to store context for agent {agent_uid} in community {community_uid}: {str(e)}")
            if isinstance(e, AgentMemoryError):
                raise
            raise AgentMemoryError(f"Failed to store context: {str(e)}")
    
    def retrieve_context(self, agent_uid: str, community_uid: str) -> Dict[str, Any]:
        """
        Retrieve stored context for agent-community pair.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            
        Returns:
            Dict[str, Any]: The stored context data, or empty dict if not found
            
        Raises:
            AgentMemoryError: If context retrieval fails
            MemoryExpiredError: If context has expired
        """
        try:
            logger.debug(f"Retrieving context for agent {agent_uid} in community {community_uid}")
            
            # Validate that agent has access to community
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentMemoryError(f"Agent {agent_uid} not authorized for community {community_uid}")
            
            try:
                memory = AgentMemory.objects.get(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    memory_type='context'
                )
                
                # Check if memory has expired
                if memory.is_expired():
                    logger.warning(f"Context memory expired for agent {agent_uid} in community {community_uid}")
                    # Clean up expired memory
                    memory.delete()
                    raise MemoryExpiredError(f"Context memory has expired")
                
                logger.debug(f"Retrieved context for agent {agent_uid} in community {community_uid}")
                return memory.content or {}
                
            except AgentMemory.DoesNotExist:
                logger.debug(f"No context found for agent {agent_uid} in community {community_uid}")
                return {}
                
        except (AgentMemoryError, MemoryExpiredError):
            # Re-raise specific errors
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve context for agent {agent_uid} in community {community_uid}: {str(e)}")
            raise AgentMemoryError(f"Failed to retrieve context: {str(e)}")
    
    def update_conversation_history(
        self, 
        agent_uid: str, 
        community_uid: str, 
        conversation_data: Dict[str, Any],
        max_history_items: int = 100
    ) -> AgentMemory:
        """
        Update conversation history for agent.
        
        This method maintains a rolling history of conversations and interactions
        to provide context continuity across sessions.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            conversation_data: New conversation data to add
            max_history_items: Maximum number of history items to keep
            
        Returns:
            AgentMemory: The updated memory record
            
        Raises:
            AgentMemoryError: If conversation update fails
        """
        try:
            logger.debug(f"Updating conversation history for agent {agent_uid} in community {community_uid}")
            
            # Validate that agent has access to community
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentMemoryError(f"Agent {agent_uid} not authorized for community {community_uid}")
            
            # Get existing conversation history or create new
            try:
                memory = AgentMemory.objects.get(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    memory_type='conversation'
                )
                history = memory.content.get('history', [])
            except AgentMemory.DoesNotExist:
                memory = None
                history = []
            
            # Add new conversation data with timestamp
            new_entry = {
                'timestamp': datetime.now().isoformat(),
                'data': conversation_data
            }
            history.append(new_entry)
            
            # Trim history to max items (keep most recent)
            if len(history) > max_history_items:
                history = history[-max_history_items:]
            
            # Store updated history
            updated_content = {
                'history': history,
                'last_updated': datetime.now().isoformat(),
                'total_entries': len(history)
            }
            
            if memory:
                memory.content = updated_content
                memory.save()
            else:
                memory = AgentMemory.objects.create(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    memory_type='conversation',
                    content=updated_content,
                    priority=1  # Conversation history has medium priority
                )
            
            logger.info(f"Updated conversation history for agent {agent_uid} in community {community_uid} ({len(history)} entries)")
            return memory
            
        except Exception as e:
            logger.error(f"Failed to update conversation history for agent {agent_uid} in community {community_uid}: {str(e)}")
            if isinstance(e, AgentMemoryError):
                raise
            raise AgentMemoryError(f"Failed to update conversation history: {str(e)}")
    
    def get_conversation_history(
        self, 
        agent_uid: str, 
        community_uid: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for agent in community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            limit: Optional limit on number of entries to return (most recent first)
            
        Returns:
            List[Dict[str, Any]]: List of conversation history entries
            
        Raises:
            AgentMemoryError: If history retrieval fails
        """
        try:
            logger.debug(f"Getting conversation history for agent {agent_uid} in community {community_uid}")
            
            # Validate that agent has access to community
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentMemoryError(f"Agent {agent_uid} not authorized for community {community_uid}")
            
            try:
                memory = AgentMemory.objects.get(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    memory_type='conversation'
                )
                
                history = memory.content.get('history', [])
                
                # Return most recent entries first
                history = list(reversed(history))
                
                if limit:
                    history = history[:limit]
                
                logger.debug(f"Retrieved {len(history)} conversation history entries for agent {agent_uid}")
                return history
                
            except AgentMemory.DoesNotExist:
                logger.debug(f"No conversation history found for agent {agent_uid} in community {community_uid}")
                return []
                
        except AgentMemoryError:
            raise
        except Exception as e:
            logger.error(f"Failed to get conversation history for agent {agent_uid} in community {community_uid}: {str(e)}")
            raise AgentMemoryError(f"Failed to get conversation history: {str(e)}")
    
    def store_knowledge(
        self, 
        agent_uid: str, 
        community_uid: str, 
        knowledge_data: Dict[str, Any],
        knowledge_key: str = None
    ) -> AgentMemory:
        """
        Store community-specific knowledge for agent.
        
        Knowledge includes learned information, community insights, patterns,
        and other persistent information that should be retained long-term.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            knowledge_data: Knowledge data to store
            knowledge_key: Optional key to organize knowledge by topic
            
        Returns:
            AgentMemory: The stored memory record
            
        Raises:
            AgentMemoryError: If knowledge storage fails
        """
        try:
            logger.debug(f"Storing knowledge for agent {agent_uid} in community {community_uid}")
            
            # Validate that agent has access to community
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentMemoryError(f"Agent {agent_uid} not authorized for community {community_uid}")
            
            # Get existing knowledge or create new
            try:
                memory = AgentMemory.objects.get(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    memory_type='knowledge'
                )
                knowledge = memory.content.get('knowledge', {})
            except AgentMemory.DoesNotExist:
                memory = None
                knowledge = {}
            
            # Store knowledge data
            if knowledge_key:
                # Store under specific key
                knowledge[knowledge_key] = {
                    'data': knowledge_data,
                    'stored_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            else:
                # Merge with existing knowledge
                knowledge.update(knowledge_data)
                knowledge['last_updated'] = datetime.now().isoformat()
            
            updated_content = {
                'knowledge': knowledge,
                'last_updated': datetime.now().isoformat(),
                'total_keys': len(knowledge)
            }
            
            if memory:
                memory.content = updated_content
                memory.save()
            else:
                memory = AgentMemory.objects.create(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    memory_type='knowledge',
                    content=updated_content,
                    priority=2  # Knowledge has high priority
                )
            
            logger.info(f"Stored knowledge for agent {agent_uid} in community {community_uid}")
            return memory
            
        except Exception as e:
            logger.error(f"Failed to store knowledge for agent {agent_uid} in community {community_uid}: {str(e)}")
            if isinstance(e, AgentMemoryError):
                raise
            raise AgentMemoryError(f"Failed to store knowledge: {str(e)}")
    
    def get_community_knowledge(
        self, 
        agent_uid: str, 
        community_uid: str,
        knowledge_key: str = None
    ) -> Dict[str, Any]:
        """
        Retrieve community-specific knowledge for agent.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            knowledge_key: Optional specific key to retrieve
            
        Returns:
            Dict[str, Any]: The stored knowledge data
            
        Raises:
            AgentMemoryError: If knowledge retrieval fails
        """
        try:
            logger.debug(f"Retrieving knowledge for agent {agent_uid} in community {community_uid}")
            
            # Validate that agent has access to community
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentMemoryError(f"Agent {agent_uid} not authorized for community {community_uid}")
            
            try:
                memory = AgentMemory.objects.get(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    memory_type='knowledge'
                )
                
                knowledge = memory.content.get('knowledge', {})
                
                if knowledge_key:
                    # Return specific knowledge key
                    key_data = knowledge.get(knowledge_key, {})
                    logger.debug(f"Retrieved knowledge key '{knowledge_key}' for agent {agent_uid}")
                    return key_data.get('data', {}) if isinstance(key_data, dict) else key_data
                else:
                    # Return all knowledge
                    logger.debug(f"Retrieved all knowledge for agent {agent_uid} in community {community_uid}")
                    return knowledge
                    
            except AgentMemory.DoesNotExist:
                logger.debug(f"No knowledge found for agent {agent_uid} in community {community_uid}")
                return {}
                
        except AgentMemoryError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge for agent {agent_uid} in community {community_uid}: {str(e)}")
            raise AgentMemoryError(f"Failed to retrieve knowledge: {str(e)}")
    
    def store_preferences(
        self, 
        agent_uid: str, 
        community_uid: str, 
        preferences: Dict[str, Any]
    ) -> AgentMemory:
        """
        Store agent preferences for a community.
        
        Preferences include agent configuration, behavior settings,
        and customization options specific to the community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            preferences: Preferences data to store
            
        Returns:
            AgentMemory: The stored memory record
            
        Raises:
            AgentMemoryError: If preferences storage fails
        """
        try:
            logger.debug(f"Storing preferences for agent {agent_uid} in community {community_uid}")
            
            # Validate that agent has access to community
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentMemoryError(f"Agent {agent_uid} not authorized for community {community_uid}")
            
            # Store or update preferences
            memory, created = AgentMemory.objects.update_or_create(
                agent_uid=agent_uid,
                community_uid=community_uid,
                memory_type='preferences',
                defaults={
                    'content': {
                        'preferences': preferences,
                        'last_updated': datetime.now().isoformat()
                    },
                    'priority': 1  # Preferences have medium priority
                }
            )
            
            action = "created" if created else "updated"
            logger.info(f"Preferences {action} for agent {agent_uid} in community {community_uid}")
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to store preferences for agent {agent_uid} in community {community_uid}: {str(e)}")
            if isinstance(e, AgentMemoryError):
                raise
            raise AgentMemoryError(f"Failed to store preferences: {str(e)}")
    
    def get_preferences(self, agent_uid: str, community_uid: str) -> Dict[str, Any]:
        """
        Retrieve agent preferences for a community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            
        Returns:
            Dict[str, Any]: The stored preferences data
            
        Raises:
            AgentMemoryError: If preferences retrieval fails
        """
        try:
            logger.debug(f"Retrieving preferences for agent {agent_uid} in community {community_uid}")
            
            # Validate that agent has access to community
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentMemoryError(f"Agent {agent_uid} not authorized for community {community_uid}")
            
            try:
                memory = AgentMemory.objects.get(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    memory_type='preferences'
                )
                
                preferences = memory.content.get('preferences', {})
                logger.debug(f"Retrieved preferences for agent {agent_uid} in community {community_uid}")
                return preferences
                
            except AgentMemory.DoesNotExist:
                logger.debug(f"No preferences found for agent {agent_uid} in community {community_uid}")
                return {}
                
        except AgentMemoryError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve preferences for agent {agent_uid} in community {community_uid}: {str(e)}")
            raise AgentMemoryError(f"Failed to retrieve preferences: {str(e)}")
    
    def clear_memory(
        self, 
        agent_uid: str, 
        community_uid: str, 
        memory_type: str = None
    ) -> int:
        """
        Clear memory for agent in community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            memory_type: Optional specific memory type to clear (context, conversation, knowledge, preferences)
            
        Returns:
            int: Number of memory records deleted
            
        Raises:
            AgentMemoryError: If memory clearing fails
        """
        try:
            logger.debug(f"Clearing memory for agent {agent_uid} in community {community_uid} (type: {memory_type or 'all'})")
            
            # Build query filters
            filters = {
                'agent_uid': agent_uid,
                'community_uid': community_uid
            }
            
            if memory_type:
                valid_types = ['context', 'conversation', 'knowledge', 'preferences']
                if memory_type not in valid_types:
                    raise AgentMemoryError(f"Invalid memory type: {memory_type}. Must be one of {valid_types}")
                filters['memory_type'] = memory_type
            
            # Delete matching memory records
            deleted_count, _ = AgentMemory.objects.filter(**filters).delete()
            
            logger.info(f"Cleared {deleted_count} memory records for agent {agent_uid} in community {community_uid}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clear memory for agent {agent_uid} in community {community_uid}: {str(e)}")
            if isinstance(e, AgentMemoryError):
                raise
            raise AgentMemoryError(f"Failed to clear memory: {str(e)}")
    
    def cleanup_expired_memory(self) -> int:
        """
        Clean up expired memory records across all agents.
        
        This method should be called periodically to remove expired memory
        and free up storage space.
        
        Returns:
            int: Number of expired memory records deleted
        """
        try:
            logger.debug("Starting expired memory cleanup")
            
            # Find expired memory records
            now = datetime.now()
            expired_memories = AgentMemory.objects.filter(
                expires_at__lt=now
            )
            
            count = expired_memories.count()
            if count > 0:
                expired_memories.delete()
                logger.info(f"Cleaned up {count} expired memory records")
            else:
                logger.debug("No expired memory records found")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired memory: {str(e)}")
            return 0
    
    def get_memory_stats(self, agent_uid: str, community_uid: str = None) -> Dict[str, Any]:
        """
        Get memory usage statistics for an agent.
        
        Args:
            agent_uid: UID of the agent
            community_uid: Optional community UID to filter by
            
        Returns:
            Dict[str, Any]: Memory usage statistics
        """
        try:
            logger.debug(f"Getting memory stats for agent {agent_uid}")
            
            # Build query filters
            filters = {'agent_uid': agent_uid}
            if community_uid:
                filters['community_uid'] = community_uid
            
            # Get memory records
            memories = AgentMemory.objects.filter(**filters)
            
            # Calculate statistics
            stats = {
                'total_records': memories.count(),
                'by_type': {},
                'by_community': {},
                'expired_count': 0,
                'total_size_estimate': 0
            }
            
            for memory in memories:
                # Count by type
                memory_type = memory.memory_type
                stats['by_type'][memory_type] = stats['by_type'].get(memory_type, 0) + 1
                
                # Count by community
                community = memory.community_uid
                stats['by_community'][community] = stats['by_community'].get(community, 0) + 1
                
                # Count expired
                if memory.is_expired():
                    stats['expired_count'] += 1
                
                # Estimate size (rough approximation)
                content_size = len(json.dumps(memory.content)) if memory.content else 0
                stats['total_size_estimate'] += content_size
            
            logger.debug(f"Generated memory stats for agent {agent_uid}: {stats['total_records']} records")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats for agent {agent_uid}: {str(e)}")
            return {
                'error': str(e),
                'total_records': 0,
                'by_type': {},
                'by_community': {},
                'expired_count': 0,
                'total_size_estimate': 0
            }