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
        print("🔔 NOTIFICATION DEBUG: Starting comment notification...")
        print("🔔 NOTIFICATION DEBUG: Notification URL:", self.notification_service_url)
        print("🔔 NOTIFICATION DEBUG: Commenter:", commenter_name)
        print("🔔 NOTIFICATION DEBUG: Post ID:", post_id)
        print("🔔 NOTIFICATION DEBUG: Comment ID:", comment_id)
        print("🔔 NOTIFICATION DEBUG: Comment content preview:", comment_content)
        print("🔔 NOTIFICATION DEBUG: Target device ID:", post_creator_device_id)
        
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
        
        print("🔔 NOTIFICATION DEBUG: Sending comment notification...")
        print("🔔 NOTIFICATION DEBUG: Notification data:", notification_data)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.notification_service_url}/notifications",
                    json=notification_data,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    print(f"🔔 NOTIFICATION DEBUG: Response status: {response.status}")
                    print(f"🔔 NOTIFICATION DEBUG: Response body: {response_text}")
                    if response.status != 200:
                        print(f"🔔 NOTIFICATION DEBUG: Error response: {response_text}")
                    else:
                        print(f"🔔 NOTIFICATION DEBUG: ✅ Comment notification sent successfully!")
            except Exception as e:
                print(f"🔔 NOTIFICATION DEBUG: ❌ Error sending comment notification: {str(e)}")
                print(f"🔔 NOTIFICATION DEBUG: Full error details: {type(e).__name__}: {str(e)}")

    async def notify_user_mentioned(self, mentioned_user_uid: str, mentioner_uid: str, content_type: str, content_uid: str):
        """
        Send notification to user when they are mentioned in content
        """
        print("🔔 MENTION NOTIFICATION DEBUG: Starting mention notification...")
        print("🔔 MENTION NOTIFICATION DEBUG: Mentioned user UID:", mentioned_user_uid)
        print("🔔 MENTION NOTIFICATION DEBUG: Mentioner UID:", mentioner_uid)
        print("🔔 MENTION NOTIFICATION DEBUG: Content type:", content_type)
        print("🔔 MENTION NOTIFICATION DEBUG: Content UID:", content_uid)
        
        # Get mentioned user's device ID
        try:
            from auth_manager.models import Users
            mentioned_user = Users.nodes.get(uid=mentioned_user_uid)
            mentioner = Users.nodes.get(uid=mentioner_uid)
            
            profile = mentioned_user.profile.single()
            if not profile or not profile.device_id:
                print("🔔 MENTION NOTIFICATION DEBUG: ❌ No device ID found for mentioned user")
                return
                
            print("🔔 MENTION NOTIFICATION DEBUG: Target device ID:", profile.device_id)
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            notification_data = {
                "title": f"You were mentioned by {mentioner.username}",
                "body": f"You were mentioned in a {content_type}",
                "token": profile.device_id,
                "priority": "high",
                "click_action": f"/{content_type}/{content_uid}",
                "data": {
                    "content_type": content_type,
                    "content_uid": content_uid,
                    "mentioner_uid": mentioner_uid,
                    "type": "mention"
                }
            }
            
            print("🔔 MENTION NOTIFICATION DEBUG: Sending mention notification...")
            print("🔔 MENTION NOTIFICATION DEBUG: Notification data:", notification_data)
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.notification_service_url}/notifications",
                        json=notification_data,
                        headers=headers
                    ) as response:
                        response_text = await response.text()
                        print(f"🔔 MENTION NOTIFICATION DEBUG: Response status: {response.status}")
                        print(f"🔔 MENTION NOTIFICATION DEBUG: Response body: {response_text}")
                        if response.status != 200:
                            print(f"🔔 MENTION NOTIFICATION DEBUG: Error response: {response_text}")
                        else:
                            print(f"🔔 MENTION NOTIFICATION DEBUG: ✅ Mention notification sent successfully!")
                except Exception as e:
                    print(f"🔔 MENTION NOTIFICATION DEBUG: ❌ Error sending mention notification: {str(e)}")
                    print(f"🔔 MENTION NOTIFICATION DEBUG: Full error details: {type(e).__name__}: {str(e)}")
                    
        except Exception as e:
            print(f"🔔 MENTION NOTIFICATION DEBUG: ❌ Error getting user data: {str(e)}")

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