import os
import aiohttp
import asyncio
from typing import List
from settings.base import NOTIFICATION_SERVICE_URL

class NotificationService:
    def __init__(self):
        self.notification_service_url = NOTIFICATION_SERVICE_URL

    async def notifyNewComment(self, commenter_name: str, post_creator_device_id: str, post_id: str, comment_id: str, comment_content: str):
        """
        Send notification to post creator about new comment
        """
        print("Starting comment notification...")
        print("Notification URL:", self.notification_service_url)
        print("Commenter:", commenter_name)
        print("Post ID:", post_id)
        print("Comment content preview:", comment_content)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        notification_data = {
            "title": f"New comment from {commenter_name}",
            "body": f'"{comment_content}"',
            "token": post_creator_device_id,
            "priority": "high",
            "click_action": f"/post/{post_id}",
            "data": {
                "post_id": post_id,
                "comment_id": comment_id,
                "type": "new_comment"
            }
        }
        
        print("Sending comment notification...")
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
                print(f"Error sending comment notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notifyNewPost(self, post_creator_name: str, followers: List[dict], post_id: str, post_image_url: str = None):
        """
        Send notifications to all followers in parallel when a new post is created
        """
        print("Starting post notification service...")
        print("Notification URL:", self.notification_service_url)
        print("Post creator:", post_creator_name)
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
                        "title": f"New post from {post_creator_name}",
                        "body": "Check out their latest post!",
                        "token": follower['device_id'],
                        "priority": "high",
                        "image_url": post_image_url,
                        "click_action": f"/post/{post_id}",
                        "data": {
                            "post_id": post_id,
                            "type": "new_post"
                        }
                    }
                    print("Sending post notification to:", follower['device_id'])
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
                        print(f"Error sending post notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}")

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

    async def notifyConnectionRequest(self, sender_name: str, receiver_device_id: str, connection_id: str):
        """
        Send notification to receiver about new connection request
        """
        print("Starting connection request notification...")
        print("Notification URL:", self.notification_service_url)
        print("Sender:", sender_name)
        print("Receiver device ID:", receiver_device_id)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        notification_data = {
            "title": f"New connection request from {sender_name}",
            "body": "Someone wants to connect with you!",
            "token": receiver_device_id,
            "priority": "high",
            "click_action": f"/connection/{connection_id}",
            "data": {
                "connection_id": connection_id,
                "type": "connection_request"
            }
        }
        
        print("Sending connection request notification...")
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
                print(f"Error sending connection request notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notifyConnectionAccepted(self, receiver_name: str, sender_device_id: str, connection_id: str):
        """
        Send notification to sender about accepted connection
        """
        print("Starting connection accepted notification...")
        print("Notification URL:", self.notification_service_url)
        print("Receiver:", receiver_name)
        print("Sender device ID:", sender_device_id)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        notification_data = {
            "title": f"{receiver_name} accepted your connection request",
            "body": "You are now connected!",
            "token": sender_device_id,
            "priority": "high",
            "click_action": f"/connection/{connection_id}",
            "data": {
                "connection_id": connection_id,
                "type": "connection_accepted"
            }
        }
        
        print("Sending connection accepted notification...")
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
                print(f"Error sending connection accepted notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notifyConnectionRejected(self, receiver_name: str, sender_device_id: str, connection_id: str):
        """
        Send notification to sender about rejected connection
        """
        print("Starting connection rejected notification...")
        print("Notification URL:", self.notification_service_url)
        print("Receiver:", receiver_name)
        print("Sender device ID:", sender_device_id)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        notification_data = {
            "title": f"{receiver_name} declined your connection request",
            "body": "Your connection request was not accepted",
            "token": sender_device_id,
            "priority": "high",
            "click_action": f"/connection/{connection_id}",
            "data": {
                "connection_id": connection_id,
                "type": "connection_rejected"
            }
        }
        
        print("Sending connection rejected notification...")
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
                print(f"Error sending connection rejected notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}") 