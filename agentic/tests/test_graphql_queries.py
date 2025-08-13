# Agent GraphQL Queries Tests
# This module contains integration tests for the GraphQL queries.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from datetime import datetime

from ..graphql.queries import AgentQueries
from ..models import Agent, AgentCommunityAssignment, AgentActionLog, AgentMemory


class AgentGraphQLQueriesTest(TestCase):
    """Test cases for Agent GraphQL queries."""
    
    def setUp(self):
        """Set up test data."""
        # Mock GraphQL info object
        self.mock_info = Mock()
        self.mock_info.context.user.is_anonymous = False
        self.mock_info.context.user.username = "testuser"
        
        # Mock agent
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.uid = "agent_123"
        self.mock_agent.name = "Test Agent"
        self.mock_agent.agent_type = "COMMUNITY_LEADER"
        self.mock_agent.status = "ACTIVE"
        self.mock_agent.capabilities = ["edit_community", "moderate_users"]
        self.mock_agent.created_date = datetime(2024, 1, 1, 12, 0, 0)
        self.mock_agent.has_capability.return_value = True
        
        # Mock assignment
        self.mock_assignment = Mock(spec=AgentCommunityAssignment)
        self.mock_assignment.uid = "assignment_123"
        self.mock_assignment.status = "ACTIVE"
        self.mock_assignment.is_active.return_value = True
        self.mock_assignment.assignment_date = datetime(2024, 1, 1, 12, 0, 0)
        self.mock_assignment.community.single.return_value = Mock(uid="community_456")
        
        # Mock memory
        self.mock_memory = Mock(spec=AgentMemory)
        self.mock_memory.id = 1
        self.mock_memory.agent_uid = "agent_123"
        self.mock_memory.community_uid = "community_456"
        self.mock_memory.memory_type = "context"
        
        # Mock action log
        self.mock_log = Mock(spec=AgentActionLog)
        self.mock_log.id = 1
        self.mock_log.agent_uid = "agent_123"
        self.mock_log.community_uid = "community_456"
        self.mock_log.action_type = "edit_community"
        
        # Create queries instance
        self.queries = AgentQueries()
    
    @patch('agentic.graphql.queries.AgentService')
    @patch('agentic.graphql.queries.AgentType')
    def test_resolve_get_agent_success(self, mock_agent_type, mock_service_class):
        """Test successful agent retrieval."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_agent_by_uid.return_value = self.mock_agent
        mock_service_class.return_value = mock_service
        
        mock_agent_type.from_neomodel.return_value = Mock()
        
        # Execute query
        result = self.queries.resolve_get_agent(self.mock_info, "agent_123")
        
        # Verify service was called
        mock_service.get_agent_by_uid.assert_called_once_with("agent_123")
        
        # Verify result
        self.assertIsNotNone(result)
        mock_agent_type.from_neomodel.assert_called_once_with(self.mock_agent)
    
    @patch('agentic.graphql.queries.AgentService')
    def test_resolve_get_agent_not_found(self, mock_service_class):
        """Test agent retrieval when agent doesn't exist."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_agent_by_uid.side_effect = Exception("Agent not found")
        mock_service_class.return_value = mock_service
        
        # Execute query
        result = self.queries.resolve_get_agent(self.mock_info, "nonexistent_agent")
        
        # Verify result
        self.assertIsNone(result)
    
    @patch('agentic.graphql.queries.Agent')
    @patch('agentic.graphql.queries.AgentType')
    def test_resolve_get_agents_success(self, mock_agent_type, mock_agent_class):
        """Test successful agents list retrieval."""
        # Setup mocks
        mock_agent_class.nodes.filter.return_value = [self.mock_agent]
        mock_agent_type.from_neomodel.return_value = Mock()
        
        # Create filters
        filters = Mock()
        filters.agent_type = "COMMUNITY_LEADER"
        filters.status = "ACTIVE"
        filters.has_capability = None
        filters.created_after = None
        filters.created_before = None
        
        # Execute query
        result = self.queries.resolve_get_agents(self.mock_info, filters=filters)
        
        # Verify service was called with correct filters
        mock_agent_class.nodes.filter.assert_called_once_with(
            agent_type="COMMUNITY_LEADER",
            status="ACTIVE"
        )
        
        # Verify result
        self.assertEqual(len(result), 1)
    
    @patch('agentic.graphql.queries.Agent')
    @patch('agentic.graphql.queries.AgentSummaryType')
    def test_resolve_get_agents_summary_with_pagination(self, mock_summary_type, mock_agent_class):
        """Test agents summary with pagination."""
        # Setup mocks - create multiple agents
        agents = [Mock(spec=Agent) for _ in range(25)]  # 25 agents
        mock_agent_class.nodes.filter.return_value = agents
        mock_summary_type.from_neomodel.return_value = Mock()
        
        # Create pagination
        pagination = Mock()
        pagination.page = 2
        pagination.page_size = 10
        
        # Execute query
        result = self.queries.resolve_get_agents_summary(self.mock_info, pagination=pagination)
        
        # Verify pagination was applied (page 2, size 10 = items 10-19)
        self.assertEqual(len(result), 10)
    
    @patch('agentic.graphql.queries.Agent')
    @patch('agentic.graphql.queries.AgentType')
    def test_resolve_search_agents_with_query(self, mock_agent_type, mock_agent_class):
        """Test agent search with text query."""
        # Setup mocks
        agent1 = Mock(spec=Agent)
        agent1.name = "Community Leader Agent"
        agent1.description = "Manages community activities"
        agent1.capabilities = ["edit_community"]
        
        agent2 = Mock(spec=Agent)
        agent2.name = "Moderator Agent"
        agent2.description = "Handles user moderation"
        agent2.capabilities = ["moderate_users"]
        
        mock_agent_class.nodes.all.return_value = [agent1, agent2]
        mock_agent_type.from_neomodel.return_value = Mock()
        
        # Create search input
        search_input = Mock()
        search_input.query = "community"
        search_input.search_fields = ["name", "description"]
        search_input.filters = None
        search_input.pagination = None
        
        # Execute query
        result = self.queries.resolve_search_agents(self.mock_info, search_input)
        
        # Verify only matching agent was returned
        self.assertEqual(len(result), 1)
        mock_agent_type.from_neomodel.assert_called_once_with(agent1)
    
    @patch('agentic.graphql.queries.AgentService')
    @patch('agentic.graphql.queries.AgentType')
    def test_resolve_get_community_leader_success(self, mock_agent_type, mock_service_class):
        """Test successful community leader retrieval."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_community_leader.return_value = self.mock_agent
        mock_service_class.return_value = mock_service
        
        mock_agent_type.from_neomodel.return_value = Mock()
        
        # Execute query
        result = self.queries.resolve_get_community_leader(self.mock_info, "community_456")
        
        # Verify service was called
        mock_service.get_community_leader.assert_called_once_with("community_456")
        
        # Verify result
        self.assertIsNotNone(result)
    
    @patch('agentic.graphql.queries.AgentService')
    def test_resolve_get_community_leader_none_found(self, mock_service_class):
        """Test community leader retrieval when no leader exists."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_community_leader.return_value = None
        mock_service_class.return_value = mock_service
        
        # Execute query
        result = self.queries.resolve_get_community_leader(self.mock_info, "community_456")
        
        # Verify result
        self.assertIsNone(result)
    
    @patch('agentic.graphql.queries.AgentService')
    @patch('agentic.graphql.queries.AgentCommunityAssignment')
    @patch('agentic.graphql.queries.CommunityAgentSummaryType')
    def test_resolve_get_community_agents_success(self, mock_summary_type, mock_assignment_class, mock_service_class):
        """Test successful community agents retrieval."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_community_agents.return_value = [self.mock_agent]
        mock_service_class.return_value = mock_service
        
        mock_assignment_class.nodes.all.return_value = [self.mock_assignment]
        mock_summary_type.from_assignment.return_value = Mock()
        
        # Execute query
        result = self.queries.resolve_get_community_agents(self.mock_info, "community_456")
        
        # Verify result
        self.assertEqual(len(result), 1)
        mock_summary_type.from_assignment.assert_called_once_with(self.mock_assignment)
    
    @patch('agentic.graphql.queries.AgentService')
    @patch('agentic.graphql.queries.AgentAssignmentType')
    def test_resolve_get_agent_assignments_with_filters(self, mock_assignment_type, mock_service_class):
        """Test agent assignments retrieval with filters."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_agent_assignments.return_value = [self.mock_assignment]
        mock_service_class.return_value = mock_service
        
        mock_assignment_type.from_neomodel.return_value = Mock()
        
        # Create filters
        filters = Mock()
        filters.community_uid = "community_456"
        filters.status = "ACTIVE"
        filters.assigned_after = None
        filters.assigned_before = None
        
        # Execute query
        result = self.queries.resolve_get_agent_assignments(self.mock_info, "agent_123", filters=filters)
        
        # Verify service was called
        mock_service.get_agent_assignments.assert_called_once_with("agent_123")
        
        # Verify result
        self.assertEqual(len(result), 1)
    
    @patch('agentic.graphql.queries.AgentCommunityAssignment')
    @patch('agentic.graphql.queries.AgentAssignmentType')
    def test_resolve_get_agent_assignment_success(self, mock_assignment_type, mock_assignment_class):
        """Test successful single assignment retrieval."""
        # Setup mocks
        mock_assignment_class.nodes.get.return_value = self.mock_assignment
        mock_assignment_type.from_neomodel.return_value = Mock()
        
        # Execute query
        result = self.queries.resolve_get_agent_assignment(self.mock_info, "assignment_123")
        
        # Verify service was called
        mock_assignment_class.nodes.get.assert_called_once_with(uid="assignment_123")
        
        # Verify result
        self.assertIsNotNone(result)
    
    @patch('agentic.graphql.queries.AgentCommunityAssignment')
    def test_resolve_get_agent_assignment_not_found(self, mock_assignment_class):
        """Test assignment retrieval when assignment doesn't exist."""
        # Setup mocks
        mock_assignment_class.nodes.get.side_effect = AgentCommunityAssignment.DoesNotExist()
        
        # Execute query
        result = self.queries.resolve_get_agent_assignment(self.mock_info, "nonexistent_assignment")
        
        # Verify result
        self.assertIsNone(result)
    
    @patch('agentic.graphql.queries.AgentMemoryService')
    def test_resolve_get_agent_context_success(self, mock_service_class):
        """Test successful agent context retrieval."""
        # Setup mocks
        mock_service = Mock()
        mock_service.retrieve_context.return_value = {"current_task": "test_task"}
        mock_service_class.return_value = mock_service
        
        # Execute query
        result = self.queries.resolve_get_agent_context(self.mock_info, "agent_123", "community_456")
        
        # Verify service was called
        mock_service.retrieve_context.assert_called_once_with("agent_123", "community_456")
        
        # Verify result
        self.assertEqual(result, {"current_task": "test_task"})
    
    @patch('agentic.graphql.queries.AgentMemoryService')
    def test_resolve_get_conversation_history_success(self, mock_service_class):
        """Test successful conversation history retrieval."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_conversation_history.return_value = [
            {"timestamp": "2024-01-01T12:00:00", "data": {"message": "Hello"}}
        ]
        mock_service_class.return_value = mock_service
        
        # Create input
        input_data = Mock()
        input_data.agent_uid = "agent_123"
        input_data.community_uid = "community_456"
        input_data.limit = 10
        
        # Execute query
        result = self.queries.resolve_get_conversation_history(self.mock_info, input_data)
        
        # Verify service was called
        mock_service.get_conversation_history.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            limit=10
        )
        
        # Verify result
        self.assertEqual(len(result), 1)
    
    @patch('agentic.graphql.queries.AgentMemory')
    @patch('agentic.graphql.queries.AgentMemoryType')
    def test_resolve_get_agent_memory_with_filters(self, mock_memory_type, mock_memory_class):
        """Test agent memory retrieval with filters."""
        # Setup mocks
        mock_memory_class.objects.filter.return_value.order_by.return_value = [self.mock_memory]
        mock_memory_type.from_django_model.return_value = Mock()
        
        # Execute query
        result = self.queries.resolve_get_agent_memory(
            self.mock_info, 
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context"
        )
        
        # Verify service was called with correct filters
        mock_memory_class.objects.filter.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context"
        )
        
        # Verify result
        self.assertEqual(len(result), 1)
    
    @patch('agentic.graphql.queries.AgentAuthService')
    @patch('agentic.graphql.queries.AgentActionLogType')
    def test_resolve_get_agent_action_history_success(self, mock_log_type, mock_service_class):
        """Test successful agent action history retrieval."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_agent_action_history.return_value = [self.mock_log]
        mock_service_class.return_value = mock_service
        
        mock_log_type.from_django_model.return_value = Mock()
        
        # Create input
        input_data = Mock()
        input_data.agent_uid = "agent_123"
        input_data.community_uid = "community_456"
        input_data.action_type = "edit_community"
        input_data.limit = 50
        
        # Execute query
        result = self.queries.resolve_get_agent_action_history(self.mock_info, input_data)
        
        # Verify service was called
        mock_service.get_agent_action_history.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="edit_community",
            limit=50
        )
        
        # Verify result
        self.assertEqual(len(result), 1)
    
    @patch('agentic.graphql.queries.AgentActionLog')
    @patch('agentic.graphql.queries.AgentActionLogType')
    def test_resolve_get_community_action_history_success(self, mock_log_type, mock_log_class):
        """Test successful community action history retrieval."""
        # Setup mocks
        mock_log_class.objects.filter.return_value.order_by.return_value.__getitem__.return_value = [self.mock_log]
        mock_log_type.from_django_model.return_value = Mock()
        
        # Execute query
        result = self.queries.resolve_get_community_action_history(
            self.mock_info,
            community_uid="community_456",
            action_type="edit_community",
            limit=100
        )
        
        # Verify service was called with correct filters
        mock_log_class.objects.filter.assert_called_once_with(
            community_uid="community_456",
            action_type="edit_community"
        )
        
        # Verify result
        self.assertEqual(len(result), 1)
    
    @patch('agentic.graphql.queries.AgentAuthService')
    @patch('agentic.graphql.queries.AgentAuditReportType')
    def test_resolve_generate_agent_audit_report_success(self, mock_report_type, mock_service_class):
        """Test successful audit report generation."""
        # Setup mocks
        mock_service = Mock()
        mock_service.audit_agent_access.return_value = {
            'agent_uid': 'agent_123',
            'community_uid': 'community_456',
            'authenticated': True,
            'permissions': ['edit_community']
        }
        mock_service_class.return_value = mock_service
        
        mock_report_type.from_audit_dict.return_value = Mock()
        
        # Create input
        input_data = Mock()
        input_data.agent_uid = "agent_123"
        input_data.community_uid = "community_456"
        
        # Execute query
        result = self.queries.resolve_generate_agent_audit_report(self.mock_info, input_data)
        
        # Verify service was called
        mock_service.audit_agent_access.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456"
        )
        
        # Verify result
        self.assertIsNotNone(result)
    
    @patch('agentic.graphql.queries.Agent')
    @patch('agentic.graphql.queries.AgentCommunityAssignment')
    @patch('agentic.graphql.queries.AgentStatsType')
    def test_resolve_get_agent_stats_success(self, mock_stats_type, mock_assignment_class, mock_agent_class):
        """Test successful agent statistics retrieval."""
        # Setup mocks
        agents = [
            Mock(status='ACTIVE', agent_type='COMMUNITY_LEADER'),
            Mock(status='ACTIVE', agent_type='MODERATOR'),
            Mock(status='INACTIVE', agent_type='ASSISTANT')
        ]
        mock_agent_class.nodes.all.return_value = agents
        
        assignments = [Mock(is_active=Mock(return_value=True)), Mock(is_active=Mock(return_value=False))]
        mock_assignment_class.nodes.all.return_value = assignments
        
        mock_stats_type.from_stats_dict.return_value = Mock()
        
        # Execute query
        result = self.queries.resolve_get_agent_stats(self.mock_info)
        
        # Verify result
        self.assertIsNotNone(result)
        
        # Verify stats calculation was called
        mock_stats_type.from_stats_dict.assert_called_once()
        call_args = mock_stats_type.from_stats_dict.call_args[0][0]
        self.assertEqual(call_args['total_agents'], 3)
        self.assertEqual(call_args['active_agents'], 2)
        self.assertEqual(call_args['inactive_agents'], 1)
    
    @patch('agentic.graphql.queries.AgentAuthService')
    def test_resolve_get_agent_permissions_success(self, mock_service_class):
        """Test successful agent permissions retrieval."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_agent_permissions.return_value = ["edit_community", "moderate_users"]
        mock_service_class.return_value = mock_service
        
        # Execute query
        result = self.queries.resolve_get_agent_permissions(self.mock_info, "agent_123", "community_456")
        
        # Verify service was called
        mock_service.get_agent_permissions.assert_called_once_with("agent_123", "community_456")
        
        # Verify result
        self.assertEqual(result, ["edit_community", "moderate_users"])
    
    @patch('agentic.graphql.queries.AgentAuthService')
    def test_resolve_validate_agent_permission_success(self, mock_service_class):
        """Test successful agent permission validation."""
        # Setup mocks
        mock_service = Mock()
        mock_service.check_permission.return_value = True
        mock_service_class.return_value = mock_service
        
        # Execute query
        result = self.queries.resolve_validate_agent_permission(
            self.mock_info, "agent_123", "community_456", "edit_community"
        )
        
        # Verify service was called
        mock_service.check_permission.assert_called_once_with("agent_123", "community_456", "edit_community")
        
        # Verify result
        self.assertTrue(result)