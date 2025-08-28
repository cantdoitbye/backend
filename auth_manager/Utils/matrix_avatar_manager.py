import asyncio
import aiohttp
from django.conf import settings
from auth_manager.Utils.generate_presigned_url import generate_file_info
import logging
from auth_manager.Utils import generate_presigned_url
from concurrent.futures import ThreadPoolExecutor
import json

matrix_logger = logging.getLogger("matrix_logger")

async def set_user_avatar_from_image_id(
    access_token: str,
    user_id: str,
    image_id: str,
    timeout: int = 30
) -> dict:
    """
    Set user avatar in Matrix using your existing image_id system.
    """
    print(f"DEBUG: Starting set_user_avatar_from_image_id with image_id: {image_id}")
    
    try:
        # Get image URL from your existing system using thread executor
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
        
        # 1. Set avatar URL
        avatar_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/profile/{user_id}/avatar_url"
        avatar_data = {"avatar_url": image_url}
        
        # 2. Set custom score data in Matrix profile
        score_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/user/{user_id}/account_data/com.ooumph.user.score"
        score_data = {
            "overall_score": 4.0,
            "updated_at": int(asyncio.get_event_loop().time())
        }
        
        print(f"DEBUG: Setting avatar and score in Matrix")
        
        async with aiohttp.ClientSession() as session:
            # Set avatar
            async with session.put(avatar_url, json=avatar_data, headers=headers, timeout=timeout) as response:
                avatar_response_text = await response.text()
                print(f"DEBUG: Avatar HTTP Response status: {response.status}")
                print(f"DEBUG: Avatar HTTP Response text: {avatar_response_text}")
                
                if response.status != 200:
                    return {"success": False, "error": f"Avatar update failed: HTTP {response.status}: {avatar_response_text}"}
            
            # Set score data
            async with session.put(score_url, json=score_data, headers=headers, timeout=timeout) as response:
                score_response_text = await response.text()
                print(f"DEBUG: Score HTTP Response status: {response.status}")
                print(f"DEBUG: Score HTTP Response text: {score_response_text}")
                
                if response.status == 200:
                    # Also save score to local database
                    await save_user_score_local(user_id, 4.0)
                    
                    matrix_logger.info(f"Set user avatar and score for {user_id}: {image_url}, score: 4.0")
                    return {
                        "success": True,
                        "avatar_url": image_url,
                        "score_set": True
                    }
                else:
                    return {"success": False, "error": f"Score update failed: HTTP {response.status}: {score_response_text}"}
        
    except Exception as e:
        print(f"DEBUG: Exception in set_user_avatar_from_image_id: {e}")
        matrix_logger.error(f"Error setting user avatar: {e}")
        return {"success": False, "error": str(e)}

async def save_user_score_local(user_id: str, score_value: float):
    """Save score to local database as well"""
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor, 
                _update_score_sync, 
                user_id, 
                score_value
            )
        print(f"DEBUG: Updated local score {score_value} for user {user_id}")
    except Exception as e:
        print(f"DEBUG: Error updating local score: {e}")

def _update_score_sync(user_id: str, score_value: float):
    """Synchronous function to update existing score in local DB"""
    try:
        from auth_manager.models import Users, Score
        import time
        
        # Get the user node
        user_node = Users.nodes.get(user_id=user_id)
        
        # Get existing score or create new one
        existing_score = user_node.score.single()
        
        if existing_score:
            # Update existing score
            existing_score.overall_score = score_value
            existing_score.save()
            print(f"Updated existing score with overall_score: {score_value}")
        else:
            # Create new score if none exists
            score_node = Score(
                overall_score=score_value,
                vibersCount=0,
                cumulativeVibescore=0,
                intelligenceScore=0,
                appealScore=0,
                socialScore=0,
                humanScore=0,
                repoScore=0,
                created_at=int(time.time())
            )
            score_node.save()
            user_node.score.connect(score_node)
            print(f"Created new score with overall_score: {score_value}")
        
    except Exception as e:
        print(f"Error in _update_score_sync: {e}")
        raise e