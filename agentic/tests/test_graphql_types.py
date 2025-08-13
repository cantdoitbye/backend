# Agent GraphQL Types Tests
# This module contains unit tests for the GraphQL types.

import pytest
from unittest.mock import Mock, patch
from django.test import TestCase
from datetime import datetime

from ..graphql.types import (
    AgentType, AgentAssignmentType, AgentActionLogType, AgentMemoryType,
    AgentStatsType, AgentMemoryStatsType, AgentAuditReportType,
    AgentSummaryType, CommunityAgentSummaryType
)
from ..models import Agent, AgentCommunityAssignment, AgentActionLog, AgentMemory


class AgentGraphQLTypesTest(TestCase):
    """Test cases for Agent GraphQL types."""
    
    def setUp(self):
        """Set up test data."""
        # Mock agent
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.uid = "agent_123"
        self.mock_agent.name = "Test Agent"
        self.mock_agent.description = "A test agent"
        self.mock_agent.agent_type = "COMMUNITY_LEADER"
        self.mock_agent.icon_id = "icon_123"
        self.mock_agent.status = "ACTIVE"
        self.mock_agent.capabilities = ["edit_community", "moderate_users"]
        self.mock_agent.created_date = datetime(2024, 1, 1, 12, 0, 0)
        self.mock_agent.updated_date = datetime(2024, 1, 1, 12, 0, 0)
        self.mock_agent.version = "1.0"
        self.mock_agent.created_by.single.return_value = None
        self.mock_agent.assigned_communities.all.return_value = []
        
        # Mock assignment
        self.mock_assignment = Mock(spec=AgentCommunityAssignment)
        self.mock_assignment.uid = "assignment_123"
        self.mock_assignment.assignment_date = datetime(2024, 1, 1, 12, 0, 0)
        self.mock_assignment.status = "ACTIVE"
        self.mock_assignment.permissions = ["custom_permission"]
        self.mock_assignment.created_date = datetime(2024, 1, 1, 12, 0, 0)
        self.mock_assignment.updated_date = datetime(2024, 1, 1, 12, 0, 0)
        self.mock_assignment.is_active.return_value = True
        self.mock_assignment.get_effective_permissions.return_value = ["edit_community", "custom_permission"]
        self.mock_assignment.agent.single.return_value = self.mock_agent
        self.mock_assignment.community.single.return_value = None
        self.mock_assignment.assigned_by.single.return_value = None
    
    @patch('agentic.graphql.types.generate_presigned_url')
    def test_agent_type_from_neomodel_success(self, mock_generate_url):
        """Test successful conversion of Agent to GraphQL type."""
        # Mock file info generation
        mock_generate_url.generate_file_info.return_value = {
            'url': 'https://example.com/icon.png',
            'file_type': 'image/png'
        }
        
        result = AgentType.from_neomodel(self.mock_agent)
        
        # Verify conversion
        self.assertIsNotNone(result)
        self.assertEqual(result.uid, "agent_123")
        self.assertEqual(result.name, "Test Agent")
        self.assertEqual(result.description, "A test agent")
        self.assertEqual(result.agent_type, "COMMUNITY_LEADER")
        self.assertEqual(result.status, "ACTIVE")
        self.assertEqual(result.capabilities, ["edit_community", "moderate_users"])
        self.assertEqual(result.version, "1.0")
    
    @patch('agentic.graphql.types.generate_presigned_url')
    def test_agent_type_from_neomodel_icon_error(self, mock_generate_url):
        """Test Agent conversion when icon URL generation fails."""
        # Mock file info generation to raise exception
        mock_generate_url.generate_file_info.side_effect = Exception("S3 error")
        
        result = AgentType.from_neomodel(self.mock_agent)
        
        # Should still convert successfully with None icon_url
        self.assertIsNotNone(result)
        self.assertEqual(result.uid, "agent_123")
        self.assertIsNone(result.icon_url)
    
    def test_agent_type_from_neomodel_error_handling(self):
        """Test Agent conversion error handling."""
        # Mock agent that raises exception
        broken_agent = Mock()
        broken_agent.uid = Mock(side_effect=Exception("Database error"))
        
        result = AgentType.from_neomodel(broken_agent)
        
        # Should return None on error
        self.assertIsNone(result)
    
    def test_agent_assignment_type_from_neomodel_success(self):
        """Test successful conversion of AgentCommunityAssignment to GraphQL type."""
        result = AgentAssignmentType.from_neomodel(self.mock_assignment)
        
        # Verify conversion
        self.assertIsNotNone(result)
        self.assertEqual(result.uid, "assignment_123")
        self.assertEqual(result.status, "ACTIVE")
        self.assertEqual(result.permissions, ["custom_permission"])
        self.assertTrue(result.is_active)
        self.assertEqual(result.effective_permissions, ["edit_community", "custom_permission"])
    
    def test_agent_assignment_type_from_neomodel_error_handling(self):
        """Test AgentCommunityAssignment conversion error handling."""
        # Mock assignment that raises exception
        broken_assignment = Mock()
        broken_assignment.uid = Mock(side_effect=Exception("Database error"))
        
        result = AgentAssignmentType.from_neomodel(broken_assignment)
        
        # Should return None on error
        self.assertIsNone(result)
    
    def test_agent_action_log_type_from_django_model(self):
        """Test conversion of Django AgentActionLog to GraphQL type."""
        # Create mock Django model instance
        mock_log = Mock()
        mock_log.id = 1
        mock_log.agent_uid = "agent_123"
        mock_log.community_uid = "community_456"
        mock_log.action_type = "edit_community"
        mock_log.action_details = {"field": "description", "new_value": "Updated"}
        mock_log.timestamp = datetime(2024, 1, 1, 12, 0, 0)
        mock_log.success = True
        mock_log.error_message = None
        mock_log.execution_time_ms = 150
        mock_log.user_context = {"user_id": "user_789"}
        
        result = AgentActionLogType.from_django_model(mock_log)
        
        # Verify conversion
        self.assertEqual(result.id, 1)
        self.assertEqual(result.agent_uid, "agent_123")
        self.assertEqual(result.community_uid, "community_456")
        self.assertEqual(result.action_type, "edit_community")
        self.assertEqual(result.action_details, {"field": "description", "new_value": "Updated"})
        self.assertTrue(result.success)
        self.assertEqual(result.execution_time_ms, 150)
    
    def test_agent_memory_type_from_django_model(self):
        """Test conversion of Django AgentMemory to GraphQL type."""
        # Create mock Django model instance
        mock_memory = Mock()
        mock_memory.id = 1
        mock_memory.agent_uid = "agent_123"
        mock_memory.community_uid = "community_456"
        mock_memory.memory_type = "context"
        mock_memory.content = {"current_task": "test_task"}
        mock_memory.created_date = datetime(2024, 1, 1, 12, 0, 0)
        mock_memory.updated_date = datetime(2024, 1, 1, 12, 0, 0)
        mock_memory.expires_at = None
        mock_memory.priority = 1
        mock_memory.is_expired.return_value = False
        
        result = AgentMemoryType.from_django_model(mock_memory)
        
        # Verify conversion
        self.assertEqual(result.id, 1)
        self.assertEqual(result.agent_uid, "agent_123")
        self.assertEqual(result.community_uid, "community_456")
        self.assertEqual(result.memory_type, "context")
        self.assertEqual(result.content, {"current_task": "test_task"})
        self.assertEqual(result.priority, 1)
        self.assertFalse(result.is_expired)
    
    def test_agent_stats_type_from_stats_dict(self):
        """Test conversion of statistics dictionary to GraphQL type."""
        stats_dict = {
            'total_agents': 10,
            'active_agents': 8,
            'inactive_agents': 2,
            'suspended_agents': 0,
            'total_assignments': 15,
            'active_assignments': 12,
            'agents_by_type': {'COMMUNITY_LEADER': 5, 'MODERATOR': 3, 'ASSISTANT': 2},
            'assignments_by_community': {'comm1': 5, 'comm2': 7}
        }
        
        result = AgentStatsType.from_stats_dict(stats_dict)
        
        # Verify conversion
        self.assertEqual(result.total_agents, 10)
        self.assertEqual(result.active_agents, 8)
        self.assertEqual(result.inactive_agents, 2)
        self.assertEqual(result.suspended_agents, 0)
        self.assertEqual(result.total_assignments, 15)
        self.assertEqual(result.active_assignments, 12)
        self.assertEqual(result.agents_by_type, {'COMMUNITY_LEADER': 5, 'MODERATOR': 3, 'ASSISTANT': 2})
    
    def test_agent_memory_stats_type_from_stats_dict(self):
        """Test conversion of memory statistics dictionary to GraphQL type."""
        stats_dict = {
            'total_records': 25,
            'by_type': {'context': 10, 'conversation': 8, 'knowledge': 5, 'preferences': 2},
            'by_community': {'comm1': 15, 'comm2': 10},
            'expired_count': 3,
            'total_size_estimate': 1024000
        }
        
        result = AgentMemoryStatsType.from_stats_dict(stats_dict)
        
        # Verify conversion
        self.assertEqual(result.total_records, 25)
        self.assertEqual(result.by_type, {'context': 10, 'conversation': 8, 'knowledge': 5, 'preferences': 2})
        self.assertEqual(result.by_community, {'comm1': 15, 'comm2': 10})
        self.assertEqual(result.expired_count, 3)
        self.assertEqual(result.total_size_estimate, 1024000)
    
    def test_agent_audit_report_type_from_audit_dict(self):
        """Test conversion of audit dictionary to GraphQL type."""
        audit_dict = {
            'agent_uid': 'agent_123',
            'community_uid': 'community_456',
            'authenticated': True,
            'permissions': ['edit_community', 'moderate_users'],
            'permission_descriptions': {'edit_community': 'Edit community settings'},
            'available_actions': ['edit_community', 'moderate_user'],
            'is_admin': True,
            'recent_actions': [
                {
                    'action_type': 'edit_community',
                    'timestamp': '2024-01-01T12:00:00',
                    'success': True,
                    'error_message': None
                }
            ],
            'audit_timestamp': '2024-01-01T12:00:00'
        }
        
        result = AgentAuditReportType.from_audit_dict(audit_dict)
        
        # Verify conversion
        self.assertEqual(result.agent_uid, 'agent_123')
        self.assertEqual(result.community_uid, 'community_456')
        self.assertTrue(result.authenticated)
        self.assertEqual(result.permissions, ['edit_community', 'moderate_users'])
        self.assertTrue(result.is_admin)
        self.assertEqual(len(result.recent_actions), 1)
    
    @patch('agentic.graphql.types.generate_presigned_url')
    def test_agent_summary_type_from_neomodel_success(self, mock_generate_url):
        """Test successful conversion of Agent to summary GraphQL type."""
        # Mock file info generation
        mock_generate_url.generate_file_info.return_value = {
            'url': 'https://example.com/icon.png',
            'file_type': 'image/png'
        }
        
        result = AgentSummaryType.from_neomodel(self.mock_agent)
        
        # Verify conversion
        self.assertIsNotNone(result)
        self.assertEqual(result.uid, "agent_123")
        self.assertEqual(result.name, "Test Agent")
        self.assertEqual(result.agent_type, "COMMUNITY_LEADER")
        self.assertEqual(result.status, "ACTIVE")
        self.assertEqual(result.capabilities_count, 2)
        self.assertEqual(result.assignments_count, 0)
    
    def test_community_agent_summary_type_from_assignment(self):
        """Test conversion of assignment to community agent summary."""
        result = CommunityAgentSummaryType.from_assignment(self.mock_assignment)
        
        # Verify conversion
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.agent)
        self.assertIsNotNone(result.assignment)
        self.assertTrue(result.is_leader)  # Active assignment with COMMUNITY_LEADER type
        self.assertEqual(result.assignment_date, datetime(2024, 1, 1, 12, 0, 0))
    
    def test_community_agent_summary_type_error_handling(self):
        """Test community agent summary conversion error handling."""
        # Mock assignment that raises exception
        broken_assignment = Mock()
        broken_assignment.agent.single.side_effect = Exception("Database error")
        
        result = CommunityAgentSummaryType.from_assignment(broken_assignment)
        
        # Should return None on error
        self.assertIsNone(result)