"""
Broadcast live updates from backend to connected WebSocket clients.
Use this when backend events should update frontend in real-time.
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


class RealtimeBroadcaster:
    """
    Broadcast real-time updates to WebSocket clients.
    
    Usage in mutations:
        from realtime.broadcaster import RealtimeBroadcaster
        
        broadcaster = RealtimeBroadcaster()
        broadcaster.send_notification(user_uid, notification_data)
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_notification(self, user_uid: str, notification_data: dict):
        """
        Send live notification to a specific user's WebSocket.
        Used alongside push notifications for instant UI updates.
        
        Args:
            user_uid: Target user's UID
            notification_data: Notification payload
        """
        try:
            async_to_sync(self.channel_layer.group_send)(
                f'user_{user_uid}',
                {
                    'type': 'live_notification',
                    'data': notification_data
                }
            )
            logger.info(f"Live notification broadcasted to user {user_uid}")
        except Exception as e:
            logger.error(f"Error broadcasting notification to {user_uid}: {e}")
    
    def send_update(self, user_uid: str, update_type: str, update_data: dict):
        """
        Send live updates to user's WebSocket.
        Used for real-time feed updates, new comments, etc.
        
        Args:
            user_uid: Target user's UID
            update_type: Type of update (e.g., 'new_post', 'new_comment')
            update_data: Update payload
        """
        try:
            async_to_sync(self.channel_layer.group_send)(
                f'user_{user_uid}',
                {
                    'type': 'live_update',
                    'update_type': update_type,
                    'data': update_data
                }
            )
            logger.info(f"Live update ({update_type}) broadcasted to user {user_uid}")
        except Exception as e:
            logger.error(f"Error broadcasting update to {user_uid}: {e}")
    
    def broadcast_to_multiple(self, user_uids: list, notification_data: dict):
        """
        Broadcast notification to multiple users at once.
        
        Args:
            user_uids: List of user UIDs
            notification_data: Notification payload
        """
        for user_uid in user_uids:
            self.send_notification(user_uid, notification_data)