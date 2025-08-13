# Integration Tests for Complete Agent Workflows
# This module contains end-to-end integration tests for agent workflows.

import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from community.models import Community, Membership
from auth_manager.models import Users, Profile
from ..models import Agent, AgentCommunityAssignment, AgentActionLog, AgentMemory
from ..services.agent_service import AgentService
from ..services.auth_service import AgentAuthService
from ..services.memory_service import AgentMemoryService
from ..services.notification_integration import AgentNotificationService
from ..services.audit_service import audit_service
from ..exceptions import (
    AgentNotFoundError, CommunityNotFoundError, AgentAuthorizationError,
    CommunityAlreadyHasLeaderError
)


class AgentWorkflowIntegrationTest(TransactionTestCase):
    """
    Integration tests for complete agent workflows.
    
    These tests verify that all components work together correctly
    in realistic scenarios.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = Users(
            uid='test-user-123',
            username='testuser',
            email='test@example.com'
        )
        self.user.save()
        
        # Create user profile
        self.profile = Profile(
            uid='test-profile-123',
            device_id='test-device-123'
        )
        self.profile.save()
        self.profile.user.connect(self.user)
        
        # Create test community
        self.community = Community(
            uid='test-community-123',
            name='Test Community',
            description='A test community',
            is_private=False
        )
        self.community.save()
        
        # Create community membership
        self.membership = Membership(
            uid='test-membership-123',
            is_admin=True,
            is_blocked=False,
            is_notification_muted=False
        )
        self.membership.save()
        self.membership.user.connect(self.user)
        self.membership.community.connect(self.community)
        self.community.members.connect(self.membership)
        
        # Initialize services
        self.agent_service = AgentService()
        self.auth_service = AgentAuthService()
        self.memory_service = AgentMemoryService()
        self.notification_service = AgentNotificationService()
    
    def test_complete_agent_creation_and_assignment_workflow(self):
        """Test the complete workflow of creating and assigning an agent."""
        # Step 1: Create an agent
        agent = self.agent_service.create_agent(
            name='Test Leader Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community', 'moderate_users', 'send_messages'],
            description='A test community leader agent',
            created_by_uid=self.user.uid
        )
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'Test Leader Agent')
        self.assertEqual(agent.agent_type, 'COMMUNITY_LEADER')
        self.assertIn('edit_community', agent.capabilities)
        
        # Step 2: Assign agent to community
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid,
            permissions=['manage_events']
        )
        
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.status, 'ACTIVE')
        self.assertIn('manage_events', assignment.permissions)
        
        # Step 3: Verify agent can authenticate
        is_authenticated = self.auth_service.authenticate_agent(
            agent_uid=agent.uid,
            community_uid=self.community.uid
        )
        
        self.assertTrue(is_authenticated)
        
        # Step 4: Verify agent has correct permissions
        has_permission = self.auth_service.check_permission(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            permission='edit_community'
        )
        
        self.assertTrue(has_permission)
        
        # Step 5: Test agent action logging
        self.auth_service.log_agent_action(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            action_type='edit_community',
            details={'field': 'description', 'old_value': 'old', 'new_value': 'new'},
            success=True
        )
        
        # Verify action was logged
        logs = AgentActionLog.objects.filter(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            action_type='edit_community'
        )
        self.assertEqual(logs.count(), 1)
        
        # Step 6: Store agent memory
        context_data = {'last_action': 'community_update', 'timestamp': timezone.now().isoformat()}
        memory = self.memory_service.store_context(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            context=context_data
        )
        
        self.assertIsNotNone(memory)
        
        # Step 7: Retrieve agent memory
        retrieved_context = self.memory_service.retrieve_context(
            agent_uid=agent.uid,
            community_uid=self.community.uid
        )
        
        self.assertEqual(retrieved_context['last_action'], 'community_update')
        
        # Step 8: Verify community has leader
        leader = self.agent_service.get_community_leader(self.community.uid)
        self.assertIsNotNone(leader)
        self.assertEqual(leader.uid, agent.uid)
    
    @patch('agentic.services.notification_integration.NotificationService')
    def test_agent_assignment_with_notifications(self, mock_notification_service):
        """Test agent assignment workflow with notification integration."""
        # Mock the notification service
        mock_notification_service.return_value.notify_agent_assigned = AsyncMock()
        mock_notification_service.return_value.notify_assignment_confirmation = AsyncMock()
        
        # Create agent
        agent = self.agent_service.create_agent(
            name='Notification Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community', 'send_messages'],
            created_by_uid=self.user.uid
        )
        
        # Assign agent with notification
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Test notification sending
        async def test_notifications():
            result = await self.notification_service.notify_agent_assigned(
                agent_uid=agent.uid,
                community_uid=self.community.uid,
                assignment_uid=assignment.uid,
                assigned_by_uid=self.user.uid
            )
            
            self.assertTrue(result['success'])
            self.assertIn('notification_results', result)
        
        # Run async test
        asyncio.run(test_notifications())
    
    def test_agent_permission_enforcement_workflow(self):
        """Test that agent permissions are properly enforced."""
        # Create agent with limited capabilities
        agent = self.agent_service.create_agent(
            name='Limited Agent',
            agent_type='ASSISTANT',
            capabilities=['send_messages'],  # No moderation capabilities
            created_by_uid=self.user.uid
        )
        
        # Assign agent
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Test allowed permission
        has_send_permission = self.auth_service.check_permission(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            permission='send_messages'
        )
        self.assertTrue(has_send_permission)
        
        # Test denied permission
        has_moderate_permission = self.auth_service.check_permission(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            permission='moderate_users'
        )
        self.assertFalse(has_moderate_permission)
        
        # Test action that should fail
        with self.assertRaises(AgentAuthorizationError):
            self.auth_service.require_permission(
                agent_uid=agent.uid,
                community_uid=self.community.uid,
                permission='moderate_users'
            )
    
    def test_agent_memory_persistence_workflow(self):
        """Test agent memory persistence across operations."""
        # Create and assign agent
        agent = self.agent_service.create_agent(
            name='Memory Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Store different types of memory
        context_data = {'current_task': 'community_setup', 'progress': 50}
        self.memory_service.store_context(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            context=context_data
        )
        
        conversation_data = {'user': 'admin', 'message': 'Update community description'}
        self.memory_service.update_conversation_history(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            conversation_data=conversation_data
        )
        
        knowledge_data = {'community_rules': ['Be respectful', 'No spam']}
        self.memory_service.store_knowledge(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            knowledge_data=knowledge_data
        )
        
        preferences_data = {'notification_frequency': 'daily', 'auto_moderate': True}
        self.memory_service.store_preferences(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            preferences=preferences_data
        )
        
        # Retrieve and verify all memory types
        retrieved_context = self.memory_service.retrieve_context(agent.uid, self.community.uid)
        self.assertEqual(retrieved_context['current_task'], 'community_setup')
        
        conversation_history = self.memory_service.get_conversation_history(
            agent.uid, self.community.uid, limit=10
        )
        self.assertEqual(len(conversation_history), 1)
        self.assertEqual(conversation_history[0]['user'], 'admin')
        
        knowledge = self.memory_service.get_community_knowledge(agent.uid, self.community.uid)
        self.assertIn('community_rules', knowledge)
        
        preferences = self.memory_service.get_preferences(agent.uid, self.community.uid)
        self.assertEqual(preferences['notification_frequency'], 'daily')
    
    def test_multiple_agent_assignment_conflict_handling(self):
        """Test handling of multiple agent assignments to the same community."""
        # Create first agent and assign as leader
        agent1 = self.agent_service.create_agent(
            name='First Leader',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        assignment1 = self.agent_service.assign_agent_to_community(
            agent_uid=agent1.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Create second agent
        agent2 = self.agent_service.create_agent(
            name='Second Leader',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        # Try to assign second leader (should fail by default)
        with self.assertRaises(CommunityAlreadyHasLeaderError):
            self.agent_service.assign_agent_to_community(
                agent_uid=agent2.uid,
                community_uid=self.community.uid,
                assigned_by_uid=self.user.uid
            )
        
        # Allow multiple leaders and try again
        assignment2 = self.agent_service.assign_agent_to_community(
            agent_uid=agent2.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid,
            allow_multiple_leaders=True
        )
        
        self.assertIsNotNone(assignment2)
        
        # Verify both agents are assigned
        community_agents = self.agent_service.get_community_agents(self.community.uid)
        self.assertEqual(len(community_agents), 2)
    
    def test_agent_deactivation_workflow(self):
        """Test the complete agent deactivation workflow."""
        # Create and assign agent
        agent = self.agent_service.create_agent(
            name='Deactivation Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Store some memory
        self.memory_service.store_context(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            context={'test': 'data'}
        )
        
        # Verify agent is active
        self.assertTrue(assignment.is_active())
        
        # Deactivate assignment
        success = self.agent_service.deactivate_agent_assignment(assignment.uid)
        self.assertTrue(success)
        
        # Verify assignment is deactivated
        updated_assignment = self.agent_service.get_assignment_by_uid(assignment.uid)
        self.assertFalse(updated_assignment.is_active())
        
        # Verify agent can no longer authenticate
        is_authenticated = self.auth_service.authenticate_agent(
            agent_uid=agent.uid,
            community_uid=self.community.uid
        )
        self.assertFalse(is_authenticated)
        
        # Verify community no longer has this leader
        leader = self.agent_service.get_community_leader(self.community.uid)
        self.assertIsNone(leader)
    
    def test_audit_logging_integration(self):
        """Test that audit logging works across all operations."""
        # Create and assign agent
        agent = self.agent_service.create_agent(
            name='Audit Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community', 'moderate_users'],
            created_by_uid=self.user.uid
        )
        
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Perform various operations that should be audited
        self.auth_service.authenticate_agent(agent.uid, self.community.uid)
        self.auth_service.check_permission(agent.uid, self.community.uid, 'edit_community')
        
        self.auth_service.log_agent_action(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            action_type='edit_community',
            details={'field': 'name', 'new_value': 'Updated Name'},
            success=True
        )
        
        self.auth_service.log_agent_action(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            action_type='moderate_user',
            details={'target_user': 'test-user', 'action': 'warn'},
            success=True
        )
        
        # Generate audit report
        report = audit_service.generate_audit_report(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            include_details=True
        )
        
        # Verify audit report contains expected data
        self.assertGreater(report['summary']['total_logs'], 0)
        self.assertIn('edit_community', report['action_breakdown'])
        self.assertIn('moderate_user', report['action_breakdown'])
        
        if 'detailed_logs' in report:
            self.assertGreater(len(report['detailed_logs']), 0)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios."""
        # Test agent not found error
        with self.assertRaises(AgentNotFoundError):
            self.agent_service.get_agent_by_uid('nonexistent-agent')
        
        # Test community not found error
        with self.assertRaises(CommunityNotFoundError):
            self.agent_service.assign_agent_to_community(
                agent_uid='any-agent',
                community_uid='nonexistent-community',
                assigned_by_uid=self.user.uid
            )
        
        # Create agent for further tests
        agent = self.agent_service.create_agent(
            name='Error Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        # Test authentication failure
        is_authenticated = self.auth_service.authenticate_agent(
            agent_uid=agent.uid,
            community_uid='nonexistent-community'
        )
        self.assertFalse(is_authenticated)
        
        # Test permission check on unassigned agent
        has_permission = self.auth_service.check_permission(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            permission='edit_community'
        )
        self.assertFalse(has_permission)  # Should be false since agent is not assigned
    
    def test_memory_expiration_and_cleanup(self):
        """Test memory expiration and cleanup functionality."""
        # Create and assign agent
        agent = self.agent_service.create_agent(
            name='Memory Expiration Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Store memory with short expiration
        memory = self.memory_service.store_context(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            context={'test': 'expiring_data'},
            expires_in_hours=1
        )
        
        # Verify memory exists
        retrieved_context = self.memory_service.retrieve_context(agent.uid, self.community.uid)
        self.assertEqual(retrieved_context['test'], 'expiring_data')
        
        # Manually expire the memory for testing
        memory.expires_at = timezone.now() - timedelta(hours=1)
        memory.save()
        
        # Verify expired memory is not retrieved
        expired_context = self.memory_service.retrieve_context(agent.uid, self.community.uid)
        self.assertEqual(expired_context, {})  # Should return empty dict for expired memory
        
        # Test memory cleanup
        cleared_count = self.memory_service.clear_memory(
            agent_uid=agent.uid,
            community_uid=self.community.uid
        )
        self.assertGreater(cleared_count, 0)


class AgentGraphQLIntegrationTest(TestCase):
    """
    Integration tests for GraphQL operations with agents.
    
    These tests verify that GraphQL mutations and queries work correctly
    with the agent system.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = Users(
            uid='test-user-456',
            username='graphqluser',
            email='graphql@example.com'
        )
        self.user.save()
        
        # Create test community
        self.community = Community(
            uid='test-community-456',
            name='GraphQL Test Community',
            description='A test community for GraphQL',
            is_private=False
        )
        self.community.save()
    
    def test_graphql_agent_creation_mutation(self):
        """Test agent creation through GraphQL mutation."""
        # This would typically use a GraphQL client to test mutations
        # For now, we'll test the underlying service that GraphQL would call
        
        from ..services.agent_service import AgentService
        
        agent_service = AgentService()
        
        # Simulate GraphQL mutation input
        mutation_input = {
            'name': 'GraphQL Test Agent',
            'agent_type': 'COMMUNITY_LEADER',
            'capabilities': ['edit_community', 'send_messages'],
            'description': 'Created via GraphQL',
            'created_by_uid': self.user.uid
        }
        
        # Create agent (this would be called by GraphQL mutation)
        agent = agent_service.create_agent(**mutation_input)
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'GraphQL Test Agent')
        self.assertEqual(agent.agent_type, 'COMMUNITY_LEADER')
    
    def test_graphql_agent_assignment_mutation(self):
        """Test agent assignment through GraphQL mutation."""
        from ..services.agent_service import AgentService
        
        agent_service = AgentService()
        
        # Create agent first
        agent = agent_service.create_agent(
            name='Assignment Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        # Simulate GraphQL assignment mutation
        assignment_input = {
            'agent_uid': agent.uid,
            'community_uid': self.community.uid,
            'assigned_by_uid': self.user.uid,
            'permissions': ['manage_events']
        }
        
        # Assign agent (this would be called by GraphQL mutation)
        assignment = agent_service.assign_agent_to_community(**assignment_input)
        
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.status, 'ACTIVE')
        self.assertIn('manage_events', assignment.permissions)
    
    def test_graphql_agent_queries(self):
        """Test agent queries through GraphQL."""
        from ..services.agent_service import AgentService
        
        agent_service = AgentService()
        
        # Create and assign agent
        agent = agent_service.create_agent(
            name='Query Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        assignment = agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Test queries (these would be called by GraphQL resolvers)
        retrieved_agent = agent_service.get_agent_by_uid(agent.uid)
        self.assertEqual(retrieved_agent.uid, agent.uid)
        
        community_leader = agent_service.get_community_leader(self.community.uid)
        self.assertEqual(community_leader.uid, agent.uid)
        
        agent_assignments = agent_service.get_agent_assignments(agent.uid)
        self.assertEqual(len(agent_assignments), 1)
        self.assertEqual(agent_assignments[0].uid, assignment.uid)


class AgentPerformanceIntegrationTest(TestCase):
    """
    Performance-focused integration tests for agent operations.
    
    These tests verify that agent operations perform well under load
    and with large datasets.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = Users(
            uid='perf-user-789',
            username='perfuser',
            email='perf@example.com'
        )
        self.user.save()
        
        self.community = Community(
            uid='perf-community-789',
            name='Performance Test Community',
            description='A test community for performance testing',
            is_private=False
        )
        self.community.save()
        
        self.agent_service = AgentService()
        self.auth_service = AgentAuthService()
        self.memory_service = AgentMemoryService()
    
    def test_bulk_agent_operations(self):
        """Test performance of bulk agent operations."""
        import time
        
        # Create multiple agents
        start_time = time.time()
        agents = []
        
        for i in range(10):  # Create 10 agents for testing
            agent = self.agent_service.create_agent(
                name=f'Bulk Test Agent {i}',
                agent_type='ASSISTANT',
                capabilities=['send_messages'],
                created_by_uid=self.user.uid
            )
            agents.append(agent)
        
        creation_time = time.time() - start_time
        
        # Assign all agents to the community
        start_time = time.time()
        assignments = []
        
        for agent in agents:
            assignment = self.agent_service.assign_agent_to_community(
                agent_uid=agent.uid,
                community_uid=self.community.uid,
                assigned_by_uid=self.user.uid,
                allow_multiple_leaders=True
            )
            assignments.append(assignment)
        
        assignment_time = time.time() - start_time
        
        # Test bulk authentication
        start_time = time.time()
        
        for agent in agents:
            self.auth_service.authenticate_agent(agent.uid, self.community.uid)
        
        auth_time = time.time() - start_time
        
        # Verify performance is reasonable
        self.assertLess(creation_time, 5.0, "Agent creation took too long")
        self.assertLess(assignment_time, 5.0, "Agent assignment took too long")
        self.assertLess(auth_time, 2.0, "Agent authentication took too long")
        
        # Verify all operations succeeded
        self.assertEqual(len(agents), 10)
        self.assertEqual(len(assignments), 10)
        
        community_agents = self.agent_service.get_community_agents(self.community.uid)
        self.assertEqual(len(community_agents), 10)
    
    def test_memory_operations_performance(self):
        """Test performance of memory operations."""
        import time
        
        # Create and assign agent
        agent = self.agent_service.create_agent(
            name='Memory Performance Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Test bulk memory storage
        start_time = time.time()
        
        for i in range(50):  # Store 50 memory entries
            self.memory_service.store_context(
                agent_uid=agent.uid,
                community_uid=self.community.uid,
                context={'iteration': i, 'data': f'test_data_{i}'}
            )
        
        storage_time = time.time() - start_time
        
        # Test memory retrieval
        start_time = time.time()
        
        for i in range(10):  # Retrieve memory 10 times
            context = self.memory_service.retrieve_context(agent.uid, self.community.uid)
            self.assertIsNotNone(context)
        
        retrieval_time = time.time() - start_time
        
        # Verify performance is reasonable
        self.assertLess(storage_time, 10.0, "Memory storage took too long")
        self.assertLess(retrieval_time, 2.0, "Memory retrieval took too long")
    
    def test_audit_log_performance(self):
        """Test performance of audit logging operations."""
        import time
        
        # Create and assign agent
        agent = self.agent_service.create_agent(
            name='Audit Performance Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community'],
            created_by_uid=self.user.uid
        )
        
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        # Test bulk audit logging
        start_time = time.time()
        
        for i in range(100):  # Log 100 actions
            self.auth_service.log_agent_action(
                agent_uid=agent.uid,
                community_uid=self.community.uid,
                action_type='test_action',
                details={'iteration': i},
                success=True
            )
        
        logging_time = time.time() - start_time
        
        # Test audit report generation
        start_time = time.time()
        
        report = audit_service.generate_audit_report(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            include_details=False  # Exclude details for performance
        )
        
        report_time = time.time() - start_time
        
        # Verify performance is reasonable
        self.assertLess(logging_time, 10.0, "Audit logging took too long")
        self.assertLess(report_time, 5.0, "Audit report generation took too long")
        
        # Verify report contains expected data
        self.assertGreaterEqual(report['summary']['total_logs'], 100)