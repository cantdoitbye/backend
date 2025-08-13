import os
import aiohttp
import asyncio
from typing import List
from settings.base import NOTIFICATION_SERVICE_URL

class NotificationService:
    def __init__(self):
        self.notification_service_url = NOTIFICATION_SERVICE_URL

    async def notifyAchievementCreated(self, creator_name: str, connections: List[dict], achievement_title: str, achievement_id: str):
        """
        Send notifications to user's connections when a new achievement is created
        """
        print("Starting achievement notification...")
        print("Notification URL:", self.notification_service_url)
        print("Creator:", creator_name)
        print("Achievement:", achievement_title)
        print("Number of connections:", len(connections))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for connection in connections:
                if connection.get('device_id'):
                    notification_data = {
                        "title": f"New achievement from {creator_name}",
                        "body": f"{creator_name} achieved: {achievement_title}",
                        "token": connection['device_id'],
                        "priority": "high",
                        "click_action": f"/profile/{connection['uid']}",
                        "data": {
                            "achievement_id": achievement_id,
                            "type": "achievement_created"
                        }
                    }
                    
                    task = asyncio.create_task(self._send_notification(session, notification_data, headers))
                    tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_notification(self, session, notification_data, headers):
        """Helper method to send individual notifications"""
        try:
            async with session.post(
                f"{self.notification_service_url}/notifications",
                json=notification_data,
                headers=headers
            ) as response:
                response_text = await response.text()
                print(f"Response status: {response.status}")
                if response.status != 200:
                    print(f"Error response: {response_text}")
        except Exception as e:
            print(f"Error sending notification: {str(e)}")