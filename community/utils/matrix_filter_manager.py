import asyncio
import aiohttp
import logging
from django.conf import settings
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

matrix_logger = logging.getLogger("matrix_logger")

async def set_community_filter_data(
    access_token: str,
    user_id: str,
    room_id: str,
    community_data: Dict[str, Any],
    timeout: int = 30
) -> dict:
    """
    Set community filter data in Matrix room state for client-side filtering.
    
    Args:
        access_token: Matrix access token
        user_id: Matrix user ID
        room_id: Matrix room ID
        community_data: Dictionary containing community filter information
        timeout: Request timeout
        
    Returns:
        dict: Success status and any error messages
    """
    print(f"DEBUG: Setting community filter data for room {room_id}")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Set community filter data in Matrix room state
        filter_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.community.filter"
        filter_data = {
            "community_type": community_data.get('community_type', ''),
            "community_circle": community_data.get('community_circle', ''),
            "community_category": community_data.get('category', ''),
            "created_date": str(community_data.get('created_date', '')),
            "room_type": "community",
            "updated_at": str(int(asyncio.get_event_loop().time()))
        }
        
        print(f"DEBUG: Setting community filter data in Matrix: {filter_data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(filter_url, json=filter_data, headers=headers, timeout=timeout) as response:
                response_text = await response.text()
                print(f"DEBUG: Community Filter HTTP Response status: {response.status}")
                print(f"DEBUG: Community Filter HTTP Response text: {response_text}")
                
                if response.status != 200:
                    return {"success": False, "error": f"Community filter data update failed: HTTP {response.status}: {response_text}"}
        
        matrix_logger.info(f"Successfully set community filter data for room {room_id}")
        return {"success": True}
        
    except Exception as e:
        matrix_logger.error(f"Error setting community filter data for room {room_id}: {e}")
        return {"success": False, "error": str(e)}