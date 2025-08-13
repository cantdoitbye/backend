
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

    async def notifyChatInvitationAccepted(self, accepter_name: str, inviter_device_id: str, chat_id: str, chat_name: str = None):
        """
        Send notification to chat creator when someone accepts the chat invitation
        """
        print("Starting chat invitation accepted notification...")
        print("Notification URL:", self.notification_service_url)
        print("Accepter:", accepter_name)
        print("Chat ID:", chat_id)

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        notification_data = {
            "title": f"{accepter_name} joined your chat",
            "body": f"{accepter_name} accepted your chat invitation" + (f" for '{chat_name}'" if chat_name else ""),
            "token": inviter_device_id,
            "priority": "high",
            "click_action": f"/chat/{chat_id}",
            "data": {
                "chat_id": chat_id,
                "type": "chat_invitation_accepted"
            }
        }

        print("Sending chat invitation accepted notification...")
        print("Notification data:", notification_data)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.notification_service_url}/notifications",
                    json=notification_data,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    print(f"Response status: {response.status}")
                    print(f"Response body: {response_text}")
                    if response.status != 200:
                        print(f"Error response: {response_text}")
            except Exception as e:
                print(f"Error sending chat invitation accepted notification: {str(e)}")