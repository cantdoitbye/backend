import asyncio
import logging
from nio import (
    AsyncClient,
    RoomCreateResponse,
    RoomVisibility,
    RoomPreset,
)
import aiohttp
from django.conf import settings

matrix_logger = logging.getLogger("matrix_logger")

async def create_room(
    access_token: str,
    user_id: str,
    room_name: str,
    topic: str = "",
    visibility: str = "public",  # "public" for a public room, "private" for invite-only.
    preset: str = "public_chat", # "public_chat" or "private_chat"
    timeout: int = 10
) -> str:
    """
    Creates a room on the Matrix server using a user's login token.

    Args:
        access_token (str): The access token for the user.
        user_id (str): The Matrix user ID of the user.
        room_name (str): The name of the room to be created.
        topic (str, optional): The topic/description of the room.
        visibility (str, optional): "public" or "private" visibility for the room.
        preset (str, optional): Room preset (e.g., "public_chat" or "private_chat").
        timeout (int, optional): Timeout (in seconds) for the room creation API call.

    Returns:
        str: The room_id of the created room.

    Raises:
        Exception: If the room creation fails.
    """
    # First check if the Matrix server is reachable
    try:
        async with aiohttp.ClientSession() as session:
            versions_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/versions"
            matrix_logger.info(f"Testing connection to Matrix server at {versions_url}")
            async with session.get(versions_url, timeout=timeout) as response:
                if response.status != 200:
                    error_msg = f"Matrix server returned status {response.status}: {await response.text()}"
                    matrix_logger.error(error_msg)
                    raise Exception(f"Could not connect to the endpoint URL: {settings.MATRIX_SERVER_URL}")
    except aiohttp.ClientConnectorError as e:
        error_msg = f"Could not connect to the Matrix server at {settings.MATRIX_SERVER_URL}: {e}"
        matrix_logger.error(error_msg)
        raise Exception(f"Could not connect to the endpoint URL: {settings.MATRIX_SERVER_URL}")
    except asyncio.TimeoutError:
        error_msg = f"Connection to Matrix server at {settings.MATRIX_SERVER_URL} timed out"
        matrix_logger.error(error_msg)
        raise Exception(f"Connection to Matrix server timed out: {settings.MATRIX_SERVER_URL}")
    except Exception as e:
        error_msg = f"Error checking Matrix server availability: {e}"
        matrix_logger.error(error_msg)
        raise Exception(f"Could not connect to the endpoint URL: {settings.MATRIX_SERVER_URL}")

    # Force the conversion into the enum types by calling the enum constructors.
    # This will raise a ValueError if the provided strings are not valid.
    try:
        room_visibility = RoomVisibility(visibility.lower())
    except Exception as e:
        error_msg = f"Invalid room visibility '{visibility}': {e}"
        matrix_logger.error(error_msg)
        raise Exception(error_msg)

    try:
        room_preset = RoomPreset(preset.lower())
    except Exception as e:
        error_msg = f"Invalid room preset '{preset}': {e}"
        matrix_logger.error(error_msg)
        raise Exception(error_msg)

    matrix_logger.info(
        f"Using room_visibility: {room_visibility} (type: {type(room_visibility)}), room_preset: {room_preset} (type: {type(room_preset)})"
    )

    # Initialize the AsyncClient with the homeserver URL.
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    # Set the access token and user_id so that the client is authenticated.
    client.access_token = access_token
    client.user_id = user_id

    try:
        matrix_logger.info(f"Attempting to create room '{room_name}' for user {user_id}.")
        response = await asyncio.wait_for(
            client.room_create(
                name=room_name,
                topic=topic,
                visibility=room_visibility,  # Pass the enum object directly.
                preset=room_preset           # Pass the enum object directly.
            ),
            timeout=timeout
        )
        if isinstance(response, RoomCreateResponse) and response.room_id:
            matrix_logger.info(f"Room created successfully: {response.room_id}")
            return response.room_id
        else:
            error_msg = f"Failed to create room: {response}"
            matrix_logger.error(error_msg)
            raise Exception(error_msg)
    except asyncio.TimeoutError:
        error_msg = f"Room creation timed out for user {user_id}."
        matrix_logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        matrix_logger.error(f"An error occurred while creating the room for user {user_id}: {e}")
        raise e
    finally:
        await client.close()

# Example usage of the utility function
# async def main():
#     # Replace these values with your actual credentials and desired room details.
#     access_token = "syt_MDRkZDBhNjM4YmU2NGVmY2FkZDAyZGY4NzdjM2VmMmQ_EHFevhKjKRaXpMvjhOzM_22TY72"
#     user_id = "@04dd0a638be64efcadd02df877c3ef2d:localhost"
#     room_name = "My Utility Room"
#     topic = "A room created using a utility function with a stored login token."
    
#     try:
#         room_id = await create_room(
#             access_token=access_token,
#             user_id=user_id,
#             room_name=room_name,
#             topic=topic,
#             visibility="public",    # Use "private" for invite-only rooms.
#             preset="public_chat"    # Change to "private_chat" if needed.
#         )
#         print("Room created with ID:", room_id)
#     except Exception as e:
#         print("Error creating room:", e)

# if __name__ == "__main__":
#     # Use asyncio.run if available (Python 3.7+)
#     try:
#         asyncio.run(main())
#     except Exception as e:
#         print("Error running main:", e)
