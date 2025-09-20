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


    async def notifyCommunityPost(self, creator_name: str, members: List[dict], community_name: str, post_title: str, post_id: str, community_id: str):
        """
        Send notifications to community members when a new post is created
        """
        print("Starting community post notification...")
        print("Notification URL:", self.notification_service_url)
        print("Creator:", creator_name)
        print("Community:", community_name)
        print("Post:", post_title)
        print("Number of members:", len(members))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"New post in {community_name}",
                        "body": f"{creator_name} posted: {post_title[:50]}...",
                        "token": member['device_id'],
                        "priority": "high",
                        "click_action": f"/community/{community_id}/post/{post_id}",
                        "data": {
                            "community_id": community_id,
                            "post_id": post_id,
                            "type": "community_post"
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
                            if response.status != 200:
                                print(f"Error response: {response_text}")
                    except Exception as e:
                        print(f"Error sending community post notification: {str(e)}")


    async def notifyCommunityAchievement(self, creator_name: str, members: List[dict], community_name: str, achievement_title: str, achievement_id: str, community_id: str):
        """
        Send notifications to community members when a new achievement is created
        """
        print("Starting community achievement notification...")

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"New achievement in {community_name}",
                        "body": f"{creator_name} added achievement: {achievement_title}",
                        "token": member['device_id'],
                        "priority": "high",
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "achievement_id": achievement_id,
                            "type": "community_achievement"
                        }
                    }

                    try:
                        async with session.post(
                            f"{self.notification_service_url}/notifications",
                            json=notification_data,
                            headers=headers
                        ) as response:
                            response_text = await response.text()
                            if response.status != 200:
                                print(f"Error response: {response_text}")
                    except Exception as e:
                        print(f"Error sending community achievement notification: {str(e)}")
    
    async def notifyCommunityActivity(
        self,
        creator_name: str,
        members: List[dict],
        community_name: str,
        activity_name: str,
        activity_id: str,
        community_id: str
    ):
        """
        Send notifications to community members when a new activity is created
        """
        print("Starting community activity notification...")

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"New activity in {community_name}",
                        "body": f"{creator_name} added activity: {activity_name}",
                        "token": member['device_id'],
                        "priority": "high",
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "activity_id": activity_id,
                            "type": "community_activity"
                        }
                    }

                    try:
                        async with session.post(
                            f"{self.notification_service_url}/notifications",
                            json=notification_data,
                            headers=headers
                        ) as response:
                            response_text = await response.text()
                            if response.status != 200:
                                print(f"Error response: {response_text}")
                    except Exception as e:
                        print(f"Error sending community activity notification: {str(e)}")
    async def notifyCommunityGoal(self, creator_name: str, members: List[dict], community_name: str, goal_name: str, goal_id: str, community_id: str):
        """
        Send notifications to community members when a new goal is created
        """
        print("Starting community goal notification...")
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"New goal in {community_name}",
                        "body": f"{creator_name} created goal: {goal_name}",
                        "token": member['device_id'],
                        "priority": "high",
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "goal_id": goal_id,
                            "type": "community_goal"
                        }
                    }
                    
                    try:
                        async with session.post(
                            f"{self.notification_service_url}/notifications",
                            json=notification_data,
                            headers=headers
                        ) as response:
                            response_text = await response.text()
                            if response.status != 200:
                                print(f"Error response: {response_text}")
                    except Exception as e:
                        print(f"Error sending community goal notification: {str(e)}")


    async def notifyCommunityAffiliation(self, creator_name: str, members: List[dict], community_name: str, affiliation_entity: str, affiliation_id: str, community_id: str):
        """
        Send notifications to community members when a new affiliation is created
        """
        print("Starting community affiliation notification...")
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"New affiliation in {community_name}",
                        "body": f"{creator_name} added affiliation: {affiliation_entity}",
                        "token": member['device_id'],
                        "priority": "high",
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "affiliation_id": affiliation_id,
                            "type": "community_affiliation"
                        }
                    }
                    
                    try:
                        async with session.post(
                            f"{self.notification_service_url}/notifications",
                            json=notification_data,
                            headers=headers
                        ) as response:
                            response_text = await response.text()
                            if response.status != 200:
                                print(f"Error response: {response_text}")
                    except Exception as e:
                        print(f"Error sending community affiliation notification: {str(e)}")

    async def notifyCommunityUpdated(self, updater_name: str, members: List[dict], community_name: str, community_id: str):
        """
        Send notifications to community members when community info is updated
        """
        print("Starting community update notification...")
        print("Notification URL:", self.notification_service_url)
        print("Updater:", updater_name)
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
                        "title": f"{community_name} updated",
                        "body": f"{updater_name} updated the community information",
                        "token": member['device_id'],
                        "priority": "normal",
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "type": "community_updated"
                        }
                    }
                    try:
                        async with session.post(
                            f"{self.notification_service_url}/notifications",
                            json=notification_data,
                            headers=headers
                        ) as response:
                            response_text = await response.text()
                            if response.status != 200:
                                print(f"Error response: {response_text}")
                    except Exception as e:
                        print(f"Error sending community update notification: {str(e)}")


    async def notifyCommunityMessage(self, sender_name: str, members: List[dict], community_name: str, message_preview: str, message_id: str, community_id: str):
        """
        Send notifications to community members when a new message is posted in community chat
        """
        print("Starting community message notification...")
        print("Notification URL:", self.notification_service_url)
        print("Sender:", sender_name)
        print("Community:", community_name)
        print("Message preview:", message_preview)
        print("Number of members:", len(members))

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"New message in {community_name}",
                        "body": f"{sender_name}: {message_preview[:50]}..." if len(message_preview) > 50 else f"{sender_name}: {message_preview}",
                        "token": member['device_id'],
                        "priority": "high",
                        "click_action": f"/community/{community_id}/chat",
                        "data": {
                            "community_id": community_id,
                            "message_id": message_id,
                            "type": "community_message"
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
                            if response.status != 200:
                                print(f"Error response: {response_text}")
                    except Exception as e:
                        print(f"Error sending community message notification: {str(e)}")

    # Agent Notifications
    async def notify_agent_assigned(self, agent_name: str, community_name: str, members: List[dict], community_id: str):
        """
        Send notifications when an agent is assigned to a community
        """
        print("Starting agent assignment notification...")
        print("Notification URL:", self.notification_service_url)
        print("Agent:", agent_name)
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
                        "title": f"New AI Agent in {community_name}",
                        "body": f"{agent_name} has been assigned as your community leader",
                        "token": member['device_id'],
                        "priority": "normal",
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "agent_name": agent_name,
                            "type": "agent_assigned"
                        }
                    }
                    print("Sending agent assignment notification to:", member['device_id'])
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
                        print(f"Error sending agent assignment notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notify_assignment_confirmation(self, assignee_name: str, agent_name: str, community_name: str, device_id: str):
        """
        Send confirmation notification to the user who assigned the agent
        """
        print("Starting assignment confirmation notification...")
        print("Notification URL:", self.notification_service_url)
        print("Assignee:", assignee_name)
        print("Agent:", agent_name)
        print("Community:", community_name)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        notification_data = {
            "title": "Agent Assignment Successful",
            "body": f"You successfully assigned {agent_name} to {community_name}",
            "token": device_id,
            "priority": "normal",
            "data": {
                "agent_name": agent_name,
                "community_name": community_name,
                "type": "assignment_confirmation"
            }
        }
        print("Sending assignment confirmation notification to:", device_id)
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
                print(f"Error sending assignment confirmation notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notify_community_update(self, agent_name: str, community_name: str, action_type: str, action_details: dict, members: List[dict], community_id: str):
        """
        Send notifications when an agent updates the community
        """
        print("Starting community update notification...")
        print("Notification URL:", self.notification_service_url)
        print("Agent:", agent_name)
        print("Community:", community_name)
        print("Action:", action_type)
        print("Number of members:", len(members))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Create user-friendly action descriptions
        action_descriptions = {
            'edit_community': 'updated the community settings',
            'send_announcement': 'sent a community announcement',
            'moderate_content': 'moderated community content',
            'manage_events': 'updated community events'
        }
        
        action_description = action_descriptions.get(action_type, f'performed {action_type}')
        
        async with aiohttp.ClientSession() as session:
            for member in members:
                if member.get('device_id'):
                    notification_data = {
                        "title": f"Update from {community_name}",
                        "body": f"Your AI leader {agent_name} {action_description}",
                        "token": member['device_id'],
                        "priority": "normal",
                        "click_action": f"/community/{community_id}",
                        "data": {
                            "community_id": community_id,
                            "agent_name": agent_name,
                            "action_type": action_type,
                            "action_details": action_details,
                            "type": "community_update"
                        }
                    }
                    print("Sending community update notification to:", member['device_id'])
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
                        print(f"Error sending community update notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notify_user_moderated(self, user_name: str, community_name: str, action: str, reason: str, agent_name: str, device_id: str):
        """
        Send notification to a user who has been moderated by an agent
        """
        print("Starting user moderation notification...")
        print("Notification URL:", self.notification_service_url)
        print("User:", user_name)
        print("Community:", community_name)
        print("Action:", action)
        print("Agent:", agent_name)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Create user-friendly action descriptions
        action_descriptions = {
            'warn': 'received a warning',
            'mute': 'been temporarily muted',
            'ban': 'been banned',
            'remove': 'been removed'
        }
        
        action_description = action_descriptions.get(action, f'been {action}ed')
        
        notification_data = {
            "title": f"Moderation Action in {community_name}",
            "body": f"You have {action_description} by {agent_name}. Reason: {reason}",
            "token": device_id,
            "priority": "high",
            "data": {
                "community_name": community_name,
                "agent_name": agent_name,
                "action": action,
                "reason": reason,
                "type": "user_moderated"
            }
        }
        print("Sending user moderation notification to:", device_id)
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
                print(f"Error sending user moderation notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notify_moderation_action(self, agent_name: str, community_name: str, target_user: str, action: str, reason: str, admins: List[dict], community_id: str):
        """
        Send notifications to community admins about moderation actions
        """
        print("Starting moderation action notification...")
        print("Notification URL:", self.notification_service_url)
        print("Agent:", agent_name)
        print("Community:", community_name)
        print("Target user:", target_user)
        print("Action:", action)
        print("Number of admins:", len(admins))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            for admin in admins:
                if admin.get('device_id'):
                    notification_data = {
                        "title": f"Moderation Alert - {community_name}",
                        "body": f"{agent_name} {action}ed {target_user}. Reason: {reason}",
                        "token": admin['device_id'],
                        "priority": "high",
                        "click_action": f"/community/{community_id}/moderation",
                        "data": {
                            "community_id": community_id,
                            "agent_name": agent_name,
                            "target_user": target_user,
                            "action": action,
                            "reason": reason,
                            "type": "moderation_action"
                        }
                    }
                    print("Sending moderation action notification to admin:", admin['device_id'])
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
                        print(f"Error sending moderation action notification: {str(e)}")
                        print(f"Full error details: {type(e).__name__}: {str(e)}")