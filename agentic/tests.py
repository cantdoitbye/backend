# Agentic Models Tests
# This module contains unit tests for all agentic models and their functionality.

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from .models import Agent, AgentCommunityAssignment, AgentActionLog, AgentMemory
from auth_manager.models import Users
from community.models import Community


class AgentModelTest(TestCase):
    """Test cases for the Agent model."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user for agent creation
        self.test_user = Users(
            user_id="test_user_123",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        self.test_user.save()
    
    def test_agent_creation(self):
        """Test basic agent creation with required fields."""
        agent = Agent(
            name="Test Community Leader",
            description="A test agent for community leadership",
            agent_type="COMMUNITY_LEADER",
            capabilities=["edit_community", "moderate_users", "fetch_metrics"]
        )
        agent.save()
        
        # Verify agent was created with correct properties
        self.assertEqual(agent.name, "Test Community Leader")
        self.assertEqual(agent.agent_type, "COMMUNITY_LEADER")
        self.assertEqual(agent.status, "ACTIVE")  # Default status
        self.assertEqual(agent.version, "1.0")    # Default version
        self.assertIsNotNone(agent.uid)
        self.assertIsNotNone(agent.created_date)
        self.assertIsNotNone(agent.updated_date)
    
    def test_agent_with_relationships(self):
        """Test agent creation with user relationships."""
        agent = Agent(
            name="Test Agent",
            agent_type="MODERATOR",
            capabilities=["moderate_users"]
        )
        agent.save()
        
        # Connect agent to creator
        agent.created_by.connect(self.test_user)
        
        # Verify relationship
        creator = agent.created_by.single()
        self.assertEqual(creator.email, self.test_user.email)
    
    def test_agent_is_active(self):
        """Test agent active status checking."""
        # Test active agent
        active_agent = Agent(name="Active Agent", agent_type="ASSISTANT", status="ACTIVE")
        active_agent.save()
        self.assertTrue(active_agent.is_active())
        
        # Test inactive agent
        inactive_agent = Agent(name="Inactive Agent", agent_type="ASSISTANT", status="INACTIVE")
        inactive_agent.save()
        self.assertFalse(inactive_agent.is_active())
    
    def test_agent_has_capability(self):
        """Test agent capability checking."""
        agent = Agent(
            name="Test Agent",
            agent_type="COMMUNITY_LEADER",
            capabilities=["edit_community", "moderate_users"]
        )
        agent.save()
        
        # Test existing capabilities
        self.assertTrue(agent.has_capability("edit_community"))
        self.assertTrue(agent.has_capability("moderate_users"))
        
        # Test non-existing capability
        self.assertFalse(agent.has_capability("delete_community"))
    
    def test_agent_save_updates_timestamp(self):
        """Test that saving an agent updates the updated_date timestamp."""
        agent = Agent(name="Test Agent", agent_type="ASSISTANT")
        agent.save()
        
        original_updated_date = agent.updated_date
        
        # Simulate time passing and update
        with patch('agentic.models.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 2, 12, 0, 0)
            agent.description = "Updated description"
            agent.save()
        
        # Verify timestamp was updated
        self.assertNotEqual(agent.updated_date, original_updated_date)
    
    def test_agent_string_representation(self):
        """Test agent string representation."""
        agent = Agent(name="Test Agent", agent_type="MODERATOR")
        agent.save()
        
        expected_str = "Test Agent (MODERATOR)"
        self.assertEqual(str(agent), expected_str)


class AgentCommunityAssignmentModelTest(TestCase):
    """Test cases for the AgentCommunityAssignment model."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.test_user = Users(
            user_id="test_user_123",
            username="testuser",
            email="test@example.com"
        )
        self.test_user.save()
        
        # Create test agent
        self.test_agent = Agent(
            name="Test Agent",
            agent_type="COMMUNITY_LEADER",
            capabilities=["edit_community", "moderate_users"]
        )
        self.test_agent.save()
        
        # Create test community
        self.test_community = Community(
            name="Test Community",
            description="A test community",
            community_circle="outer"
        )
        self.test_community.save()
    
    def test_assignment_creation(self):
        """Test basic assignment creation."""
        assignment = AgentCommunityAssignment()
        assignment.save()
        
        # Connect relationships
        assignment.agent.connect(self.test_agent)
        assignment.community.connect(self.test_community)
        assignment.assigned_by.connect(self.test_user)
        
        # Verify assignment properties
        self.assertEqual(assignment.status, "ACTIVE")  # Default status
        self.assertIsNotNone(assignment.uid)
        self.assertIsNotNone(assignment.assignment_date)
        self.assertIsNotNone(assignment.created_date)
        self.assertIsNotNone(assignment.updated_date)
    
    def test_assignment_is_active(self):
        """Test assignment active status checking."""
        # Test active assignment
        active_assignment = AgentCommunityAssignment(status="ACTIVE")
        active_assignment.save()
        self.assertTrue(active_assignment.is_active())
        
        # Test inactive assignment
        inactive_assignment = AgentCommunityAssignment(status="INACTIVE")
        inactive_assignment.save()
        self.assertFalse(inactive_assignment.is_active())
    
    def test_assignment_effective_permissions(self):
        """Test effective permissions calculation."""
        assignment = AgentCommunityAssignment(
            permissions=["custom_permission", "edit_community"]  # edit_community overlaps with agent capabilities
        )
        assignment.save()
        assignment.agent.connect(self.test_agent)
        
        effective_permissions = assignment.get_effective_permissions()
        
        # Should include both agent capabilities and assignment permissions, deduplicated
        expected_permissions = {"edit_community", "moderate_users", "custom_permission"}
        self.assertEqual(set(effective_permissions), expected_permissions)
    
    def test_assignment_has_permission(self):
        """Test permission checking for assignments."""
        assignment = AgentCommunityAssignment(permissions=["custom_permission"])
        assignment.save()
        assignment.agent.connect(self.test_agent)
        
        # Test agent capability
        self.assertTrue(assignment.has_permission("edit_community"))
        
        # Test assignment-specific permission
        self.assertTrue(assignment.has_permission("custom_permission"))
        
        # Test non-existing permission
        self.assertFalse(assignment.has_permission("non_existing_permission"))
    
    def test_assignment_string_representation(self):
        """Test assignment string representation."""
        assignment = AgentCommunityAssignment()
        assignment.save()
        assignment.agent.connect(self.test_agent)
        assignment.community.connect(self.test_community)
        
        expected_str = "Test Agent -> Test Community (ACTIVE)"
        self.assertEqual(str(assignment), expected_str)


class AgentActionLogModelTest(TestCase):
    """Test cases for the AgentActionLog model."""
    
    def test_action_log_creation(self):
        """Test basic action log creation."""
        log = AgentActionLog.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="edit_community",
            action_details={"field": "description", "old_value": "old", "new_value": "new"},
            success=True
        )
        
        # Verify log properties
        self.assertEqual(log.agent_uid, "agent_123")
        self.assertEqual(log.community_uid, "community_456")
        self.assertEqual(log.action_type, "edit_community")
        self.assertTrue(log.success)
        self.assertIsNotNone(log.timestamp)
    
    def test_action_log_with_error(self):
        """Test action log creation with error details."""
        log = AgentActionLog.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="moderate_user",
            action_details={"user_id": "user_789", "action": "ban"},
            success=False,
            error_message="User not found"
        )
        
        # Verify error handling
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "User not found")
    
    def test_action_log_string_representation(self):
        """Test action log string representation."""
        log = AgentActionLog.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            action_type="fetch_metrics",
            action_details={},
            success=True
        )
        
        expected_str = "fetch_metrics by agent_123 in community_456 - SUCCESS"
        self.assertEqual(str(log), expected_str)


class AgentMemoryModelTest(TestCase):
    """Test cases for the AgentMemory model."""
    
    def test_memory_creation(self):
        """Test basic memory creation."""
        memory = AgentMemory.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context",
            content={"current_topic": "community_rules", "last_action": "edit_description"}
        )
        
        # Verify memory properties
        self.assertEqual(memory.agent_uid, "agent_123")
        self.assertEqual(memory.community_uid, "community_456")
        self.assertEqual(memory.memory_type, "context")
        self.assertIsNotNone(memory.created_date)
        self.assertIsNotNone(memory.updated_date)
    
    def test_memory_expiration(self):
        """Test memory expiration functionality."""
        # Test non-expiring memory
        permanent_memory = AgentMemory.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="knowledge",
            content={"learned_fact": "Community prefers morning meetings"}
        )
        self.assertFalse(permanent_memory.is_expired())
        
        # Test expired memory
        expired_memory = AgentMemory.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context",
            content={"session_data": "temporary"},
            expires_at=timezone.now() - timedelta(hours=1)  # Expired 1 hour ago
        )
        self.assertTrue(expired_memory.is_expired())
        
        # Test future expiration
        future_memory = AgentMemory.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context",
            content={"session_data": "temporary"},
            expires_at=timezone.now() + timedelta(hours=1)  # Expires in 1 hour
        )
        self.assertFalse(future_memory.is_expired())
    
    def test_memory_unique_constraint(self):
        """Test that memory type is unique per agent-community pair."""
        # Create first memory
        AgentMemory.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="context",
            content={"data": "first"}
        )
        
        # Attempting to create duplicate should raise IntegrityError
        with self.assertRaises(Exception):  # Django will raise IntegrityError
            AgentMemory.objects.create(
                agent_uid="agent_123",
                community_uid="community_456",
                memory_type="context",
                content={"data": "second"}
            )
    
    def test_memory_string_representation(self):
        """Test memory string representation."""
        memory = AgentMemory.objects.create(
            agent_uid="agent_123",
            community_uid="community_456",
            memory_type="conversation",
            content={"messages": []}
        )
        
        expected_str = "conversation memory for agent_123 in community_456"
        self.assertEqual(str(memory), expected_str)


# Integration tests for model relationships
class AgentModelIntegrationTest(TestCase):
    """Integration tests for agent model relationships."""
    
    def setUp(self):
        """Set up test data for integration tests."""
        self.test_user = Users(
            user_id="test_user_123",
            username="testuser",
            email="test@example.com"
        )
        self.test_user.save()
        
        self.test_community = Community(
            name="Test Community",
            description="A test community"
        )
        self.test_community.save()
    
    def test_complete_agent_assignment_workflow(self):
        """Test the complete workflow of creating agent and assigning to community."""
        # Create agent
        agent = Agent(
            name="Integration Test Agent",
            agent_type="COMMUNITY_LEADER",
            capabilities=["edit_community", "moderate_users", "fetch_metrics"]
        )
        agent.save()
        agent.created_by.connect(self.test_user)
        
        # Create assignment
        assignment = AgentCommunityAssignment(
            permissions=["custom_admin_permission"]
        )
        assignment.save()
        assignment.agent.connect(agent)
        assignment.community.connect(self.test_community)
        assignment.assigned_by.connect(self.test_user)
        
        # Connect assignment to agent
        agent.assigned_communities.connect(assignment)
        
        # Verify complete relationship chain
        retrieved_agent = Agent.nodes.get(uid=agent.uid)
        assignments = list(retrieved_agent.assigned_communities.all())
        self.assertEqual(len(assignments), 1)
        
        assignment = assignments[0]
        self.assertTrue(assignment.is_active())
        self.assertTrue(assignment.has_permission("edit_community"))
        self.assertTrue(assignment.has_permission("custom_admin_permission"))
        
        # Verify community relationship
        assigned_community = assignment.community.single()
        self.assertEqual(assigned_community.name, "Test Community")
        
        # Create action log for this assignment
        AgentActionLog.objects.create(
            agent_uid=agent.uid,
            community_uid=self.test_community.uid,
            action_type="edit_community",
            action_details={"field": "description", "new_value": "Updated by agent"},
            success=True
        )
        
        # Create memory for this assignment
        AgentMemory.objects.create(
            agent_uid=agent.uid,
            community_uid=self.test_community.uid,
            memory_type="context",
            content={"last_edit": "description", "timestamp": "2024-01-01T12:00:00Z"}
        )
        
        # Verify logs and memory exist
        logs = AgentActionLog.objects.filter(agent_uid=agent.uid)
        self.assertEqual(logs.count(), 1)
        
        memories = AgentMemory.objects.filter(agent_uid=agent.uid)
        self.assertEqual(memories.count(), 1)