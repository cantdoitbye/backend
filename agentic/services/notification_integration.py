# Agent Notification Integration Service
# This module integrates agent events with the existing notification system.

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging

from community.services.notification_service import NotificationService
from .webhook_service import webhook_service
from .auth_service import AgentAuthService
from ..models import Agent, AgentCommunityAssignment
from community.models import Community, Membership
from auth_manager.models import Users


logger = logging.getLogger(__name__)


class AgentNotificationError(Exception):
    """Base exception for agent notification errors."""
    pass


class AgentNotificationService:
    """
    Service for integrating agent events with the notification system.
    
    This service handles sending notifications for agent-related events
    and integrates with both the existing notification service and webhook system.
    """
    
    def __init__(self):
        """Initialize the notification service."""
        self.notification_service = NotificationService()
        self.auth_service = AgentAuthService()
        
        # Register webhook event handlers
        self._register_webhook_handlers()
    
    def _register_webhook_handlers(self):
        """Register webhook event handlers for agent events."""
        webhook_service.register_event_handler('agent.assigned', self._handle_agent_assigned)
        webhook_service.register_event_handler('agent.action', self._handle_agent_action)
        webhook_service.register_event_handler('community.updated', self._handle_community_updated)
        webhook_service.register_event_handler('user.moderated', self._handle_user_moderated)
        
        logger.info("Registered webhook event handlers for agent notifications")
    
    async def notify_agent_assigned(
        self, 
        agent_uid: str, 
        community_uid: str, 
        assignment_uid: str,
        assigned_by_uid: str
    ) -> Dict[str, Any]:
        """
        Send notifications when an agent is assigned to a community.
        
        Args:
            agent_uid: UID of the assigned agent
            community_uid: UID of the community
            assignment_uid: UID of the assignment
            assigned_by_uid: UID of the user who made the assignment
            
        Returns:
            Dict containing notification results
        """
        try:
            logger.info(f"Sending agent assignment notifications for agent {agent_uid}")
            
            # Get agent, community, and assignment details
            agent = Agent.nodes.get(uid=agent_uid)
            community = Community.nodes.get(uid=community_uid)
            assigned_by = Users.nodes.get(user_id=assigned_by_uid)
            
            # Prepare notification data
            notification_data = {
                'agent_name': agent.name,
                'agent_type': agent.agent_type,
                'community_name': community.name,
                'community_uid': community_uid,
                'assigned_by': assigned_by.username,
                'assignment_date': datetime.now().isoformat()
            }
            
            # Get community members to notify
            members_to_notify = self._get_community_members_for_notification(community)
            
            # Send notifications to community members
            notification_results = []
            if members_to_notify:
                try:
                    # Use existing notification service
                    await self.notification_service.notify_agent_assigned(
                        agent_name=agent.name,
                        community_name=community.name,
                        members=members_to_notify,
                        community_id=community_uid
                    )
                    
                    notification_results.append({
                        'type': 'community_members',
                        'recipients_count': len(members_to_notify),
                        'success': True
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to send community member notifications: {str(e)}")
                    notification_results.append({
                        'type': 'community_members',
                        'recipients_count': len(members_to_notify),
                        'success': False,
                        'error': str(e)
                    })
            
            # Send notification to the user who made the assignment
            try:
                assigned_by_profile = assigned_by.profile.single()
                if assigned_by_profile and assigned_by_profile.device_id:
                    await self.notification_service.notify_assignment_confirmation(
                        assignee_name=assigned_by.username,
                        agent_name=agent.name,
                        community_name=community.name,
                        device_id=assigned_by_profile.device_id
                    )
                    
                    notification_results.append({
                        'type': 'assignment_confirmation',
                        'recipients_count': 1,
                        'success': True
                    })
                
            except Exception as e:
                logger.error(f"Failed to send assignment confirmation: {str(e)}")
                notification_results.append({
                    'type': 'assignment_confirmation',
                    'recipients_count': 1,
                    'success': False,
                    'error': str(e)
                })
            
            # Dispatch webhook event
            try:
                await webhook_service.dispatch_agent_assigned(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    assignment_uid=assignment_uid,
                    assigned_by_uid=assigned_by_uid
                )
                
                notification_results.append({
                    'type': 'webhook_dispatch',
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Failed to dispatch webhook event: {str(e)}")
                notification_results.append({
                    'type': 'webhook_dispatch',
                    'success': False,
                    'error': str(e)
                })
            
            # Log the notification activity
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="notification_sent",
                details={
                    "notification_type": "agent_assigned",
                    "notification_results": notification_results
                },
                success=True
            )
            
            return {
                'success': True,
                'message': 'Agent assignment notifications sent',
                'notification_results': notification_results,
                'notification_data': notification_data
            }
            
        except Exception as e:
            logger.error(f"Failed to send agent assignment notifications: {str(e)}")
            raise AgentNotificationError(f"Failed to send notifications: {str(e)}")
    
    async def notify_agent_action(
        self, 
        agent_uid: str, 
        community_uid: str, 
        action_type: str,
        action_details: Dict[str, Any],
        notify_members: bool = True
    ) -> Dict[str, Any]:
        """
        Send notifications for agent actions.
        
        Args:
            agent_uid: UID of the agent that performed the action
            community_uid: UID of the community
            action_type: Type of action performed
            action_details: Details about the action
            notify_members: Whether to notify community members
            
        Returns:
            Dict containing notification results
        """
        try:
            logger.info(f"Sending agent action notifications for {action_type}")
            
            # Get agent and community details
            agent = Agent.nodes.get(uid=agent_uid)
            community = Community.nodes.get(uid=community_uid)
            
            # Prepare notification based on action type
            notification_results = []
            
            if notify_members and action_type in ['edit_community', 'send_announcement']:
                # Notify community members about significant actions
                members_to_notify = self._get_community_members_for_notification(community)
                
                if members_to_notify:
                    try:
                        await self.notification_service.notify_community_update(
                            agent_name=agent.name,
                            community_name=community.name,
                            action_type=action_type,
                            action_details=action_details,
                            members=members_to_notify,
                            community_id=community_uid
                        )
                        
                        notification_results.append({
                            'type': 'community_members',
                            'recipients_count': len(members_to_notify),
                            'success': True
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to send community update notifications: {str(e)}")
                        notification_results.append({
                            'type': 'community_members',
                            'recipients_count': len(members_to_notify),
                            'success': False,
                            'error': str(e)
                        })
            
            # Dispatch webhook event
            try:
                await webhook_service.dispatch_agent_action(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    action_type=action_type,
                    action_details=action_details
                )
                
                notification_results.append({
                    'type': 'webhook_dispatch',
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Failed to dispatch webhook event: {str(e)}")
                notification_results.append({
                    'type': 'webhook_dispatch',
                    'success': False,
                    'error': str(e)
                })
            
            return {
                'success': True,
                'message': f'Agent action notifications sent for {action_type}',
                'notification_results': notification_results
            }
            
        except Exception as e:
            logger.error(f"Failed to send agent action notifications: {str(e)}")
            raise AgentNotificationError(f"Failed to send notifications: {str(e)}")
    
    async def notify_user_moderated(
        self, 
        agent_uid: str, 
        community_uid: str, 
        target_user_uid: str,
        action: str, 
        reason: str
    ) -> Dict[str, Any]:
        """
        Send notifications for user moderation actions.
        
        Args:
            agent_uid: UID of the agent that performed the moderation
            community_uid: UID of the community
            target_user_uid: UID of the user being moderated
            action: Moderation action performed
            reason: Reason for the moderation
            
        Returns:
            Dict containing notification results
        """
        try:
            logger.info(f"Sending user moderation notifications for action {action}")
            
            # Get relevant details
            agent = Agent.nodes.get(uid=agent_uid)
            community = Community.nodes.get(uid=community_uid)
            target_user = Users.nodes.get(uid=target_user_uid)
            
            notification_results = []
            
            # Notify the moderated user
            try:
                target_profile = target_user.profile.single()
                if target_profile and target_profile.device_id:
                    await self.notification_service.notify_user_moderated(
                        user_name=target_user.username,
                        community_name=community.name,
                        action=action,
                        reason=reason,
                        agent_name=agent.name,
                        device_id=target_profile.device_id
                    )
                    
                    notification_results.append({
                        'type': 'moderated_user',
                        'recipients_count': 1,
                        'success': True
                    })
                
            except Exception as e:
                logger.error(f"Failed to send moderation notification to user: {str(e)}")
                notification_results.append({
                    'type': 'moderated_user',
                    'recipients_count': 1,
                    'success': False,
                    'error': str(e)
                })
            
            # Notify community admins for serious actions
            if action in ['ban', 'remove']:
                try:
                    admin_members = self._get_community_admins_for_notification(community)
                    
                    if admin_members:
                        await self.notification_service.notify_moderation_action(
                            agent_name=agent.name,
                            community_name=community.name,
                            target_user=target_user.username,
                            action=action,
                            reason=reason,
                            admins=admin_members,
                            community_id=community_uid
                        )
                        
                        notification_results.append({
                            'type': 'community_admins',
                            'recipients_count': len(admin_members),
                            'success': True
                        })
                    
                except Exception as e:
                    logger.error(f"Failed to send admin notifications: {str(e)}")
                    notification_results.append({
                        'type': 'community_admins',
                        'recipients_count': len(admin_members) if 'admin_members' in locals() else 0,
                        'success': False,
                        'error': str(e)
                    })
            
            # Dispatch webhook event
            try:
                await webhook_service.dispatch_user_moderated(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    target_user_uid=target_user_uid,
                    action=action,
                    reason=reason
                )
                
                notification_results.append({
                    'type': 'webhook_dispatch',
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Failed to dispatch webhook event: {str(e)}")
                notification_results.append({
                    'type': 'webhook_dispatch',
                    'success': False,
                    'error': str(e)
                })
            
            return {
                'success': True,
                'message': f'User moderation notifications sent for {action}',
                'notification_results': notification_results
            }
            
        except Exception as e:
            logger.error(f"Failed to send user moderation notifications: {str(e)}")
            raise AgentNotificationError(f"Failed to send notifications: {str(e)}")
    
    def _get_community_members_for_notification(self, community: Community) -> List[Dict[str, str]]:
        """
        Get community members who should receive notifications.
        
        Args:
            community: Community object
            
        Returns:
            List of member notification data
        """
        members_to_notify = []
        
        try:
            members = community.members.all()
            
            for membership in members:
                if membership.is_blocked or membership.is_notification_muted:
                    continue
                
                user = membership.user.single()
                if not user:
                    continue
                
                profile = user.profile.single()
                if profile and profile.device_id:
                    members_to_notify.append({
                        'device_id': profile.device_id,
                        'uid': user.uid,
                        'username': user.username
                    })
        
        except Exception as e:
            logger.error(f"Error getting community members for notification: {str(e)}")
        
        return members_to_notify
    
    def _get_community_admins_for_notification(self, community: Community) -> List[Dict[str, str]]:
        """
        Get community admins who should receive notifications.
        
        Args:
            community: Community object
            
        Returns:
            List of admin notification data
        """
        admins_to_notify = []
        
        try:
            members = community.members.all()
            
            for membership in members:
                if not membership.is_admin or membership.is_blocked or membership.is_notification_muted:
                    continue
                
                user = membership.user.single()
                if not user:
                    continue
                
                profile = user.profile.single()
                if profile and profile.device_id:
                    admins_to_notify.append({
                        'device_id': profile.device_id,
                        'uid': user.uid,
                        'username': user.username
                    })
        
        except Exception as e:
            logger.error(f"Error getting community admins for notification: {str(e)}")
        
        return admins_to_notify
    
    # Webhook event handlers
    
    async def _handle_agent_assigned(self, event_payload: Dict[str, Any]):
        """Handle agent assignment webhook events."""
        try:
            data = event_payload['data']
            
            # Send real-time notification update
            await self._send_realtime_update(
                event_type='agent_assigned',
                data=data
            )
            
        except Exception as e:
            logger.error(f"Error handling agent assigned webhook event: {str(e)}")
    
    async def _handle_agent_action(self, event_payload: Dict[str, Any]):
        """Handle agent action webhook events."""
        try:
            data = event_payload['data']
            
            # Send real-time notification update for significant actions
            if data['action_type'] in ['edit_community', 'moderate_user', 'send_announcement']:
                await self._send_realtime_update(
                    event_type='agent_action',
                    data=data
                )
            
        except Exception as e:
            logger.error(f"Error handling agent action webhook event: {str(e)}")
    
    async def _handle_community_updated(self, event_payload: Dict[str, Any]):
        """Handle community update webhook events."""
        try:
            data = event_payload['data']
            
            # Send real-time notification update
            await self._send_realtime_update(
                event_type='community_updated',
                data=data
            )
            
        except Exception as e:
            logger.error(f"Error handling community updated webhook event: {str(e)}")
    
    async def _handle_user_moderated(self, event_payload: Dict[str, Any]):
        """Handle user moderation webhook events."""
        try:
            data = event_payload['data']
            
            # Send real-time notification update
            await self._send_realtime_update(
                event_type='user_moderated',
                data=data
            )
            
        except Exception as e:
            logger.error(f"Error handling user moderated webhook event: {str(e)}")
    
    async def _send_realtime_update(self, event_type: str, data: Dict[str, Any]):
        """
        Send real-time updates to connected clients.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            # In a full implementation, this would integrate with WebSocket connections
            # or Server-Sent Events to send real-time updates to connected clients
            
            logger.info(f"Sending real-time update for {event_type}")
            
            # For now, we'll just log the event
            # In production, this would:
            # 1. Find connected clients for the community
            # 2. Send WebSocket/SSE messages
            # 3. Update any real-time dashboards
            # 4. Trigger UI refresh notifications
            
        except Exception as e:
            logger.error(f"Error sending real-time update: {str(e)}")


# Global notification service instance
agent_notification_service = AgentNotificationService()