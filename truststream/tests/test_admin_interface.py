# truststream/tests/test_admin_interface.py

"""
Unit Tests for TrustStream Admin Interface

This module contains comprehensive unit tests for the Admin Interface,
testing dashboard functionality, real-time monitoring, configuration management,
analytics, user management, and Streamlit integration.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from truststream.admin_interface import (
    TrustStreamAdminInterface, DashboardMetrics, SystemAlert,
    UserAppeal, ConfigurationUpdate, AnalyticsData
)


class TestDashboardMetrics(unittest.TestCase):
    """Test cases for DashboardMetrics data class."""
    
    def test_dashboard_metrics_creation(self):
        """Test DashboardMetrics creation with comprehensive data."""
        metrics = DashboardMetrics(
            total_content_analyzed=15420,
            content_approved=13876,
            content_flagged=1234,
            content_rejected=310,
            average_trust_score=0.742,
            active_users=8950,
            new_users_today=127,
            moderation_actions_today=89,
            system_health_score=0.94,
            ai_provider_uptime=0.987,
            agent_ecosystem_performance=0.91,
            cache_hit_rate=0.85,
            average_response_time=0.34,
            error_rate=0.002,
            timestamp=datetime.now()
        )
        
        self.assertEqual(metrics.total_content_analyzed, 15420)
        self.assertEqual(metrics.content_approved, 13876)
        self.assertEqual(metrics.content_flagged, 1234)
        self.assertEqual(metrics.content_rejected, 310)
        self.assertAlmostEqual(metrics.average_trust_score, 0.742, places=3)
        self.assertEqual(metrics.active_users, 8950)
        self.assertAlmostEqual(metrics.system_health_score, 0.94, places=2)


class TestSystemAlert(unittest.TestCase):
    """Test cases for SystemAlert data class."""
    
    def test_system_alert_creation(self):
        """Test SystemAlert creation with all severity levels."""
        alert = SystemAlert(
            alert_id="alert_12345",
            alert_type="performance_degradation",
            severity="high",
            title="AI Provider Response Time Spike",
            message="OpenAI provider response time has increased to 2.3s (threshold: 1.0s)",
            component="ai_providers",
            affected_services=["content_analysis", "real_time_moderation"],
            metrics={
                "current_response_time": 2.3,
                "threshold": 1.0,
                "duration_minutes": 15,
                "affected_requests": 234
            },
            timestamp=datetime.now(),
            acknowledged=False,
            resolved=False,
            resolution_notes=None
        )
        
        self.assertEqual(alert.alert_id, "alert_12345")
        self.assertEqual(alert.alert_type, "performance_degradation")
        self.assertEqual(alert.severity, "high")
        self.assertIn("OpenAI", alert.message)
        self.assertEqual(alert.component, "ai_providers")
        self.assertIn("content_analysis", alert.affected_services)
        self.assertFalse(alert.acknowledged)
        self.assertFalse(alert.resolved)


class TestUserAppeal(unittest.TestCase):
    """Test cases for UserAppeal data class."""
    
    def test_user_appeal_creation(self):
        """Test UserAppeal creation with complete information."""
        appeal = UserAppeal(
            appeal_id="appeal_67890",
            user_id="user_12345",
            username="@appealing_user",
            moderation_action_id="action_54321",
            original_action="temporary_ban",
            original_reason="Inappropriate content posted",
            appeal_reason="I believe this was a false positive. The content was satirical and not intended to be harmful.",
            evidence_provided=[
                "Context of the conversation showing satirical intent",
                "Similar approved content from other users",
                "Community feedback supporting the appeal"
            ],
            status="pending",
            priority="medium",
            submitted_at=datetime.now(),
            reviewed_by=None,
            reviewed_at=None,
            decision=None,
            decision_reason=None,
            metadata={
                "original_content": "The satirical post content",
                "community_id": "community_789",
                "trust_score_at_time": 0.65
            }
        )
        
        self.assertEqual(appeal.appeal_id, "appeal_67890")
        self.assertEqual(appeal.user_id, "user_12345")
        self.assertEqual(appeal.original_action, "temporary_ban")
        self.assertIn("false positive", appeal.appeal_reason)
        self.assertEqual(len(appeal.evidence_provided), 3)
        self.assertEqual(appeal.status, "pending")
        self.assertIsNone(appeal.reviewed_by)


class TestTrustStreamAdminInterface(unittest.TestCase):
    """Test cases for TrustStreamAdminInterface main class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.admin_interface = TrustStreamAdminInterface()
        
        # Mock configuration
        self.mock_config = {
            'dashboard_refresh_interval': 30,
            'alert_thresholds': {
                'response_time': 1.0,
                'error_rate': 0.01,
                'trust_score_drop': 0.1
            },
            'analytics_retention_days': 90,
            'max_appeals_per_page': 50
        }
        
        # Mock metrics data
        self.mock_metrics = DashboardMetrics(
            total_content_analyzed=10000,
            content_approved=8500,
            content_flagged=1200,
            content_rejected=300,
            average_trust_score=0.75,
            active_users=5000,
            new_users_today=50,
            moderation_actions_today=25,
            system_health_score=0.95,
            ai_provider_uptime=0.99,
            agent_ecosystem_performance=0.92,
            cache_hit_rate=0.88,
            average_response_time=0.25,
            error_rate=0.001,
            timestamp=datetime.now()
        )
    
    def test_admin_interface_initialization(self):
        """Test TrustStreamAdminInterface initialization."""
        self.assertIsInstance(self.admin_interface, TrustStreamAdminInterface)
        self.assertIsInstance(self.admin_interface.alerts, list)
        self.assertIsInstance(self.admin_interface.appeals, list)
        self.assertIsInstance(self.admin_interface.config_history, list)
    
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    def test_dashboard_setup(self, mock_title, mock_config):
        """Test dashboard setup and configuration."""
        self.admin_interface._setup_dashboard()
        
        mock_config.assert_called_once()
        mock_title.assert_called_once_with("TrustStream Admin Dashboard")
    
    @patch('truststream.admin_interface.TrustStreamAdminInterface._fetch_system_metrics')
    def test_metrics_collection(self, mock_fetch):
        """Test system metrics collection."""
        mock_fetch.return_value = self.mock_metrics
        
        metrics = self.admin_interface.get_current_metrics()
        
        self.assertIsInstance(metrics, DashboardMetrics)
        self.assertEqual(metrics.total_content_analyzed, 10000)
        self.assertEqual(metrics.content_approved, 8500)
        self.assertAlmostEqual(metrics.average_trust_score, 0.75, places=2)
        mock_fetch.assert_called_once()
    
    def test_alert_generation(self):
        """Test system alert generation."""
        # Test performance alert
        performance_metrics = {
            'response_time': 1.5,  # Above threshold
            'error_rate': 0.005,   # Below threshold
            'trust_score_drop': 0.15  # Above threshold
        }
        
        alerts = self.admin_interface._generate_alerts(performance_metrics, self.mock_config['alert_thresholds'])
        
        self.assertGreater(len(alerts), 0)
        
        # Should have alerts for response_time and trust_score_drop
        alert_types = [alert.alert_type for alert in alerts]
        self.assertIn('performance_degradation', alert_types)
        self.assertIn('trust_score_decline', alert_types)
        
        # Check alert details
        response_time_alert = next(alert for alert in alerts if alert.alert_type == 'performance_degradation')
        self.assertEqual(response_time_alert.severity, 'high')
        self.assertIn('response time', response_time_alert.message.lower())
    
    def test_alert_management(self):
        """Test alert acknowledgment and resolution."""
        # Create test alert
        alert = SystemAlert(
            alert_id="test_alert_001",
            alert_type="test_alert",
            severity="medium",
            title="Test Alert",
            message="This is a test alert",
            component="test_component",
            affected_services=["test_service"],
            metrics={},
            timestamp=datetime.now(),
            acknowledged=False,
            resolved=False,
            resolution_notes=None
        )
        
        self.admin_interface.alerts.append(alert)
        
        # Acknowledge alert
        self.admin_interface.acknowledge_alert("test_alert_001", "admin_user")
        
        updated_alert = next(a for a in self.admin_interface.alerts if a.alert_id == "test_alert_001")
        self.assertTrue(updated_alert.acknowledged)
        
        # Resolve alert
        self.admin_interface.resolve_alert("test_alert_001", "Issue resolved by restarting service", "admin_user")
        
        resolved_alert = next(a for a in self.admin_interface.alerts if a.alert_id == "test_alert_001")
        self.assertTrue(resolved_alert.resolved)
        self.assertIn("restarting service", resolved_alert.resolution_notes)
    
    @patch('streamlit.plotly_chart')
    def test_analytics_visualization(self, mock_chart):
        """Test analytics data visualization."""
        # Mock time series data
        dates = pd.date_range(start='2024-01-01', end='2024-01-07', freq='D')
        analytics_data = pd.DataFrame({
            'date': dates,
            'content_analyzed': np.random.randint(1000, 2000, len(dates)),
            'trust_score_avg': np.random.uniform(0.7, 0.8, len(dates)),
            'moderation_actions': np.random.randint(50, 150, len(dates))
        })
        
        # Test trust score trend visualization
        self.admin_interface._render_trust_score_trend(analytics_data)
        mock_chart.assert_called()
        
        # Test content analysis volume visualization
        self.admin_interface._render_content_analysis_volume(analytics_data)
        self.assertEqual(mock_chart.call_count, 2)
    
    def test_user_management(self):
        """Test user management functionality."""
        # Mock user data
        user_data = {
            'user_id': 'user_12345',
            'username': '@test_user',
            'trust_score': 0.65,
            'reputation_score': 0.72,
            'join_date': datetime.now() - timedelta(days=30),
            'last_active': datetime.now() - timedelta(hours=2),
            'total_posts': 150,
            'flagged_posts': 3,
            'moderation_actions': 1
        }
        
        # Test user search
        with patch('truststream.admin_interface.TrustStreamAdminInterface._search_users') as mock_search:
            mock_search.return_value = [user_data]
            
            results = self.admin_interface.search_users("test_user")
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['username'], '@test_user')
            mock_search.assert_called_once_with("test_user")
        
        # Test user trust score update
        with patch('truststream.admin_interface.TrustStreamAdminInterface._update_user_trust_score') as mock_update:
            mock_update.return_value = True
            
            result = self.admin_interface.update_user_trust_score('user_12345', 0.75, 'Manual adjustment by admin')
            
            self.assertTrue(result)
            mock_update.assert_called_once_with('user_12345', 0.75, 'Manual adjustment by admin')
    
    def test_appeal_management(self):
        """Test user appeal management."""
        # Create test appeal
        appeal = UserAppeal(
            appeal_id="test_appeal_001",
            user_id="user_12345",
            username="@appealing_user",
            moderation_action_id="action_54321",
            original_action="temporary_mute",
            original_reason="Spam posting",
            appeal_reason="This was not spam, just enthusiastic sharing",
            evidence_provided=["Screenshots of context", "Community support"],
            status="pending",
            priority="medium",
            submitted_at=datetime.now(),
            reviewed_by=None,
            reviewed_at=None,
            decision=None,
            decision_reason=None,
            metadata={}
        )
        
        self.admin_interface.appeals.append(appeal)
        
        # Test appeal review
        decision_result = self.admin_interface.review_appeal(
            "test_appeal_001",
            "approved",
            "Upon review, the content was not spam. Appeal granted.",
            "admin_reviewer"
        )
        
        self.assertTrue(decision_result)
        
        # Verify appeal was updated
        updated_appeal = next(a for a in self.admin_interface.appeals if a.appeal_id == "test_appeal_001")
        self.assertEqual(updated_appeal.status, "approved")
        self.assertEqual(updated_appeal.decision, "approved")
        self.assertEqual(updated_appeal.reviewed_by, "admin_reviewer")
        self.assertIsNotNone(updated_appeal.reviewed_at)
    
    def test_configuration_management(self):
        """Test system configuration management."""
        # Test configuration update
        config_update = ConfigurationUpdate(
            update_id="config_001",
            component="ai_providers",
            setting_name="response_timeout",
            old_value="30",
            new_value="45",
            reason="Increase timeout to reduce failures",
            updated_by="admin_user",
            timestamp=datetime.now(),
            applied=False,
            rollback_available=True
        )
        
        # Apply configuration update
        result = self.admin_interface.apply_configuration_update(config_update)
        
        self.assertTrue(result)
        self.assertIn(config_update, self.admin_interface.config_history)
        
        # Test configuration rollback
        rollback_result = self.admin_interface.rollback_configuration("config_001", "admin_user")
        
        self.assertTrue(rollback_result)
        
        # Verify rollback was logged
        rollback_entry = next(
            c for c in self.admin_interface.config_history 
            if c.update_id == "config_001_rollback"
        )
        self.assertEqual(rollback_entry.new_value, "30")  # Back to original value
    
    @patch('streamlit.dataframe')
    def test_real_time_monitoring(self, mock_dataframe):
        """Test real-time monitoring dashboard."""
        # Mock real-time data
        monitoring_data = pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now() - timedelta(minutes=10), 
                                     end=datetime.now(), freq='1min'),
            'active_users': np.random.randint(800, 1200, 11),
            'content_per_minute': np.random.randint(50, 150, 11),
            'moderation_actions': np.random.randint(0, 10, 11),
            'system_load': np.random.uniform(0.3, 0.8, 11)
        })
        
        # Render real-time monitoring
        self.admin_interface._render_real_time_monitoring(monitoring_data)
        
        mock_dataframe.assert_called()
    
    def test_ai_provider_monitoring(self):
        """Test AI provider performance monitoring."""
        # Mock AI provider metrics
        provider_metrics = {
            'openai': {
                'status': 'active',
                'response_time_avg': 0.8,
                'success_rate': 0.95,
                'requests_today': 1500,
                'cost_today': 12.50,
                'last_error': None
            },
            'claude': {
                'status': 'active',
                'response_time_avg': 0.6,
                'success_rate': 0.93,
                'requests_today': 1200,
                'cost_today': 8.75,
                'last_error': None
            },
            'gemini': {
                'status': 'degraded',
                'response_time_avg': 1.5,
                'success_rate': 0.87,
                'requests_today': 800,
                'cost_today': 6.20,
                'last_error': 'Rate limit exceeded at 14:30'
            }
        }
        
        # Test provider health assessment
        health_assessment = self.admin_interface._assess_provider_health(provider_metrics)
        
        self.assertIn('openai', health_assessment)
        self.assertIn('claude', health_assessment)
        self.assertIn('gemini', health_assessment)
        
        # OpenAI and Claude should be healthy
        self.assertEqual(health_assessment['openai']['status'], 'healthy')
        self.assertEqual(health_assessment['claude']['status'], 'healthy')
        
        # Gemini should be flagged as degraded
        self.assertEqual(health_assessment['gemini']['status'], 'degraded')
        self.assertIn('Rate limit', health_assessment['gemini']['issues'][0])
    
    def test_agent_ecosystem_monitoring(self):
        """Test agent ecosystem performance monitoring."""
        # Mock agent performance data
        agent_metrics = {
            'toxicity_detector_001': {
                'status': 'active',
                'total_tasks': 2500,
                'successful_tasks': 2375,
                'average_response_time': 0.3,
                'accuracy': 0.94,
                'last_active': datetime.now()
            },
            'quality_assessor_002': {
                'status': 'active',
                'total_tasks': 1800,
                'successful_tasks': 1620,
                'average_response_time': 0.45,
                'accuracy': 0.89,
                'last_active': datetime.now()
            },
            'bias_detector_003': {
                'status': 'inactive',
                'total_tasks': 1200,
                'successful_tasks': 1032,
                'average_response_time': 0.6,
                'accuracy': 0.86,
                'last_active': datetime.now() - timedelta(hours=2)
            }
        }
        
        # Test agent performance analysis
        performance_analysis = self.admin_interface._analyze_agent_performance(agent_metrics)
        
        self.assertIn('active_agents', performance_analysis)
        self.assertIn('inactive_agents', performance_analysis)
        self.assertIn('performance_summary', performance_analysis)
        
        self.assertEqual(performance_analysis['active_agents'], 2)
        self.assertEqual(performance_analysis['inactive_agents'], 1)
        
        # Check performance summary
        summary = performance_analysis['performance_summary']
        self.assertIn('average_accuracy', summary)
        self.assertIn('average_response_time', summary)
        self.assertGreater(summary['average_accuracy'], 0.8)
    
    def test_security_monitoring(self):
        """Test security monitoring and threat detection."""
        # Mock security events
        security_events = [
            {
                'event_id': 'sec_001',
                'event_type': 'suspicious_login',
                'severity': 'medium',
                'user_id': 'user_12345',
                'details': 'Login from unusual location',
                'timestamp': datetime.now() - timedelta(minutes=30)
            },
            {
                'event_id': 'sec_002',
                'event_type': 'rate_limit_exceeded',
                'severity': 'low',
                'user_id': 'user_67890',
                'details': 'API rate limit exceeded',
                'timestamp': datetime.now() - timedelta(minutes=15)
            },
            {
                'event_id': 'sec_003',
                'event_type': 'potential_abuse',
                'severity': 'high',
                'user_id': 'user_54321',
                'details': 'Multiple accounts from same IP posting similar content',
                'timestamp': datetime.now() - timedelta(minutes=5)
            }
        ]
        
        # Test security threat analysis
        threat_analysis = self.admin_interface._analyze_security_threats(security_events)
        
        self.assertIn('high_severity_count', threat_analysis)
        self.assertIn('medium_severity_count', threat_analysis)
        self.assertIn('low_severity_count', threat_analysis)
        self.assertIn('recent_threats', threat_analysis)
        
        self.assertEqual(threat_analysis['high_severity_count'], 1)
        self.assertEqual(threat_analysis['medium_severity_count'], 1)
        self.assertEqual(threat_analysis['low_severity_count'], 1)
        
        # Recent threats should include the high severity one
        recent_high_severity = [
            event for event in threat_analysis['recent_threats'] 
            if event['severity'] == 'high'
        ]
        self.assertEqual(len(recent_high_severity), 1)
        self.assertIn('potential_abuse', recent_high_severity[0]['event_type'])
    
    @patch('streamlit.success')
    @patch('streamlit.error')
    def test_bulk_operations(self, mock_error, mock_success):
        """Test bulk operations on users and content."""
        # Test bulk user trust score update
        user_updates = [
            {'user_id': 'user_001', 'new_trust_score': 0.8},
            {'user_id': 'user_002', 'new_trust_score': 0.6},
            {'user_id': 'user_003', 'new_trust_score': 0.9}
        ]
        
        with patch('truststream.admin_interface.TrustStreamAdminInterface._update_user_trust_score') as mock_update:
            mock_update.return_value = True
            
            results = self.admin_interface.bulk_update_user_trust_scores(
                user_updates, 
                "Bulk adjustment for community health",
                "admin_user"
            )
            
            self.assertEqual(len(results['successful']), 3)
            self.assertEqual(len(results['failed']), 0)
            self.assertEqual(mock_update.call_count, 3)
        
        # Test bulk content moderation
        content_actions = [
            {'content_id': 'content_001', 'action': 'approve'},
            {'content_id': 'content_002', 'action': 'flag'},
            {'content_id': 'content_003', 'action': 'reject'}
        ]
        
        with patch('truststream.admin_interface.TrustStreamAdminInterface._moderate_content') as mock_moderate:
            mock_moderate.return_value = True
            
            results = self.admin_interface.bulk_moderate_content(
                content_actions,
                "Bulk moderation review",
                "admin_user"
            )
            
            self.assertEqual(len(results['successful']), 3)
            self.assertEqual(len(results['failed']), 0)
            self.assertEqual(mock_moderate.call_count, 3)
    
    def test_export_functionality(self):
        """Test data export functionality."""
        # Test metrics export
        with patch('pandas.DataFrame.to_csv') as mock_to_csv:
            mock_to_csv.return_value = None
            
            export_result = self.admin_interface.export_metrics_data(
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now(),
                format='csv'
            )
            
            self.assertTrue(export_result)
            mock_to_csv.assert_called_once()
        
        # Test audit log export
        with patch('pandas.DataFrame.to_json') as mock_to_json:
            mock_to_json.return_value = '[]'
            
            export_result = self.admin_interface.export_audit_logs(
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                format='json'
            )
            
            self.assertTrue(export_result)
            mock_to_json.assert_called_once()


class TestAdminInterfaceIntegration(unittest.TestCase):
    """Integration tests for Admin Interface."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.admin_interface = TrustStreamAdminInterface()
    
    @patch('streamlit.run')
    def test_full_dashboard_integration(self, mock_run):
        """Test complete dashboard integration."""
        # Mock Streamlit app
        mock_run.return_value = None
        
        # Test dashboard launch
        self.admin_interface.launch_dashboard()
        
        mock_run.assert_called_once()
    
    @patch('truststream.admin_interface.TrustStreamAdminInterface._fetch_system_metrics')
    @patch('truststream.admin_interface.TrustStreamAdminInterface._fetch_ai_provider_metrics')
    @patch('truststream.admin_interface.TrustStreamAdminInterface._fetch_agent_metrics')
    def test_comprehensive_monitoring_integration(self, mock_agent_metrics, mock_provider_metrics, mock_system_metrics):
        """Test comprehensive monitoring integration."""
        # Mock all metrics
        mock_system_metrics.return_value = DashboardMetrics(
            total_content_analyzed=50000,
            content_approved=42500,
            content_flagged=6000,
            content_rejected=1500,
            average_trust_score=0.78,
            active_users=12000,
            new_users_today=200,
            moderation_actions_today=150,
            system_health_score=0.96,
            ai_provider_uptime=0.98,
            agent_ecosystem_performance=0.93,
            cache_hit_rate=0.89,
            average_response_time=0.28,
            error_rate=0.0015,
            timestamp=datetime.now()
        )
        
        mock_provider_metrics.return_value = {
            'openai': {'status': 'active', 'success_rate': 0.95},
            'claude': {'status': 'active', 'success_rate': 0.93}
        }
        
        mock_agent_metrics.return_value = {
            'toxicity_detector': {'status': 'active', 'accuracy': 0.94},
            'quality_assessor': {'status': 'active', 'accuracy': 0.89}
        }
        
        # Generate comprehensive monitoring report
        monitoring_report = self.admin_interface.generate_comprehensive_monitoring_report()
        
        self.assertIn('system_metrics', monitoring_report)
        self.assertIn('provider_metrics', monitoring_report)
        self.assertIn('agent_metrics', monitoring_report)
        self.assertIn('health_assessment', monitoring_report)
        
        # Verify all metrics were fetched
        mock_system_metrics.assert_called_once()
        mock_provider_metrics.assert_called_once()
        mock_agent_metrics.assert_called_once()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)