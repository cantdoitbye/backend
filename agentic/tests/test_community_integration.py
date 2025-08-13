# Community Integration Tests
# This module contains integration tests for agent assignment during community creation.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from community.graphql.mutations import CreateCommunity
from ..services.agent_service import AgentService
from ..services.auth_service import AgentAuthService
from ..models import Agent, AgentCommunityAssignment


class CommunityAgentIntegrationTest(TestCase):
    """Test cases for agent integration with community creation."""
    
    def setUp(self):
        """Set up test data."""
        # Mock GraphQL info object
        self.mock_info = Mock()
        self.mock_info.context.user.is_anonymous = False
        self.mock_info.context.user.username = "testuser"
        self.mock_info.context.payload = {'user_id': 'user_123'}
        
        # Mock community input
        self.mock_input = Mock()
        self.mock_input.get.side_effect = lambda key, default=None: {
            'name': 'Test Community',
            'description': 'A test community',
            'community_circle': Mock(value='outer'),
            'community_type': Mock(value='interest'),
            'category': 'test',
            'group_icon_id': 'icon_123',
            'member_uid': ['member_1', 'member_2']
        }.get(key, default)
        
        # Mock agent
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.uid = "agent_123"
        self.mock_agent.name = "Test Community Leader"
        
        # Mock assignment
        self.mock_assignment = Mock(spec=AgentCommunityAssignment)
        self.mock_assignment.uid = "assignment_123"
    
    @patch('community.graphql.mutations.Users')
    @patch('community.graphql.mutations.Community')
    @patch('community.graphql.mutations.Membership')
    @patch('community.graphql.mutations.userlist')
    @patch('community.graphql.mutations.NotificationService')
    @patch('community.graphql.mutations.MatrixProfile')
    @patch('agentic.services.agent_service.AgentService')
    @patch('agentic.services.auth_service.AgentAuthService')
    def test_create_community_with_agent_assignment_success(
        self, mock_auth_service_class, mock_agent_service_class, mock_matrix_profile,
        mock_notification_service, mock_userlist, mock_membership_class,
        mock_community_class, mock_users_class
    ):
        """Test successful community creation with agent assignment."""
        
        # Setup mocks for existing community creation logic
        mock_user = Mock()
        mock_user.uid = "user_123"
        mock_user.username = "testuser"
        mock_users_class.nodes.get.return_value = mock_user
        
        mock_community = Mock()
        mock_community.uid = "community_123"
        mock_community.name = "Test Community"
        mock_community_class.return_value = mock_community
        
        mock_membership = Mock()
        mock_membership_class.return_value = mock_membership
        
        mock_userlist.get_unavailable_list_user.return_value = []
        
        # Mock Matrix profile to not exist (skip Matrix room creation)
        mock_matrix_profile.objects.get.side_effect = mock_matrix_profile.DoesNotExist()
        
        # Mock notification service
        mock_notification_service.return_value = Mock()
        
        # Setup agent service mocks
        mock_agent_service = Mock()
        mock_agent_service.get_default_community_agent.return_value = self.mock_agent
        mock_agent_service.assign_agent_to_community.return_value = self.mock_assignment
        mock_agent_service_class.return_value = mock_agent_service
        
        # Setup auth service mocks
        mock_auth_service = Mock()
        mock_auth_service.log_agent_action.return_value = Mock()
        mock_auth_service_class.return_value = mock_auth_service
        
        # Execute mutation
        mutation = CreateCommunity()
        result = mutation.mutate(self.mock_info, self.mock_input)
        
        # Verify community creation succeeded
        self.assertTrue(result.success)
        self.assertIn("created successfully", result.message)
        self.assertIn("Test Community Leader", result.message)
        
        # Verify agent service was called
        mock_agent_service.get_default_community_agent.assert_called_once()
        mock_agent_service.assign_agent_to_community.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_123",
            assigned_by_uid="user_123",
            allow_multiple_leaders=False
        )
        
        # Verify action was logged
        mock_auth_service.log_agent_action.assert_called_once()
        log_call_args = mock_auth_service.log_agent_action.call_args[1]
        self.assertEqual(log_call_args['agent_uid'], "agent_123")
        self.assertEqual(log_call_args['community_uid'], "community_123")
        self.assertEqual(log_call_args['action_type'], "auto_assignment")
        self.assertTrue(log_call_args['success'])
    
    @patch('community.graphql.mutations.Users')
    @patch('community.graphql.mutations.Community')
    @patch('community.graphql.mutations.Membership')
    @patch('community.graphql.mutations.userlist')
    @patch('community.graphql.mutations.NotificationService')
    @patch('community.graphql.mutations.MatrixProfile')
    @patch('agentic.services.agent_service.AgentService')
    def test_create_community_no_default_agent(
        self, mock_agent_service_class, mock_matrix_profile, mock_notification_service,
        mock_userlist, mock_membership_class, mock_community_class, mock_users_class
    ):
        """Test community creation when no default agent is available."""
        
        # Setup mocks for existing community creation logic
        mock_user = Mock()
        mock_user.uid = "user_123"
        mock_users_class.nodes.get.return_value = mock_user
        
        mock_community = Mock()
        mock_community.uid = "community_123"
        mock_community.name = "Test Community"
        mock_community_class.return_value = mock_community
        
        mock_membership = Mock()
        mock_membership_class.return_value = mock_membership
        
        mock_userlist.get_unavailable_list_user.return_value = []
        mock_matrix_profile.objects.get.side_effect = mock_matrix_profile.DoesNotExist()
        mock_notification_service.return_value = Mock()
        
        # Setup agent service to return no default agent
        mock_agent_service = Mock()
        mock_agent_service.get_default_community_agent.return_value = None
        mock_agent_service_class.return_value = mock_agent_service
        
        # Execute mutation
        mutation = CreateCommunity()
        result = mutation.mutate(self.mock_info, self.mock_input)
        
        # Verify community creation succeeded but no agent was assigned
        self.assertTrue(result.success)
        self.assertIn("created successfully", result.message)
        self.assertIn("No AI agent was assigned", result.message)
        
        # Verify agent service was called but no assignment was made
        mock_agent_service.get_default_community_agent.assert_called_once()
        mock_agent_service.assign_agent_to_community.assert_not_called()
    
    @patch('community.graphql.mutations.Users')
    @patch('community.graphql.mutations.Community')
    @patch('community.graphql.mutations.Membership')
    @patch('community.graphql.mutations.userlist')
    @patch('community.graphql.mutations.NotificationService')
    @patch('community.graphql.mutations.MatrixProfile')
    @patch('agentic.services.agent_service.AgentService')
    def test_create_community_agent_assignment_fails(
        self, mock_agent_service_class, mock_matrix_profile, mock_notification_service,
        mock_userlist, mock_membership_class, mock_community_class, mock_users_class
    ):
        """Test community creation when agent assignment fails."""
        
        # Setup mocks for existing community creation logic
        mock_user = Mock()
        mock_user.uid = "user_123"
        mock_users_class.nodes.get.return_value = mock_user
        
        mock_community = Mock()
        mock_community.uid = "community_123"
        mock_community.name = "Test Community"
        mock_community_class.return_value = mock_community
        
        mock_membership = Mock()
        mock_membership_class.return_value = mock_membership
        
        mock_userlist.get_unavailable_list_user.return_value = []
        mock_matrix_profile.objects.get.side_effect = mock_matrix_profile.DoesNotExist()
        mock_notification_service.return_value = Mock()
        
        # Setup agent service to fail assignment
        mock_agent_service = Mock()
        mock_agent_service.get_default_community_agent.return_value = self.mock_agent
        mock_agent_service.assign_agent_to_community.side_effect = Exception("Assignment failed")
        mock_agent_service_class.return_value = mock_agent_service
        
        # Execute mutation
        mutation = CreateCommunity()
        result = mutation.mutate(self.mock_info, self.mock_input)
        
        # Verify community creation still succeeded despite agent assignment failure
        self.assertTrue(result.success)
        self.assertIn("created successfully", result.message)
        self.assertIn("No AI agent was assigned", result.message)
        
        # Verify agent service was called but assignment failed
        mock_agent_service.get_default_community_agent.assert_called_once()
        mock_agent_service.assign_agent_to_community.assert_called_once()
    
    @patch('community.graphql.mutations.Users')
    @patch('community.graphql.mutations.Community')
    @patch('community.graphql.mutations.Membership')
    @patch('community.graphql.mutations.userlist')
    @patch('community.graphql.mutations.NotificationService')
    @patch('community.graphql.mutations.MatrixProfile')
    @patch('agentic.services.agent_service.AgentService')
    @patch('agentic.services.auth_service.AgentAuthService')
    def test_create_community_agent_logging_fails(
        self, mock_auth_service_class, mock_agent_service_class, mock_matrix_profile,
        mock_notification_service, mock_userlist, mock_membership_class,
        mock_community_class, mock_users_class
    ):
        """Test community creation when agent action logging fails."""
        
        # Setup mocks for existing community creation logic
        mock_user = Mock()
        mock_user.uid = "user_123"
        mock_users_class.nodes.get.return_value = mock_user
        
        mock_community = Mock()
        mock_community.uid = "community_123"
        mock_community.name = "Test Community"
        mock_community_class.return_value = mock_community
        
        mock_membership = Mock()
        mock_membership_class.return_value = mock_membership
        
        mock_userlist.get_unavailable_list_user.return_value = []
        mock_matrix_profile.objects.get.side_effect = mock_matrix_profile.DoesNotExist()
        mock_notification_service.return_value = Mock()
        
        # Setup agent service mocks
        mock_agent_service = Mock()
        mock_agent_service.get_default_community_agent.return_value = self.mock_agent
        mock_agent_service.assign_agent_to_community.return_value = self.mock_assignment
        mock_agent_service_class.return_value = mock_agent_service
        
        # Setup auth service to fail logging
        mock_auth_service = Mock()
        mock_auth_service.log_agent_action.side_effect = Exception("Logging failed")
        mock_auth_service_class.return_value = mock_auth_service
        
        # Execute mutation
        mutation = CreateCommunity()
        result = mutation.mutate(self.mock_info, self.mock_input)
        
        # Verify community creation and agent assignment still succeeded
        self.assertTrue(result.success)
        self.assertIn("created successfully", result.message)
        self.assertIn("Test Community Leader", result.message)
        
        # Verify agent was assigned despite logging failure
        mock_agent_service.assign_agent_to_community.assert_called_once()
        mock_auth_service.log_agent_action.assert_called_once()
    
    def test_create_community_backward_compatibility(self):
        """Test that community creation still works without agent services available."""
        
        # This test ensures that if the agentic module is not available or fails to import,
        # community creation still works as before
        
        with patch('community.graphql.mutations.Users') as mock_users_class, \
             patch('community.graphql.mutations.Community') as mock_community_class, \
             patch('community.graphql.mutations.Membership') as mock_membership_class, \
             patch('community.graphql.mutations.userlist') as mock_userlist, \
             patch('community.graphql.mutations.NotificationService') as mock_notification_service, \
             patch('community.graphql.mutations.MatrixProfile') as mock_matrix_profile:
            
            # Setup mocks for existing community creation logic
            mock_user = Mock()
            mock_user.uid = "user_123"
            mock_users_class.nodes.get.return_value = mock_user
            
            mock_community = Mock()
            mock_community.uid = "community_123"
            mock_community.name = "Test Community"
            mock_community_class.return_value = mock_community
            
            mock_membership = Mock()
            mock_membership_class.return_value = mock_membership
            
            mock_userlist.get_unavailable_list_user.return_value = []
            mock_matrix_profile.objects.get.side_effect = mock_matrix_profile.DoesNotExist()
            mock_notification_service.return_value = Mock()
            
            # Mock import failure for agentic services
            with patch('builtins.__import__', side_effect=ImportError("No module named 'agentic'")):
                # Execute mutation
                mutation = CreateCommunity()
                result = mutation.mutate(self.mock_info, self.mock_input)
                
                # Verify community creation still succeeded
                self.assertTrue(result.success)
                self.assertIn("created successfully", result.message)
                # Should not mention agent assignment
                self.assertNotIn("AI agent", result.message)