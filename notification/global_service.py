"""
Global Unified Notification Service
Simple, template-driven notification service
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from django.utils import timezone

from settings.base import NOTIFICATION_SERVICE_URL
from .notification_templates import NotificationEventType, format_notification
from .models import UserNotification, NotificationLog

logger = logging.getLogger(__name__)


class GlobalNotificationService:
    """
    Global notification service - simple and easy to use
    
    Usage:
        service = GlobalNotificationService()
        service.send(
            event_type="new_post_from_connection",
            recipients=[{'device_id': '...', 'uid': '...'}],
            username="John Doe",
            post_id="123"
        )
    """
    
    def __init__(self):
        self.notification_service_url = NOTIFICATION_SERVICE_URL
        self.max_retries = 3
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    def send(
        self,
        event_type: str,
        recipients: List[Dict[str, str]],
        **template_vars
    ):
        """
        Send notification (sync wrapper for async send)
        
        Args:
            event_type: Notification event type (e.g., "new_post_from_connection")
            recipients: List of dicts with 'device_id' and 'uid'
            **template_vars: Variables to fill in the template (username, post_id, etc.)
        
        Returns:
            List of send results
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.send_async(event_type, recipients, **template_vars)
            )
        finally:
            loop.close()
    
    async def send_async(
        self,
        event_type: str,
        recipients: List[Dict[str, str]],
        **template_vars
    ) -> List[Dict[str, Any]]:
        """
        Send notification asynchronously
        
        Args:
            event_type: Notification event type
            recipients: List of dicts with 'device_id' and 'uid'
            **template_vars: Variables to fill template
            
        Returns:
            List of send results
        """
        # Validate event type
        try:
            event = NotificationEventType(event_type)
        except ValueError:
            logger.error(f"Invalid notification event type: {event_type}")
            return []
        
        # Filter valid recipients
        valid_recipients = [r for r in recipients if r.get('device_id') and r.get('uid')]
        
        if not valid_recipients:
            logger.warning(f"No valid recipients for {event_type}")
            return []
        
        # Format notification from template
        notification_data = format_notification(event, **template_vars)
        
        logger.info(f"📨 Sending {event_type} notification to {len(valid_recipients)} recipients")
        
        # Create batch log
        log = NotificationLog.objects.create(
            notification_type=event_type,
            recipient_count=len(valid_recipients),
            status='pending',
            metadata={**template_vars, 'event_type': event_type}
        )
        
        # Send to all recipients
        results = []
        successful = 0
        failed = 0
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for recipient in valid_recipients:
                result = await self._send_to_recipient(
                    session,
                    recipient,
                    notification_data,
                    event_type
                )
                results.append(result)
                
                if result.get('success'):
                    successful += 1
                else:
                    failed += 1
        
        # Update batch log
        log.successful_count = successful
        log.failed_count = failed
        log.status = 'sent' if failed == 0 else ('partial' if successful > 0 else 'failed')
        log.save()
        
        logger.info(f"✅ Batch complete: {successful}/{len(valid_recipients)} successful")
        
        return results
    
    async def _send_to_recipient(
        self,
        session: aiohttp.ClientSession,
        recipient: Dict[str, str],
        notification_data: Dict[str, Any],
        event_type: str
    ) -> Dict[str, Any]:
        """
        Send notification to a single recipient
        
        Args:
            session: aiohttp session
            recipient: Dict with device_id and uid
            notification_data: Formatted notification data
            event_type: Notification event type
            
        Returns:
            Result dict
        """
        device_id = recipient['device_id']
        user_uid = recipient['uid']
        
        # Create notification record in PostgreSQL
        notification = UserNotification.objects.create(
            user_uid=user_uid,
            notification_type=event_type,
            title=notification_data.get('title', ''),
            body=notification_data.get('body', ''),
            device_id=device_id,
            status='pending',
            priority=notification_data.get('priority', 'normal'),
            click_action=notification_data.get('click_action'),
            image_url=notification_data.get('image_url'),
            data=notification_data.get('data', {})
        )
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            "title": notification_data['title'],
            "body": notification_data['body'],
            "token": device_id,
            "priority": notification_data.get('priority', 'normal'),
            "click_action": notification_data.get('click_action', '/'),
            "data": {
                "type": event_type,
                **notification_data.get('data', {})
            }
        }
        
        if notification_data.get('image_url'):
            payload['image_url'] = notification_data['image_url']
        
        # Send with retries
        for attempt in range(self.max_retries):
            try:
                async with session.post(
                    f"{self.notification_service_url}/notifications",
                    json=payload,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        # Update notification record
                        notification.status = 'sent'
                        notification.sent_at = timezone.now()
                        notification.save()
                        
                        logger.debug(f"✅ Sent to {user_uid}")
                        
                        return {
                            'success': True,
                            'user_uid': user_uid,
                            'notification_id': notification.id
                        }
                    else:
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            # Update notification record with error
                            notification.status = 'failed'
                            notification.error_message = f"Status {response.status}: {response_text}"
                            notification.save()
                            
                            logger.warning(f"❌ Failed to send to {user_uid}: {response.status}")
                            
                            return {
                                'success': False,
                                'user_uid': user_uid,
                                'error': f"Status {response.status}"
                            }
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    # Update notification record with error
                    notification.status = 'failed'
                    notification.error_message = str(e)
                    notification.save()
                    
                    logger.error(f"❌ Error sending to {user_uid}: {str(e)}")
                    
                    return {
                        'success': False,
                        'user_uid': user_uid,
                        'error': str(e)
                    }

