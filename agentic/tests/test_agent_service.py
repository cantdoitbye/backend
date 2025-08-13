# Agent Service Tests
# This module contains unit tests for the AgentService class.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from ..services.agent_service import (
    AgentService, AgentServiceError, AgentNotFoundError, 
    CommunityNotFoundError, UserNotFoundError, CommunityAlreadyHasLeaderError
)
from ..models import Agent, AgentCommunityAssignment
from community.models import Community
from auth_manager.models import Users


class AgentServiceTest(TestCase):
    """Test cases for the AgentService class."""
    
    def setUp(self):
        """Set up test data."""
        self.agent_service = AgentService()
        
        # Mock objects for testing
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.uid = "agent_123"
        self.mock_agent.name = "Test Agent"
        self.mock_agent.agent_type = "COMMUNITY_LEADER"
        self.mock_agent.status = "ACTIVE"
        self.mock_agent.capabilities = ["edit_community", "moderate_users"]
        self.mock_agent.is_active.return_value = True
        self.mock_agent.has_capability.return_value = True
        
        self.mock_community = Mock()
        self.mock_community.uid = "community_456"
        self.mock_community.name = "Test Community"
        
        self.mock_user = Mock()
        self.mock_user.uid = "user_789"
        self.mock_user.username = "testuser"
        
        self.mock_assignment = Mock(spec=AgentCommunityAssignment)
        self.mock_assignment.uid = "assignment_101"
        self.mock_assignment.status = "ACTIVE"
        self.mock_assignment.is_active.return_value = True
    
    @patch('agentic.services.agent_service.Agent')
    @patch('agentic.services.agent_service.Users')
    def test_create_agent_success(self, mock_users, mock_agent_class):
        """Test successful agent creation."""
        # Setup mocks
        mock_agent_instance = Mock(spec=Agent)
        mock_agent_instance.uid = "new_agent_123"
        mock_agent_class.return_value = mock_agent_instance
        
        mock_creator = Mock()
        mock_users.nodes.get.return_value = mock_creator
        
        # Test agent creation
        result = self.agent_service.create_agent(
            name="New Test Agent",
            agent_type="COMMUNITY_LEADER",
            capabilities=["edit_community", "moderate_users"],
            description="A test agent",
            created_by_uid="creator_123"
        )
        
        # Verify agent was created with correct parameters
        mock_agent_class.assert_called_once()
        mock_agent_instance.save.assert_called_once()
        mock_agent_instance.created_by.connect.assert_called_once_with(mock_creator)
        
        self.assertEqual(result, mock_agent_instance)
    
    def test_create_agent_invalid_type(self):
        """Test agent creation with invalid agent type."""
        with self.assertRaises(AgentServiceError) as context:
            self.agent_service.create_agent(
                name="Invalid Agent",
                agent_type="INVALID_TYPE",
                capabilities=["some_capability"]
            )
        
        self.assertIn("Invalid agent type", str(context.exception))
    
    def test_create_agent_no_capabilities(self):
        """Test agent creation without capabilities."""
        with self.assertRaises(AgentServiceError) as context:
            self.agent_service.create_agent(
                name="No Capabilities Agent",
                agent_type="ASSISTANT",
                capabilities=[]
            )
        
        self.assertIn("must have at least one capability", str(context.exception))
    
    @patch('agentic.services.agent_service.Agent')
    @patch('agentic.services.agent_service.Community')
    @patch('agentic.services.agent_service.Users')
    @patch('agentic.services.agent_service.AgentCommunityAssignment')
    def test_assign_agent_to_community_success(self, mock_assignment_class, mock_users, mock_community_class, mock_agent_class):
        """Test successful agent assignment to community."""
        # Setup mocks
        mock_agent_class.nodes.get.return_value = self.mock_agent
        mock_community_class.nodes.get.return_value = self.mock_community
        mock_users.nodes.get.return_value = self.mock_user
        
        mock_assignment_instance = Mock(spec=AgentCommunityAssignment)
        mock_assignment_instance.uid = "new_assignment_123"
        mock_assignment_class.return_value = mock_assignment_instance
        
        # Mock get_community_leader to return None (no existing leader)
        with patch.object(self.agent_service, 'get_community_leader', return_value=None):
            result = self.agent_service.assign_agent_to_community(
                agent_uid="agent_123",
                community_uid="community_456",
                assigned_by_uid="user_789",
                permissions=["custom_permission"]
            )
        
        # Verify assignment was created and connected
        mock_assignment_class.assert_called_once()
        mock_assignment_instance.save.assert_called_once()
        mock_assignment_instance.agent.connect.assert_called_once_with(self.mock_agent)
        mock_assignment_instance.community.connect.assert_called_once_with(self.mock_community)
        mock_assignment_instance.assigned_by.connect.assert_called_once_with(self.mock_user)
        self.mock_agent.assigned_communities.connect.assert_called_once_with(mock_assignment_instance)
        
        self.assertEqual(result, mock_assignment_instance)
    
    @patch('agentic.services.agent_service.Agent')
    def test_assign_agent_not_found(self, mock_agent_class):
        """Test agent assignment when agent doesn't exist."""
        mock_agent_class.nodes.get.side_effect = Agent.DoesNotExist("Agent not found")
        
        with self.assertRaises(AgentNotFoundError) as context:
            self.agent_service.assign_agent_to_community(
                agent_uid="nonexistent_agent",
                community_uid="community_456",
                assigned_by_uid="user_789"
            )
        
        self.assertIn("Agent nonexistent_agent not found", str(context.exception))
    
    @patch('agentic.services.agent_service.Agent')
    @patch('agentic.services.agent_service.Community')
    def test_assign_agent_community_not_found(self, mock_community_class, mock_agent_class):
        """Test agent assignment when community doesn't exist."""
        mock_agent_class.nodes.get.return_value = self.mock_agent
        mock_community_class.nodes.get.side_effect = Community.DoesNotExist("Community not found")
        
        with self.assertRaises(CommunityNotFoundError) as context:
            self.agent_service.assign_agent_to_community(
                agent_uid="agent_123",
                community_uid="nonexistent_community",
                assigned_by_uid="user_789"
            )
        
        self.assertIn("Community nonexistent_community not found", str(context.exception))
    
    @patch('agentic.services.agent_service.Agent')
    @patch('agentic.services.agent_service.Community')
    @patch('agentic.services.agent_service.Users')
    def test_assign_agent_community_has_leader(self, mock_users_class, mock_community_class, mock_agent_class):
        """Test agent assignment when community already has a leader."""
        mock_agent_class.nodes.get.return_value = self.mock_agent
        mock_community_class.nodes.get.return_value = self.mock_community
        mock_users_class.nodes.get.return_value = self.mock_user
        
        # Mock get_community_leader to return existing leader
        existing_leader = Mock()
        existing_leader.uid = "existing_leader_123"
        
        with patch.object(self.agent_service, 'get_community_leader', return_value=existing_leader):
            with self.assertRaises(CommunityAlreadyHasLeaderError) as context:
                self.agent_service.assign_agent_to_community(
                    agent_uid="agent_123",
                    community_uid="community_456",
                    assigned_by_uid="user_789"
                )
        
        self.assertIn("already has an active leader", str(context.exception))
    
    @patch('agentic.services.agent_service.Community')
    @patch('agentic.services.agent_service.AgentCommunityAssignment')
    def test_get_community_leader_success(self, mock_assignment_class, mock_community_class):
        """Test successful retrieval of community leader."""
        mock_community_class.nodes.get.return_value = self.mock_community
        
        # Mock assignment with active leader
        mock_assignment = Mock()
        mock_assignment.community.single.return_value = self.mock_community
        mock_assignment.is_active.return_value = True
        mock_assignment.agent.single.return_value = self.mock_agent
        
        mock_assignment_class.nodes.all.return_value = [mock_assignment]
        
        result = self.agent_service.get_community_leader("community_456")
        
        self.assertEqual(result, self.mock_agent)
    
    @patch('agentic.services.agent_service.Community')
    @patch('agentic.services.agent_service.AgentCommunityAssignment')
    def test_get_community_leader_none_found(self, mock_assignment_class, mock_community_class):
        """Test community leader retrieval when no leader exists."""
        mock_community_class.nodes.get.return_value = self.mock_community
        mock_assignment_class.nodes.all.return_value = []
        
        result = self.agent_service.get_community_leader("community_456")
        
        self.assertIsNone(result)
    
    @patch('agentic.services.agent_service.Community')
    def test_get_community_leader_community_not_found(self, mock_community_class):
        """Test community leader retrieval when community doesn't exist."""
        mock_community_class.nodes.get.side_effect = Community.DoesNotExist("Community not found")
        
        with self.assertRaises(CommunityNotFoundError) as context:
            self.agent_service.get_community_leader("nonexistent_community")
        
        self.assertIn("Community nonexistent_community not found", str(context.exception))
    
    @patch('agentic.services.agent_service.AgentCommunityAssignment')
    def test_update_agent_assignment_success(self, mock_assignment_class):
        """Test successful assignment update."""
        mock_assignment_class.nodes.get.return_value = self.mock_assignment
        
        result = self.agent_service.update_agent_assignment(
            assignment_uid="assignment_101",
            status="INACTIVE",
            permissions=["new_permission"]
        )
        
        self.assertEqual(self.mock_assignment.status, "INACTIVE")
        self.assertEqual(self.mock_assignment.permissions, ["new_permission"])
        self.mock_assignment.save.assert_called_once()
        self.assertEqual(result, self.mock_assignment)
    
    @patch('agentic.services.agent_service.AgentCommunityAssignment')
    def test_update_agent_assignment_not_found(self, mock_assignment_class):
        """Test assignment update when assignment doesn't exist."""
        mock_assignment_class.nodes.get.side_effect = AgentCommunityAssignment.DoesNotExist("Assignment not found")
        
        with self.assertRaises(AgentServiceError) as context:
            self.agent_service.update_agent_assignment(
                assignment_uid="nonexistent_assignment",
                status="INACTIVE"
            )
        
        self.assertIn("Assignment nonexistent_assignment not found", str(context.exception))
    
    def test_update_agent_assignment_invalid_status(self):
        """Test assignment update with invalid status."""
        with patch.object(self.agent_service, 'update_agent_assignment') as mock_update:
            mock_update.side_effect = AgentServiceError("Invalid status")
            
            with self.assertRaises(AgentServiceError) as context:
                self.agent_service.update_agent_assignment(
                    assignment_uid="assignment_101",
                    status="INVALID_STATUS"
                )
    
    def test_deactivate_agent_assignment_success(self):
        """Test successful assignment deactivation."""
        with patch.object(self.agent_service, 'update_agent_assignment') as mock_update:
            mock_update.return_value = self.mock_assignment
            
            result = self.agent_service.deactivate_agent_assignment("assignment_101")
            
            mock_update.assert_called_once_with("assignment_101", status='INACTIVE')
            self.assertTrue(result)
    
    @patch('agentic.services.agent_service.Agent')
    def test_get_agent_assignments_success(self, mock_agent_class):
        """Test successful retrieval of agent assignments."""
        mock_agent_class.nodes.get.return_value = self.mock_agent
        self.mock_agent.assigned_communities.all.return_value = [self.mock_assignment]
        
        result = self.agent_service.get_agent_assignments("agent_123")
        
        self.assertEqual(result, [self.mock_assignment])
    
    @patch('agentic.services.agent_service.Agent')
    def test_get_agent_assignments_agent_not_found(self, mock_agent_class):
        """Test agent assignments retrieval when agent doesn't exist."""
        mock_agent_class.nodes.get.side_effect = Agent.DoesNotExist("Agent not found")
        
        with self.assertRaises(AgentNotFoundError) as context:
            self.agent_service.get_agent_assignments("nonexistent_agent")
        
        self.assertIn("Agent nonexistent_agent not found", str(context.exception))
    
    @patch('agentic.services.agent_service.Agent')
    def test_get_default_community_agent_success(self, mock_agent_class):
        """Test successful retrieval of default community agent."""
        mock_agent_class.nodes.filter.return_value = [self.mock_agent]
        
        result = self.agent_service.get_default_community_agent()
        
        self.assertEqual(result, self.mock_agent)
        mock_agent_class.nodes.filter.assert_called_once_with(
            agent_type='COMMUNITY_LEADER',
            status='ACTIVE'
        )
    
    @patch('agentic.services.agent_service.Agent')
    def test_get_default_community_agent_none_found(self, mock_agent_class):
        """Test default community agent retrieval when none available."""
        mock_agent_class.nodes.filter.return_value = []
        
        result = self.agent_service.get_default_community_agent()
        
        self.assertIsNone(result)
    
    @patch('agentic.services.agent_service.Agent')
    def test_get_agent_by_uid_success(self, mock_agent_class):
        """Test successful agent retrieval by UID."""
        mock_agent_class.nodes.get.return_value = self.mock_agent
        
        result = self.agent_service.get_agent_by_uid("agent_123")
        
        self.assertEqual(result, self.mock_agent)
        mock_agent_class.nodes.get.assert_called_once_with(uid="agent_123")
    
    @patch('agentic.services.agent_service.Agent')
    def test_get_agent_by_uid_not_found(self, mock_agent_class):
        """Test agent retrieval by UID when agent doesn't exist."""
        mock_agent_class.nodes.get.side_effect = Agent.DoesNotExist("Agent not found")
        
        with self.assertRaises(AgentNotFoundError) as context:
            self.agent_service.get_agent_by_uid("nonexistent_agent")
        
        self.assertIn("Agent nonexistent_agent not found", str(context.exception))
    
    def test_update_agent_success(self):
        """Test successful agent update."""
        with patch.object(self.agent_service, 'get_agent_by_uid') as mock_get:
            mock_get.return_value = self.mock_agent
            
            result = self.agent_service.update_agent(
                agent_uid="agent_123",
                name="Updated Agent Name",
                description="Updated description",
                capabilities=["new_capability"],
                status="INACTIVE"
            )
            
            self.assertEqual(self.mock_agent.name, "Updated Agent Name")
            self.assertEqual(self.mock_agent.description, "Updated description")
            self.assertEqual(self.mock_agent.capabilities, ["new_capability"])
            self.assertEqual(self.mock_agent.status, "INACTIVE")
            self.mock_agent.save.assert_called_once()
            self.assertEqual(result, self.mock_agent)