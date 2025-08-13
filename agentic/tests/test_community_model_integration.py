# Community Model Integration Tests
# This module contains tests for the Community model agent integration.

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from community.models import Community
from ..models import Agent, AgentCommunityAssignment


class CommunityModelAgentIntegrationTest(TestCase):
    """Test cases for Community model agent integration."""
    
    def setUp(self):
        """Set up test data."""
        # Mock community
        self.mock_community = Mock(spec=Community)
        self.mock_community.uid = "community_123"
        self.mock_community.name = "Test Community"
        
        # Mock agent
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.uid = "agent_123"
        self.mock_agent.name = "Test Agent"
        self.mock_agent.is_active.return_value = True
        
        # Mock assignment
        self.mock_assignment = Mock(spec=AgentCommunityAssignment)
        self.mock_assignment.uid = "assignment_123"
        self.mock_assignment.is_active.return_value = True
        self.mock_assignment.agent.single.return_value = self.mock_agent
    
    def test_get_leader_agent_success(self):
        """Test successful leader agent retrieval."""
        # Setup mock community with leader agent
        self.mock_community.leader_agent.all.return_value = [self.mock_assignment]
        
        # Test the method
        result = Community.get_leader_agent(self.mock_community)
        
        # Verify result
        self.assertEqual(result, self.mock_agent)
        self.mock_community.leader_agent.all.assert_called_once()
        self.mock_assignment.is_active.assert_called_once()
        self.mock_assignment.agent.single.assert_called_once()
    
    def test_get_leader_agent_no_assignments(self):
        """Test leader agent retrieval when no assignments exist."""
        # Setup mock community with no assignments
        self.mock_community.leader_agent.all.return_value = []
        
        # Test the method
        result = Community.get_leader_agent(self.mock_community)
        
        # Verify result
        self.assertIsNone(result)
    
    def test_get_leader_agent_inactive_assignment(self):
        """Test leader agent retrieval when assignment is inactive."""
        # Setup mock assignment as inactive
        self.mock_assignment.is_active.return_value = False
        self.mock_community.leader_agent.all.return_value = [self.mock_assignment]
        
        # Test the method
        result = Community.get_leader_agent(self.mock_community)
        
        # Verify result
        self.assertIsNone(result)
    
    def test_get_leader_agent_inactive_agent(self):
        """Test leader agent retrieval when agent is inactive."""
        # Setup mock agent as inactive
        self.mock_agent.is_active.return_value = False
        self.mock_community.leader_agent.all.return_value = [self.mock_assignment]
        
        # Test the method
        result = Community.get_leader_agent(self.mock_community)
        
        # Verify result
        self.assertIsNone(result)
    
    def test_get_leader_agent_exception_handling(self):
        """Test leader agent retrieval with exception handling."""
        # Setup mock to raise exception
        self.mock_community.leader_agent.all.side_effect = Exception("Database error")
        
        # Test the method
        result = Community.get_leader_agent(self.mock_community)
        
        # Verify result (should return None on exception)
        self.assertIsNone(result)
    
    def test_has_leader_agent_true(self):
        """Test has_leader_agent when community has an active leader."""
        # Mock get_leader_agent to return an agent
        with patch.object(Community, 'get_leader_agent', return_value=self.mock_agent):
            result = Community.has_leader_agent(self.mock_community)
            self.assertTrue(result)
    
    def test_has_leader_agent_false(self):
        """Test has_leader_agent when community has no leader."""
        # Mock get_leader_agent to return None
        with patch.object(Community, 'get_leader_agent', return_value=None):
            result = Community.has_leader_agent(self.mock_community)
            self.assertFalse(result)
    
    def test_get_agent_assignments_success(self):
        """Test successful agent assignments retrieval."""
        # Setup mock community with assignments
        assignments = [self.mock_assignment, Mock()]
        self.mock_community.leader_agent.all.return_value = assignments
        
        # Test the method
        result = Community.get_agent_assignments(self.mock_community)
        
        # Verify result
        self.assertEqual(result, assignments)
        self.mock_community.leader_agent.all.assert_called_once()
    
    def test_get_agent_assignments_empty(self):
        """Test agent assignments retrieval when no assignments exist."""
        # Setup mock community with no assignments
        self.mock_community.leader_agent.all.return_value = []
        
        # Test the method
        result = Community.get_agent_assignments(self.mock_community)
        
        # Verify result
        self.assertEqual(result, [])
    
    def test_get_agent_assignments_exception_handling(self):
        """Test agent assignments retrieval with exception handling."""
        # Setup mock to raise exception
        self.mock_community.leader_agent.all.side_effect = Exception("Database error")
        
        # Test the method
        result = Community.get_agent_assignments(self.mock_community)
        
        # Verify result (should return empty list on exception)
        self.assertEqual(result, [])


class CommunityTypeAgentIntegrationTest(TestCase):
    """Test cases for CommunityType GraphQL type agent integration."""
    
    def setUp(self):
        """Set up test data."""
        # Mock community
        self.mock_community = Mock(spec=Community)
        self.mock_community.uid = "community_123"
        self.mock_community.name = "Test Community"
        self.mock_community.description = "A test community"
        self.mock_community.community_type = "interest"
        self.mock_community.community_circle = "outer"
        self.mock_community.room_id = "room_123"
        self.mock_community.created_date = Mock()
        self.mock_community.updated_date = Mock()
        self.mock_community.number_of_members = 5
        self.mock_community.group_invite_link = "invite_link"
        self.mock_community.group_icon_id = None
        self.mock_community.cover_image_id = None
        self.mock_community.category = "test"
        self.mock_community.generated_community = False
        self.mock_community.created_by.single.return_value = None
        self.mock_community.communitymessage = []
        self.mock_community.community_review = []
        self.mock_community.members.all.return_value = []
        
        # Mock agent methods
        self.mock_community.has_leader_agent.return_value = True
        self.mock_community.get_leader_agent.return_value = Mock()
        self.mock_community.get_agent_assignments.return_value = [Mock()]
    
    @patch('community.graphql.types.generate_presigned_url')
    def test_community_type_from_neomodel_with_agent_fields(self, mock_generate_url):
        """Test CommunityType conversion includes agent fields."""
        from community.graphql.types import CommunityType
        
        # Mock file URL generation
        mock_generate_url.generate_file_info.return_value = None
        
        # Mock the agent-related methods
        with patch.object(CommunityType, '_get_leader_agent', return_value=Mock()) as mock_get_leader, \
             patch.object(CommunityType, '_get_agent_assignments', return_value=[Mock()]) as mock_get_assignments:
            
            # Test conversion
            result = CommunityType.from_neomodel(self.mock_community)
            
            # Verify agent fields are included
            self.assertIsNotNone(result.leader_agent)
            self.assertTrue(result.has_leader_agent)
            self.assertEqual(len(result.agent_assignments), 1)
            
            # Verify helper methods were called
            mock_get_leader.assert_called_once_with(self.mock_community)
            mock_get_assignments.assert_called_once_with(self.mock_community)
    
    def test_get_leader_agent_helper_success(self):
        """Test _get_leader_agent helper method success."""
        from community.graphql.types import CommunityType
        
        # Mock agent and AgentType
        mock_agent = Mock()
        self.mock_community.get_leader_agent.return_value = mock_agent
        
        with patch('community.graphql.types.AgentType') as mock_agent_type:
            mock_agent_type.from_neomodel.return_value = Mock()
            
            # Test the helper method
            result = CommunityType._get_leader_agent(self.mock_community)
            
            # Verify result
            self.assertIsNotNone(result)
            mock_agent_type.from_neomodel.assert_called_once_with(mock_agent)
    
    def test_get_leader_agent_helper_no_agent(self):
        """Test _get_leader_agent helper method when no agent exists."""
        from community.graphql.types import CommunityType
        
        # Mock community with no leader agent
        self.mock_community.get_leader_agent.return_value = None
        
        # Test the helper method
        result = CommunityType._get_leader_agent(self.mock_community)
        
        # Verify result
        self.assertIsNone(result)
    
    def test_get_leader_agent_helper_exception_handling(self):
        """Test _get_leader_agent helper method exception handling."""
        from community.graphql.types import CommunityType
        
        # Mock community to raise exception
        self.mock_community.get_leader_agent.side_effect = Exception("Import error")
        
        # Test the helper method
        result = CommunityType._get_leader_agent(self.mock_community)
        
        # Verify result (should return None on exception)
        self.assertIsNone(result)
    
    def test_get_agent_assignments_helper_success(self):
        """Test _get_agent_assignments helper method success."""
        from community.graphql.types import CommunityType
        
        # Mock assignments
        mock_assignments = [Mock(), Mock()]
        self.mock_community.get_agent_assignments.return_value = mock_assignments
        
        with patch('community.graphql.types.AgentAssignmentType') as mock_assignment_type:
            mock_assignment_type.from_neomodel.return_value = Mock()
            
            # Test the helper method
            result = CommunityType._get_agent_assignments(self.mock_community)
            
            # Verify result
            self.assertEqual(len(result), 2)
            self.assertEqual(mock_assignment_type.from_neomodel.call_count, 2)
    
    def test_get_agent_assignments_helper_empty(self):
        """Test _get_agent_assignments helper method with no assignments."""
        from community.graphql.types import CommunityType
        
        # Mock community with no assignments
        self.mock_community.get_agent_assignments.return_value = []
        
        # Test the helper method
        result = CommunityType._get_agent_assignments(self.mock_community)
        
        # Verify result
        self.assertEqual(result, [])
    
    def test_get_agent_assignments_helper_exception_handling(self):
        """Test _get_agent_assignments helper method exception handling."""
        from community.graphql.types import CommunityType
        
        # Mock community to raise exception
        self.mock_community.get_agent_assignments.side_effect = Exception("Import error")
        
        # Test the helper method
        result = CommunityType._get_agent_assignments(self.mock_community)
        
        # Verify result (should return empty list on exception)
        self.assertEqual(result, [])