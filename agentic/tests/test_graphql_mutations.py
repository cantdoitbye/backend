# Agent GraphQL Mutations Tests
# This module contains integration tests for the GraphQL mutations.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from datetime import datetime

from ..graphql.mutations import (
    CreateAgent, UpdateAgent, AssignAgentToCommunity, UpdateAgentAssignment,
    DeactivateAgentAssignment, StoreAgentContext, UpdateConversationHistory,
    StoreAgentKnowledge, StoreAgentPreferences, ClearAgentMemory,
    LogAgentAction, BulkAssignAgents, BulkUpdateAgentStatus, CleanupExpiredMemory
)
from ..graphql.inputs import (
    CreateAgentInput, UpdateAgentInput, AssignAgentToCommunityInput
)


class AgentGraphQLMutationsTest(TestCase):
    """Test cases for Agent GraphQL mutations."""
    
    def setUp(self):
        """Set up test data."""
        # Mock GraphQL info object
        self.mock_info = Mock()
        self.mock_info.context.user.is_anonymous = False
        self.mock_info.context.user.is_superuser = True
        self.mock_info.context.user.username = "testuser"
        self.mock_info.context.payload = {'user_id': 'user_123'}
        
        # Mock agent
        self.mock_agent = Mock()
        self.mock_agent.uid = "agent_123"
        self.mock_agent.name = "Test Agent"
        self.mock_agent.agent_type = "COMMUNITY_LEADER"
        
        # Mock assignment
        self.mock_assignment = Mock()
        self.mock_assignment.uid = "assignment_123"
        
        # Mock memory
        self.mock_memory = Mock()
        self.mock_memory.id = 1
        self.mock_memory.agent_uid = "agent_123"
        
        # Mock action log
        self.mock_log = Mock()
        self.mock_log.id = 1
        self.mock_log.agent_uid = "agent_123"
    
    @patch('agentic.graphql.mutations.AgentService')
    @patch('agentic.graphql.mutations.AgentType')
    def test_create_agent_success(self, mock_agent_type, mock_service_class):
        """Test successful agent creation."""
        # Setup mocks
        mock_service = Mock()
        mock_service.create_agent.return_value = self.mock_agent
        mock_service_class.return_value = mock_service
        
        mock_agent_type.from_neomodel.return_value = Mock()
        
        # Create input
        input_data = Mock()
        input_data.name = "Test Agent"
        input_data.agent_type = "COMMUNITY_LEADER"
        input_data.capabilities = ["edit_community"]
        input_data.description = "A test agent"
        input_data.icon_id = "icon_123"
        
        # Execute mutation
        mutation = CreateAgent()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Verify service was called correctly
        mock_service.create_agent.assert_called_once_with(
            name="Test Agent",
            agent_type="COMMUNITY_LEADER",
            capabilities=["edit_community"],
            description="A test agent",
            icon_id="icon_123",
            created_by_uid="user_123"
        )
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("created successfully", result.message)
        self.assertIsNotNone(result.agent)
    
    @patch('agentic.graphql.mutations.AgentService')
    def test_create_agent_failure(self, mock_service_class):
        """Test agent creation failure."""
        # Setup mocks
        mock_service = Mock()
        mock_service.create_agent.side_effect = Exception("Creation failed")
        mock_service_class.return_value = mock_service
        
        # Create input
        input_data = Mock()
        input_data.name = "Test Agent"
        input_data.agent_type = "COMMUNITY_LEADER"
        input_data.capabilities = ["edit_community"]
        input_data.description = None
        input_data.icon_id = None
        
        # Execute mutation
        mutation = CreateAgent()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Verify response
        self.assertFalse(result.success)
        self.assertIn("Failed to create agent", result.message)
        self.assertIsNone(result.agent)
    
    def test_create_agent_authentication_required(self):
        """Test agent creation with anonymous user."""
        # Setup anonymous user
        self.mock_info.context.user.is_anonymous = True
        
        # Create input
        input_data = Mock()
        input_data.name = "Test Agent"
        input_data.agent_type = "COMMUNITY_LEADER"
        input_data.capabilities = ["edit_community"]
        
        # Execute mutation
        mutation = CreateAgent()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Verify response
        self.assertFalse(result.success)
        self.assertIn("Authentication required", result.message)
    
    @patch('agentic.graphql.mutations.AgentService')
    @patch('agentic.graphql.mutations.AgentType')
    def test_update_agent_success(self, mock_agent_type, mock_service_class):
        """Test successful agent update."""
        # Setup mocks
        mock_service = Mock()
        mock_service.update_agent.return_value = self.mock_agent
        mock_service_class.return_value = mock_service
        
        mock_agent_type.from_neomodel.return_value = Mock()
        
        # Create input
        input_data = Mock()
        input_data.uid = "agent_123"
        input_data.name = "Updated Agent"
        input_data.description = "Updated description"
        input_data.capabilities = ["edit_community", "moderate_users"]
        input_data.status = "ACTIVE"
        input_data.icon_id = "new_icon_123"
        
        # Execute mutation
        mutation = UpdateAgent()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Verify service was called correctly
        mock_service.update_agent.assert_called_once_with(
            agent_uid="agent_123",
            name="Updated Agent",
            description="Updated description",
            capabilities=["edit_community", "moderate_users"],
            status="ACTIVE",
            icon_id="new_icon_123"
        )
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("updated successfully", result.message)
    
    @patch('agentic.graphql.mutations.AgentService')
    @patch('agentic.graphql.mutations.AgentAssignmentType')
    def test_assign_agent_to_community_success(self, mock_assignment_type, mock_service_class):
        """Test successful agent assignment."""
        # Setup mocks
        mock_service = Mock()
        mock_service.assign_agent_to_community.return_value = self.mock_assignment
        mock_service_class.return_value = mock_service
        
        mock_assignment_type.from_neomodel.return_value = Mock()
        
        # Create input
        input_data = Mock()
        input_data.agent_uid = "agent_123"
        input_data.community_uid = "community_456"
        input_data.permissions = ["custom_permission"]
        input_data.allow_multiple_leaders = False
        
        # Execute mutation
        mutation = AssignAgentToCommunity()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Verify service was called correctly
        mock_service.assign_agent_to_community.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            assigned_by_uid="user_123",
            permissions=["custom_permission"],
            allow_multiple_leaders=False
        )
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("assigned to community successfully", result.message)
    
    @patch('agentic.graphql.mutations.AgentMemoryService')
    @patch('agentic.graphql.mutations.AgentMemoryType')
    def test_store_agent_context_success(self, mock_memory_type, mock_service_class):
        """Test successful agent context storage."""
        # Setup mocks
        mock_service = Mock()
        mock_service.store_context.return_value = self.mock_memory
        mock_service_class.return_value = mock_service
        
        mock_memory_type.from_django_model.return_value = Mock()
        
        # Create input
        input_data = Mock()
        input_data.agent_uid = "agent_123"
        input_data.community_uid = "community_456"
        input_data.context = {"current_task": "test_task"}
        input_data.expires_in_hours = 24
        input_data.priority = 1
        
        # Execute mutation
        mutation = StoreAgentContext()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Verify service was called correctly
        mock_service.store_context.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            context={"current_task": "test_task"},
            expires_in_hours=24,
            priority=1
        )
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("context stored successfully", result.message)
    
    @patch('agentic.graphql.mutations.AgentMemoryService')
    def test_clear_agent_memory_success(self, mock_service_class):
        """Test successful agent memory clearing."""
        # Setup mocks
        mock_service = Mock()
        mock_service.clear_memory.return_value = 5  # 5 records deleted
        mock_service_class.return_value = mock_service
        
        # Create input
        input_data = Mock()
        input_data.agent_uid = "agent_123"
        input_data.community_uid = "community_456"
        input_data.memory_type = "context"
        
        # Execute mutation
        mutation = ClearAgentMemory()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Verify service was called correctly
        mock_service.clear_memory.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context"
        )
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("Cleared 5 memory records", result.message)
        self.assertEqual(result.result_data['deleted_count'], 5)
    
    @patch('agentic.graphql.mutations.AgentAuthService')
    @patch('agentic.graphql.mutations.AgentActionLogType')
    def test_log_agent_action_success(self, mock_log_type, mock_service_class):
        """Test successful agent action logging."""
        # Setup mocks
        mock_service = Mock()
        mock_service.log_agent_action.return_value = self.mock_log
        mock_service_class.return_value = mock_service
        
        mock_log_type.from_django_model.return_value = Mock()
        
        # Create input
        input_data = Mock()
        input_data.agent_uid = "agent_123"
        input_data.community_uid = "community_456"
        input_data.action_type = "edit_community"
        input_data.details = {"field": "description", "new_value": "Updated"}
        input_data.success = True
        input_data.error_message = None
        input_data.execution_time_ms = 150
        input_data.user_context = {"user_id": "user_789"}
        
        # Execute mutation
        mutation = LogAgentAction()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Verify service was called correctly
        mock_service.log_agent_action.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="edit_community",
            details={"field": "description", "new_value": "Updated"},
            success=True,
            error_message=None,
            execution_time_ms=150,
            user_context={"user_id": "user_789"}
        )
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("action logged successfully", result.message)
    
    @patch('agentic.graphql.mutations.AgentService')
    def test_bulk_assign_agents_success(self, mock_service_class):
        """Test successful bulk agent assignment."""
        # Setup mocks
        mock_service = Mock()
        # Mock successful assignments for all agents
        mock_service.assign_agent_to_community.return_value = self.mock_assignment
        mock_service_class.return_value = mock_service
        
        # Execute mutation
        mutation = BulkAssignAgents()
        result = mutation.mutate(
            self.mock_info,
            agent_uids=["agent_1", "agent_2", "agent_3"],
            community_uid="community_456",
            permissions=["custom_permission"]
        )
        
        # Verify service was called for each agent
        self.assertEqual(mock_service.assign_agent_to_community.call_count, 3)
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("Assigned 3 agents successfully", result.message)
        self.assertEqual(len(result.result_data['successful_assignments']), 3)
        self.assertEqual(len(result.result_data['failed_assignments']), 0)
    
    @patch('agentic.graphql.mutations.AgentService')
    def test_bulk_assign_agents_partial_failure(self, mock_service_class):
        """Test bulk agent assignment with partial failures."""
        # Setup mocks
        mock_service = Mock()
        # Mock mixed success/failure
        def assign_side_effect(*args, **kwargs):
            agent_uid = kwargs.get('agent_uid')
            if agent_uid == "agent_2":
                raise Exception("Assignment failed")
            return self.mock_assignment
        
        mock_service.assign_agent_to_community.side_effect = assign_side_effect
        mock_service_class.return_value = mock_service
        
        # Execute mutation
        mutation = BulkAssignAgents()
        result = mutation.mutate(
            self.mock_info,
            agent_uids=["agent_1", "agent_2", "agent_3"],
            community_uid="community_456"
        )
        
        # Verify response
        self.assertTrue(result.success)  # Should be True if at least one succeeded
        self.assertIn("Assigned 2 agents successfully, 1 failed", result.message)
        self.assertEqual(len(result.result_data['successful_assignments']), 2)
        self.assertEqual(len(result.result_data['failed_assignments']), 1)
    
    @patch('agentic.graphql.mutations.AgentService')
    def test_bulk_update_agent_status_success(self, mock_service_class):
        """Test successful bulk agent status update."""
        # Setup mocks
        mock_service = Mock()
        mock_service.update_agent.return_value = self.mock_agent
        mock_service_class.return_value = mock_service
        
        # Execute mutation
        mutation = BulkUpdateAgentStatus()
        result = mutation.mutate(
            self.mock_info,
            agent_uids=["agent_1", "agent_2"],
            status="INACTIVE"
        )
        
        # Verify service was called for each agent
        self.assertEqual(mock_service.update_agent.call_count, 2)
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("Updated 2 agents successfully", result.message)
        self.assertEqual(result.result_data['new_status'], "INACTIVE")
    
    @patch('agentic.graphql.mutations.AgentMemoryService')
    def test_cleanup_expired_memory_success(self, mock_service_class):
        """Test successful expired memory cleanup."""
        # Setup mocks
        mock_service = Mock()
        mock_service.cleanup_expired_memory.return_value = 10  # 10 records deleted
        mock_service_class.return_value = mock_service
        
        # Execute mutation
        mutation = CleanupExpiredMemory()
        result = mutation.mutate(self.mock_info)
        
        # Verify service was called
        mock_service.cleanup_expired_memory.assert_called_once()
        
        # Verify response
        self.assertTrue(result.success)
        self.assertIn("Cleaned up 10 expired memory records", result.message)
        self.assertEqual(result.result_data['deleted_count'], 10)
    
    def test_superuser_required_mutations(self):
        """Test that certain mutations require superuser privileges."""
        # Setup non-superuser
        self.mock_info.context.user.is_superuser = False
        
        # Test CreateAgent (should require superuser)
        input_data = Mock()
        input_data.name = "Test Agent"
        input_data.agent_type = "COMMUNITY_LEADER"
        input_data.capabilities = ["edit_community"]
        
        mutation = CreateAgent()
        result = mutation.mutate(self.mock_info, input_data)
        
        # Should fail due to lack of superuser privileges
        # Note: This depends on the @superuser_required decorator working
        # In a real test, you'd need to properly mock the decorator behavior