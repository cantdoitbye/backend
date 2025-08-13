# Agent Webhook Service Tests
# This module contains tests for the agent webhook service.

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from django.test import TestCase
from datetime import datetime
import json

from ..services.webhook_service import (
    AgentWebhookService, WebhookError, WebhookDeliveryError, 
    WebhookConfigurationError, webhook_service
)


class AgentWebhookServiceTest(TestCase):
    """Test cases for AgentWebhookService class."""
    
    def setUp(self):
        """Set up test data."""
        self.webhook_service = AgentWebhookService()
        
        # Mock auth service
        self.mock_auth_service = Mock()
        self.mock_auth_service.log_agent_action.return_value = Mock()
        self.webhook_service.auth_service = self.mock_auth_service
    
    def test_register_webhook_endpoint_success(self):
        """Test successful webhook endpoint registration."""
        self.webhook_service.register_webhook_endpoint(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["agent.assigned", "agent.action"],
            secret="test_secret",
            headers={"Authorization": "Bearer token"}
        )
        
        # Verify endpoint was registered
        self.assertIn("test_webhook", self.webhook_service.webhook_endpoints)
        
        endpoint = self.webhook_service.webhook_endpoints["test_webhook"]
        self.assertEqual(endpoint['url'], "https://example.com/webhook")
        self.assertEqual(endpoint['events'], ["agent.assigned", "agent.action"])
        self.assertEqual(endpoint['secret'], "test_secret")
        self.assertEqual(endpoint['headers']['Authorization'], "Bearer token")
        self.assertTrue(endpoint['active'])
    
    def test_register_webhook_endpoint_invalid_url(self):
        """Test webhook registration with invalid URL."""
        with self.assertRaises(WebhookConfigurationError) as context:
            self.webhook_service.register_webhook_endpoint(
                name="invalid_webhook",
                url="not-a-valid-url",
                events=["agent.assigned"]
            )
        
        self.assertIn("Invalid webhook URL", str(context.exception))
    
    def test_register_webhook_endpoint_empty_events(self):
        """Test webhook registration with empty events list."""
        with self.assertRaises(WebhookConfigurationError) as context:
            self.webhook_service.register_webhook_endpoint(
                name="no_events_webhook",
                url="https://example.com/webhook",
                events=[]
            )
        
        self.assertIn("Events list cannot be empty", str(context.exception))
    
    def test_unregister_webhook_endpoint_success(self):
        """Test successful webhook endpoint unregistration."""
        # First register an endpoint
        self.webhook_service.register_webhook_endpoint(
            name="temp_webhook",
            url="https://example.com/webhook",
            events=["agent.assigned"]
        )
        
        # Then unregister it
        result = self.webhook_service.unregister_webhook_endpoint("temp_webhook")
        
        self.assertTrue(result)
        self.assertNotIn("temp_webhook", self.webhook_service.webhook_endpoints)
    
    def test_unregister_webhook_endpoint_not_found(self):
        """Test unregistering non-existent webhook endpoint."""
        result = self.webhook_service.unregister_webhook_endpoint("nonexistent_webhook")
        
        self.assertFalse(result)
    
    def test_register_event_handler(self):
        """Test event handler registration."""
        def test_handler(event_payload):
            pass
        
        self.webhook_service.register_event_handler("test.event", test_handler)
        
        # Verify handler was registered
        self.assertIn("test.event", self.webhook_service.event_handlers)
        self.assertIn(test_handler, self.webhook_service.event_handlers["test.event"])
    
    @pytest.mark.asyncio
    async def test_dispatch_event_success(self):
        """Test successful event dispatching."""
        # Register a webhook endpoint
        self.webhook_service.register_webhook_endpoint(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["test.event"]
        )
        
        # Register an event handler
        handler_called = False
        def test_handler(event_payload):
            nonlocal handler_called
            handler_called = True
        
        self.webhook_service.register_event_handler("test.event", test_handler)
        
        # Mock webhook delivery
        with patch.object(self.webhook_service, '_dispatch_to_webhooks', new_callable=AsyncMock) as mock_webhook_dispatch:
            mock_webhook_dispatch.return_value = [{'webhook_name': 'test_webhook', 'success': True}]
            
            with patch.object(self.webhook_service, '_dispatch_to_handlers', new_callable=AsyncMock) as mock_handler_dispatch:
                mock_handler_dispatch.return_value = [{'handler_index': 0, 'success': True}]
                
                # Dispatch event
                result = await self.webhook_service.dispatch_event(
                    event_type="test.event",
                    event_data={"test": "data"},
                    source_agent_uid="agent_123",
                    source_community_uid="community_456"
                )
        
        # Verify result
        self.assertIn('event_id', result)
        self.assertEqual(result['event_type'], 'test.event')
        self.assertIn('webhook_results', result)
        self.assertIn('handler_results', result)
        
        # Verify action was logged
        self.mock_auth_service.log_agent_action.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dispatch_to_webhooks_success(self):
        """Test successful webhook dispatching."""
        # Register webhook endpoints
        self.webhook_service.register_webhook_endpoint(
            name="webhook1",
            url="https://example.com/webhook1",
            events=["test.event"]
        )
        
        self.webhook_service.register_webhook_endpoint(
            name="webhook2",
            url="https://example.com/webhook2",
            events=["other.event"]  # Should not receive test.event
        )
        
        event_payload = {
            'event_type': 'test.event',
            'data': {'test': 'data'}
        }
        
        # Mock webhook delivery
        with patch.object(self.webhook_service, '_deliver_webhook', new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = {'webhook_name': 'webhook1', 'success': True}
            
            result = await self.webhook_service._dispatch_to_webhooks('test.event', event_payload)
        
        # Verify only webhook1 was called (webhook2 doesn't subscribe to test.event)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['webhook_name'], 'webhook1')
        mock_deliver.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dispatch_to_handlers_success(self):
        """Test successful handler dispatching."""
        # Register event handlers
        handler1_called = False
        handler2_called = False
        
        def handler1(event_payload):
            nonlocal handler1_called
            handler1_called = True
        
        async def handler2(event_payload):
            nonlocal handler2_called
            handler2_called = True
        
        self.webhook_service.register_event_handler("test.event", handler1)
        self.webhook_service.register_event_handler("test.event", handler2)
        
        event_payload = {
            'event_type': 'test.event',
            'data': {'test': 'data'}
        }
        
        result = await self.webhook_service._dispatch_to_handlers('test.event', event_payload)
        
        # Verify both handlers were executed
        self.assertEqual(len(result), 2)
        self.assertTrue(all(r['success'] for r in result))
        self.assertTrue(handler1_called)
        self.assertTrue(handler2_called)
    
    @pytest.mark.asyncio
    async def test_dispatch_to_handlers_with_error(self):
        """Test handler dispatching with one handler failing."""
        def good_handler(event_payload):
            pass
        
        def bad_handler(event_payload):
            raise Exception("Handler error")
        
        self.webhook_service.register_event_handler("test.event", good_handler)
        self.webhook_service.register_event_handler("test.event", bad_handler)
        
        event_payload = {
            'event_type': 'test.event',
            'data': {'test': 'data'}
        }
        
        result = await self.webhook_service._dispatch_to_handlers('test.event', event_payload)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]['success'])  # good_handler
        self.assertFalse(result[1]['success'])  # bad_handler
        self.assertIn('error', result[1])
    
    @pytest.mark.asyncio
    async def test_deliver_webhook_success(self):
        """Test successful webhook delivery."""
        webhook_config = {
            'url': 'https://example.com/webhook',
            'headers': {},
            'secret': None,
            'delivery_count': 0,
            'failure_count': 0
        }
        
        event_payload = {
            'event_type': 'test.event',
            'data': {'test': 'data'}
        }
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await self.webhook_service._deliver_webhook(
                'test_webhook', webhook_config, event_payload
            )
        
        # Verify successful delivery
        self.assertTrue(result['success'])
        self.assertEqual(result['webhook_name'], 'test_webhook')
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['attempt'], 1)
        
        # Verify webhook stats were updated
        self.assertEqual(webhook_config['delivery_count'], 1)
        self.assertIsNotNone(webhook_config['last_delivery'])
    
    @pytest.mark.asyncio
    async def test_deliver_webhook_with_retries(self):
        """Test webhook delivery with retries."""
        webhook_config = {
            'url': 'https://example.com/webhook',
            'headers': {},
            'secret': None,
            'delivery_count': 0,
            'failure_count': 0
        }
        
        event_payload = {
            'event_type': 'test.event',
            'data': {'test': 'data'}
        }
        
        # Mock aiohttp to fail first two attempts, succeed on third
        call_count = 0
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = AsyncMock()
            if call_count <= 2:
                mock_response.status = 500  # Server error
            else:
                mock_response.status = 200  # Success
            
            mock_response.__aenter__.return_value = mock_response
            mock_response.__aexit__.return_value = None
            return mock_response
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up test
                result = await self.webhook_service._deliver_webhook(
                    'test_webhook', webhook_config, event_payload
                )
        
        # Verify successful delivery after retries
        self.assertTrue(result['success'])
        self.assertEqual(result['attempt'], 3)  # Third attempt succeeded
        self.assertEqual(call_count, 3)
    
    def test_generate_signature(self):
        """Test webhook signature generation."""
        payload = {'test': 'data', 'number': 123}
        secret = 'test_secret'
        
        signature = self.webhook_service._generate_signature(payload, secret)
        
        # Verify signature format
        self.assertTrue(signature.startswith('sha256='))
        self.assertEqual(len(signature), 71)  # sha256= + 64 hex chars
    
    def test_get_webhook_stats(self):
        """Test webhook statistics retrieval."""
        # Register some webhooks with different stats
        self.webhook_service.register_webhook_endpoint(
            name="webhook1",
            url="https://example.com/webhook1",
            events=["test.event"]
        )
        
        self.webhook_service.register_webhook_endpoint(
            name="webhook2",
            url="https://example.com/webhook2",
            events=["other.event"],
            active=False
        )
        
        # Simulate some deliveries
        self.webhook_service.webhook_endpoints["webhook1"]["delivery_count"] = 10
        self.webhook_service.webhook_endpoints["webhook1"]["failure_count"] = 2
        
        stats = self.webhook_service.get_webhook_stats()
        
        # Verify stats
        self.assertEqual(stats['total_endpoints'], 2)
        self.assertEqual(stats['active_endpoints'], 1)  # Only webhook1 is active
        self.assertEqual(stats['total_deliveries'], 10)
        self.assertEqual(stats['total_failures'], 2)
        
        # Verify endpoint-specific stats
        webhook1_stats = stats['endpoints']['webhook1']
        self.assertEqual(webhook1_stats['delivery_count'], 10)
        self.assertEqual(webhook1_stats['failure_count'], 2)
        self.assertEqual(webhook1_stats['success_rate'], 0.8)  # (10-2)/10
    
    @pytest.mark.asyncio
    async def test_dispatch_agent_assigned(self):
        """Test agent assignment event dispatching."""
        with patch.object(self.webhook_service, 'dispatch_event', new_callable=AsyncMock) as mock_dispatch:
            mock_dispatch.return_value = {'event_id': 'test_event_id'}
            
            result = await self.webhook_service.dispatch_agent_assigned(
                agent_uid="agent_123",
                community_uid="community_456",
                assignment_uid="assignment_789",
                assigned_by_uid="user_101"
            )
        
        # Verify dispatch_event was called with correct parameters
        mock_dispatch.assert_called_once_with(
            event_type='agent.assigned',
            event_data={
                'agent_uid': 'agent_123',
                'community_uid': 'community_456',
                'assignment_uid': 'assignment_789',
                'assigned_by_uid': 'user_101'
            },
            source_agent_uid='agent_123',
            source_community_uid='community_456'
        )
    
    @pytest.mark.asyncio
    async def test_dispatch_agent_action(self):
        """Test agent action event dispatching."""
        with patch.object(self.webhook_service, 'dispatch_event', new_callable=AsyncMock) as mock_dispatch:
            mock_dispatch.return_value = {'event_id': 'test_event_id'}
            
            result = await self.webhook_service.dispatch_agent_action(
                agent_uid="agent_123",
                community_uid="community_456",
                action_type="edit_community",
                action_details={"field": "name", "new_value": "Updated Name"}
            )
        
        # Verify dispatch_event was called with correct parameters
        mock_dispatch.assert_called_once_with(
            event_type='agent.action',
            event_data={
                'agent_uid': 'agent_123',
                'community_uid': 'community_456',
                'action_type': 'edit_community',
                'action_details': {"field": "name", "new_value": "Updated Name"}
            },
            source_agent_uid='agent_123',
            source_community_uid='community_456'
        )
    
    @pytest.mark.asyncio
    async def test_dispatch_community_updated(self):
        """Test community update event dispatching."""
        with patch.object(self.webhook_service, 'dispatch_event', new_callable=AsyncMock) as mock_dispatch:
            mock_dispatch.return_value = {'event_id': 'test_event_id'}
            
            result = await self.webhook_service.dispatch_community_updated(
                agent_uid="agent_123",
                community_uid="community_456",
                updates={"name": "New Name", "description": "New Description"}
            )
        
        # Verify dispatch_event was called with correct parameters
        mock_dispatch.assert_called_once_with(
            event_type='community.updated',
            event_data={
                'community_uid': 'community_456',
                'updates': {"name": "New Name", "description": "New Description"},
                'updated_by_agent': 'agent_123'
            },
            source_agent_uid='agent_123',
            source_community_uid='community_456'
        )
    
    @pytest.mark.asyncio
    async def test_dispatch_user_moderated(self):
        """Test user moderation event dispatching."""
        with patch.object(self.webhook_service, 'dispatch_event', new_callable=AsyncMock) as mock_dispatch:
            mock_dispatch.return_value = {'event_id': 'test_event_id'}
            
            result = await self.webhook_service.dispatch_user_moderated(
                agent_uid="agent_123",
                community_uid="community_456",
                target_user_uid="user_789",
                action="mute",
                reason="Inappropriate behavior"
            )
        
        # Verify dispatch_event was called with correct parameters
        mock_dispatch.assert_called_once_with(
            event_type='user.moderated',
            event_data={
                'community_uid': 'community_456',
                'target_user_uid': 'user_789',
                'moderation_action': 'mute',
                'reason': 'Inappropriate behavior',
                'moderated_by_agent': 'agent_123'
            },
            source_agent_uid='agent_123',
            source_community_uid='community_456'
        )