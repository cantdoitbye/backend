import asyncio
import aiohttp
from django.conf import settings
from auth_manager.Utils.generate_presigned_url import generate_file_info
import logging
from auth_manager.Utils import generate_presigned_url
from concurrent.futures import ThreadPoolExecutor
import json

matrix_logger = logging.getLogger("matrix_logger")

# auth_manager/Utils/matrix_avatar_manager.py

async def set_user_avatar_and_score(
    access_token: str,
    user_id: str,
    database_user_id: str,
    user_uid: str,
    image_id: str = None,
    score: float = 4.0,
    additional_data: dict = None,
    timeout: int = 30
) -> dict:
    """
    Set user avatar and score in Matrix profile (for create/update profile).
    """
    print(f"DEBUG: Setting user avatar and score for user {user_id}")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare profile data
        profile_data = {
            "user_id": database_user_id,
            "user_uid": user_uid,
            "overall_score": score,
            "updated_at": int(asyncio.get_event_loop().time())
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
                profile_data["avatar_url"] = file_info['url']
                print(f"DEBUG: Avatar URL added: {file_info['url']}")
        
        # Add any additional profile data
        if additional_data:
            profile_data.update(additional_data)
        
        # Set avatar and score data
        profile_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/v3/user/{user_id}/account_data/com.ooumph.user.profile"
        
        print(f"DEBUG: Setting avatar and score data: {profile_data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(profile_url, json=profile_data, headers=headers, timeout=timeout) as response:
                response_text = await response.text()
                print(f"DEBUG: Avatar/Score HTTP Response status: {response.status}")
                print(f"DEBUG: Avatar/Score HTTP Response text: {response_text}")
                
                if response.status == 200:
                    # Save score locally
                    await save_user_score_local(user_id, score)
                    
                    matrix_logger.info(f"Set user avatar and score for {user_id}")
                    return {
                        "success": True,
                        "avatar_url": profile_data.get("avatar_url"),
                        "score_set": True,
                        "score_value": score
                    }
                else:
                    return {"success": False, "error": f"Avatar/Score update failed: HTTP {response.status}: {response_text}"}
        
    except Exception as e:
        print(f"DEBUG: Exception in set_user_avatar_and_score: {e}")
        matrix_logger.error(f"Error setting user avatar and score: {e}")
        return {"success": False, "error": str(e)}


async def set_user_relations_data(
    access_token: str,
    user_id: str,
    user_relations: list,
    timeout: int = 30
) -> dict:
    """
    Set user relations data in Matrix (called when connections are made/updated).
    This updates existing profile data and adds relations.
    """
    print(f"DEBUG: Setting user relations for user {user_id}")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        profile_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/user/{user_id}/account_data/com.ooumph.user.profile"
        
        # First, get existing profile data
        existing_data = {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(profile_url, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        existing_data = await response.json()
                        print(f"DEBUG: Retrieved existing profile data")
            except:
                print(f"DEBUG: No existing profile data found, creating new")
        
        # Update relations in existing data
        existing_data["relations"] = user_relations
        existing_data["relation_count"] = len(user_relations)
        existing_data["relations_updated_at"] = int(asyncio.get_event_loop().time())
        
        print(f"DEBUG: Updating relations data: {user_relations}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(profile_url, json=existing_data, headers=headers, timeout=timeout) as response:
                response_text = await response.text()
                print(f"DEBUG: Relations HTTP Response status: {response.status}")
                print(f"DEBUG: Relations HTTP Response text: {response_text}")
                
                if response.status == 200:
                    matrix_logger.info(f"Set user relations for {user_id}: {user_relations}")
                    return {
                        "success": True,
                        "relations_count": len(user_relations),
                        "relations": user_relations
                    }
                else:
                    return {"success": False, "error": f"Relations update failed: HTTP {response.status}: {response_text}"}
        
    except Exception as e:
        print(f"DEBUG: Exception in set_user_relations_data: {e}")
        matrix_logger.error(f"Error setting user relations: {e}")
        return {"success": False, "error": str(e)}


# Helper function to get user relations from connections (only main relations)
def get_user_relations(user_node):
    """
    Get list of main relations from user's connections (not sub_relations).
    """
    try:
        relations = []
        connections = user_node.connection.all()
        
        for connection in connections:
            circle = connection.circle.single()
            if circle and circle.relation:  # Only main relation
                relations.append(circle.relation)
        
        # Return unique relations
        return list(set(relations))
        
    except Exception as e:
        print(f"Error getting user relations: {e}")
        return []


# Keep your existing save_user_score_local function as is
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
    # Your existing implementation
    pass