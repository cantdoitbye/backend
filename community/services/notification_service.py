import os
import aiohttp
import asyncio
from typing import List
from settings.base import NOTIFICATION_SERVICE_URL

class NotificationService:
    def __init__(self):
        self.notification_service_url = NOTIFICATION_SERVICE_URL

    async def notifyCommunityCreated(self, creator_name: str, members: List[dict], community_id: str, community_name: str, community_icon: str = None):
        """
        Send notifications to initial members when a community is created
        """
        print("Starting community creation notification...")
        print("Notification URL:", self.notification_service_url)
        print("Creator:", creator_name)
        print("Community:", community_name)
        print("Number of members:", len(members))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"You've been added to {community_name}",
                        "body": f"{creator_name} created a new community and added you as a member",
                        "token": member['device_id'],
                        "priority": "high",
                        "image_url": community_icon,
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "type": "community_created"
                        }
                    }
                    print("Sending community creation notification to:", member['device_id'])
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
                        print(f"Error sending community creation notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notifyCommunityMemberAdded(self, added_by_name: str, members: List[dict], community_id: str, community_name: str, community_icon: str = None):
        """
        Send notifications to new members when they are added to a community
        """
        print("Starting community member added notification...")
        print("Notification URL:", self.notification_service_url)
        print("Added by:", added_by_name)
        print("Community:", community_name)
        print("Number of new members:", len(members))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"You've been added to {community_name}",
                        "body": f"{added_by_name} added you to the community",
                        "token": member['device_id'],
                        "priority": "high",
                        "image_url": community_icon,
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "type": "community_member_added"
                        }
                    }
                    print("Sending community member added notification to:", member['device_id'])
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
                        print(f"Error sending community member added notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notifySubCommunityCreated(self, creator_name: str, members: List[dict], sub_community_id: str, sub_community_name: str, sub_community_icon: str = None):
        """
        Send notifications to initial members when a subcommunity is created
        """
        print("Starting subcommunity creation notification...")
        print("Notification URL:", self.notification_service_url)
        print("Creator:", creator_name)
        print("Subcommunity:", sub_community_name)
        print("Number of members:", len(members))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"You've been added to {sub_community_name}",
                        "body": f"{creator_name} created a new subcommunity and added you as a member",
                        "token": member['device_id'],
                        "priority": "high",
                        "image_url": sub_community_icon,
                        "click_action": f"/subcommunity/{sub_community_id}",
                        "data": {
                            "sub_community_id": sub_community_id,
                            "type": "subcommunity_created"
                        }
                    }
                    print("Sending subcommunity creation notification to:", member['device_id'])
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
                        print(f"Error sending subcommunity creation notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notifySubCommunityMemberAdded(self, added_by_name: str, members: List[dict], sub_community_id: str, sub_community_name: str, sub_community_icon: str = None):
        """
        Send notifications to new members when they are added to a subcommunity
        """
        print("Starting subcommunity member added notification...")
        print("Notification URL:", self.notification_service_url)
        print("Added by:", added_by_name)
        print("Subcommunity:", sub_community_name)
        print("Number of new members:", len(members))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"You've been added to {sub_community_name}",
                        "body": f"{added_by_name} added you to the subcommunity",
                        "token": member['device_id'],
                        "priority": "high",
                        "image_url": sub_community_icon,
                        "click_action": f"/subcommunity/{sub_community_id}",
                        "data": {
                            "sub_community_id": sub_community_id,
                            "type": "subcommunity_member_added"
                        }
                    }
                    print("Sending subcommunity member added notification to:", member['device_id'])
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
                        print(f"Error sending subcommunity member added notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}") 