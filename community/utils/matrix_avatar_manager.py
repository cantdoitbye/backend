import asyncio
import aiohttp
from django.conf import settings
from auth_manager.Utils.generate_presigned_url import generate_file_info
import logging
from auth_manager.Utils import generate_presigned_url
from concurrent.futures import ThreadPoolExecutor
import json

async def set_room_avatar_and_score_from_image_id(
    access_token: str,
    user_id: str,
    room_id: str,
    image_id: str,
    timeout: int = 30
) -> dict:
    """
    Set room avatar and score in Matrix using your existing image_id system.
    """
    print(f"DEBUG: Starting set_room_avatar_and_score_from_image_id with room_id: {room_id}, image_id: {image_id}")
    
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            file_info = await loop.run_in_executor(
                executor, 
                generate_presigned_url.generate_file_info, 
                image_id
            )
        
        print(f"DEBUG: file_info result: {file_info}")
        
        if not file_info or not file_info.get('url'):
            print("DEBUG: No file_info or URL found")
            return {"success": False, "error": "Invalid image ID or URL not found"}
        
        image_url = file_info['url']
        print(f"DEBUG: Image URL: {image_url}")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        avatar_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/m.room.avatar"
        avatar_data = {"url": image_url}
        
        score_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.room.score"
        score_data = {
            "overall_score": "4.0",
            "room_type": "community",
            "updated_at": str(int(asyncio.get_event_loop().time()))  # Convert to string
        }
        
        print(f"DEBUG: Setting room avatar and score in Matrix")
        
        async with aiohttp.ClientSession() as session:
            # Set room avatar
            async with session.put(avatar_url, json=avatar_data, headers=headers, timeout=timeout) as response:
                avatar_response_text = await response.text()
                print(f"DEBUG: Room Avatar HTTP Response status: {response.status}")
                print(f"DEBUG: Room Avatar HTTP Response text: {avatar_response_text}")
                
                if response.status != 200:
                    return {"success": False, "error": f"Room avatar update failed: HTTP {response.status}: {avatar_response_text}"}
            
            # Set room score data
            async with session.put(score_url, json=score_data, headers=headers, timeout=timeout) as response:
                score_response_text = await response.text()
                print(f"DEBUG: Room Score HTTP Response status: {response.status}")
                print(f"DEBUG: Room Score HTTP Response text: {score_response_text}")
                
                if response.status == 200:
                    print(f"Set room avatar and score for {room_id}: {image_url}, score: 4.0")
                    return {
                        "success": True,
                        "avatar_url": image_url,
                        "score_set": True,
                        "room_id": room_id
                    }
                else:
                    return {"success": False, "error": f"Room score update failed: HTTP {response.status}: {score_response_text}"}
        
    except Exception as e:
        print(f"DEBUG: Exception in set_room_avatar_and_score_from_image_id: {e}")
        print(f"Error setting room avatar and score: {e}")
        return {"success": False, "error": str(e)}