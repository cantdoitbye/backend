# opportunity/utils/create_opportunity_matrix_room.py

"""
Matrix Room Creation for Opportunities

This module handles the creation of Matrix rooms for job opportunities, events, causes, etc.
Each opportunity gets its own Matrix room where applicants can join and communicate with the creator.

Pattern: Based on community/utils/create_matrix_room_with_token.py
"""

import asyncio
import logging
from nio import AsyncClient, RoomCreateResponse, RoomVisibility, RoomPreset
from django.conf import settings

opportunity_logger = logging.getLogger("opportunity_logger")


async def create_opportunity_room(
    access_token: str,
    user_id: str,
    opportunity_data: dict,
    timeout: int = 10
) -> str:
    """
    Creates a Matrix room for an opportunity (job/event/cause).
    
    This function creates a new Matrix room that will serve as a chat space for the opportunity.
    Applicants can join this room to apply and communicate with the opportunity creator.
    
    Args:
        access_token: Creator's Matrix access token
        user_id: Creator's Matrix user ID (e.g., @uid:chat.ooumph.com)
        opportunity_data: Dictionary containing:
            - role: Opportunity title/role
            - opportunity_type: "job", "event", "cause", etc.
            - location: Location of opportunity
            - description: Brief description (used as room topic)
            - opportunity_uid: UID of the opportunity
        timeout: Request timeout in seconds
        
    Returns:
        str: Matrix room ID (e.g., "!abc123:chat.ooumph.com")
        
    Raises:
        Exception: If room creation fails
        
    Example:
        >>> room_id = await create_opportunity_room(
        ...     access_token="syt_...",
        ...     user_id="@user123:chat.ooumph.com",
        ...     opportunity_data={
        ...         'role': 'UI/UX Designer',
        ...         'opportunity_type': 'job',
        ...         'location': 'Bengaluru',
        ...         'description': 'Looking for experienced designer',
        ...         'opportunity_uid': 'opp_123'
        ...     }
        ... )
        >>> print(room_id)  # "!xyz789:chat.ooumph.com"
    """
    
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        # Extract opportunity info
        role = opportunity_data.get('role', 'Opportunity')
        opportunity_type = opportunity_data.get('opportunity_type', 'job')
        location = opportunity_data.get('location', '')
        description = opportunity_data.get('description', '')[:200]  # Max 200 chars for topic
        opportunity_uid = opportunity_data.get('opportunity_uid', '')
        
        # Format room name based on type
        type_emoji = {
            'job': '💼',
            'event': '📅',
            'cause': '❤️',
            'collaboration': '🤝',
            'mentorship': '👨‍🏫',
            'internship': '🎓',
            'gig': '⚡'
        }
        emoji = type_emoji.get(opportunity_type, '💼')
        
        # Room name: "💼 UI/UX Designer - Bengaluru"
        room_name = f"{emoji} {role}"
        if location:
            room_name += f" - {location}"
        
        # Room topic: Brief description
        room_topic = description or f"{opportunity_type.title()} opportunity: {role}"
        
        # Room alias: opportunity_<uid> (optional, for easy discovery)
        room_alias = f"opportunity_{opportunity_uid}" if opportunity_uid else None
        
        opportunity_logger.info(
            f"Creating Matrix room for {opportunity_type}: {role} (user: {user_id})"
        )
        
        # Create the room
        # Public room so applicants can discover and join
        response = await asyncio.wait_for(
            client.room_create(
                name=room_name,
                topic=room_topic,
                alias=room_alias,
                visibility=RoomVisibility.public,  # Public visibility for discoverability
                preset=RoomPreset.public_chat,  # Public chat preset
                initial_state=[
                    {
                        "type": "m.room.history_visibility",
                        "state_key": "",
                        "content": {"history_visibility": "shared"}
                    },
                    {
                        "type": "m.room.join_rules",
                        "state_key": "",
                        "content": {"join_rule": "public"}
                    }
                ]
            ),
            timeout=timeout
        )
        
        # Check if room creation was successful
        if isinstance(response, RoomCreateResponse):
            room_id = response.room_id
            opportunity_logger.info(
                f"✓ Successfully created Matrix room: {room_id} for opportunity {opportunity_uid}"
            )
            return room_id
        else:
            error_msg = f"Failed to create Matrix room: {response}"
            opportunity_logger.error(error_msg)
            raise Exception(error_msg)
            
    except asyncio.TimeoutError:
        error_msg = f"Timeout creating Matrix room for opportunity {opportunity_data.get('opportunity_uid')}"
        opportunity_logger.error(error_msg)
        raise Exception(error_msg)
        
    except Exception as e:
        opportunity_logger.error(
            f"Error creating Matrix room for opportunity {opportunity_data.get('opportunity_uid')}: {e}"
        )
        raise e
        
    finally:
        await client.close()


async def create_private_opportunity_room(
    access_token: str,
    user_id: str,
    opportunity_data: dict,
    invited_user_ids: list = None,
    timeout: int = 10
) -> str:
    """
    Creates a PRIVATE Matrix room for an opportunity (for inner/outer circle postings).
    
    Use this for opportunities posted with privacy settings (connections, inner, outer).
    Only invited users can join these rooms.
    
    Args:
        access_token: Creator's Matrix access token
        user_id: Creator's Matrix user ID
        opportunity_data: Same as create_opportunity_room
        invited_user_ids: List of Matrix user IDs to invite (optional)
        timeout: Request timeout
        
    Returns:
        str: Matrix room ID
        
    Example:
        >>> room_id = await create_private_opportunity_room(
        ...     access_token="syt_...",
        ...     user_id="@user123:chat.ooumph.com",
        ...     opportunity_data={...},
        ...     invited_user_ids=["@user456:chat.ooumph.com", "@user789:chat.ooumph.com"]
        ... )
    """
    
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        role = opportunity_data.get('role', 'Opportunity')
        opportunity_type = opportunity_data.get('opportunity_type', 'job')
        location = opportunity_data.get('location', '')
        description = opportunity_data.get('description', '')[:200]
        
        type_emoji = {
            'job': '💼',
            'event': '📅',
            'cause': '❤️',
            'collaboration': '🤝',
            'mentorship': '👨‍🏫',
            'internship': '🎓',
            'gig': '⚡'
        }
        emoji = type_emoji.get(opportunity_type, '💼')
        
        room_name = f"🔒 {emoji} {role}"
        if location:
            room_name += f" - {location}"
        
        room_topic = description or f"Private {opportunity_type} opportunity: {role}"
        
        opportunity_logger.info(
            f"Creating PRIVATE Matrix room for {opportunity_type}: {role}"
        )
        
        # Create private room
        response = await asyncio.wait_for(
            client.room_create(
                name=room_name,
                topic=room_topic,
                visibility=RoomVisibility.private,  # Private visibility
                preset=RoomPreset.private_chat,  # Private preset
                invite=invited_user_ids or [],  # Invite specific users
                initial_state=[
                    {
                        "type": "m.room.history_visibility",
                        "state_key": "",
                        "content": {"history_visibility": "invited"}
                    },
                    {
                        "type": "m.room.join_rules",
                        "state_key": "",
                        "content": {"join_rule": "invite"}
                    }
                ]
            ),
            timeout=timeout
        )
        
        if isinstance(response, RoomCreateResponse):
            room_id = response.room_id
            opportunity_logger.info(
                f"✓ Created PRIVATE Matrix room: {room_id}"
            )
            return room_id
        else:
            error_msg = f"Failed to create private Matrix room: {response}"
            opportunity_logger.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        opportunity_logger.error(f"Error creating private Matrix room: {e}")
        raise e
        
    finally:
        await client.close()


# Example usage (for testing)
# async def main():
#     access_token = "syt_..."
#     user_id = "@user123:chat.ooumph.com"
#     
#     opportunity_data = {
#         'role': 'Senior Backend Developer',
#         'opportunity_type': 'job',
#         'location': 'Remote',
#         'description': 'We are looking for an experienced backend developer to join our team.',
#         'opportunity_uid': 'opp_abc123'
#     }
#     
#     try:
#         room_id = await create_opportunity_room(
#             access_token=access_token,
#             user_id=user_id,
#             opportunity_data=opportunity_data
#         )
#         print(f"Room created: {room_id}")
#     except Exception as e:
#         print(f"Error: {e}")
# 
# if __name__ == "__main__":
#     asyncio.run(main())
