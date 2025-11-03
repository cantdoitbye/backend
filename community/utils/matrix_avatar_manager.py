# community/utils/matrix_avatar_manager.py - Combined version

import asyncio
import aiohttp
from django.conf import settings
from auth_manager.Utils.generate_presigned_url import generate_file_info
import logging
from auth_manager.Utils import generate_presigned_url
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Dict, Any, Optional

matrix_logger = logging.getLogger("matrix_logger")

async def set_room_avatar_score_and_filter(
    access_token: str,
    user_id: str,
    room_id: str,
    image_id: str = None,
    community_data: Dict[str, Any] = None,
    timeout: int = 30
) -> dict:
    """
    Set room avatar, score, and filter data in Matrix using single state event.
    """
    print(f"DEBUG: Setting room avatar, score and filter data for room {room_id}")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare combined room data
        room_data = {
            "overall_score": "4.0",
            "room_type": "community",
            "updated_at": str(int(asyncio.get_event_loop().time()))
        }
        
        # Add avatar URL if image_id provided
        if image_id:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                file_info = await loop.run_in_executor(
                    executor,
                    generate_presigned_url.generate_file_info,
                    image_id
                )
            
            if file_info and file_info.get('url'):
                room_data["avatar_url"] = file_info['url']
                print(f"DEBUG: Avatar URL added: {file_info['url']}")
        
        # Add community filter data if provided
        if community_data:
            room_data.update({
                "community_type": community_data.get('community_type', ''),
                "community_circle": community_data.get('community_circle', ''),
                "community_category": community_data.get('category', ''),
                "created_date": str(community_data.get('created_date', '')),
                "community_uid": community_data.get('community_uid', ''),
                "community_name": community_data.get('community_name', '')
            })
            print(f"DEBUG: Community filter data added")
        
        # Use single state event for everything
        room_state_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.room.data"
        
        print(f"DEBUG: Setting combined room data in Matrix: {room_data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(room_state_url, json=room_data, headers=headers, timeout=timeout) as response:
                response_text = await response.text()
                print(f"DEBUG: Room Data HTTP Response status: {response.status}")
                print(f"DEBUG: Room Data HTTP Response text: {response_text}")
                
                if response.status == 200:
                    # Also set the standard Matrix avatar state if avatar is provided
                    if room_data.get("avatar_url"):
                        await set_standard_room_avatar(
                            session, headers, room_id, room_data["avatar_url"], timeout
                        )
                    
                    matrix_logger.info(f"Set complete room data for {room_id}")
                    return {
                        "success": True,
                        "avatar_url": room_data.get("avatar_url"),
                        "score_set": True,
                        "filter_set": bool(community_data),
                        "room_id": room_id
                    }
                else:
                    return {"success": False, "error": f"Room data update failed: HTTP {response.status}: {response_text}"}
        
    except Exception as e:
        print(f"DEBUG: Exception in set_room_avatar_score_and_filter: {e}")
        matrix_logger.error(f"Error setting room data: {e}")
        return {"success": False, "error": str(e)}


async def set_standard_room_avatar(session, headers, room_id, avatar_url, timeout):
    """
    Also set the standard Matrix room avatar state for client compatibility.
    """
    try:
        avatar_state_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/m.room.avatar"
        avatar_data = {"url": avatar_url}
        
        async with session.put(avatar_state_url, json=avatar_data, headers=headers, timeout=timeout) as response:
            if response.status == 200:
                print(f"DEBUG: Standard room avatar also set")
            else:
                print(f"DEBUG: Failed to set standard room avatar: {response.status}")
    except Exception as e:
        print(f"DEBUG: Error setting standard room avatar: {e}")


# Separate functions for backward compatibility or specific use cases
async def set_room_avatar_and_score_from_image_id(
    access_token: str,
    user_id: str,
    room_id: str,
    image_id: str,
    timeout: int = 30
) -> dict:
    """
    Set room avatar and score only (backward compatibility).
    """
    return await set_room_avatar_score_and_filter(
        access_token=access_token,
        user_id=user_id,
        room_id=room_id,
        image_id=image_id,
        community_data=None,
        timeout=timeout
    )


async def set_community_filter_data(
    access_token: str,
    user_id: str,
    room_id: str,
    community_data: Dict[str, Any],
    timeout: int = 30
) -> dict:
    """
    Set community filter data only (backward compatibility).
    """
    return await set_room_avatar_score_and_filter(
        access_token=access_token,
        user_id=user_id,
        room_id=room_id,
        image_id=None,
        community_data=community_data,
        timeout=timeout
    )