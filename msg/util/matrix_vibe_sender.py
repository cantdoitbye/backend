import asyncio
import logging
from nio import AsyncClient, RoomSendResponse
from django.conf import settings

matrix_logger = logging.getLogger("matrix_logger")


async def send_vibe_reaction_to_matrix(
    access_token: str,
    user_id: str,
    room_id: str,
    original_event_id: str,
    vibe_name: str,
    vibe_intensity: float,
    individual_vibe_id: int,
    profile_image_url: str = None,
    timeout: int = 10
) -> str:
    """
    Sends a vibe reaction to a Matrix message with proper float handling.
    
    Args:
        access_token: User's Matrix access token
        user_id: Matrix user ID 
        room_id: Matrix room ID
        original_event_id: Event ID of message being reacted to
        vibe_name: Name from IndividualVibe.name_of_vibe
        vibe_intensity: Intensity level (1.0 to 5.0)
        individual_vibe_id: ID from IndividualVibe model
        profile_image_url: User's profile image URL (optional)
        timeout: Request timeout
        
    Returns:
        str: Event ID of the reaction, or None if failed
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        # Sanitize all values to avoid JSON errors
        clean_intensity = round(float(vibe_intensity), 2)
        clean_vibe_id = int(individual_vibe_id)
        clean_vibe_name = str(vibe_name).replace(":", "_").replace(" ", "_").strip()
        
        # Sanitize profile image URL if provided
        clean_profile_image = ""
        if profile_image_url:
            # Remove problematic characters and encode URL-safe characters
            clean_profile_image = str(profile_image_url).replace(":", "_").replace(" ", "_").replace("/", "_").strip()
        
        # Create vibe key with profile image
        if clean_profile_image:
            vibe_key = f"ooumph_vibe_{clean_vibe_id}_{clean_vibe_name}_{clean_intensity}_{clean_profile_image}"
        else:
            vibe_key = f"ooumph_vibe_{clean_vibe_id}_{clean_vibe_name}_{clean_intensity}"
        
        # Simple reaction content - no custom fields that might cause JSON issues
        reaction_content = {
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": str(original_event_id),
                "key": vibe_key
            }
        }
        
        matrix_logger.info(f"Sending vibe reaction: {vibe_key} to event {original_event_id}")
        
        response = await asyncio.wait_for(
            client.room_send(
                room_id=room_id,
                message_type="m.reaction",
                content=reaction_content
            ),
            timeout=timeout
        )
        
        if isinstance(response, RoomSendResponse):
            matrix_logger.info(f"Vibe reaction sent successfully: {response.event_id}")
            return response.event_id
        else:
            matrix_logger.error(f"Failed to send vibe reaction: {response}")
            return None
            
    except Exception as e:
        matrix_logger.error(f"Error sending vibe reaction: {e}")
        return None
    finally:
        await client.close()


async def send_emoji_reaction_to_matrix(
    access_token: str,
    user_id: str,
    room_id: str,
    original_event_id: str,
    emoji: str,
    timeout: int = 10
) -> str:
    """
    Sends a standard emoji reaction to a Matrix message.
    
    Args:
        access_token: User's Matrix access token
        user_id: Matrix user ID
        room_id: Matrix room ID
        original_event_id: Event ID of message being reacted to
        emoji: Emoji character (e.g., "👍", "❤️", "😂")
        timeout: Request timeout
        
    Returns:
        str: Event ID of the reaction, or None if failed
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        # Standard Matrix emoji reaction
        reaction_content = {
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": str(original_event_id),
                "key": str(emoji)
            }
        }
        
        matrix_logger.info(f"Sending emoji reaction: {emoji} to event {original_event_id}")
        
        response = await asyncio.wait_for(
            client.room_send(
                room_id=room_id,
                message_type="m.reaction",
                content=reaction_content
            ),
            timeout=timeout
        )
        
        if isinstance(response, RoomSendResponse):
            matrix_logger.info(f"Emoji reaction sent successfully: {response.event_id}")
            return response.event_id
        else:
            matrix_logger.error(f"Failed to send emoji reaction: {response}")
            return None
            
    except Exception as e:
        matrix_logger.error(f"Error sending emoji reaction: {e}")
        return None
    finally:
        await client.close()


async def create_test_room_and_message(
    access_token: str,
    user_id: str,
    room_name: str = "Vibe Test Room",
    timeout: int = 10
) -> dict:
    """
    Creates a test room and sends a message for vibe testing.
    
    Args:
        access_token: User's Matrix access token
        user_id: Matrix user ID
        room_name: Name for the test room
        timeout: Request timeout
        
    Returns:
        dict: Contains room_id, message_event_id, and success status
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        # Create room
        room_response = await asyncio.wait_for(
            client.room_create(
                name=room_name,
                topic="Testing vibe reactions",
                is_public=True,
                preset="public_chat"
            ),
            timeout=timeout
        )
        
        if hasattr(room_response, 'room_id') and room_response.room_id:
            room_id = room_response.room_id
            matrix_logger.info(f"Created test room: {room_id}")
            
            # Send a test message to react to
            message_response = await asyncio.wait_for(
                client.room_send(
                    room_id=room_id,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.text",
                        "body": "This is a test message for vibe reactions! 🎉"
                    }
                ),
                timeout=timeout
            )
            
            if hasattr(message_response, 'event_id') and message_response.event_id:
                message_event_id = message_response.event_id
                matrix_logger.info(f"Sent test message: {message_event_id}")
                
                return {
                    "success": True,
                    "room_id": room_id,
                    "message_event_id": message_event_id
                }
        
        return {
            "success": False,
            "error": "Failed to create room or send message"
        }
        
    except Exception as e:
        matrix_logger.error(f"Error creating test room: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        await client.close()


async def join_room_by_id(
    access_token: str,
    user_id: str,
    room_id: str,
    timeout: int = 10
) -> bool:
    """
    Joins a user to a specific Matrix room.
    
    Args:
        access_token: User's Matrix access token
        user_id: Matrix user ID
        room_id: Matrix room ID to join
        timeout: Request timeout
        
    Returns:
        bool: True if successful, False otherwise
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        response = await asyncio.wait_for(
            client.join(room_id),
            timeout=timeout
        )
        
        if hasattr(response, 'room_id'):
            matrix_logger.info(f"Successfully joined room: {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to join room {room_id}: {response}")
            return False
            
    except Exception as e:
        matrix_logger.error(f"Error joining room {room_id}: {e}")
        return False
    finally:
        await client.close()


async def get_room_messages(
    access_token: str,
    user_id: str,
    room_id: str,
    limit: int = 20,
    timeout: int = 10
) -> list:
    """
    Gets recent messages from a Matrix room.
    
    Args:
        access_token: User's Matrix access token
        user_id: Matrix user ID
        room_id: Matrix room ID
        limit: Number of messages to retrieve
        timeout: Request timeout
        
    Returns:
        list: List of recent messages
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id
    
    try:
        response = await asyncio.wait_for(
            client.room_messages(
                room_id=room_id,
                start="",
                limit=limit
            ),
            timeout=timeout
        )
        
        if hasattr(response, 'chunk'):
            matrix_logger.info(f"Retrieved {len(response.chunk)} messages from room {room_id}")
            return response.chunk
        else:
            matrix_logger.error(f"Failed to get messages from room {room_id}: {response}")
            return []
            
    except Exception as e:
        matrix_logger.error(f"Error getting messages from room {room_id}: {e}")
        return []
    finally:
        await client.close()


def sanitize_vibe_name(vibe_name: str) -> str:
    """
    Sanitizes vibe name for use in Matrix reaction keys.
    
    Args:
        vibe_name: Original vibe name
        
    Returns:
        str: Sanitized vibe name safe for Matrix keys
    """
    if not vibe_name:
        return "unknown"
    
    # Replace problematic characters
    sanitized = str(vibe_name).strip()
    sanitized = sanitized.replace(":", "_")
    sanitized = sanitized.replace(" ", "_")
    sanitized = sanitized.replace("-", "_")
    sanitized = sanitized.replace("/", "_")
    sanitized = sanitized.replace("\\", "_")
    
    # Remove any remaining non-alphanumeric characters except underscores
    sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in sanitized)
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "vibe"
    
    return sanitized


def validate_vibe_intensity(intensity: float) -> float:
    """
    Validates and sanitizes vibe intensity value.
    
    Args:
        intensity: Raw intensity value
        
    Returns:
        float: Sanitized intensity value (1.0 to 5.0)
        
    Raises:
        ValueError: If intensity is invalid
    """
    try:
        clean_intensity = float(intensity)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid intensity value: {intensity}")
    
    # Check for infinity or NaN
    if not (-1000 <= clean_intensity <= 1000):  # Reasonable bounds check
        raise ValueError(f"Intensity value out of reasonable range: {clean_intensity}")
    
    # Round to 2 decimal places
    clean_intensity = round(clean_intensity, 2)
    
    # Validate range
    if not (1.0 <= clean_intensity <= 5.0):
        raise ValueError(f"Intensity must be between 1.0 and 5.0, got: {clean_intensity}")
    
    return clean_intensity