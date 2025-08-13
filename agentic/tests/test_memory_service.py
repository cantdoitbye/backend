# Agent Memory Service Tests
# This module contains unit tests for the AgentMemoryService class.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from datetime import datetime, timedelta

from ..services.memory_service import (
    AgentMemoryService, AgentMemoryError, MemoryNotFoundError, MemoryExpiredError
)
from ..models import AgentMemory


class AgentMemoryServiceTest(TestCase):
    """Test cases for the AgentMemoryService class."""
    
    def setUp(self):
        """Set up test data."""
        self.memory_service = AgentMemoryService()
        
        # Mock objects for testing
        self.mock_memory = Mock(spec=AgentMemory)
        self.mock_memory.agent_uid = "agent_123"
        self.mock_memory.community_uid = "community_456"
        self.mock_memory.memory_type = "context"
        self.mock_memory.content = {"test_key": "test_value"}
        self.mock_memory.is_expired.return_value = False
        
        # Mock auth service
        self.mock_auth_service = Mock()
        self.mock_auth_service.authenticate_agent.return_value = True
        self.memory_service.auth_service = self.mock_auth_service
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_store_context_success(self, mock_memory_class):
        """Test successful context storage."""
        mock_memory_class.objects.update_or_create.return_value = (self.mock_memory, True)
        
        context_data = {"current_task": "test_task", "session_id": "session_123"}
        
        result = self.memory_service.store_context(
            agent_uid="agent_123",
            community_uid="community_456",
            context=context_data,
            expires_in_hours=24,
            priority=1
        )
        
        # Verify authentication was checked
        self.mock_auth_service.authenticate_agent.assert_called_once_with("agent_123", "community_456")
        
        # Verify memory was stored
        mock_memory_class.objects.update_or_create.assert_called_once()
        call_args = mock_memory_class.objects.update_or_create.call_args
        
        self.assertEqual(call_args[1]['agent_uid'], "agent_123")
        self.assertEqual(call_args[1]['community_uid'], "community_456")
        self.assertEqual(call_args[1]['memory_type'], "context")
        self.assertEqual(call_args[1]['defaults']['content'], context_data)
        self.assertEqual(call_args[1]['defaults']['priority'], 1)
        
        self.assertEqual(result, self.mock_memory)
    
    def test_store_context_unauthorized(self):
        """Test context storage when agent is not authorized."""
        self.mock_auth_service.authenticate_agent.return_value = False
        
        with self.assertRaises(AgentMemoryError) as context:
            self.memory_service.store_context(
                agent_uid="agent_123",
                community_uid="community_456",
                context={"test": "data"}
            )
        
        self.assertIn("not authorized", str(context.exception))
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_retrieve_context_success(self, mock_memory_class):
        """Test successful context retrieval."""
        mock_memory_class.objects.get.return_value = self.mock_memory
        
        result = self.memory_service.retrieve_context("agent_123", "community_456")
        
        # Verify authentication was checked
        self.mock_auth_service.authenticate_agent.assert_called_once_with("agent_123", "community_456")
        
        # Verify memory was retrieved
        mock_memory_class.objects.get.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context"
        )
        
        # Verify expiration was checked
        self.mock_memory.is_expired.assert_called_once()
        
        self.assertEqual(result, {"test_key": "test_value"})
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_retrieve_context_not_found(self, mock_memory_class):
        """Test context retrieval when no context exists."""
        mock_memory_class.objects.get.side_effect = AgentMemory.DoesNotExist()
        
        result = self.memory_service.retrieve_context("agent_123", "community_456")
        
        # Should return empty dict when no context found
        self.assertEqual(result, {})
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_retrieve_context_expired(self, mock_memory_class):
        """Test context retrieval when context has expired."""
        expired_memory = Mock(spec=AgentMemory)
        expired_memory.is_expired.return_value = True
        mock_memory_class.objects.get.return_value = expired_memory
        
        with self.assertRaises(MemoryExpiredError) as context:
            self.memory_service.retrieve_context("agent_123", "community_456")
        
        # Verify expired memory was deleted
        expired_memory.delete.assert_called_once()
        self.assertIn("expired", str(context.exception))
    
    @patch('agentic.services.memory_service.AgentMemory')
    @patch('agentic.services.memory_service.datetime')
    def test_update_conversation_history_new(self, mock_datetime, mock_memory_class):
        """Test updating conversation history when no history exists."""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # No existing memory
        mock_memory_class.objects.get.side_effect = AgentMemory.DoesNotExist()
        mock_memory_class.objects.create.return_value = self.mock_memory
        
        conversation_data = {"message": "Hello", "user": "test_user"}
        
        result = self.memory_service.update_conversation_history(
            agent_uid="agent_123",
            community_uid="community_456",
            conversation_data=conversation_data
        )
        
        # Verify new memory was created
        mock_memory_class.objects.create.assert_called_once()
        call_args = mock_memory_class.objects.create.call_args[1]
        
        self.assertEqual(call_args['agent_uid'], "agent_123")
        self.assertEqual(call_args['community_uid'], "community_456")
        self.assertEqual(call_args['memory_type'], "conversation")
        self.assertEqual(call_args['priority'], 1)
        
        # Verify conversation data was added to history
        content = call_args['content']
        self.assertEqual(len(content['history']), 1)
        self.assertEqual(content['history'][0]['data'], conversation_data)
        
        self.assertEqual(result, self.mock_memory)
    
    @patch('agentic.services.memory_service.AgentMemory')
    @patch('agentic.services.memory_service.datetime')
    def test_update_conversation_history_existing(self, mock_datetime, mock_memory_class):
        """Test updating conversation history when history already exists."""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Existing memory with history
        existing_memory = Mock(spec=AgentMemory)
        existing_memory.content = {
            'history': [
                {'timestamp': '2024-01-01T11:00:00', 'data': {'message': 'Previous message'}}
            ]
        }
        mock_memory_class.objects.get.return_value = existing_memory
        
        conversation_data = {"message": "New message", "user": "test_user"}
        
        result = self.memory_service.update_conversation_history(
            agent_uid="agent_123",
            community_uid="community_456",
            conversation_data=conversation_data
        )
        
        # Verify existing memory was updated
        existing_memory.save.assert_called_once()
        
        # Verify new conversation data was added
        updated_content = existing_memory.content
        self.assertEqual(len(updated_content['history']), 2)
        self.assertEqual(updated_content['history'][1]['data'], conversation_data)
        
        self.assertEqual(result, existing_memory)
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_get_conversation_history_success(self, mock_memory_class):
        """Test successful conversation history retrieval."""
        history_data = [
            {'timestamp': '2024-01-01T12:00:00', 'data': {'message': 'Message 1'}},
            {'timestamp': '2024-01-01T11:00:00', 'data': {'message': 'Message 2'}}
        ]
        
        memory_with_history = Mock(spec=AgentMemory)
        memory_with_history.content = {'history': history_data}
        mock_memory_class.objects.get.return_value = memory_with_history
        
        result = self.memory_service.get_conversation_history("agent_123", "community_456", limit=5)
        
        # Verify history was returned in reverse order (most recent first)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['data']['message'], 'Message 1')  # Most recent first
        self.assertEqual(result[1]['data']['message'], 'Message 2')
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_get_conversation_history_not_found(self, mock_memory_class):
        """Test conversation history retrieval when no history exists."""
        mock_memory_class.objects.get.side_effect = AgentMemory.DoesNotExist()
        
        result = self.memory_service.get_conversation_history("agent_123", "community_456")
        
        # Should return empty list when no history found
        self.assertEqual(result, [])
    
    @patch('agentic.services.memory_service.AgentMemory')
    @patch('agentic.services.memory_service.datetime')
    def test_store_knowledge_new(self, mock_datetime, mock_memory_class):
        """Test storing knowledge when no knowledge exists."""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # No existing memory
        mock_memory_class.objects.get.side_effect = AgentMemory.DoesNotExist()
        mock_memory_class.objects.create.return_value = self.mock_memory
        
        knowledge_data = {"community_rules": ["Rule 1", "Rule 2"], "member_count": 150}
        
        result = self.memory_service.store_knowledge(
            agent_uid="agent_123",
            community_uid="community_456",
            knowledge_data=knowledge_data,
            knowledge_key="community_info"
        )
        
        # Verify new memory was created
        mock_memory_class.objects.create.assert_called_once()
        call_args = mock_memory_class.objects.create.call_args[1]
        
        self.assertEqual(call_args['memory_type'], "knowledge")
        self.assertEqual(call_args['priority'], 2)  # Knowledge has high priority
        
        # Verify knowledge was stored under the specified key
        content = call_args['content']
        self.assertIn('community_info', content['knowledge'])
        self.assertEqual(content['knowledge']['community_info']['data'], knowledge_data)
        
        self.assertEqual(result, self.mock_memory)
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_get_community_knowledge_success(self, mock_memory_class):
        """Test successful knowledge retrieval."""
        knowledge_data = {
            'community_info': {
                'data': {'rules': ['Rule 1', 'Rule 2']},
                'stored_at': '2024-01-01T12:00:00'
            },
            'member_insights': {
                'data': {'active_members': 50},
                'stored_at': '2024-01-01T11:00:00'
            }
        }
        
        memory_with_knowledge = Mock(spec=AgentMemory)
        memory_with_knowledge.content = {'knowledge': knowledge_data}
        mock_memory_class.objects.get.return_value = memory_with_knowledge
        
        # Test retrieving specific knowledge key
        result = self.memory_service.get_community_knowledge(
            "agent_123", "community_456", knowledge_key="community_info"
        )
        
        self.assertEqual(result, {'rules': ['Rule 1', 'Rule 2']})
        
        # Test retrieving all knowledge
        result_all = self.memory_service.get_community_knowledge("agent_123", "community_456")
        
        self.assertEqual(result_all, knowledge_data)
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_store_preferences_success(self, mock_memory_class):
        """Test successful preferences storage."""
        mock_memory_class.objects.update_or_create.return_value = (self.mock_memory, True)
        
        preferences_data = {
            "notification_frequency": "daily",
            "response_style": "formal",
            "auto_moderate": True
        }
        
        result = self.memory_service.store_preferences(
            agent_uid="agent_123",
            community_uid="community_456",
            preferences=preferences_data
        )
        
        # Verify preferences were stored
        mock_memory_class.objects.update_or_create.assert_called_once()
        call_args = mock_memory_class.objects.update_or_create.call_args
        
        self.assertEqual(call_args[1]['memory_type'], "preferences")
        self.assertEqual(call_args[1]['defaults']['priority'], 1)
        
        # Verify preferences content
        content = call_args[1]['defaults']['content']
        self.assertEqual(content['preferences'], preferences_data)
        
        self.assertEqual(result, self.mock_memory)
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_get_preferences_success(self, mock_memory_class):
        """Test successful preferences retrieval."""
        preferences_data = {
            "notification_frequency": "daily",
            "response_style": "formal"
        }
        
        memory_with_preferences = Mock(spec=AgentMemory)
        memory_with_preferences.content = {'preferences': preferences_data}
        mock_memory_class.objects.get.return_value = memory_with_preferences
        
        result = self.memory_service.get_preferences("agent_123", "community_456")
        
        self.assertEqual(result, preferences_data)
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_clear_memory_specific_type(self, mock_memory_class):
        """Test clearing specific memory type."""
        mock_memory_class.objects.filter.return_value.delete.return_value = (3, {})
        
        result = self.memory_service.clear_memory(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context"
        )
        
        # Verify correct filter was applied
        mock_memory_class.objects.filter.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context"
        )
        
        self.assertEqual(result, 3)
    
    @patch('agentic.services.memory_service.AgentMemory')
    def test_clear_memory_all_types(self, mock_memory_class):
        """Test clearing all memory types."""
        mock_memory_class.objects.filter.return_value.delete.return_value = (5, {})
        
        result = self.memory_service.clear_memory(
            agent_uid="agent_123",
            community_uid="community_456"
        )
        
        # Verify filter without memory_type was applied
        mock_memory_class.objects.filter.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456"
        )
        
        self.assertEqual(result, 5)
    
    def test_clear_memory_invalid_type(self):
        """Test clearing memory with invalid type."""
        with self.assertRaises(AgentMemoryError) as context:
            self.memory_service.clear_memory(
                agent_uid="agent_123",
                community_uid="community_456",
                memory_type="invalid_type"
            )
        
        self.assertIn("Invalid memory type", str(context.exception))
    
    @patch('agentic.services.memory_service.AgentMemory')
    @patch('agentic.services.memory_service.datetime')
    def test_cleanup_expired_memory(self, mock_datetime, mock_memory_class):
        """Test cleanup of expired memory records."""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Mock expired memories
        mock_expired_queryset = Mock()
        mock_expired_queryset.count.return_value = 3
        mock_expired_queryset.delete.return_value = (3, {})
        mock_memory_class.objects.filter.return_value = mock_expired_queryset
        
        result = self.memory_service.cleanup_expired_memory()
        
        # Verify expired memories were filtered and deleted
        mock_memory_class.objects.filter.assert_called_once_with(expires_at__lt=mock_now)
        mock_expired_queryset.delete.assert_called_once()
        
        self.assertEqual(result, 3)
    
    @patch('agentic.services.memory_service.AgentMemory')
    @patch('agentic.services.memory_service.json')
    def test_get_memory_stats(self, mock_json, mock_memory_class):
        """Test memory statistics generation."""
        # Mock memory records
        mock_memories = [
            Mock(memory_type='context', community_uid='comm1', content={'data': 'test1'}, is_expired=Mock(return_value=False)),
            Mock(memory_type='conversation', community_uid='comm1', content={'data': 'test2'}, is_expired=Mock(return_value=True)),
            Mock(memory_type='context', community_uid='comm2', content={'data': 'test3'}, is_expired=Mock(return_value=False))
        ]
        
        mock_memory_class.objects.filter.return_value = mock_memories
        mock_json.dumps.return_value = '{"data": "test"}'  # Mock JSON serialization
        
        result = self.memory_service.get_memory_stats("agent_123")
        
        # Verify statistics
        self.assertEqual(result['total_records'], 3)
        self.assertEqual(result['by_type']['context'], 2)
        self.assertEqual(result['by_type']['conversation'], 1)
        self.assertEqual(result['by_community']['comm1'], 2)
        self.assertEqual(result['by_community']['comm2'], 1)
        self.assertEqual(result['expired_count'], 1)
        self.assertEqual(result['total_size_estimate'], 3 * len('{"data": "test"}'))  # 3 records * JSON length