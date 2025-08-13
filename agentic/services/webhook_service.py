# Agent Webhook Service
# This module provides webhook functionality for agent events and notifications.

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
import logging
import asyncio
import aiohttp
from urllib.parse import urlparse

from ..models import AgentActionLog
from .auth_service import AgentAuthService


logger = logging.getLogger(__name__)


class WebhookError(Exception):
    """Base exception for webhook errors."""
    pass


class WebhookDeliveryError(WebhookError):
    """Raised when webhook delivery fails."""
    pass


class WebhookConfigurationError(WebhookError):
    """Raised when webhook configuration is invalid."""
    pass


class AgentWebhookService:
    """
    Service for managing and dispatching agent-related webhooks.
    
    This service provides comprehensive webhook functionality for agent events,
    including event dispatching, delivery management, and retry logic.
    """
    
    def __init__(self):
        """Initialize the webhook service."""
        self.auth_service = AgentAuthService()
        self.webhook_endpoints = {}
        self.event_handlers = {}
        self.delivery_timeout = 30  # seconds
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # seconds
    
    def register_webhook_endpoint(
        self, 
        name: str, 
        url: str, 
        events: List[str],
        secret: str = None,
        headers: Dict[str, str] = None,
        active: bool = True
    ) -> None:
        """
        Register a webhook endpoint for specific events.
        
        Args:
            name: Unique name for the webhook endpoint
            url: URL to send webhook requests to
            events: List of event types this endpoint should receive
            secret: Optional secret for webhook signature verification
            headers: Optional custom headers to include in requests
            active: Whether the webhook is active
            
        Raises:
            WebhookConfigurationError: If configuration is invalid
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise WebhookConfigurationError(f"Invalid webhook URL: {url}")
            
            # Validate events
            if not events or not isinstance(events, list):
                raise WebhookConfigurationError("Events list cannot be empty")
            
            self.webhook_endpoints[name] = {
                'url': url,
                'events': events,
                'secret': secret,
                'headers': headers or {},
                'active': active,
                'created_at': datetime.now().isoformat(),
                'last_delivery': None,
                'delivery_count': 0,
                'failure_count': 0
            }
            
            logger.info(f"Registered webhook endpoint '{name}' for events: {events}")
            
        except Exception as e:
            logger.error(f"Failed to register webhook endpoint '{name}': {str(e)}")
            raise WebhookConfigurationError(f"Failed to register webhook: {str(e)}")
    
    def unregister_webhook_endpoint(self, name: str) -> bool:
        """
        Unregister a webhook endpoint.
        
        Args:
            name: Name of the webhook endpoint to remove
            
        Returns:
            bool: True if endpoint was removed, False if not found
        """
        if name in self.webhook_endpoints:
            del self.webhook_endpoints[name]
            logger.info(f"Unregistered webhook endpoint '{name}'")
            return True
        return False
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for '{event_type}'")
    
    async def dispatch_event(
        self, 
        event_type: str, 
        event_data: Dict[str, Any],
        source_agent_uid: str = None,
        source_community_uid: str = None
    ) -> Dict[str, Any]:
        """
        Dispatch an event to all registered webhooks and handlers.
        
        Args:
            event_type: Type of event being dispatched
            event_data: Event payload data
            source_agent_uid: UID of the agent that triggered the event
            source_community_uid: UID of the community where event occurred
            
        Returns:
            Dict containing dispatch results
        """
        try:
            logger.info(f"Dispatching event '{event_type}' from agent {source_agent_uid}")
            
            # Create event payload
            event_payload = {
                'event_type': event_type,
                'event_id': f"evt_{datetime.now().timestamp()}",
                'timestamp': datetime.now().isoformat(),
                'source': {
                    'agent_uid': source_agent_uid,
                    'community_uid': source_community_uid
                },
                'data': event_data
            }
            
            # Dispatch to webhook endpoints
            webhook_results = await self._dispatch_to_webhooks(event_type, event_payload)
            
            # Dispatch to local event handlers
            handler_results = await self._dispatch_to_handlers(event_type, event_payload)
            
            # Log the event dispatch
            if source_agent_uid and source_community_uid:
                self.auth_service.log_agent_action(
                    agent_uid=source_agent_uid,
                    community_uid=source_community_uid,
                    action_type="webhook_event_dispatch",
                    details={
                        "event_type": event_type,
                        "event_id": event_payload['event_id'],
                        "webhook_deliveries": len(webhook_results),
                        "handler_executions": len(handler_results)
                    },
                    success=True
                )
            
            return {
                'event_id': event_payload['event_id'],
                'event_type': event_type,
                'webhook_results': webhook_results,
                'handler_results': handler_results,
                'dispatched_at': event_payload['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Failed to dispatch event '{event_type}': {str(e)}")
            
            # Log the failed dispatch
            if source_agent_uid and source_community_uid:
                self.auth_service.log_agent_action(
                    agent_uid=source_agent_uid,
                    community_uid=source_community_uid,
                    action_type="webhook_event_dispatch",
                    details={
                        "event_type": event_type,
                        "error": str(e)
                    },
                    success=False,
                    error_message=str(e)
                )
            
            raise WebhookError(f"Failed to dispatch event: {str(e)}")
    
    async def _dispatch_to_webhooks(
        self, 
        event_type: str, 
        event_payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Dispatch event to webhook endpoints.
        
        Args:
            event_type: Type of event
            event_payload: Event payload
            
        Returns:
            List of webhook delivery results
        """
        results = []
        
        # Find webhooks that should receive this event
        target_webhooks = []
        for name, config in self.webhook_endpoints.items():
            if config['active'] and event_type in config['events']:
                target_webhooks.append((name, config))
        
        if not target_webhooks:
            logger.debug(f"No active webhooks found for event type '{event_type}'")
            return results
        
        # Dispatch to all target webhooks concurrently
        tasks = []
        for name, config in target_webhooks:
            task = self._deliver_webhook(name, config, event_payload)
            tasks.append(task)
        
        # Wait for all deliveries to complete
        delivery_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(delivery_results):
            webhook_name = target_webhooks[i][0]
            
            if isinstance(result, Exception):
                results.append({
                    'webhook_name': webhook_name,
                    'success': False,
                    'error': str(result),
                    'delivered_at': datetime.now().isoformat()
                })
            else:
                results.append(result)
        
        return results
    
    async def _deliver_webhook(
        self, 
        webhook_name: str, 
        webhook_config: Dict[str, Any], 
        event_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deliver webhook to a specific endpoint with retry logic.
        
        Args:
            webhook_name: Name of the webhook
            webhook_config: Webhook configuration
            event_payload: Event payload to send
            
        Returns:
            Dict containing delivery result
        """
        url = webhook_config['url']
        headers = webhook_config['headers'].copy()
        headers['Content-Type'] = 'application/json'
        headers['User-Agent'] = 'Ooumph-Agent-Webhook/1.0'
        
        # Add signature if secret is configured
        if webhook_config.get('secret'):
            signature = self._generate_signature(event_payload, webhook_config['secret'])
            headers['X-Webhook-Signature'] = signature
        
        # Attempt delivery with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.delivery_timeout)) as session:
                    async with session.post(
                        url,
                        json=event_payload,
                        headers=headers
                    ) as response:
                        
                        # Update webhook stats
                        webhook_config['last_delivery'] = datetime.now().isoformat()
                        webhook_config['delivery_count'] += 1
                        
                        if response.status >= 200 and response.status < 300:
                            logger.info(f"Webhook '{webhook_name}' delivered successfully (attempt {attempt + 1})")
                            
                            return {
                                'webhook_name': webhook_name,
                                'success': True,
                                'status_code': response.status,
                                'attempt': attempt + 1,
                                'delivered_at': webhook_config['last_delivery']
                            }
                        else:
                            error_msg = f"HTTP {response.status}"
                            try:
                                error_body = await response.text()
                                if error_body:
                                    error_msg += f": {error_body[:200]}"
                            except:
                                pass
                            
                            raise WebhookDeliveryError(error_msg)
            
            except Exception as e:
                last_error = e
                webhook_config['failure_count'] += 1
                
                if attempt < self.max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.warning(f"Webhook '{webhook_name}' delivery failed (attempt {attempt + 1}), retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Webhook '{webhook_name}' delivery failed after {self.max_retries + 1} attempts: {str(e)}")
        
        return {
            'webhook_name': webhook_name,
            'success': False,
            'error': str(last_error),
            'attempts': self.max_retries + 1,
            'delivered_at': datetime.now().isoformat()
        }
    
    async def _dispatch_to_handlers(
        self, 
        event_type: str, 
        event_payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Dispatch event to local event handlers.
        
        Args:
            event_type: Type of event
            event_payload: Event payload
            
        Returns:
            List of handler execution results
        """
        results = []
        
        handlers = self.event_handlers.get(event_type, [])
        if not handlers:
            return results
        
        for i, handler in enumerate(handlers):
            try:
                # Execute handler
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_payload)
                else:
                    handler(event_payload)
                
                results.append({
                    'handler_index': i,
                    'success': True,
                    'executed_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Event handler {i} for '{event_type}' failed: {str(e)}")
                results.append({
                    'handler_index': i,
                    'success': False,
                    'error': str(e),
                    'executed_at': datetime.now().isoformat()
                })
        
        return results
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate webhook signature for payload verification.
        
        Args:
            payload: Event payload
            secret: Webhook secret
            
        Returns:
            Signature string
        """
        import hmac
        import hashlib
        
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def get_webhook_stats(self) -> Dict[str, Any]:
        """
        Get statistics about webhook endpoints and deliveries.
        
        Returns:
            Dict containing webhook statistics
        """
        stats = {
            'total_endpoints': len(self.webhook_endpoints),
            'active_endpoints': len([w for w in self.webhook_endpoints.values() if w['active']]),
            'total_deliveries': sum(w['delivery_count'] for w in self.webhook_endpoints.values()),
            'total_failures': sum(w['failure_count'] for w in self.webhook_endpoints.values()),
            'endpoints': {}
        }
        
        for name, config in self.webhook_endpoints.items():
            stats['endpoints'][name] = {
                'url': config['url'],
                'events': config['events'],
                'active': config['active'],
                'delivery_count': config['delivery_count'],
                'failure_count': config['failure_count'],
                'last_delivery': config['last_delivery'],
                'success_rate': (
                    (config['delivery_count'] - config['failure_count']) / config['delivery_count']
                    if config['delivery_count'] > 0 else 0
                )
            }
        
        return stats
    
    # Convenience methods for common agent events
    
    async def dispatch_agent_assigned(
        self, 
        agent_uid: str, 
        community_uid: str, 
        assignment_uid: str,
        assigned_by_uid: str
    ) -> Dict[str, Any]:
        """Dispatch agent assignment event."""
        return await self.dispatch_event(
            event_type='agent.assigned',
            event_data={
                'agent_uid': agent_uid,
                'community_uid': community_uid,
                'assignment_uid': assignment_uid,
                'assigned_by_uid': assigned_by_uid
            },
            source_agent_uid=agent_uid,
            source_community_uid=community_uid
        )
    
    async def dispatch_agent_action(
        self, 
        agent_uid: str, 
        community_uid: str, 
        action_type: str,
        action_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch agent action event."""
        return await self.dispatch_event(
            event_type='agent.action',
            event_data={
                'agent_uid': agent_uid,
                'community_uid': community_uid,
                'action_type': action_type,
                'action_details': action_details
            },
            source_agent_uid=agent_uid,
            source_community_uid=community_uid
        )
    
    async def dispatch_community_updated(
        self, 
        agent_uid: str, 
        community_uid: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch community update event."""
        return await self.dispatch_event(
            event_type='community.updated',
            event_data={
                'community_uid': community_uid,
                'updates': updates,
                'updated_by_agent': agent_uid
            },
            source_agent_uid=agent_uid,
            source_community_uid=community_uid
        )
    
    async def dispatch_user_moderated(
        self, 
        agent_uid: str, 
        community_uid: str, 
        target_user_uid: str,
        action: str, 
        reason: str
    ) -> Dict[str, Any]:
        """Dispatch user moderation event."""
        return await self.dispatch_event(
            event_type='user.moderated',
            event_data={
                'community_uid': community_uid,
                'target_user_uid': target_user_uid,
                'moderation_action': action,
                'reason': reason,
                'moderated_by_agent': agent_uid
            },
            source_agent_uid=agent_uid,
            source_community_uid=community_uid
        )


# Global webhook service instance
webhook_service = AgentWebhookService()