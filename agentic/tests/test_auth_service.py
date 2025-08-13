# Agent Auth Service Tests
# This module contains unit tests for the AgentAuthService class.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from datetime import datetime

from ..services.auth_service import (
    AgentAuthService, AgentAuthError, AgentAuthenticationError, AgentAuthorizationError
)
from ..models import Agent, AgentCommunityAssignment, AgentActionLog


class AgentAuthServiceTest(TestCase):
    """Test cases for the AgentAuthService class."""
    
    def setUp(self):
        """Set up test data."""
        self.auth_service = AgentAuthService()
        
        # Mock objects for testing
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.uid = "agent_123"
        self.mock_agent.name = "Test Agent"
        self.mock_agent.status = "ACTIVE"
        self.mock_agent.is_active.return_value = True
        
        self.mock_community = Mock()
        self.mock_community.uid = "community_456"
        self.mock_community.name = "Test Community"
        
        self.mock_assignment = Mock(spec=AgentCommunityAssignment)
        self.mock_assignment.uid = "assignment_101"
        self.mock_assignment.status = "ACTIVE"
        self.mock_assignment.is_active.return_value = True
        self.mock_assignment.community.single.return_value = self.mock_community
        self.mock_assignment.get_effective_permissions.return_value = ["edit_community", "moderate_users"]
        
        self.mock_agent.assigned_communities.all.return_value = [self.mock_assignment]
    
    @patch('agentic.services.auth_service.Agent')
    @patch('agentic.services.auth_service.Community')
    def test_authenticate_agent_success(self, mock_community_class, mock_agent_class):
        """Test successful agent authentication."""
        # Setup mocks
        mock_agent_class.nodes.get.return_value = self.mock_agent
        mock_community_class.nodes.get.return_value = self.mock_community
        
        # Test authentication
        result = self.auth_service.authenticate_agent("agent_123", "community_456")
        
        # Verify authentication succeeded
        self.assertTrue(result)
        mock_agent_class.nodes.get.assert_called_once_with(uid="agent_123")
        mock_community_class.nodes.get.assert_called_once_with(uid="community_456")
        self.mock_agent.is_active.assert_called_once()
    
    @patch('agentic.services.auth_service.Agent')
    def test_authenticate_agent_not_found(self, mock_agent_class):
        """Test authentication when agent doesn't exist."""
        # Create a mock DoesNotExist exception class
        class MockDoesNotExist(Exception):
            pass
        
        mock_agent_class.DoesNotExist = MockDoesNotExist
        mock_agent_class.nodes.get.side_effect = MockDoesNotExist("Agent not found")
        
        with self.assertRaises(AgentAuthenticationError) as context:
            self.auth_service.authenticate_agent("nonexistent_agent", "community_456")
        
        self.assertIn("Agent nonexistent_agent not found", str(context.exception))
    
    @patch('agentic.services.auth_service.Agent')
    def test_authenticate_agent_inactive(self, mock_agent_class):
        """Test authentication when agent is inactive."""
        inactive_agent = Mock(spec=Agent)
        inactive_agent.uid = "inactive_agent"
        inactive_agent.status = "INACTIVE"
        inactive_agent.is_active.return_value = False
        
        mock_agent_class.nodes.get.return_value = inactive_agent
        
        with self.assertRaises(AgentAuthenticationError) as context:
            self.auth_service.authenticate_agent("inactive_agent", "community_456")
        
        self.assertIn("is not active", str(context.exception))
    
    @patch('agentic.services.auth_service.Agent')
    @patch('agentic.services.auth_service.Community')
    def test_authenticate_agent_community_not_found(self, mock_community_class, mock_agent_class):
        """Test authentication when community doesn't exist."""
        # Create a mock DoesNotExist exception class
        class MockDoesNotExist(Exception):
            pass
        
        mock_community_class.DoesNotExist = MockDoesNotExist
        
        mock_agent_class.nodes.get.return_value = self.mock_agent
        mock_community_class.nodes.get.side_effect = MockDoesNotExist("Community not found")
        
        with self.assertRaises(AgentAuthenticationError) as context:
            self.auth_service.authenticate_agent("agent_123", "nonexistent_community")
        
        self.assertIn("Community nonexistent_community not found", str(context.exception))
    
    @patch('agentic.services.auth_service.Agent')
    @patch('agentic.services.auth_service.Community')
    def test_authenticate_agent_no_assignment(self, mock_community_class, mock_agent_class):
        """Test authentication when agent has no assignment to community."""
        # Agent with no assignments
        agent_no_assignments = Mock(spec=Agent)
        agent_no_assignments.uid = "agent_no_assign"
        agent_no_assignments.is_active.return_value = True
        agent_no_assignments.assigned_communities.all.return_value = []
        
        mock_agent_class.nodes.get.return_value = agent_no_assignments
        mock_community_class.nodes.get.return_value = self.mock_community
        
        result = self.auth_service.authenticate_agent("agent_no_assign", "community_456")
        
        # Should return False, not raise exception
        self.assertFalse(result)
    
    def test_get_agent_permissions_success(self):
        """Test successful retrieval of agent permissions."""
        with patch.object(self.auth_service, 'authenticate_agent', return_value=True):
            with patch('agentic.services.auth_service.Agent') as mock_agent_class:
                mock_agent_class.nodes.get.return_value = self.mock_agent
                
                result = self.auth_service.get_agent_permissions("agent_123", "community_456")
                
                self.assertEqual(result, ["edit_community", "moderate_users"])
                self.mock_assignment.get_effective_permissions.assert_called_once()
    
    def test_get_agent_permissions_not_authenticated(self):
        """Test permissions retrieval when agent is not authenticated."""
        with patch.object(self.auth_service, 'authenticate_agent', return_value=False):
            with self.assertRaises(AgentAuthenticationError) as context:
                self.auth_service.get_agent_permissions("agent_123", "community_456")
            
            self.assertIn("not authenticated", str(context.exception))
    
    def test_check_permission_success(self):
        """Test successful permission checking."""
        with patch.object(self.auth_service, 'get_agent_permissions', return_value=["edit_community", "moderate_users"]):
            result = self.auth_service.check_permission("agent_123", "community_456", "edit_community")
            self.assertTrue(result)
            
            result = self.auth_service.check_permission("agent_123", "community_456", "nonexistent_permission")
            self.assertFalse(result)
    
    def test_check_permission_error_handling(self):
        """Test permission checking with error handling."""
        with patch.object(self.auth_service, 'get_agent_permissions', side_effect=Exception("Test error")):
            result = self.auth_service.check_permission("agent_123", "community_456", "edit_community")
            # Should return False on error for security
            self.assertFalse(result)
    
    def test_require_permission_success(self):
        """Test successful permission requirement."""
        with patch.object(self.auth_service, 'check_permission', return_value=True):
            # Should not raise exception
            self.auth_service.require_permission("agent_123", "community_456", "edit_community")
    
    def test_require_permission_failure(self):
        """Test permission requirement failure."""
        with patch.object(self.auth_service, 'check_permission', return_value=False):
            with self.assertRaises(AgentAuthorizationError) as context:
                self.auth_service.require_permission("agent_123", "community_456", "edit_community")
            
            self.assertIn("lacks required permission", str(context.exception))
    
    @patch('agentic.services.auth_service.AgentActionLog')
    def test_log_agent_action_success(self, mock_log_class):
        """Test successful action logging."""
        mock_log_instance = Mock()
        mock_log_class.objects.create.return_value = mock_log_instance
        
        result = self.auth_service.log_agent_action(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="edit_community",
            details={"field": "description", "new_value": "Updated"},
            success=True,
            execution_time_ms=150
        )
        
        self.assertEqual(result, mock_log_instance)
        mock_log_class.objects.create.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_log_class.objects.create.call_args[1]
        self.assertEqual(call_args['agent_uid'], "agent_123")
        self.assertEqual(call_args['community_uid'], "community_456")
        self.assertEqual(call_args['action_type'], "edit_community")
        self.assertTrue(call_args['success'])
        self.assertEqual(call_args['execution_time_ms'], 150)
    
    @patch('agentic.services.auth_service.AgentActionLog')
    def test_log_agent_action_failure(self, mock_log_class):
        """Test action logging with failure."""
        mock_log_class.objects.create.side_effect = Exception("Database error")
        
        # Should not raise exception, just return None
        result = self.auth_service.log_agent_action(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="edit_community",
            details={},
            success=False,
            error_message="Test error"
        )
        
        self.assertIsNone(result)
    
    @patch('agentic.services.auth_service.AgentActionLog')
    def test_get_agent_action_history(self, mock_log_class):
        """Test retrieval of agent action history."""
        mock_logs = [Mock(), Mock(), Mock()]
        mock_log_class.objects.filter.return_value.order_by.return_value.__getitem__.return_value = mock_logs
        
        result = self.auth_service.get_agent_action_history(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="edit_community",
            limit=10
        )
        
        self.assertEqual(result, mock_logs)
        mock_log_class.objects.filter.assert_called_once_with(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="edit_community"
        )
    
    def test_validate_action_permission_success(self):
        """Test successful action permission validation."""
        with patch.object(self.auth_service, 'check_permission', return_value=True):
            result = self.auth_service.validate_action_permission(
                "agent_123", "community_456", "edit_community"
            )
            self.assertTrue(result)
    
    def test_validate_action_permission_unknown_action(self):
        """Test action permission validation with unknown action."""
        result = self.auth_service.validate_action_permission(
            "agent_123", "community_456", "unknown_action"
        )
        # Should return False for unknown actions
        self.assertFalse(result)
    
    def test_get_available_actions_success(self):
        """Test successful retrieval of available actions."""
        with patch.object(self.auth_service, 'get_agent_permissions', return_value=["edit_community", "moderate_users"]):
            result = self.auth_service.get_available_actions("agent_123", "community_456")
            
            # Should include actions mapped from permissions
            expected_actions = [
                'edit_community', 'moderate_user', 'remove_user', 
                'update_community_description', 'update_community_settings'
            ]
            
            # Check that all expected actions are present (order may vary)
            for action in expected_actions:
                self.assertIn(action, result)
    
    def test_is_agent_admin_success(self):
        """Test successful admin status checking."""
        with patch.object(self.auth_service, 'get_agent_permissions', return_value=["edit_community", "moderate_users"]):
            result = self.auth_service.is_agent_admin("agent_123", "community_456")
            self.assertTrue(result)
    
    def test_is_agent_admin_insufficient_permissions(self):
        """Test admin status checking with insufficient permissions."""
        with patch.object(self.auth_service, 'get_agent_permissions', return_value=["fetch_metrics"]):
            result = self.auth_service.is_agent_admin("agent_123", "community_456")
            self.assertFalse(result)
    
    def test_get_permission_description(self):
        """Test permission description retrieval."""
        # Test standard permission
        result = self.auth_service.get_permission_description("edit_community")
        self.assertEqual(result, "Modify community settings and information")
        
        # Test custom permission
        result = self.auth_service.get_permission_description("custom_permission")
        self.assertEqual(result, "Custom permission: custom_permission")
    
    def test_audit_agent_access_authenticated(self):
        """Test comprehensive audit report for authenticated agent."""
        with patch.object(self.auth_service, 'authenticate_agent', return_value=True):
            with patch.object(self.auth_service, 'get_agent_permissions', return_value=["edit_community"]):
                with patch.object(self.auth_service, 'get_available_actions', return_value=["edit_community"]):
                    with patch.object(self.auth_service, 'is_agent_admin', return_value=True):
                        with patch.object(self.auth_service, 'get_agent_action_history', return_value=[]):
                            
                            result = self.auth_service.audit_agent_access("agent_123", "community_456")
                            
                            self.assertTrue(result['authenticated'])
                            self.assertEqual(result['agent_uid'], "agent_123")
                            self.assertEqual(result['community_uid'], "community_456")
                            self.assertEqual(result['permissions'], ["edit_community"])
                            self.assertTrue(result['is_admin'])
                            self.assertIn('audit_timestamp', result)
    
    def test_audit_agent_access_not_authenticated(self):
        """Test audit report for non-authenticated agent."""
        with patch.object(self.auth_service, 'authenticate_agent', return_value=False):
            result = self.auth_service.audit_agent_access("agent_123", "community_456")
            
            self.assertFalse(result['authenticated'])
            self.assertEqual(result['permissions'], [])
            self.assertEqual(result['available_actions'], [])
            self.assertFalse(result['is_admin'])
    
    def test_audit_agent_access_error_handling(self):
        """Test audit report with error handling."""
        with patch.object(self.auth_service, 'authenticate_agent', side_effect=Exception("Test error")):
            result = self.auth_service.audit_agent_access("agent_123", "community_456")
            
            self.assertIn('error', result)
            self.assertEqual(result['agent_uid'], "agent_123")
            self.assertEqual(result['community_uid'], "community_456")