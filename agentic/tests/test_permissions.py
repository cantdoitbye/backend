# Agent Permission Utilities Tests
# This module contains unit tests for the agent permission utilities.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from ..utils.permissions import (
    AgentPermissionUtils, AgentPermissionError, AgentPermissionChecker,
    agent_required, require_agent_permission, require_any_agent_permission,
    log_agent_permission_check, create_agent_permission_validator
)
from ..services.auth_service import AgentAuthorizationError


class AgentPermissionUtilsTest(TestCase):
    """Test cases for AgentPermissionUtils class."""
    
    def test_get_permission_info_standard_permission(self):
        """Test getting info for a standard permission."""
        result = AgentPermissionUtils.get_permission_info('edit_community')
        
        self.assertEqual(result['name'], 'Edit Community')
        self.assertEqual(result['description'], 'Modify community settings and information')
        self.assertEqual(result['category'], 'community_management')
    
    def test_get_permission_info_custom_permission(self):
        """Test getting info for a custom permission."""
        result = AgentPermissionUtils.get_permission_info('custom_permission')
        
        self.assertEqual(result['name'], 'Custom Permission')
        self.assertEqual(result['description'], 'Custom permission: custom_permission')
        self.assertEqual(result['category'], 'custom')
    
    def test_expand_permission_hierarchy(self):
        """Test expanding permission hierarchies."""
        permissions = ['community_admin', 'custom_permission']
        result = AgentPermissionUtils.expand_permission_hierarchy(permissions)
        
        # Should include all admin permissions plus the custom one
        self.assertIn('edit_community', result)
        self.assertIn('moderate_users', result)
        self.assertIn('fetch_metrics', result)
        self.assertIn('custom_permission', result)
        self.assertGreater(len(result), len(permissions))
    
    def test_expand_permission_hierarchy_no_hierarchy(self):
        """Test expanding permissions with no hierarchies."""
        permissions = ['edit_community', 'moderate_users']
        result = AgentPermissionUtils.expand_permission_hierarchy(permissions)
        
        # Should return the same permissions
        self.assertEqual(set(result), set(permissions))
    
    def test_validate_permissions_all_valid(self):
        """Test validating all valid permissions."""
        permissions = ['edit_community', 'moderate_users', 'community_admin']
        result = AgentPermissionUtils.validate_permissions(permissions)
        
        # Should return empty list (no invalid permissions)
        self.assertEqual(result, [])
    
    def test_validate_permissions_with_invalid(self):
        """Test validating permissions with some invalid ones."""
        permissions = ['edit_community', 'invalid_permission', 'another_invalid']
        result = AgentPermissionUtils.validate_permissions(permissions)
        
        # Should return the invalid permissions
        self.assertEqual(set(result), {'invalid_permission', 'another_invalid'})
    
    def test_validate_permissions_custom_allowed(self):
        """Test that custom permissions are allowed."""
        permissions = ['edit_community', 'custom_my_permission']
        result = AgentPermissionUtils.validate_permissions(permissions)
        
        # Custom permissions should be valid
        self.assertEqual(result, [])
    
    def test_get_permissions_by_category(self):
        """Test getting permissions by category."""
        result = AgentPermissionUtils.get_permissions_by_category('user_management')
        
        # Should include user management permissions
        self.assertIn('moderate_users', result)
        self.assertIn('manage_roles', result)
        self.assertIn('ban_users', result)
        
        # Should not include other categories
        self.assertNotIn('edit_community', result)
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_check_agent_permission_sync_success(self, mock_auth_service_class):
        """Test successful synchronous permission check."""
        # Setup mock
        mock_auth_service = Mock()
        mock_auth_service.check_permission.return_value = True
        mock_auth_service_class.return_value = mock_auth_service
        
        # Test permission check
        result = AgentPermissionUtils.check_agent_permission_sync(
            'agent_123', 'community_456', 'edit_community'
        )
        
        # Verify result
        self.assertTrue(result)
        mock_auth_service.check_permission.assert_called_once_with(
            'agent_123', 'community_456', 'edit_community'
        )
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_check_agent_permission_sync_failure(self, mock_auth_service_class):
        """Test synchronous permission check with failure."""
        # Setup mock to raise exception
        mock_auth_service = Mock()
        mock_auth_service.check_permission.side_effect = Exception("Auth error")
        mock_auth_service_class.return_value = mock_auth_service
        
        # Test permission check
        result = AgentPermissionUtils.check_agent_permission_sync(
            'agent_123', 'community_456', 'edit_community'
        )
        
        # Should return False on error
        self.assertFalse(result)
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_get_agent_effective_permissions_success(self, mock_auth_service_class):
        """Test successful effective permissions retrieval."""
        # Setup mock
        mock_auth_service = Mock()
        mock_auth_service.get_agent_permissions.return_value = ['edit_community', 'moderate_users']
        mock_auth_service_class.return_value = mock_auth_service
        
        # Test permissions retrieval
        result = AgentPermissionUtils.get_agent_effective_permissions('agent_123', 'community_456')
        
        # Verify result
        self.assertEqual(result, ['edit_community', 'moderate_users'])
    
    def test_create_permission_matrix(self):
        """Test creating permission matrix."""
        agents = ['agent_1', 'agent_2']
        communities = ['community_1', 'community_2']
        
        with patch.object(AgentPermissionUtils, 'get_agent_effective_permissions') as mock_get_perms:
            mock_get_perms.return_value = ['edit_community']
            
            result = AgentPermissionUtils.create_permission_matrix(agents, communities)
            
            # Verify structure
            self.assertIn('agent_1', result)
            self.assertIn('agent_2', result)
            self.assertIn('community_1', result['agent_1'])
            self.assertIn('community_2', result['agent_1'])
            
            # Verify permissions
            self.assertEqual(result['agent_1']['community_1'], ['edit_community'])


class AgentPermissionCheckerTest(TestCase):
    """Test cases for AgentPermissionChecker class."""
    
    def setUp(self):
        """Set up test data."""
        self.checker = AgentPermissionChecker('agent_123', 'community_456')
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_check_permission_success(self, mock_auth_service_class):
        """Test successful permission check."""
        # Setup mock
        mock_auth_service = Mock()
        mock_auth_service.check_permission.return_value = True
        mock_auth_service_class.return_value = mock_auth_service
        
        # Override the auth_service instance
        self.checker.auth_service = mock_auth_service
        
        # Test permission check
        result = self.checker.check_permission('edit_community')
        
        # Verify result
        self.assertTrue(result)
        self.assertEqual(len(self.checker.get_errors()), 0)
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_check_permission_failure(self, mock_auth_service_class):
        """Test permission check failure."""
        # Setup mock
        mock_auth_service = Mock()
        mock_auth_service.check_permission.return_value = False
        mock_auth_service_class.return_value = mock_auth_service
        
        # Override the auth_service instance
        self.checker.auth_service = mock_auth_service
        
        # Test permission check
        result = self.checker.check_permission('edit_community')
        
        # Verify result
        self.assertFalse(result)
        self.assertEqual(len(self.checker.get_errors()), 1)
        self.assertIn('Missing permission: edit_community', self.checker.get_errors())
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_require_permission_success(self, mock_auth_service_class):
        """Test successful permission requirement."""
        # Setup mock
        mock_auth_service = Mock()
        mock_auth_service.check_permission.return_value = True
        mock_auth_service_class.return_value = mock_auth_service
        
        # Override the auth_service instance
        self.checker.auth_service = mock_auth_service
        
        # Test permission requirement (should not raise exception)
        self.checker.require_permission('edit_community')
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_require_permission_failure(self, mock_auth_service_class):
        """Test permission requirement failure."""
        # Setup mock
        mock_auth_service = Mock()
        mock_auth_service.check_permission.return_value = False
        mock_auth_service_class.return_value = mock_auth_service
        
        # Override the auth_service instance
        self.checker.auth_service = mock_auth_service
        
        # Test permission requirement (should raise exception)
        with self.assertRaises(AgentAuthorizationError) as context:
            self.checker.require_permission('edit_community')
        
        self.assertIn('lacks required permission', str(context.exception))
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_check_any_permission_success(self, mock_auth_service_class):
        """Test successful any permission check."""
        # Setup mock to return True for second permission
        mock_auth_service = Mock()
        mock_auth_service.check_permission.side_effect = [False, True]
        mock_auth_service_class.return_value = mock_auth_service
        
        # Override the auth_service instance
        self.checker.auth_service = mock_auth_service
        
        # Test any permission check
        result = self.checker.check_any_permission(['moderate_users', 'edit_community'])
        
        # Verify result
        self.assertTrue(result)
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_check_any_permission_failure(self, mock_auth_service_class):
        """Test any permission check failure."""
        # Setup mock to return False for all permissions
        mock_auth_service = Mock()
        mock_auth_service.check_permission.return_value = False
        mock_auth_service_class.return_value = mock_auth_service
        
        # Override the auth_service instance
        self.checker.auth_service = mock_auth_service
        
        # Test any permission check
        result = self.checker.check_any_permission(['moderate_users', 'edit_community'])
        
        # Verify result
        self.assertFalse(result)
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_require_any_permission_success(self, mock_auth_service_class):
        """Test successful any permission requirement."""
        # Setup mock to return True for one permission
        mock_auth_service = Mock()
        mock_auth_service.check_permission.side_effect = [False, True]
        mock_auth_service_class.return_value = mock_auth_service
        
        # Override the auth_service instance
        self.checker.auth_service = mock_auth_service
        
        # Test any permission requirement (should not raise exception)
        self.checker.require_any_permission(['moderate_users', 'edit_community'])
    
    @patch('agentic.utils.permissions.AgentAuthService')
    def test_require_any_permission_failure(self, mock_auth_service_class):
        """Test any permission requirement failure."""
        # Setup mock to return False for all permissions
        mock_auth_service = Mock()
        mock_auth_service.check_permission.return_value = False
        mock_auth_service_class.return_value = mock_auth_service
        
        # Override the auth_service instance
        self.checker.auth_service = mock_auth_service
        
        # Test any permission requirement (should raise exception)
        with self.assertRaises(AgentAuthorizationError) as context:
            self.checker.require_any_permission(['moderate_users', 'edit_community'])
        
        self.assertIn('lacks any of the required permissions', str(context.exception))


class AgentPermissionDecoratorsTest(TestCase):
    """Test cases for agent permission decorators."""
    
    def test_agent_required_decorator_success(self):
        """Test agent_required decorator with valid agent context."""
        # Create mock function
        @agent_required
        def test_function(info):
            return "success"
        
        # Create mock info with agent context
        mock_info = Mock()
        mock_info.context.agent_context = {'agent_uid': 'agent_123'}
        
        # Test function call
        result = test_function(mock_info)
        
        # Verify result
        self.assertEqual(result, "success")
    
    def test_agent_required_decorator_failure(self):
        """Test agent_required decorator without agent context."""
        # Create mock function
        @agent_required
        def test_function(info):
            return "success"
        
        # Create mock info without agent context
        mock_info = Mock()
        mock_info.context.agent_context = None
        
        # Test function call (should raise exception)
        with self.assertRaises(AgentPermissionError) as context:
            test_function(mock_info)
        
        self.assertIn('Agent context required', str(context.exception))
    
    @patch('agentic.utils.permissions.AgentPermissionUtils.check_agent_permission_sync')
    def test_require_agent_permission_decorator_success(self, mock_check_permission):
        """Test require_agent_permission decorator with valid permission."""
        # Setup mock
        mock_check_permission.return_value = True
        
        # Create mock function
        @require_agent_permission('edit_community')
        def test_function(info, community_uid):
            return "success"
        
        # Create mock info with agent context
        mock_info = Mock()
        mock_info.context.agent_context = {'agent_uid': 'agent_123'}
        
        # Test function call
        result = test_function(mock_info, community_uid='community_456')
        
        # Verify result
        self.assertEqual(result, "success")
        mock_check_permission.assert_called_once_with('agent_123', 'community_456', 'edit_community')
    
    @patch('agentic.utils.permissions.AgentPermissionUtils.check_agent_permission_sync')
    def test_require_agent_permission_decorator_failure(self, mock_check_permission):
        """Test require_agent_permission decorator without permission."""
        # Setup mock
        mock_check_permission.return_value = False
        
        # Create mock function
        @require_agent_permission('edit_community')
        def test_function(info, community_uid):
            return "success"
        
        # Create mock info with agent context
        mock_info = Mock()
        mock_info.context.agent_context = {'agent_uid': 'agent_123'}
        
        # Test function call (should raise exception)
        with self.assertRaises(AgentAuthorizationError) as context:
            test_function(mock_info, community_uid='community_456')
        
        self.assertIn('lacks required permission', str(context.exception))


class AgentPermissionValidatorTest(TestCase):
    """Test cases for agent permission validator."""
    
    def test_create_agent_permission_validator(self):
        """Test creating and using a permission validator."""
        # Create validator
        validator = create_agent_permission_validator(['edit_community', 'moderate_users'])
        
        with patch('agentic.utils.permissions.AgentPermissionChecker') as mock_checker_class:
            # Setup mock checker
            mock_checker = Mock()
            mock_checker.check_permission.side_effect = [True, False]  # First permission OK, second not
            mock_checker.get_errors.return_value = ['Missing permission: moderate_users']
            mock_checker_class.return_value = mock_checker
            
            # Test validator
            result = validator('agent_123', 'community_456')
            
            # Verify result
            self.assertEqual(result['agent_uid'], 'agent_123')
            self.assertEqual(result['community_uid'], 'community_456')
            self.assertEqual(result['required_permissions'], ['edit_community', 'moderate_users'])
            self.assertFalse(result['has_all_permissions'])
            self.assertEqual(result['missing_permissions'], ['moderate_users'])
            self.assertEqual(result['errors'], ['Missing permission: moderate_users'])