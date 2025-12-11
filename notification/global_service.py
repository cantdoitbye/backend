"""
Global Unified Notification Service
Simple, template-driven notification service
"""

import requests
import logging
import time
import threading
from typing import List, Dict, Any, Optional
from django.utils import timezone

from settings.base import NOTIFICATION_SERVICE_URL
from .notification_templates import NOTIFICATION_TEMPLATES, format_notification
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
        self.timeout = 30  # seconds
    
    def send(
        self,
        event_type: str,
        recipients: List[Dict[str, str]],
        **template_vars
    ):
        """
        Send notification in BACKGROUND THREAD (non-blocking!)
        Returns immediately without waiting for notifications to complete.
        
        Args:
            event_type: Notification event type (e.g., "new_post_from_connection")
            recipients: List of dicts with 'device_id' and 'uid'
            **template_vars: Variables to fill in the template (username, post_id, etc.)
        
        Returns:
            None (notifications sent in background)
        """
        # Start background thread for sending
        thread = threading.Thread(
            target=self._send_all,
            args=(event_type, recipients),
            kwargs=template_vars,
            daemon=True  # Thread dies when main program exits
        )
        thread.start()
        print(f"🚀 Notification thread started for {event_type}")
        # Return immediately - don't wait for thread!
    
    def _send_all(
        self,
        event_type: str,
        recipients: List[Dict[str, str]],
        **template_vars
    ):
        """
        Internal method that does the actual sending (runs in background thread)
        
        Args:
            event_type: Notification event type
            recipients: List of dicts with 'device_id' and 'uid'
            **template_vars: Variables to fill in the template
        """
        # Validate event type
        if event_type not in NOTIFICATION_TEMPLATES:
            print(f"Invalid notification event type: {event_type}")
            return
        
        # Filter valid recipients
        valid_recipients = [r for r in recipients if r.get('device_id') and r.get('uid')]
        
        if not valid_recipients:
            print(f"No valid recipients for {event_type}")
            return
        
        # Format notification from template
        try:
            notification_data = format_notification(event_type, **template_vars)
            logger.debug(f"Formatted notification data: {notification_data}")
        except Exception as e:
            logger.error(f"Error formatting notification: {e}")
            print(f"Error formatting notification: {e}")
            return
        
        logger.info(f"📨 Sending {event_type} notification to {len(valid_recipients)} recipients")
        print(f"📨 Sending {event_type} notification to {len(valid_recipients)} recipients")
        print(f"📋 Title: '{notification_data.get('title')}'")
        print(f"📋 Body: '{notification_data.get('body')}'")
        print(f"📋 Deep Link: '{notification_data.get('deep_link')}'")
        print(f"📋 Web Link: '{notification_data.get('web_link')}'")
        
        # Create batch log
        log = NotificationLog.objects.create(
            notification_type=event_type,
            recipient_count=len(valid_recipients),
            status='pending',
            metadata={**template_vars, 'event_type': event_type}
        )
        
        # Send to all recipients synchronously (but in background)
        successful = 0
        failed = 0
        
        for recipient in valid_recipients:
            result = self._send_to_recipient(
                recipient,
                notification_data,
                event_type
            )
            
            if result.get('success'):
                successful += 1
            else:
                failed += 1
        
        # Update batch log
        log.successful_count = successful
        log.failed_count = failed
        log.status = 'sent' if failed == 0 else ('partial' if successful > 0 else 'failed')
        log.save()
        
        print(f"✅ Batch complete: {successful}/{len(valid_recipients)} successful")
    
    def _send_to_recipient(
        self,
        recipient: Dict[str, str],
        notification_data: Dict[str, Any],
        event_type: str
    ) -> Dict[str, Any]:
        """
        Send notification to a single recipient using synchronous HTTP request
        
        Args:
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
            deep_link=notification_data.get('deep_link'),
            web_link=notification_data.get('web_link'),
            image_url=notification_data.get('image_url'),
            data=notification_data.get('data', {})
        )
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Build payload with new format including deep_link and web_link
        payload = {
            "title": notification_data['title'],
            "body": notification_data['body'],
            "token": device_id,
            "priority": notification_data.get('priority', 'normal'),
            "click_action": notification_data.get('click_action', '/'),
            "deep_link": notification_data.get('deep_link', ''),
            "web_link": notification_data.get('web_link', ''),
            "data": {
                "type": event_type,
                **notification_data.get('data', {})
            }
        }
        
        # Add optional image_url if present
        if notification_data.get('image_url'):
            payload['image_url'] = notification_data['image_url']
        
        # Send with retries using requests library (synchronous)
        for attempt in range(self.max_retries):
            try:
                # Log the payload being sent
                logger.info(f"📤 Sending notification to {user_uid}")
                logger.debug(f"Payload: {payload}")
                
                response = requests.post(
                    f"{self.notification_service_url}/notifications",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Log the response
                logger.info(f"📥 Response status: {response.status_code}")
                logger.debug(f"Response body: {response.text}")
                
                if response.status_code == 200:
                    # Update notification record
                    notification.status = 'sent'
                    notification.sent_at = timezone.now()
                    notification.save()
                    
                    # Parse response to check if notification was actually delivered
                    try:
                        response_data = response.json()
                        logger.info(f"✅ Sent to {user_uid} - Response: {response_data}")
                        print(f"✅ Sent to {user_uid} - FCM Response: {response_data}")
                    except:
                        logger.info(f"✅ Sent to {user_uid}")
                        print(f"✅ Sent to {user_uid}")
                    
                    return {
                        'success': True,
                        'user_uid': user_uid,
                        'notification_id': notification.id
                    }
                else:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"⚠️ Attempt {attempt + 1} failed for {user_uid}, retrying...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        # Update notification record with error
                        notification.status = 'failed'
                        notification.error_message = f"Status {response.status_code}: {response.text}"
                        notification.save()
                        
                        logger.error(f"❌ Failed to send to {user_uid}: {response.status_code} - {response.text}")
                        print(f"❌ Failed to send to {user_uid}: {response.status_code} - {response.text}")
                        
                        return {
                            'success': False,
                            'user_uid': user_uid,
                            'error': f"Status {response.status_code}: {response.text}"
                        }
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    # Update notification record with error
                    notification.status = 'failed'
                    notification.error_message = str(e)
                    notification.save()
                    
                    print(f"❌ Error sending to {user_uid}: {str(e)}")
                    
                    return {
                        'success': False,
                        'user_uid': user_uid,
                        'error': str(e)
                    }

