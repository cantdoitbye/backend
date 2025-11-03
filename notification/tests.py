"""
Tests for Unified Notification Service
"""

import asyncio
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, AsyncMock, MagicMock

from notification.services import UnifiedNotificationService, NotificationBuilder, NotificationDispatcher
from notification.enums import NotificationType, NotificationPriority
from notification.models import NotificationLog, NotificationPreference


class NotificationBuilderTestCase(TestCase):
    """Test notification builder"""
    
    def test_basic_build(self):
        """Test basic notification building"""
        builder = NotificationBuilder()
        notification = (
            builder
            .set_title("Test Title")
            .set_body("Test Body")
            .set_recipient("device123")
            .set_notification_type(NotificationType.NEW_POST)
            .build()
        )
        
        self.assertEqual(notification['title'], "Test Title")
        self.assertEqual(notification['body'], "Test Body")
        self.assertEqual(notification['token'], "device123")
        self.assertEqual(notification['data']['type'], "new_post")
    
    def test_quick_build(self):
        """Test quick build method"""
        notification = NotificationBuilder.quick_build(
            title="Quick Test",
            body="Quick Body",
            recipient="device456",
            notification_type=NotificationType.NEW_COMMENT,
            click_action="/post/123"
        )
        
        self.assertEqual(notification['title'], "Quick Test")
        self.assertEqual(notification['click_action'], "/post/123")
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise errors"""
        builder = NotificationBuilder()
        
        with self.assertRaises(ValueError):
            builder.set_title("Title").build()  # Missing body and recipient
        
        with self.assertRaises(ValueError):
            builder.set_body("Body").build()  # Missing title and recipient


class NotificationDispatcherTestCase(TestCase):
    """Test notification dispatcher"""
    
    @patch('aiohttp.ClientSession')
    async def test_send_single_success(self, mock_session):
        """Test successful single notification send"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"success": true}')
        
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        dispatcher = NotificationDispatcher()
        
        notification_data = {
            "title": "Test",
            "body": "Test body",
            "token": "device123",
            "data": {"type": "new_post"}
        }
        
        result = await dispatcher.send_single(notification_data, log_to_db=False)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 200)
    
    @patch('aiohttp.ClientSession')
    async def test_send_batch(self, mock_session):
        """Test batch notification sending"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"success": true}')
        
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        dispatcher = NotificationDispatcher()
        
        notifications = [
            {"title": "Test 1", "body": "Body 1", "token": "device1", "data": {"type": "test"}},
            {"title": "Test 2", "body": "Body 2", "token": "device2", "data": {"type": "test"}},
        ]
        
        results = await dispatcher.send_batch(notifications, log_to_db=False)
        
        self.assertEqual(len(results), 2)


class UnifiedNotificationServiceTestCase(TestCase):
    """Test unified notification service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = UnifiedNotificationService()
    
    @patch.object(NotificationDispatcher, 'send_to_multiple_recipients')
    async def test_notify_new_post(self, mock_send):
        """Test notify new post"""
        mock_send.return_value = [{'success': True}]
        
        followers = [
            {'device_id': 'device1', 'uid': 'user1'},
            {'device_id': 'device2', 'uid': 'user2'},
        ]
        
        result = await self.service.notify_new_post(
            post_creator_name="John",
            followers=followers,
            post_id="post123"
        )
        
        mock_send.assert_called_once()
        self.assertEqual(len(result), 1)
    
    @patch.object(NotificationDispatcher, 'send_single')
    async def test_notify_connection_request(self, mock_send):
        """Test notify connection request"""
        mock_send.return_value = {'success': True}
        
        result = await self.service.notify_connection_request(
            sender_name="Alice",
            receiver_device_id="device123",
            connection_id="conn123"
        )
        
        mock_send.assert_called_once()
        self.assertTrue(result['success'])
    
    def test_run_async_helper(self):
        """Test run_async helper method"""
        async def dummy_coro():
            return "success"
        
        result = self.service.run_async(dummy_coro())
        self.assertEqual(result, "success")


class NotificationModelTestCase(TestCase):
    """Test notification models"""
    
    def test_notification_log_creation(self):
        """Test creating notification log"""
        log = NotificationLog.objects.create(
            notification_type="new_post",
            recipient_count=5,
            status="sent",
            metadata={"test": "data"}
        )
        
        self.assertEqual(log.notification_type, "new_post")
        self.assertEqual(log.recipient_count, 5)
        self.assertEqual(log.status, "sent")
    
    def test_notification_preference(self):
        """Test user notification preference"""
        user = User.objects.create_user(username="testuser", password="testpass")
        
        pref = NotificationPreference.objects.create(
            user=user,
            notification_type="new_post",
            is_enabled=False
        )
        
        self.assertEqual(pref.user, user)
        self.assertEqual(pref.notification_type, "new_post")
        self.assertFalse(pref.is_enabled)


class NotificationEnumTestCase(TestCase):
    """Test notification enums"""
    
    def test_notification_types(self):
        """Test notification type enum"""
        self.assertEqual(NotificationType.NEW_POST.value, "new_post")
        self.assertEqual(NotificationType.CONNECTION_REQUEST.value, "connection_request")
    
    def test_priority_auto_detection(self):
        """Test automatic priority detection"""
        priority = NotificationPriority.get_priority_for_type("connection_request")
        self.assertEqual(priority, NotificationPriority.HIGH)
        
        priority = NotificationPriority.get_priority_for_type("profile_view")
        self.assertEqual(priority, NotificationPriority.LOW)
        
        priority = NotificationPriority.get_priority_for_type("new_post")
        self.assertEqual(priority, NotificationPriority.NORMAL)
    
    def test_notification_category(self):
        """Test notification category detection"""
        category = NotificationType.get_category(NotificationType.NEW_POST)
        self.assertEqual(category, "post")
        
        category = NotificationType.get_category(NotificationType.CONNECTION_REQUEST)
        self.assertEqual(category, "connection")


