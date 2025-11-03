import asyncio
import logging
from typing import List, Dict, Optional, Any
from nio import AsyncClient, RoomSendResponse, RoomMessagesResponse
from django.conf import settings
from msg.models import MatrixProfile
from auth_manager.models import Users
from community.models import Community
from agentic.models import Agent
from auth_manager.graphql.mutations import GenerateTokenByEmail
import time

matrix_logger = logging.getLogger("matrix_logger")


class MatrixMessageError(Exception):
    """Custom exception for Matrix message operations"""
    pass


async def get_community_matrix_messages(
    access_token: str,
    user_id: str,
    room_id: str,
    limit: int = 20,
    from_token: Optional[str] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Gets messages from a Matrix room with pagination support.
    
    Args:
        access_token: User's Matrix access token
        user_id: Matrix user ID
        room_id: Matrix room ID
        limit: Number of messages to retrieve (default: 20)
        from_token: Pagination token for getting older messages
        timeout: Request timeout
        
    Returns:
        dict: Contains 'messages', 'next_token', 'prev_token' for pagination
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        response = await asyncio.wait_for(
            client.room_messages(
                room_id=room_id,
                start=from_token or "",
                limit=limit
            ),
            timeout=timeout
        )
        
        if isinstance(response, RoomMessagesResponse):
            messages = []
            
            for event in response.chunk:
                # Skip non-message events (like member events, state events, etc.)
                if not hasattr(event, 'body'):
                    continue
                    
                # Process each message and add metadata
                message_data = {
                    'event_id': event.event_id,
                    'sender': event.sender,
                    'timestamp': event.server_timestamp,
                    'content': getattr(event, 'body', ''),
                    'message_type': getattr(event, 'type', 'm.room.message'),
                    'is_agent': False,  # Will be set by calling function
                    'raw_event': event.source if hasattr(event, 'source') else {}
                }
                
                # Handle different message types
                if hasattr(event, 'formatted_body'):
                    message_data['formatted_content'] = event.formatted_body
                    
                messages.append(message_data)
            
            matrix_logger.info(f"Retrieved {len(messages)} messages from room {room_id}")
            
            return {
                'messages': messages,
                'next_token': response.end,
                'prev_token': response.start,
                'total_messages': len(messages)
            }
        else:
            matrix_logger.error(f"Failed to get messages from room {room_id}: {response}")
            raise MatrixMessageError(f"Failed to retrieve messages: {response}")
            
    except Exception as e:
        matrix_logger.error(f"Error getting messages from room {room_id}: {e}")
        raise MatrixMessageError(f"Error retrieving messages: {str(e)}")
    finally:
        await client.close()


async def send_matrix_message(
    access_token: str,
    user_id: str,
    room_id: str,
    message: str,
    message_type: str = "m.text",
    timeout: int = 10
) -> str:
    """
    Sends a message to a Matrix room.
    
    Args:
        access_token: User's Matrix access token
        user_id: Matrix user ID
        room_id: Matrix room ID
        message: Message content to send
        message_type: Type of message (default: "m.text")
        timeout: Request timeout
        
    Returns:
        str: Event ID of the sent message
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        content = {
            "msgtype": message_type,
            "body": message
        }
        
        response = await asyncio.wait_for(
            client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content=content
            ),
            timeout=timeout
        )
        
        if isinstance(response, RoomSendResponse):
            matrix_logger.info(f"Message sent successfully: {response.event_id}")
            return response.event_id
        else:
            matrix_logger.error(f"Failed to send message: {response}")
            raise MatrixMessageError(f"Failed to send message: {response}")
            
    except Exception as e:
        matrix_logger.error(f"Error sending message to room {room_id}: {e}")
        raise MatrixMessageError(f"Error sending message: {str(e)}")
    finally:
        await client.close()


def get_community_creator_token(community_uid: str) -> Optional[str]:
    """
    Gets the Matrix access token for the community creator.
    
    Args:
        community_uid: UID of the community
        
    Returns:
        str: Matrix access token or None if not available
    """
    try:
        # Get the community
        community = Community.nodes.get(uid=community_uid)
        
        # Get the creator (first admin member)
        creator = None
        for membership in community.members.all():
            if membership.is_admin:
                creator = membership.user.single()
                break
                
        if not creator:
            matrix_logger.error(f"No creator found for community {community_uid}")
            return None
            
        # Try to get Matrix profile
        try:
            matrix_profile = MatrixProfile.objects.get(user=creator.user_id)
            if matrix_profile.access_token:
                return matrix_profile.access_token
        except MatrixProfile.DoesNotExist:
            pass
            
        # If no Matrix profile, try to generate token using email
        try:
            from auth_manager.graphql.mutations import GenerateTokenByEmail
            # This would need to be called through GraphQL context
            # For now, return None and handle in GraphQL resolver
            matrix_logger.warning(f"No Matrix token available for community creator {creator.user_id}")
            return None
        except Exception as e:
            matrix_logger.error(f"Error generating token for creator: {e}")
            return None
            
    except Exception as e:
        matrix_logger.error(f"Error getting community creator token: {e}")
        return None


def flag_agent_messages(messages: List[Dict[str, Any]], community_uid: str) -> List[Dict[str, Any]]:
    """
    Flags messages sent by agents in the community.
    
    Args:
        messages: List of message dictionaries
        community_uid: UID of the community
        
    Returns:
        List[Dict]: Messages with is_agent flag set appropriately
    """
    try:
        # Get all agents assigned to this community
        community = Community.nodes.get(uid=community_uid)
        agent_matrix_ids = set()
        
        # Get agent Matrix user IDs
        for assignment in community.leader_agent.all():
            agent = assignment.agent.single()
            if agent and agent.matrix_user_id:
                agent_matrix_ids.add(agent.matrix_user_id)
                
        # Flag messages from agents
        for message in messages:
            if message['sender'] in agent_matrix_ids:
                message['is_agent'] = True
                
        return messages
        
    except Exception as e:
        matrix_logger.error(f"Error flagging agent messages: {e}")
        # Return messages as-is if flagging fails
        return messages


def get_matrix_credentials_for_community(community_uid: str) -> Optional[Dict[str, str]]:
    """
    Gets Matrix credentials for accessing a community's room.
    Uses the hardcoded OoumphLead user (ID: 771) who is part of every community.
    
    Args:
        community_uid: UID of the community
        
    Returns:
        dict: Contains 'access_token' and 'user_id' or None if not available
    """
    try:
        # Use hardcoded OoumphLead user (ID: 771) who is part of every community
        try:
            matrix_profile = MatrixProfile.objects.get(user=771)
            if matrix_profile.access_token and matrix_profile.matrix_user_id:
                return {
                    'access_token': matrix_profile.access_token,
                    'user_id': matrix_profile.matrix_user_id
                }
        except MatrixProfile.DoesNotExist:
            matrix_logger.warning(f"No Matrix profile found for OoumphLead user (ID: 771)")
            return None
                    
        matrix_logger.warning(f"No Matrix credentials found for OoumphLead user")
        return None
        
    except Exception as e:
        matrix_logger.error(f"Error getting Matrix credentials: {e}")
        return None


async def delete_matrix_message(
    access_token: str,
    user_id: str,
    room_id: str,
    event_id: str,
    reason: str = "Message deleted by moderator",
    timeout: int = 10
) -> bool:
    """
    Deletes (redacts) a message in a Matrix room.
    
    Args:
        access_token: Agent's Matrix access token
        user_id: Agent's Matrix user ID
        room_id: Matrix room ID
        event_id: Event ID of the message to delete
        reason: Reason for deletion
        timeout: Request timeout
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixMessageError: If deletion fails
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        response = await asyncio.wait_for(
            client.room_redact(room_id, event_id, reason=reason),
            timeout=timeout
        )
        
        if hasattr(response, 'event_id'):
            matrix_logger.info(f"Successfully deleted message {event_id} in room {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to delete message {event_id}: {response}")
            raise MatrixMessageError(f"Failed to delete message: {response}")
            
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout deleting message {event_id} in room {room_id}")
        raise MatrixMessageError(f"Timeout deleting message")
    except Exception as e:
        matrix_logger.error(f"Error deleting message {event_id}: {e}")
        raise MatrixMessageError(f"Error deleting message: {e}")
    finally:
        await client.close()


async def kick_user_from_room(
    access_token: str,
    user_id: str,
    room_id: str,
    target_user_id: str,
    reason: str = "Kicked by moderator",
    timeout: int = 10
) -> bool:
    """
    Kicks a user from a Matrix room.
    
    Args:
        access_token: Agent's Matrix access token
        user_id: Agent's Matrix user ID
        room_id: Matrix room ID
        target_user_id: Matrix user ID to kick
        reason: Reason for kicking
        timeout: Request timeout
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixMessageError: If kick fails
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        response = await asyncio.wait_for(
            client.room_kick(room_id, target_user_id, reason=reason),
            timeout=timeout
        )
        
        if hasattr(response, 'event_id'):
            matrix_logger.info(f"Successfully kicked user {target_user_id} from room {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to kick user {target_user_id}: {response}")
            raise MatrixMessageError(f"Failed to kick user: {response}")
            
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout kicking user {target_user_id} from room {room_id}")
        raise MatrixMessageError(f"Timeout kicking user")
    except Exception as e:
        matrix_logger.error(f"Error kicking user {target_user_id}: {e}")
        raise MatrixMessageError(f"Error kicking user: {e}")
    finally:
        await client.close()


async def ban_user_from_room(
    access_token: str,
    user_id: str,
    room_id: str,
    target_user_id: str,
    reason: str = "Banned by moderator",
    timeout: int = 10
) -> bool:
    """
    Bans a user from a Matrix room.
    
    Args:
        access_token: Agent's Matrix access token
        user_id: Agent's Matrix user ID
        room_id: Matrix room ID
        target_user_id: Matrix user ID to ban
        reason: Reason for banning
        timeout: Request timeout
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixMessageError: If ban fails
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        response = await asyncio.wait_for(
            client.room_ban(room_id, target_user_id, reason=reason),
            timeout=timeout
        )
        
        if hasattr(response, 'transport_response') and response.transport_response.status == 200:
            matrix_logger.info(f"Successfully banned user {target_user_id} from room {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to ban user {target_user_id}: {response}")
            raise MatrixMessageError(f"Failed to ban user: {response}")
            
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout banning user {target_user_id} from room {room_id}")
        raise MatrixMessageError(f"Timeout banning user")
    except Exception as e:
        matrix_logger.error(f"Error banning user {target_user_id}: {e}")
        raise MatrixMessageError(f"Error banning user: {e}")
    finally:
        await client.close()


async def unban_user_from_room(
    access_token: str,
    user_id: str,
    room_id: str,
    target_user_id: str,
    timeout: int = 10
) -> bool:
    """
    Unbans a user from a Matrix room.
    
    Args:
        access_token: Agent's Matrix access token
        user_id: Agent's Matrix user ID
        room_id: Matrix room ID
        target_user_id: Matrix user ID to unban
        timeout: Request timeout
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixMessageError: If unban fails
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        response = await asyncio.wait_for(
            client.room_unban(room_id, target_user_id),
            timeout=timeout
        )
        
        if hasattr(response, 'event_id'):
            matrix_logger.info(f"Successfully unbanned user {target_user_id} from room {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to unban user {target_user_id}: {response}")
            raise MatrixMessageError(f"Failed to unban user: {response}")
            
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout unbanning user {target_user_id} from room {room_id}")
        raise MatrixMessageError(f"Timeout unbanning user")
    except Exception as e:
        matrix_logger.error(f"Error unbanning user {target_user_id}: {e}")
        raise MatrixMessageError(f"Error unbanning user: {e}")
    finally:
        await client.close()


async def leave_matrix_room(
    access_token: str,
    user_id: str,
    room_id: str,
    timeout: int = 10
) -> bool:
    """
    Allows a user to voluntarily leave a Matrix room.
    
    Args:
        access_token: User's Matrix access token
        user_id: User's Matrix user ID
        room_id: Matrix room ID to leave
        timeout: Request timeout
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixMessageError: If leave fails
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        response = await asyncio.wait_for(
            client.room_leave(room_id),
            timeout=timeout
        )
        
        # Check if the response indicates success
        # RoomLeaveResponse doesn't have event_id, but we can check for successful HTTP response
        if hasattr(response, 'transport_response') and response.transport_response.status == 200:
            matrix_logger.info(f"Successfully left room {room_id}")
            return True
        elif hasattr(response, 'event_id'):
            # Fallback check for event_id if it exists
            matrix_logger.info(f"Successfully left room {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to leave room {room_id}: {response}")
            raise MatrixMessageError(f"Failed to leave room: {response}")
            
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout leaving room {room_id}")
        raise MatrixMessageError(f"Timeout leaving room")
    except Exception as e:
        matrix_logger.error(f"Error leaving room {room_id}: {e}")
        raise MatrixMessageError(f"Error leaving room: {e}")
    finally:
        await client.close()