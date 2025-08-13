# Agent Community Management Tests
# This module contains tests for the agent community management service.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from datetime import datetime

from ..services.community_management import (
    AgentCommunityManager, AgentCommunityManagementError
)
from ..services.auth_service import AgentAuthenticationError, AgentAuthorizationError
from community.models import Community, Membership
from auth_manager.models import Users


class AgentCommunityManagerTest(TestCase):
    """Test cases for AgentCommunityManager class."""
    
    def setUp(self):
        """Set up test data."""
        self.manager = AgentCommunityManager()
        
        # Mock objects
        self.mock_community = Mock(spec=Community)
        self.mock_community.uid = "community_123"
        self.mock_community.name = "Test Community"
        self.mock_community.description = "A test community"
        
        self.mock_membership = Mock(spec=Membership)
        self.mock_membership.uid = "membership_123"
        self.mock_membership.can_message = True
        self.mock_membership.is_blocked = False
        
        self.mock_user = Mock(spec=Users)
        self.mock_user.uid = "user_123"
        self.mock_user.username = "testuser"
        
        # Mock auth service
        self.mock_auth_service = Mock()
        self.mock_auth_service.authenticate_agent.return_value = True
        self.mock_auth_service.require_permission.return_value = None
        self.mock_auth_service.log_agent_action.return_value = Mock()
        self.manager.auth_service = self.mock_auth_service
    
    @patch('agentic.services.community_management.Community')
    def test_edit_community_success(self, mock_community_class):
        """Test successful community editing."""
        # Setup mocks
        mock_community_class.nodes.get.return_value = self.mock_community
        
        updates = {
            'name': 'Updated Community Name',
            'description': 'Updated description',
            'category': 'updated_category'
        }
        
        # Test community editing
        result = self.manager.edit_community(
            agent_uid="agent_123",
            community_uid="community_123",
            updates=updates
        )
        
        # Verify authentication and authorization were checked
        self.mock_auth_service.authenticate_agent.assert_called_once_with("agent_123", "community_123")
        self.mock_auth_service.require_permission.assert_called_once_with("agent_123", "community_123", "edit_community")
        
        # Verify community was updated
        self.mock_community.save.assert_called_once()
        
        # Verify action was logged
        self.mock_auth_service.log_agent_action.assert_called_once()
        log_call_args = self.mock_auth_service.log_agent_action.call_args[1]
        self.assertEqual(log_call_args['action_type'], 'edit_community')
        self.assertTrue(log_call_args['success'])
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertIn('Community updated successfully', result['message'])
        self.assertIn('updates_applied', result)
    
    def test_edit_community_authentication_failure(self):
        """Test community editing with authentication failure."""
        # Setup auth service to fail authentication
        self.mock_auth_service.authenticate_agent.return_value = False
        
        # Test community editing (should raise exception)
        with self.assertRaises(AgentAuthenticationError) as context:
            self.manager.edit_community(
                agent_uid="agent_123",
                community_uid="community_123",
                updates={'name': 'New Name'}
            )
        
        self.assertIn('not authenticated', str(context.exception))
    
    def test_edit_community_authorization_failure(self):
        """Test community editing with authorization failure."""
        # Setup auth service to fail authorization
        self.mock_auth_service.require_permission.side_effect = AgentAuthorizationError("No permission")
        
        # Test community editing (should raise exception)
        with self.assertRaises(AgentAuthorizationError):
            self.manager.edit_community(
                agent_uid="agent_123",
                community_uid="community_123",
                updates={'name': 'New Name'}
            )
    
    @patch('agentic.services.community_management.Community')
    def test_edit_community_not_found(self, mock_community_class):
        """Test community editing when community doesn't exist."""
        # Setup mock to raise DoesNotExist
        mock_community_class.nodes.get.side_effect = Community.DoesNotExist()
        
        # Test community editing (should raise exception)
        with self.assertRaises(AgentCommunityManagementError) as context:
            self.manager.edit_community(
                agent_uid="agent_123",
                community_uid="nonexistent_community",
                updates={'name': 'New Name'}
            )
        
        self.assertIn('not found', str(context.exception))
    
    @patch('agentic.services.community_management.Community')
    @patch('agentic.services.community_management.Users')
    def test_moderate_users_success(self, mock_users_class, mock_community_class):
        """Test successful user moderation."""
        # Setup mocks
        mock_community_class.nodes.get.return_value = self.mock_community
        mock_users_class.nodes.get.return_value = self.mock_user
        
        # Mock membership lookup
        self.mock_membership.user.single.return_value = self.mock_user
        self.mock_community.members.all.return_value = [self.mock_membership]
        
        # Test user moderation
        result = self.manager.moderate_users(
            agent_uid="agent_123",
            community_uid="community_123",
            action="mute",
            target_user_uid="user_123",
            reason="Inappropriate behavior"
        )
        
        # Verify authentication and authorization were checked
        self.mock_auth_service.authenticate_agent.assert_called_once_with("agent_123", "community_123")
        self.mock_auth_service.require_permission.assert_called_once_with("agent_123", "community_123", "moderate_users")
        
        # Verify membership was updated
        self.assertFalse(self.mock_membership.can_message)
        self.mock_membership.save.assert_called_once()
        
        # Verify action was logged
        self.mock_auth_service.log_agent_action.assert_called_once()
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'mute')
        self.assertEqual(result['target_user_uid'], 'user_123')
    
    @patch('agentic.services.community_management.Community')
    @patch('agentic.services.community_management.Users')
    def test_moderate_users_ban_action(self, mock_users_class, mock_community_class):
        """Test user moderation with ban action."""
        # Setup mocks
        mock_community_class.nodes.get.return_value = self.mock_community
        mock_users_class.nodes.get.return_value = self.mock_user
        
        # Mock membership lookup
        self.mock_membership.user.single.return_value = self.mock_user
        self.mock_community.members.all.return_value = [self.mock_membership]
        
        # Test ban action
        result = self.manager.moderate_users(
            agent_uid="agent_123",
            community_uid="community_123",
            action="ban",
            target_user_uid="user_123",
            reason="Severe violation"
        )
        
        # Verify ban_users permission was required
        self.mock_auth_service.require_permission.assert_called_once_with("agent_123", "community_123", "ban_users")
        
        # Verify membership was deleted (banned)
        self.mock_membership.delete.assert_called_once()
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'ban')
    
    @patch('agentic.services.community_management.Community')
    @patch('agentic.services.community_management.Users')
    def test_moderate_users_user_not_member(self, mock_users_class, mock_community_class):
        """Test user moderation when target user is not a member."""
        # Setup mocks
        mock_community_class.nodes.get.return_value = self.mock_community
        mock_users_class.nodes.get.return_value = self.mock_user
        
        # Mock empty membership list
        self.mock_community.members.all.return_value = []
        
        # Test user moderation (should raise exception)
        with self.assertRaises(AgentCommunityManagementError) as context:
            self.manager.moderate_users(
                agent_uid="agent_123",
                community_uid="community_123",
                action="mute",
                target_user_uid="user_123"
            )
        
        self.assertIn('not a member', str(context.exception))
    
    @patch('agentic.services.community_management.Community')
    def test_fetch_metrics_success(self, mock_community_class):
        """Test successful metrics fetching."""
        # Setup mocks
        mock_community_class.nodes.get.return_value = self.mock_community
        
        # Mock community data for metrics
        self.mock_community.members.all.return_value = [self.mock_membership]
        self.mock_community.communitymessage.all.return_value = []
        self.mock_community.community_post.all.return_value = []
        
        # Test metrics fetching
        result = self.manager.fetch_metrics(
            agent_uid="agent_123",
            community_uid="community_123",
            metric_types=['member_count', 'content_stats']
        )
        
        # Verify authentication and authorization were checked
        self.mock_auth_service.authenticate_agent.assert_called_once_with("agent_123", "community_123")
        self.mock_auth_service.require_permission.assert_called_once_with("agent_123", "community_123", "fetch_metrics")
        
        # Verify action was logged
        self.mock_auth_service.log_agent_action.assert_called_once()
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertIn('metrics', result)
        self.assertIn('member_count', result['metrics'])
        self.assertIn('content_stats', result['metrics'])
    
    @patch('agentic.services.community_management.Community')
    def test_fetch_metrics_default_types(self, mock_community_class):
        """Test metrics fetching with default metric types."""
        # Setup mocks
        mock_community_class.nodes.get.return_value = self.mock_community
        self.mock_community.members.all.return_value = []
        self.mock_community.communitymessage.all.return_value = []
        self.mock_community.community_post.all.return_value = []
        
        # Test metrics fetching without specifying types
        result = self.manager.fetch_metrics(
            agent_uid="agent_123",
            community_uid="community_123"
        )
        
        # Verify default metrics are included
        self.assertTrue(result['success'])
        metrics = result['metrics']
        self.assertIn('member_count', metrics)
        self.assertIn('activity_level', metrics)
        self.assertIn('engagement_stats', metrics)
        self.assertIn('content_stats', metrics)
        self.assertIn('growth_metrics', metrics)
    
    @patch('agentic.services.community_management.Community')
    def test_send_announcement_success(self, mock_community_class):
        """Test successful announcement sending."""
        # Setup mocks
        mock_community_class.nodes.get.return_value = self.mock_community
        self.mock_community.members.all.return_value = [self.mock_membership]
        
        # Test announcement sending
        result = self.manager.send_announcement(
            agent_uid="agent_123",
            community_uid="community_123",
            title="Important Announcement",
            content="This is an important message for all members.",
            target_audience="all"
        )
        
        # Verify authentication and authorization were checked
        self.mock_auth_service.authenticate_agent.assert_called_once_with("agent_123", "community_123")
        self.mock_auth_service.require_permission.assert_called_once_with("agent_123", "community_123", "send_messages")
        
        # Verify action was logged
        self.mock_auth_service.log_agent_action.assert_called_once()
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertIn('Announcement sent successfully', result['message'])
        self.assertIn('announcement_id', result)
        self.assertIn('recipients_count', result)
    
    @patch('agentic.services.community_management.Community')
    def test_send_announcement_admin_audience(self, mock_community_class):
        """Test announcement sending to admin audience only."""
        # Setup mocks
        admin_membership = Mock(spec=Membership)
        admin_membership.is_admin = True
        admin_membership.is_blocked = False
        
        regular_membership = Mock(spec=Membership)
        regular_membership.is_admin = False
        regular_membership.is_blocked = False
        
        mock_community_class.nodes.get.return_value = self.mock_community
        self.mock_community.members.all.return_value = [admin_membership, regular_membership]
        
        # Test announcement sending to admins only
        result = self.manager.send_announcement(
            agent_uid="agent_123",
            community_uid="community_123",
            title="Admin Announcement",
            content="This is for admins only.",
            target_audience="admins"
        )
        
        # Verify result - should only target admin members
        self.assertTrue(result['success'])
        self.assertEqual(result['recipients_count'], 1)  # Only admin member
        self.assertEqual(result['target_audience'], 'admins')
    
    def test_perform_moderation_action_warn(self):
        """Test warning moderation action."""
        result = self.manager._perform_moderation_action(
            self.mock_community, self.mock_membership, self.mock_user,
            'warn', 'Test warning'
        )
        
        self.assertEqual(result['action_performed'], 'warn')
        self.assertTrue(result['warning_issued'])
        self.assertEqual(result['warning_reason'], 'Test warning')
    
    def test_perform_moderation_action_block(self):
        """Test blocking moderation action."""
        result = self.manager._perform_moderation_action(
            self.mock_community, self.mock_membership, self.mock_user,
            'block', 'Inappropriate behavior'
        )
        
        self.assertEqual(result['action_performed'], 'block')
        self.assertTrue(result['user_blocked'])
        self.assertTrue(self.mock_membership.is_blocked)
        self.mock_membership.save.assert_called_once()
    
    def test_perform_moderation_action_remove(self):
        """Test removal moderation action."""
        result = self.manager._perform_moderation_action(
            self.mock_community, self.mock_membership, self.mock_user,
            'remove', 'Violation of rules'
        )
        
        self.assertEqual(result['action_performed'], 'remove')
        self.assertTrue(result['user_removed'])
        self.mock_membership.delete.assert_called_once()
    
    def test_perform_moderation_action_unknown(self):
        """Test unknown moderation action."""
        with self.assertRaises(AgentCommunityManagementError) as context:
            self.manager._perform_moderation_action(
                self.mock_community, self.mock_membership, self.mock_user,
                'unknown_action', 'Test reason'
            )
        
        self.assertIn('Unknown moderation action', str(context.exception))
    
    def test_collect_community_metrics_member_count(self):
        """Test collecting member count metrics."""
        # Setup mock memberships
        admin_membership = Mock(is_blocked=False, is_admin=True, is_leader=False)
        leader_membership = Mock(is_blocked=False, is_admin=False, is_leader=True)
        regular_membership = Mock(is_blocked=False, is_admin=False, is_leader=False)
        blocked_membership = Mock(is_blocked=True, is_admin=False, is_leader=False)
        
        self.mock_community.members.all.return_value = [
            admin_membership, leader_membership, regular_membership, blocked_membership
        ]
        
        # Test metrics collection
        result = self.manager._collect_community_metrics(
            self.mock_community, ['member_count']
        )
        
        # Verify member count metrics
        member_count = result['member_count']
        self.assertEqual(member_count['total_members'], 4)
        self.assertEqual(member_count['active_members'], 3)  # Excluding blocked
        self.assertEqual(member_count['admin_members'], 1)
        self.assertEqual(member_count['leader_members'], 1)
    
    def test_collect_community_metrics_content_stats(self):
        """Test collecting content statistics metrics."""
        # Setup mock content
        self.mock_community.communitymessage.all.return_value = [Mock(), Mock()]
        self.mock_community.community_post.all.return_value = [Mock()]
        
        # Test metrics collection
        result = self.manager._collect_community_metrics(
            self.mock_community, ['content_stats']
        )
        
        # Verify content stats
        content_stats = result['content_stats']
        self.assertEqual(content_stats['total_messages'], 2)
        self.assertEqual(content_stats['total_posts'], 1)
    
    def test_create_and_send_announcement_all_audience(self):
        """Test creating and sending announcement to all members."""
        # Setup mock memberships
        active_membership = Mock(is_blocked=False)
        blocked_membership = Mock(is_blocked=True)
        
        self.mock_community.members.all.return_value = [active_membership, blocked_membership]
        
        # Test announcement creation
        result = self.manager._create_and_send_announcement(
            self.mock_community, "Test Title", "Test Content", "all"
        )
        
        # Verify result
        self.assertIn('announcement_id', result)
        self.assertEqual(result['recipients_count'], 1)  # Only active member
        self.assertEqual(result['delivery_status'], 'sent')
    
    def test_create_and_send_announcement_active_members(self):
        """Test creating and sending announcement to active members only."""
        # Setup mock memberships
        active_membership = Mock(is_blocked=False, can_message=True)
        blocked_membership = Mock(is_blocked=True, can_message=True)
        muted_membership = Mock(is_blocked=False, can_message=False)
        
        self.mock_community.members.all.return_value = [
            active_membership, blocked_membership, muted_membership
        ]
        
        # Test announcement creation
        result = self.manager._create_and_send_announcement(
            self.mock_community, "Test Title", "Test Content", "active_members"
        )
        
        # Verify result - only active members who can message
        self.assertEqual(result['recipients_count'], 1)  # Only active member who can message