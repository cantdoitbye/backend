
import os
import aiohttp
import asyncio
from typing import List
from settings.base import NOTIFICATION_SERVICE_URL

class NotificationService:
    def __init__(self):
        self.notification_service_url = NOTIFICATION_SERVICE_URL

    
    async def notifyNewChatMessage(self, sender_name: str, followers: list, chat_id: str, message_preview: str):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            for follower in followers:
                if follower.get('device_id'):
                    notification_data = {
                        "title": f"New message from {sender_name}",
                        "body": message_preview,
                        "token": follower['device_id'],
                        "priority": "high",
                        "click_action": f"/chat/{chat_id}",
                        "data": {
                            "chat_id": chat_id,
                            "type": "chat_message"
                        }
                    }
                    try:
                        async with session.post(
                            f"{self.notification_service_url}/notifications",
                            json=notification_data,
                            headers=headers
                        ) as response:
                            response_text = await response.text()
                            print(f"Response status: {response.status}")
                            print(f"Response body: {response_text}")
                    except Exception as e:
                        print(f"Error sending chat message notification: {str(e)}")