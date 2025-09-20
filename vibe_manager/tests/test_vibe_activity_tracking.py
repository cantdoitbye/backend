import pytest
from django.test import TestCase
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from auth_manager.models import Users
from user_activity.models import VibeActivity
from vibe_manager.services.vibe_activity_service import VibeActivityService
from vibe_manager.services.vibe_analytics_service import VibeAnalyticsService
from user_activity.services.activity_service import ActivityService


class TestVibeActivityTracking(TestCase):
    """Test suite for vibe activity tracking functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.test_user = Mock(spec=Users)
        self.test_user.user_id = 'test_user_123'
        self.test_user.username = 'testuser'
        self.test_user.email = 'test@example.com'
        
        # Create test vibe data
        self.test_vibe_data = {
            'vibe_id': 'vibe_123',
            'vibe_name': 'Test Vibe',
            'vibe_type': 'main',
            'category': 'motivation',
            'iq': 85,
            'aq': 90,
            'sq': 88,
            'hq': 92,
            'description': 'A test vibe for testing',
            'subCategory': 'personal_growth',
            'popularity': 75
        }
        
        # Mock request context
        self.mock_context = {
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Browser 1.0'
        }
    
    @patch('vibe_manager.services.vibe_activity_service.VibeActivity.objects.create')
    def test_track_vibe_creation_success(self, mock_create):
        """Test successful vibe creation tracking."""
        # Mock the created activity
        mock_activity = Mock()
        mock_activity.id = 1
        mock_create.return_value = mock_activity
        
        # Track vibe creation
        result = VibeActivityService.track_vibe_creation(
            user=self.test_user,
            vibe_data=self.test_vibe_data,
            success=True,
            **self.mock_context
        )
        
        # Assertions
        self.assertTrue(result)
        mock_create.assert_called_once()
        
        # Check the call arguments
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['user'], self.test_user)
        self.assertEqual(call_args['activity_type'], 'creation')
        self.assertEqual(call_args['vibe_name'], 'Test Vibe')
        self.assertEqual(call_args['vibe_type'], 'main')
        self.assertTrue(call_args['success'])
        self.assertEqual(call_args['ip_address'], '127.0.0.1')
    
    @patch('vibe_manager.services.vibe_activity_service.VibeActivity.objects.create')
    def test_track_vibe_creation_failure(self, mock_create):
        """Test failed vibe creation tracking."""
        mock_activity = Mock()
        mock_activity.id = 2
        mock_create.return_value = mock_activity
        
        # Track failed vibe creation
        result = VibeActivityService.track_vibe_creation(
            user=self.test_user,
            vibe_data=self.test_vibe_data,
            success=False,
            error_message="Validation failed",
            **self.mock_context
        )
        
        # Assertions
        self.assertTrue(result)
        mock_create.assert_called_once()
        
        call_args = mock_create.call_args[1]
        self.assertFalse(call_args['success'])
        self.assertEqual(call_args['error_message'], "Validation failed")
    
    @patch('vibe_manager.services.vibe_activity_service.VibeActivity.objects.create')
    def test_track_vibe_sending_success(self, mock_create):
        """Test successful vibe sending tracking."""
        # Create receiver user
        receiver_user = Mock(spec=Users)
        receiver_user.user_id = 'receiver_123'
        receiver_user.username = 'receiver'
        
        mock_activity = Mock()
        mock_activity.id = 3
        mock_create.return_value = mock_activity
        
        # Track vibe sending
        result = VibeActivityService.track_vibe_sending(
            sender=self.test_user,
            receiver=receiver_user,
            vibe_data=self.test_vibe_data,
            success=True,
            **self.mock_context
        )
        
        # Assertions
        self.assertTrue(result)
        mock_create.assert_called_once()
        
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['user'], self.test_user)
        self.assertEqual(call_args['activity_type'], 'sending')
        self.assertEqual(call_args['target_user'], receiver_user)
        self.assertTrue(call_args['success'])
    
    @patch('vibe_manager.services.vibe_activity_service.VibeActivity.objects.create')
    def test_track_vibe_viewing(self, mock_create):
        """Test vibe viewing tracking."""
        mock_activity = Mock()
        mock_activity.id = 4
        mock_create.return_value = mock_activity
        
        # Track vibe viewing
        result = VibeActivityService.track_vibe_viewing(
            user=self.test_user,
            vibe_data=self.test_vibe_data,
            duration_seconds=45,
            **self.mock_context
        )
        
        # Assertions
        self.assertTrue(result)
        mock_create.assert_called_once()
        
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['activity_type'], 'viewing')
        self.assertEqual(call_args['additional_context']['duration_seconds'], 45)
    
    @patch('vibe_manager.services.vibe_activity_service.VibeActivity.objects.create')
    def test_track_vibe_search(self, mock_create):
        """Test vibe search tracking."""
        mock_activity = Mock()
        mock_activity.id = 5
        mock_create.return_value = mock_activity
        
        # Track vibe search
        result = VibeActivityService.track_vibe_search(
            user=self.test_user,
            search_query="motivation vibes",
            results_count=15,
            **self.mock_context
        )
        
        # Assertions
        self.assertTrue(result)
        mock_create.assert_called_once()
        
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['activity_type'], 'search')
        self.assertEqual(call_args['additional_context']['search_query'], "motivation vibes")
        self.assertEqual(call_args['additional_context']['results_count'], 15)
    
    @patch('vibe_manager.services.vibe_activity_service.VibeActivity.objects.filter')
    def test_get_user_vibe_summary(self, mock_filter):
        """Test getting user vibe activity summary."""
        # Mock queryset
        mock_queryset = Mock()
        mock_queryset.count.return_value = 10
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset
        
        # Get summary
        summary = VibeActivityService.get_user_vibe_summary(
            user=self.test_user,
            days=7
        )
        
        # Assertions
        self.assertIsInstance(summary, dict)
        mock_filter.assert_called_once_with(user=self.test_user)
    
    def test_track_creation_with_exception(self):
        """Test tracking handles exceptions gracefully."""
        with patch('vibe_manager.services.vibe_activity_service.VibeActivity.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            # Should not raise exception
            result = VibeActivityService.track_vibe_creation(
                user=self.test_user,
                vibe_data=self.test_vibe_data,
                success=True
            )
            
            # Should return False on exception
            self.assertFalse(result)


class TestVibeAnalyticsService(TestCase):
    """Test suite for vibe analytics functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.test_user = Mock(spec=Users)
        self.test_user.user_id = 'analytics_user_123'
        self.test_user.username = 'analyticsuser'
    
    @patch('vibe_manager.services.vibe_analytics_service.VibeActivity.objects.filter')
    def test_get_vibe_activity_summary(self, mock_filter):
        """Test vibe activity summary generation."""
        # Mock queryset and aggregations
        mock_queryset = Mock()
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = [
            {'activity_type': 'creation', 'count': 5, 'success_rate': 0.8},
            {'activity_type': 'sending', 'count': 10, 'success_rate': 0.9}
        ]
        mock_queryset.aggregate.return_value = {
            'total_activities': 15,
            'successful_activities': 13,
            'failed_activities': 2
        }
        mock_queryset.extra.return_value = mock_queryset
        mock_filter.return_value = mock_queryset
        
        # Get summary
        summary = VibeAnalyticsService.get_vibe_activity_summary(
            user=self.test_user,
            days=30
        )
        
        # Assertions
        self.assertIsInstance(summary, dict)
        self.assertIn('period', summary)
        self.assertIn('overview', summary)
        self.assertIn('activity_breakdown', summary)
        
        # Check overview data
        overview = summary['overview']
        self.assertEqual(overview['total_activities'], 15)
        self.assertEqual(overview['successful_activities'], 13)
        self.assertEqual(overview['failed_activities'], 2)
    
    @patch('vibe_manager.services.vibe_analytics_service.VibeActivity.objects.filter')
    def test_get_vibe_creation_analytics(self, mock_filter):
        """Test vibe creation analytics."""
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {
            'total_attempts': 8,
            'successful_creations': 7,
            'failed_creations': 1,
            'avg_iq': 85.5,
            'avg_aq': 88.2,
            'avg_sq': 87.1,
            'avg_hq': 89.3
        }
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = []
        mock_queryset.extra.return_value = mock_queryset
        mock_filter.return_value = mock_queryset
        
        # Get creation analytics
        analytics = VibeAnalyticsService.get_vibe_creation_analytics(
            user=self.test_user,
            days=30
        )
        
        # Assertions
        self.assertIsInstance(analytics, dict)
        self.assertIn('creation_overview', analytics)
        self.assertIn('quality_analysis', analytics)
        
        creation_overview = analytics['creation_overview']
        self.assertEqual(creation_overview['total_attempts'], 8)
        self.assertEqual(creation_overview['successful_creations'], 7)
    
    @patch('vibe_manager.services.vibe_analytics_service.VibeActivity.objects.filter')
    def test_get_real_time_stats(self, mock_filter):
        """Test real-time statistics."""
        mock_queryset = Mock()
        mock_queryset.aggregate.return_value = {
            'total_activities': 25,
            'creations': 8,
            'sendings': 12,
            'viewings': 4,
            'searches': 1,
            'unique_users': 5
        }
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.values.return_value = []
        mock_filter.return_value = mock_queryset
        
        # Get real-time stats
        stats = VibeAnalyticsService.get_real_time_vibe_stats()
        
        # Assertions
        self.assertIsInstance(stats, dict)
        self.assertIn('timestamp', stats)
        self.assertIn('last_24_hours', stats)
        self.assertIn('last_1_hour', stats)
        self.assertIn('recent_activities', stats)
    
    def test_analytics_with_exception(self):
        """Test analytics handles exceptions gracefully."""
        with patch('vibe_manager.services.vibe_analytics_service.VibeActivity.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception("Database connection error")
            
            # Should not raise exception
            result = VibeAnalyticsService.get_vibe_activity_summary()
            
            # Should return error dict
            self.assertIn('error', result)
            self.assertEqual(result['error'], 'Failed to generate activity summary')


class TestActivityServiceIntegration(TestCase):
    """Test suite for activity service integration with vibe analytics."""
    
    def setUp(self):
        """Set up test data."""
        self.test_user = Mock(spec=Users)
        self.test_user.user_id = 'integration_user_123'
        self.activity_service = ActivityService()
    
    @patch('user_activity.services.activity_service.VibeAnalyticsService')
    def test_get_comprehensive_analytics(self, mock_vibe_analytics):
        """Test comprehensive analytics integration."""
        # Mock vibe analytics responses
        mock_vibe_analytics.get_vibe_activity_summary.return_value = {
            'overview': {'total_activities': 20}
        }
        mock_vibe_analytics.get_vibe_engagement_metrics.return_value = {
            'engagement_overview': {'unique_users': 5}
        }
        
        # Mock regular analytics
        with patch.object(self.activity_service, 'get_user_activity_summary') as mock_regular:
            mock_regular.return_value = {'total_activities': 15}
            
            # Get comprehensive analytics
            result = self.activity_service.get_comprehensive_analytics(
                user=self.test_user,
                days=30
            )
            
            # Assertions
            self.assertIsInstance(result, dict)
            self.assertIn('user_analytics', result)
            self.assertIn('vibe_analytics', result)
            self.assertIn('vibe_engagement', result)
            self.assertIn('combined_summary', result)
            
            # Check combined total
            combined = result['combined_summary']
            self.assertEqual(combined['total_activities'], 35)  # 15 + 20
    
    @patch('user_activity.services.activity_service.VibeAnalyticsService')
    def test_get_vibe_activity_insights(self, mock_vibe_analytics):
        """Test vibe activity insights."""
        # Mock all vibe analytics methods
        mock_vibe_analytics.get_vibe_activity_summary.return_value = {'summary': 'data'}
        mock_vibe_analytics.get_vibe_creation_analytics.return_value = {'creation': 'data'}
        mock_vibe_analytics.get_vibe_engagement_metrics.return_value = {'engagement': 'data'}
        mock_vibe_analytics.get_real_time_vibe_stats.return_value = {'realtime': 'data'}
        
        # Get insights
        result = self.activity_service.get_vibe_activity_insights(
            user=self.test_user,
            days=7
        )
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn('activity_summary', result)
        self.assertIn('creation_analytics', result)
        self.assertIn('engagement_metrics', result)
        self.assertIn('real_time_stats', result)
        
        # Verify all methods were called
        mock_vibe_analytics.get_vibe_activity_summary.assert_called_once_with(self.test_user, 7)
        mock_vibe_analytics.get_vibe_creation_analytics.assert_called_once_with(self.test_user, 7)
        mock_vibe_analytics.get_vibe_engagement_metrics.assert_called_once_with(self.test_user, 7)
        mock_vibe_analytics.get_real_time_vibe_stats.assert_called_once()


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])