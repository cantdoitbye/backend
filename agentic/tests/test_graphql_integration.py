# GraphQL Integration Tests for Agent Operations
# This module contains integration tests for GraphQL operations with agents.

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from graphene.test import Client
from graphql_jwt.testcases import JSONWebTokenTestCase

from community.models import Community, Membership
from auth_manager.models import Users, Profile
from ..models import Agent, AgentCommunityAssignment
from ..services.agent_service import AgentService
from ..graphql.types import AgentType, AgentAssignmentType
from ..graphql.mutations import AgentMutations
from ..graphql.queries import AgentQueries


class GraphQLAgentIntegrationTest(JSONWebTokenTestCase):
    """
    Integration tests for GraphQL agent operations.
    
    These tests verify that GraphQL mutations and queries work correctly
    with the complete agent system.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = Users(
            uid='graphql-user-123',
            username='graphqluser',
            email='graphql@example.com'
        )
        self.user.save()
        
        # Create user profile
        self.profile = Profile(
            uid='graphql-profile-123',
            device_id='graphql-device-123'
        )
        self.profile.save()
        self.profile.user.connect(self.user)
        
        # Create test community
        self.community = Community(
            uid='graphql-community-123',
            name='GraphQL Test Community',
            description='A test community for GraphQL operations',
            is_private=False
        )
        self.community.save()
        
        # Create community membership
        self.membership = Membership(
            uid='graphql-membership-123',
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
        
        # Create GraphQL client
        from schema.schema import schema
        self.client = Client(schema)
    
    def test_create_agent_mutation(self):
        """Test creating an agent through GraphQL mutation."""
        mutation = '''
            mutation CreateAgent($input: CreateAgentInput!) {
                createAgent(input: $input) {
                    success
                    message
                    agent {
                        uid
                        name
                        agentType
                        capabilities
                        status
                        createdDate
                    }
                    errors
                }
            }
        '''
        
        variables = {
            'input': {
                'name': 'GraphQL Test Agent',
                'agentType': 'COMMUNITY_LEADER',
                'capabilities': ['edit_community', 'moderate_users', 'send_messages'],
                'description': 'An agent created through GraphQL',
                'createdByUid': self.user.uid
            }
        }
        
        # Execute mutation
        result = self.client.execute(mutation, variables=variables)
        
        # Verify response
        self.assertIsNone(result.get('errors'))
        data = result['data']['createAgent']
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['agent'])
        self.assertEqual(data['agent']['name'], 'GraphQL Test Agent')
        self.assertEqual(data['agent']['agentType'], 'COMMUNITY_LEADER')
        self.assertIn('edit_community', data['agent']['capabilities'])
        
        # Verify agent was created in database
        agent_uid = data['agent']['uid']
        agent = Agent.nodes.get(uid=agent_uid)
        self.assertEqual(agent.name, 'GraphQL Test Agent')
    
    def test_assign_agent_to_community_mutation(self):
        """Test assigning an agent to a community through GraphQL."""
        # First create an agent
        agent = self.agent_service.create_agent(
            name='Assignment Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community', 'send_messages'],
            created_by_uid=self.user.uid
        )
        
        mutation = '''
            mutation AssignAgentToCommunity($input: AssignAgentToCommunityInput!) {
                assignAgentToCommunity(input: $input) {
                    success
                    message
                    assignment {
                        uid
                        status
                        permissions
                        assignmentDate
                    }
                    agent {
                        uid
                        name
                    }
                    community {
                        uid
                        name
                    }
                    errors
                }
            }
        '''
        
        variables = {
            'input': {
                'agentUid': agent.uid,
                'communityUid': self.community.uid,
                'assignedByUid': self.user.uid,
                'permissions': ['manage_events'],
                'allowMultipleLeaders': False
            }
        }
        
        # Execute mutation
        result = self.client.execute(mutation, variables=variables)
        
        # Verify response
        self.assertIsNone(result.get('errors'))
        data = result['data']['assignAgentToCommunity']
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['assignment'])
        self.assertEqual(data['assignment']['status'], 'ACTIVE')
        self.assertIn('manage_events', data['assignment']['permissions'])
        self.assertEqual(data['agent']['uid'], agent.uid)
        self.assertEqual(data['community']['uid'], self.community.uid)
        
        # Verify assignment was created in database
        assignment_uid = data['assignment']['uid']
        assignment = AgentCommunityAssignment.nodes.get(uid=assignment_uid)
        self.assertEqual(assignment.status, 'ACTIVE')
    
    def test_get_agent_query(self):
        """Test retrieving an agent through GraphQL query."""
        # Create an agent
        agent = self.agent_service.create_agent(
            name='Query Test Agent',
            agent_type='MODERATOR',
            capabilities=['moderate_users', 'send_messages'],
            description='An agent for query testing',
            created_by_uid=self.user.uid
        )
        
        query = '''
            query GetAgent($agentUid: String!) {
                getAgent(agentUid: $agentUid) {
                    uid
                    name
                    description
                    agentType
                    capabilities
                    status
                    isActive
                    createdDate
                    assignmentCount
                }
            }
        '''
        
        variables = {
            'agentUid': agent.uid
        }
        
        # Execute query
        result = self.client.execute(query, variables=variables)
        
        # Verify response
        self.assertIsNone(result.get('errors'))
        data = result['data']['getAgent']
        
        self.assertIsNotNone(data)
        self.assertEqual(data['uid'], agent.uid)
        self.assertEqual(data['name'], 'Query Test Agent')
        self.assertEqual(data['agentType'], 'MODERATOR')
        self.assertIn('moderate_users', data['capabilities'])
        self.assertTrue(data['isActive'])
        self.assertEqual(data['assignmentCount'], 0)  # No assignments yet
    
    def test_get_community_leader_query(self):
        """Test retrieving community leader through GraphQL query."""
        # Create and assign an agent as leader
        agent = self.agent_service.create_agent(
            name='Leader Test Agent',
            agent_type='COMMUNITY_LEADER',
            capabilities=['edit_community', 'moderate_users'],
            created_by_uid=self.user.uid
        )
        
        assignment = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid
        )
        
        query = '''
            query GetCommunityLeader($communityUid: String!) {
                getCommunityLeader(communityUid: $communityUid) {
                    uid
                    name
                    agentType
                    capabilities
                    isActive
                }
            }
        '''
        
        variables = {
            'communityUid': self.community.uid
        }
        
        # Execute query
        result = self.client.execute(query, variables=variables)
        
        # Verify response
        self.assertIsNone(result.get('errors'))
        data = result['data']['getCommunityLeader']
        
        self.assertIsNotNone(data)
        self.assertEqual(data['uid'], agent.uid)
        self.assertEqual(data['name'], 'Leader Test Agent')
        self.assertEqual(data['agentType'], 'COMMUNITY_LEADER')
        self.assertTrue(data['isActive'])
    
    def test_get_agent_assignments_query(self):
        """Test retrieving agent assignments through GraphQL query."""
        # Create agent and multiple assignments
        agent = self.agent_service.create_agent(
            name='Multi-Assignment Agent',
            agent_type='ASSISTANT',
            capabilities=['send_messages'],
            created_by_uid=self.user.uid
        )
        
        # Create additional community for testing
        community2 = Community(
            uid='graphql-community-456',
            name='Second Test Community',
            description='Another test community',
            is_private=False
        )
        community2.save()
        
        # Assign agent to both communities
        assignment1 = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=self.community.uid,
            assigned_by_uid=self.user.uid,
            allow_multiple_leaders=True
        )
        
        assignment2 = self.agent_service.assign_agent_to_community(
            agent_uid=agent.uid,
            community_uid=community2.uid,
            assigned_by_uid=self.user.uid,
            allow_multiple_leaders=True
        )
        
        query = '''
            query GetAgentAssignments($agentUid: String!) {
                getAgentAssignments(agentUid: $agentUid) {
                    uid
                    status
                    assignmentDate
                    isActive
                    agent {
                        uid
                        name
                    }
                    community {
                        uid
                        name
                    }
                }
            }
        '''
        
        variables = {
            'agentUid': agent.uid
        }
        
        # Execute query
        result = self.client.execute(query, variables=variables)
        
        # Verify response
        self.assertIsNone(result.get('errors'))
        data = result['data']['getAgentAssignments']
        
        self.assertIsNotNone(data)
        self.assertEqual(len(data), 2)
        
        # Verify both assignments are returned
        assignment_uids = [assignment['uid'] for assignment in data]
        self.assertIn(assignment1.uid, assignment_uids)\n        self.assertIn(assignment2.uid, assignment_uids)\n        \n        # Verify assignment details\n        for assignment_data in data:\n            self.assertEqual(assignment_data['status'], 'ACTIVE')\n            self.assertTrue(assignment_data['isActive'])\n            self.assertEqual(assignment_data['agent']['uid'], agent.uid)\n    \n    def test_update_agent_mutation(self):\n        \"\"\"Test updating an agent through GraphQL mutation.\"\"\"\n        # Create an agent\n        agent = self.agent_service.create_agent(\n            name='Update Test Agent',\n            agent_type='ASSISTANT',\n            capabilities=['send_messages'],\n            description='Original description',\n            created_by_uid=self.user.uid\n        )\n        \n        mutation = '''\n            mutation UpdateAgent($input: UpdateAgentInput!) {\n                updateAgent(input: $input) {\n                    success\n                    message\n                    agent {\n                        uid\n                        name\n                        description\n                        capabilities\n                        status\n                    }\n                    errors\n                }\n            }\n        '''\n        \n        variables = {\n            'input': {\n                'agentUid': agent.uid,\n                'name': 'Updated Agent Name',\n                'description': 'Updated description',\n                'capabilities': ['send_messages', 'moderate_users'],\n                'status': 'ACTIVE'\n            }\n        }\n        \n        # Execute mutation\n        result = self.client.execute(mutation, variables=variables)\n        \n        # Verify response\n        self.assertIsNone(result.get('errors'))\n        data = result['data']['updateAgent']\n        \n        self.assertTrue(data['success'])\n        self.assertIsNotNone(data['agent'])\n        self.assertEqual(data['agent']['name'], 'Updated Agent Name')\n        self.assertEqual(data['agent']['description'], 'Updated description')\n        self.assertIn('moderate_users', data['agent']['capabilities'])\n        \n        # Verify agent was updated in database\n        updated_agent = Agent.nodes.get(uid=agent.uid)\n        self.assertEqual(updated_agent.name, 'Updated Agent Name')\n        self.assertIn('moderate_users', updated_agent.capabilities)\n    \n    def test_deactivate_agent_assignment_mutation(self):\n        \"\"\"Test deactivating an agent assignment through GraphQL.\"\"\"\n        # Create and assign agent\n        agent = self.agent_service.create_agent(\n            name='Deactivation Test Agent',\n            agent_type='COMMUNITY_LEADER',\n            capabilities=['edit_community'],\n            created_by_uid=self.user.uid\n        )\n        \n        assignment = self.agent_service.assign_agent_to_community(\n            agent_uid=agent.uid,\n            community_uid=self.community.uid,\n            assigned_by_uid=self.user.uid\n        )\n        \n        mutation = '''\n            mutation DeactivateAgentAssignment($input: DeactivateAgentAssignmentInput!) {\n                deactivateAgentAssignment(input: $input) {\n                    success\n                    message\n                    assignment {\n                        uid\n                        status\n                        isActive\n                    }\n                    successFlag\n                    errors\n                }\n            }\n        '''\n        \n        variables = {\n            'input': {\n                'assignmentUid': assignment.uid,\n                'reason': 'Testing deactivation'\n            }\n        }\n        \n        # Execute mutation\n        result = self.client.execute(mutation, variables=variables)\n        \n        # Verify response\n        self.assertIsNone(result.get('errors'))\n        data = result['data']['deactivateAgentAssignment']\n        \n        self.assertTrue(data['success'])\n        self.assertTrue(data['successFlag'])\n        self.assertIsNotNone(data['assignment'])\n        self.assertEqual(data['assignment']['status'], 'INACTIVE')\n        self.assertFalse(data['assignment']['isActive'])\n        \n        # Verify assignment was deactivated in database\n        updated_assignment = AgentCommunityAssignment.nodes.get(uid=assignment.uid)\n        self.assertEqual(updated_assignment.status, 'INACTIVE')\n    \n    @patch('agentic.services.memory_service.AgentMemoryService.store_context')\n    def test_store_agent_context_mutation(self, mock_store_context):\n        \"\"\"Test storing agent context through GraphQL.\"\"\"\n        # Mock the memory service\n        mock_memory = MagicMock()\n        mock_memory.id = 1\n        mock_store_context.return_value = mock_memory\n        \n        # Create and assign agent\n        agent = self.agent_service.create_agent(\n            name='Context Test Agent',\n            agent_type='COMMUNITY_LEADER',\n            capabilities=['edit_community'],\n            created_by_uid=self.user.uid\n        )\n        \n        assignment = self.agent_service.assign_agent_to_community(\n            agent_uid=agent.uid,\n            community_uid=self.community.uid,\n            assigned_by_uid=self.user.uid\n        )\n        \n        mutation = '''\n            mutation StoreAgentContext($input: StoreAgentContextInput!) {\n                storeAgentContext(input: $input) {\n                    success\n                    message\n                    errors\n                }\n            }\n        '''\n        \n        context_data = {\n            'current_task': 'community_setup',\n            'progress': 75,\n            'last_action': 'update_description'\n        }\n        \n        variables = {\n            'input': {\n                'agentUid': agent.uid,\n                'communityUid': self.community.uid,\n                'context': json.dumps(context_data),\n                'expiresInHours': 24,\n                'priority': 1\n            }\n        }\n        \n        # Execute mutation\n        result = self.client.execute(mutation, variables=variables)\n        \n        # Verify response\n        self.assertIsNone(result.get('errors'))\n        data = result['data']['storeAgentContext']\n        \n        self.assertTrue(data['success'])\n        self.assertEqual(data['message'], 'Context stored successfully')\n        \n        # Verify memory service was called\n        mock_store_context.assert_called_once_with(\n            agent_uid=agent.uid,\n            community_uid=self.community.uid,\n            context=context_data,\n            expires_in_hours=24,\n            priority=1\n        )\n    \n    def test_get_agents_with_filters_query(self):\n        \"\"\"Test retrieving agents with filters through GraphQL.\"\"\"\n        # Create multiple agents with different types\n        agent1 = self.agent_service.create_agent(\n            name='Leader Agent',\n            agent_type='COMMUNITY_LEADER',\n            capabilities=['edit_community'],\n            created_by_uid=self.user.uid\n        )\n        \n        agent2 = self.agent_service.create_agent(\n            name='Moderator Agent',\n            agent_type='MODERATOR',\n            capabilities=['moderate_users'],\n            created_by_uid=self.user.uid\n        )\n        \n        agent3 = self.agent_service.create_agent(\n            name='Assistant Agent',\n            agent_type='ASSISTANT',\n            capabilities=['send_messages'],\n            created_by_uid=self.user.uid\n        )\n        \n        query = '''\n            query GetAgents($filters: AgentFilterInput, $pagination: PaginationInput) {\n                getAgents(filters: $filters, pagination: $pagination) {\n                    uid\n                    name\n                    agentType\n                    capabilities\n                    status\n                }\n            }\n        '''\n        \n        # Test filtering by agent type\n        variables = {\n            'filters': {\n                'agentType': 'COMMUNITY_LEADER'\n            },\n            'pagination': {\n                'page': 1,\n                'pageSize': 10\n            }\n        }\n        \n        # Execute query\n        result = self.client.execute(query, variables=variables)\n        \n        # Verify response\n        self.assertIsNone(result.get('errors'))\n        data = result['data']['getAgents']\n        \n        self.assertIsNotNone(data)\n        self.assertEqual(len(data), 1)  # Only one COMMUNITY_LEADER\n        self.assertEqual(data[0]['uid'], agent1.uid)\n        self.assertEqual(data[0]['agentType'], 'COMMUNITY_LEADER')\n        \n        # Test filtering by capability\n        variables = {\n            'filters': {\n                'hasCapability': 'moderate_users'\n            }\n        }\n        \n        result = self.client.execute(query, variables=variables)\n        data = result['data']['getAgents']\n        \n        self.assertEqual(len(data), 1)  # Only moderator has moderate_users capability\n        self.assertEqual(data[0]['uid'], agent2.uid)\n    \n    def test_error_handling_in_mutations(self):\n        \"\"\"Test error handling in GraphQL mutations.\"\"\"\n        # Test creating agent with invalid data\n        mutation = '''\n            mutation CreateAgent($input: CreateAgentInput!) {\n                createAgent(input: $input) {\n                    success\n                    message\n                    agent {\n                        uid\n                    }\n                    errors\n                }\n            }\n        '''\n        \n        variables = {\n            'input': {\n                'name': '',  # Invalid empty name\n                'agentType': 'INVALID_TYPE',  # Invalid agent type\n                'capabilities': [],  # Empty capabilities\n                'createdByUid': 'nonexistent-user'  # Nonexistent user\n            }\n        }\n        \n        # Execute mutation\n        result = self.client.execute(mutation, variables=variables)\n        \n        # Verify error response\n        self.assertIsNone(result.get('errors'))  # No GraphQL errors\n        data = result['data']['createAgent']\n        \n        self.assertFalse(data['success'])\n        self.assertIsNotNone(data['errors'])\n        self.assertIsNone(data['agent'])\n        \n        # Test assigning nonexistent agent\n        assignment_mutation = '''\n            mutation AssignAgentToCommunity($input: AssignAgentToCommunityInput!) {\n                assignAgentToCommunity(input: $input) {\n                    success\n                    message\n                    errors\n                }\n            }\n        '''\n        \n        variables = {\n            'input': {\n                'agentUid': 'nonexistent-agent',\n                'communityUid': self.community.uid,\n                'assignedByUid': self.user.uid\n            }\n        }\n        \n        result = self.client.execute(assignment_mutation, variables=variables)\n        data = result['data']['assignAgentToCommunity']\n        \n        self.assertFalse(data['success'])\n        self.assertIsNotNone(data['errors'])\n    \n    def test_complex_query_with_relationships(self):\n        \"\"\"Test complex GraphQL query with nested relationships.\"\"\"\n        # Create agent and assignment\n        agent = self.agent_service.create_agent(\n            name='Relationship Test Agent',\n            agent_type='COMMUNITY_LEADER',\n            capabilities=['edit_community', 'moderate_users'],\n            created_by_uid=self.user.uid\n        )\n        \n        assignment = self.agent_service.assign_agent_to_community(\n            agent_uid=agent.uid,\n            community_uid=self.community.uid,\n            assigned_by_uid=self.user.uid,\n            permissions=['manage_events']\n        )\n        \n        query = '''\n            query GetAgentWithRelationships($agentUid: String!) {\n                getAgent(agentUid: $agentUid) {\n                    uid\n                    name\n                    agentType\n                    capabilities\n                    isActive\n                    assignmentCount\n                    assignments {\n                        uid\n                        status\n                        permissions\n                        isActive\n                        effectivePermissions\n                        community {\n                            uid\n                            name\n                        }\n                        assignedBy {\n                            uid\n                            username\n                        }\n                    }\n                    createdBy {\n                        uid\n                        username\n                    }\n                }\n            }\n        '''\n        \n        variables = {\n            'agentUid': agent.uid\n        }\n        \n        # Execute query\n        result = self.client.execute(query, variables=variables)\n        \n        # Verify response\n        self.assertIsNone(result.get('errors'))\n        data = result['data']['getAgent']\n        \n        self.assertIsNotNone(data)\n        self.assertEqual(data['uid'], agent.uid)\n        self.assertEqual(data['assignmentCount'], 1)\n        \n        # Verify assignment relationship\n        assignments = data['assignments']\n        self.assertEqual(len(assignments), 1)\n        \n        assignment_data = assignments[0]\n        self.assertEqual(assignment_data['uid'], assignment.uid)\n        self.assertEqual(assignment_data['status'], 'ACTIVE')\n        self.assertIn('manage_events', assignment_data['permissions'])\n        \n        # Verify community relationship\n        community_data = assignment_data['community']\n        self.assertEqual(community_data['uid'], self.community.uid)\n        self.assertEqual(community_data['name'], self.community.name)\n        \n        # Verify user relationships\n        assigned_by_data = assignment_data['assignedBy']\n        self.assertEqual(assigned_by_data['uid'], self.user.uid)\n        \n        created_by_data = data['createdBy']\n        self.assertEqual(created_by_data['uid'], self.user.uid)