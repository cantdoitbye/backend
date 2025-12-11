"""
WebSocket consumer for bidirectional real-time communication.

Handles:
1. Frontend → Backend: Events like profile views
2. Backend → Frontend: Live notifications and updates
"""
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RealtimeEventConsumer(AsyncWebsocketConsumer):
    """
    Bidirectional WebSocket consumer.
    
    Frontend → Backend Events:
    {
        "event_type": "profile_view",
        "data": {"target_uid": "user_123"}
    }
    
    Backend → Frontend Notifications:
    {
        "type": "notification",
        "data": {
            "title": "Someone viewed your profile",
            "body": "...",
            "notification_type": "profile_viewed"
        }
    }
    """
    
    # Map event types to handler methods
    EVENT_HANDLERS = {
        'profile_view': 'handle_profile_view',
        # Add more events here in the future:
        # 'post_comment': 'handle_post_comment',
        # 'post_vibe': 'handle_post_vibe',
    }
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            self.user = self.scope.get("user")
            
            # Authentication check
            if not self.user or not self.user.is_authenticated:
                logger.warning("Unauthenticated connection attempt")
                await self.close(code=4001)
                return
            
            # Get Neo4j user node to fetch uid
            user_node = await self._get_neo4j_user(self.user.id)
            if not user_node:
                logger.error(f"Neo4j user not found for Django user {self.user.id}")
                await self.close(code=4003)
                return
            
            # Store user info (uid from Neo4j)
            self.user_uid = user_node.uid
            
            # Join user-specific channel group to receive notifications
            self.user_channel = f'user_{self.user_uid}'
            
            await self.channel_layer.group_add(
                self.user_channel,
                self.channel_name
            )
            
            # Accept the WebSocket connection
            await self.accept()
            
            # Send connection success message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'user_uid': self.user_uid,
                'timestamp': self._get_timestamp()
            }))
            
            logger.info(f"User {self.user_uid} connected to real-time events")
            
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            await self.close(code=4002)
    
    @database_sync_to_async
    def _get_neo4j_user(self, user_id):
        """Get Neo4j Users node from Django user id"""
        try:
            from auth_manager.models import Users
            return Users.nodes.get(user_id=str(user_id))
        except Exception as e:
            logger.error(f"Error fetching Neo4j user: {e}")
            return None
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            if hasattr(self, 'user_channel'):
                await self.channel_layer.group_discard(
                    self.user_channel,
                    self.channel_name
                )
            if hasattr(self, 'user_uid'):
                logger.info(f"User {self.user_uid} disconnected (code: {close_code})")
            else:
                logger.info(f"Unauthenticated user disconnected (code: {close_code})")
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")
    
    async def receive(self, text_data):
        """
        Handle incoming messages FROM frontend.
        Routes to appropriate event handlers.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Handle system messages
            if message_type == 'ping':
                await self._handle_ping(data)
                return
            
            # Handle events
            event_type = data.get('event_type')
            event_data = data.get('data', {})
            
            if not event_type:
                await self._send_error("Missing event_type")
                return
            
            # Route to appropriate handler
            handler_name = self.EVENT_HANDLERS.get(event_type)
            
            if not handler_name:
                await self._send_error(f"Unknown event_type: {event_type}")
                logger.warning(f"Unknown event_type: {event_type} from user {self.user_uid}")
                return
            
            # Call the handler
            handler = getattr(self, handler_name)
            await handler(event_data)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self._send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self._send_error(str(e))
    
    # =========================================================================
    # EVENT HANDLERS (Frontend → Backend)
    # =========================================================================
    
    async def handle_profile_view(self, data: Dict[str, Any]):
        """
        Handle profile view event from frontend.
        Sends notification via GlobalNotificationService.
        """
        target_uid = data.get('target_uid')
        
        if not target_uid:
            await self._send_error("Missing target_uid", event_type='profile_view')
            return
        
        # Don't track self-views
        if target_uid == self.user_uid:
            await self._send_ack('profile_view', 'Self-view not tracked')
            return
        
        # Track and notify
        result = await self._track_profile_view(target_uid)
        
        if result['success']:
            await self._send_ack('profile_view', result['message'])
        else:
            await self._send_error(result['message'], event_type='profile_view')
    
    @database_sync_to_async
    def _track_profile_view(self, target_uid: str) -> Dict[str, Any]:
        """
        Track profile view and send notification.
        Uses existing GlobalNotificationService.
        """
        try:
            from auth_manager.models import Users
            from notification.global_service import GlobalNotificationService
            
            # Get target user from Neo4j by uid
            try:
                target_user = Users.nodes.get(uid=target_uid)
            except Users.DoesNotExist:
                return {'success': False, 'message': 'User not found'}
            
            # Get profile to check device_id
            profile = target_user.profile.single()
            if not profile or not profile.device_id:
                logger.info(f"User {target_uid} has no device_id")
                return {
                    'success': True, 
                    'message': 'Profile view tracked (no device for push notification)'
                }
            
            # Prepare recipient
            recipient = {
                'device_id': profile.device_id,
                'uid': target_user.uid
            }
            
            # Send push notification via GlobalNotificationService
            service = GlobalNotificationService()
            service.send(
                event_type="profile_viewed",
                recipients=[recipient],
                username=self.user.username,
                viewer_id=self.user_uid
            )
            
            logger.info(
                f"Profile view notification sent: "
                f"{self.user_uid} → {target_user.uid}"
            )
            
            return {
                'success': True, 
                'message': 'Profile view tracked and notification sent'
            }
            
        except Exception as e:
            logger.error(f"Error tracking profile view: {e}")
            return {'success': False, 'message': str(e)}
    
    # =========================================================================
    # NOTIFICATION RECEIVERS (Backend → Frontend)
    # These methods receive notifications broadcasted from backend
    # =========================================================================
    
    async def live_notification(self, event):
        """
        Receive live notification from backend and send to frontend.
        Called when backend broadcasts notification via RealtimeBroadcaster.
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'data': event['data']
            }))
            logger.info(f"Live notification sent to user {self.user_uid}")
        except Exception as e:
            logger.error(f"Error sending live notification: {e}")
    
    async def live_update(self, event):
        """
        Receive live updates from backend (e.g., new post, new comment).
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'live_update',
                'update_type': event['update_type'],
                'data': event['data']
            }))
            logger.info(f"Live update sent to user {self.user_uid}")
        except Exception as e:
            logger.error(f"Error sending live update: {e}")
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    async def _handle_ping(self, data: Dict[str, Any]):
        """Handle keep-alive ping"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': data.get('timestamp', self._get_timestamp())
        }))
    
    async def _send_ack(self, event_type: str, message: str):
        """Send acknowledgment to frontend"""
        await self.send(text_data=json.dumps({
            'type': 'event_ack',
            'status': 'success',
            'event_type': event_type,
            'message': message,
            'timestamp': self._get_timestamp()
        }))
    
    async def _send_error(self, message: str, event_type: Optional[str] = None):
        """Send error message to frontend"""
        payload = {
            'type': 'error',
            'status': 'error',
            'message': message,
            'timestamp': self._get_timestamp()
        }
        if event_type:
            payload['event_type'] = event_type
        
        await self.send(text_data=json.dumps(payload))
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from django.utils import timezone
        return timezone.now().isoformat()