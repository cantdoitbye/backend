import os
import aiohttp
import asyncio
from typing import List
from settings.base import NOTIFICATION_SERVICE_URL

class NotificationService:
    def __init__(self):
        self.notification_service_url = NOTIFICATION_SERVICE_URL

    async def notifyNewStory(self, story_creator_name: str, followers: List[dict], story_id: str, story_image_url: str = None):
        """
        Send notifications to all followers in parallel when a new story is posted
        """
        print("Starting story notification service...")
        print("Notification URL:", self.notification_service_url)
        print("Story creator:", story_creator_name)
        print("Number of followers:", len(followers))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for follower in followers:
                if follower.get('device_id'):
                    notification_data = {
                        "title": f"New story from {story_creator_name}",
                        "body": "Check out their latest story!",
                        "token": follower['device_id'],
                        "priority": "high",
                        "image_url": story_image_url,
                        "click_action": f"/story/{story_id}",
                        "data": {
                            "story_id": story_id,
                            "type": "new_story"
                        }
                    }
                    print("Sending story notification to:", follower['device_id'])
                    print("Notification data:", notification_data)
                    
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
                        print(f"Error sending story notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}")

  