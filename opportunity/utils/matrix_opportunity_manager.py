# opportunity/utils/matrix_opportunity_manager.py

"""
Matrix Opportunity Data Manager

This module manages opportunity data in Matrix room state events.
It sets the custom state event 'com.ooumph.opportunity.data' which contains all
opportunity information accessible to the frontend for filtering and display.

Pattern: Based on community/utils/matrix_avatar_manager.py
"""

import asyncio
import aiohttp
import logging
from django.conf import settings
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from auth_manager.Utils.generate_presigned_url import generate_file_info

opportunity_logger = logging.getLogger("opportunity_logger")


async def set_opportunity_room_data(
    access_token: str,
    user_id: str,
    room_id: str,
    opportunity_data: Any,  # Opportunity neomodel instance
    creator: Any,  # Users neomodel instance
    timeout: int = 30
) -> dict:
    """
    Set complete opportunity data in Matrix room state event.
    
    This function stores ALL opportunity information in the Matrix room as a custom
    state event (com.ooumph.opportunity.data). The frontend can read this event to:
    - Display opportunity details
    - Filter by type (job/event/cause)
    - Show in opportunity list
    - Enable applications
    
    Args:
        access_token: Creator's Matrix access token
        user_id: Creator's Matrix user ID
        room_id: Matrix room ID where opportunity data will be stored
        opportunity_data: Opportunity neomodel instance with all fields
        creator: Users neomodel instance (opportunity creator)
        timeout: Request timeout in seconds
        
    Returns:
        dict: {
            'success': bool,
            'avatar_url': str (if set),
            'room_id': str,
            'error': str (if failed)
        }
        
    Example:
        >>> from opportunity.models import Opportunity
        >>> from auth_manager.models import Users
        >>> 
        >>> opportunity = Opportunity.nodes.get(uid='opp_123')
        >>> creator = Users.nodes.get(uid='user_456')
        >>> 
        >>> result = await set_opportunity_room_data(
        ...     access_token="syt_...",
        ...     user_id="@user:chat.ooumph.com",
        ...     room_id="!room123:chat.ooumph.com",
        ...     opportunity_data=opportunity,
        ...     creator=creator
        ... )
        >>> print(result)  # {'success': True, 'room_id': '!room123:...'}
    """
    
    print(f"DEBUG: Setting opportunity room data for room {room_id}")
    opportunity_logger.info(f"Setting opportunity data for room {room_id}")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # ========== PREPARE OPPORTUNITY DATA ==========
        room_data = {
            # Core identifiers
            "opportunity_uid": opportunity_data.uid,
            "opportunity_type": opportunity_data.opportunity_type,  # job/event/cause/etc
            "room_type": "opportunity",  # For frontend filtering
            
            # Basic information
            "role": opportunity_data.role,
            "job_type": opportunity_data.job_type,
            "location": opportunity_data.location,
            "is_remote": opportunity_data.is_remote,
            "is_hybrid": opportunity_data.is_hybrid,
            
            # Experience & Compensation
            "experience_level": opportunity_data.experience_level or "",
            "salary_range_text": opportunity_data.salary_range_text or "",
            "salary_min": opportunity_data.salary_min or 0,
            "salary_max": opportunity_data.salary_max or 0,
            "salary_currency": opportunity_data.salary_currency or "INR",
            
            # Content (truncated for state event)
            "description": opportunity_data.description[:500] if opportunity_data.description else "",  # First 500 chars
            "key_responsibilities": opportunity_data.key_responsibilities or [],
            "requirements": opportunity_data.requirements or [],
            "good_to_have_skills": opportunity_data.good_to_have_skills or [],
            "skills": opportunity_data.skills or [],
            
            # Creator information
            "creator_uid": creator.uid,
            "creator_name": creator.username or creator.name or "Unknown",
            "creator_email": creator.email or "",
            
            # Status & Metadata
            "is_active": opportunity_data.is_active,
            "is_deleted": opportunity_data.is_deleted,
            "expires_at": str(opportunity_data.expires_at) if opportunity_data.expires_at else None,
            "created_at": str(opportunity_data.created_at) if opportunity_data.created_at else "",
            "updated_at": str(opportunity_data.updated_at) if opportunity_data.updated_at else "",
            
            # CTA
            "cta_text": opportunity_data.cta_text or "Apply Now",
            "cta_type": opportunity_data.cta_type or "apply",
            
            # Filtering & Discovery
            "tags": opportunity_data.tags or [],
            "privacy": opportunity_data.privacy or "public",
            
            # Document IDs (frontend will fetch presigned URLs separately)
            "document_ids": opportunity_data.document_ids or [],
            
            # Overall score (for ranking/sorting)
            "overall_score": "4.0",  # Default score, can be calculated from engagement
            
            # Timestamp
            "updated_at_timestamp": str(int(asyncio.get_event_loop().time()))
        }
        
        # ========== ADD COVER IMAGE AVATAR ==========
        if opportunity_data.cover_image_id:
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    file_info = await loop.run_in_executor(
                        executor,
                        generate_file_info,
                        opportunity_data.cover_image_id
                    )
                
                if file_info and file_info.get('url'):
                    room_data["avatar_url"] = file_info['url']
                    room_data["cover_image_id"] = opportunity_data.cover_image_id
                    print(f"DEBUG: Cover image URL added: {file_info['url']}")
            except Exception as e:
                print(f"DEBUG: Error getting cover image URL: {e}")
                opportunity_logger.warning(f"Could not get cover image for opportunity: {e}")
        
        # ========== ADD CREATOR AVATAR ==========
        if hasattr(creator, 'profile_picture') and creator.profile_picture:
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    creator_file_info = await loop.run_in_executor(
                        executor,
                        generate_file_info,
                        creator.profile_picture
                    )
                
                if creator_file_info and creator_file_info.get('url'):
                    room_data["creator_avatar_url"] = creator_file_info['url']
                    print(f"DEBUG: Creator avatar URL added: {creator_file_info['url']}")
            except Exception as e:
                print(f"DEBUG: Error getting creator avatar: {e}")
        
        # ========== SET CUSTOM STATE EVENT ==========
        # Use custom event type: com.ooumph.opportunity.data
        # This is similar to com.ooumph.room.data for communities
        room_state_url = (
            f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}"
            f"/state/com.ooumph.opportunity.data"
        )
        
        print(f"DEBUG: Setting opportunity data in Matrix: {room_data['opportunity_type']} - {room_data['role']}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                room_state_url, 
                json=room_data, 
                headers=headers, 
                timeout=timeout
            ) as response:
                response_text = await response.text()
                print(f"DEBUG: Opportunity Data HTTP Response status: {response.status}")
                print(f"DEBUG: Opportunity Data HTTP Response text: {response_text}")
                
                if response.status == 200:
                    # ========== SET STANDARD MATRIX ROOM AVATAR ==========
                    # Also set the standard m.room.avatar for client compatibility
                    if room_data.get("avatar_url"):
                        await set_standard_room_avatar(
                            session, headers, room_id, room_data["avatar_url"], timeout
                        )
                    
                    opportunity_logger.info(
                        f"✓ Successfully set opportunity data for room {room_id}"
                    )
                    return {
                        "success": True,
                        "avatar_url": room_data.get("avatar_url"),
                        "room_id": room_id
                    }
                else:
                    error_msg = f"Failed to set opportunity data: HTTP {response.status}: {response_text}"
                    opportunity_logger.error(error_msg)
                    return {"success": False, "error": error_msg}
        
    except Exception as e:
        error_msg = f"Exception setting opportunity room data: {e}"
        print(f"DEBUG: {error_msg}")
        opportunity_logger.error(error_msg)
        return {"success": False, "error": str(e)}


async def set_standard_room_avatar(
    session: aiohttp.ClientSession,
    headers: dict,
    room_id: str,
    avatar_url: str,
    timeout: int
) -> bool:
    """
    Set the standard Matrix room avatar (m.room.avatar state event).
    
    This ensures compatibility with Matrix clients that read the standard avatar state.
    
    Args:
        session: Active aiohttp session
        headers: HTTP headers with authorization
        room_id: Matrix room ID
        avatar_url: URL of the avatar image
        timeout: Request timeout
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        avatar_state_url = (
            f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}"
            f"/state/m.room.avatar"
        )
        
        avatar_data = {"url": avatar_url}
        
        async with session.put(
            avatar_state_url,
            json=avatar_data,
            headers=headers,
            timeout=timeout
        ) as response:
            if response.status == 200:
                print(f"DEBUG: ✓ Set standard room avatar for {room_id}")
                return True
            else:
                print(f"DEBUG: ✗ Failed to set standard avatar: {response.status}")
                return False
                
    except Exception as e:
        print(f"DEBUG: Error setting standard room avatar: {e}")
        return False


async def update_opportunity_room_avatar(
    access_token: str,
    user_id: str,
    room_id: str,
    cover_image_id: str,
    timeout: int = 30
) -> dict:
    """
    Update only the avatar/cover image of an opportunity room.
    
    Use this when the opportunity's cover image changes without updating all other data.
    
    Args:
        access_token: Creator's Matrix access token
        user_id: Creator's Matrix user ID
        room_id: Matrix room ID
        cover_image_id: New cover image ID from minio
        timeout: Request timeout
        
    Returns:
        dict: Success status and avatar URL
        
    Example:
        >>> result = await update_opportunity_room_avatar(
        ...     access_token="syt_...",
        ...     user_id="@user:chat.ooumph.com",
        ...     room_id="!room123:chat.ooumph.com",
        ...     cover_image_id="img_new_cover_123"
        ... )
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get presigned URL for new cover image
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            file_info = await loop.run_in_executor(
                executor,
                generate_file_info,
                cover_image_id
            )
        
        if not file_info or not file_info.get('url'):
            return {"success": False, "error": "Could not generate presigned URL"}
        
        avatar_url = file_info['url']
        
        # Update the avatar in the custom state event
        # We need to read existing data first, then update just the avatar fields
        room_state_url = (
            f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}"
            f"/state/com.ooumph.opportunity.data"
        )
        
        async with aiohttp.ClientSession() as session:
            # Read existing state
            async with session.get(
                room_state_url,
                headers=headers,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    existing_data = await response.json()
                    existing_data["avatar_url"] = avatar_url
                    existing_data["cover_image_id"] = cover_image_id
                    existing_data["updated_at_timestamp"] = str(int(asyncio.get_event_loop().time()))
                    
                    # Write updated state
                    async with session.put(
                        room_state_url,
                        json=existing_data,
                        headers=headers,
                        timeout=timeout
                    ) as put_response:
                        if put_response.status == 200:
                            # Also update standard avatar
                            await set_standard_room_avatar(
                                session, headers, room_id, avatar_url, timeout
                            )
                            return {
                                "success": True,
                                "avatar_url": avatar_url
                            }
                
        return {"success": False, "error": "Failed to update avatar"}
        
    except Exception as e:
        opportunity_logger.error(f"Error updating opportunity room avatar: {e}")
        return {"success": False, "error": str(e)}


async def delete_opportunity_room_data(
    access_token: str,
    user_id: str,
    room_id: str,
    timeout: int = 30
) -> dict:
    """
    Mark opportunity as deleted in Matrix room state.
    
    This doesn't delete the room, but marks the opportunity as deleted in the state event.
    
    Args:
        access_token: Creator's Matrix access token
        user_id: Creator's Matrix user ID
        room_id: Matrix room ID
        timeout: Request timeout
        
    Returns:
        dict: Success status
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        room_state_url = (
            f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}"
            f"/state/com.ooumph.opportunity.data"
        )
        
        async with aiohttp.ClientSession() as session:
            # Read existing state
            async with session.get(
                room_state_url,
                headers=headers,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    existing_data = await response.json()
                    existing_data["is_deleted"] = True
                    existing_data["is_active"] = False
                    existing_data["updated_at_timestamp"] = str(int(asyncio.get_event_loop().time()))
                    
                    # Write updated state
                    async with session.put(
                        room_state_url,
                        json=existing_data,
                        headers=headers,
                        timeout=timeout
                    ) as put_response:
                        if put_response.status == 200:
                            opportunity_logger.info(
                                f"✓ Marked opportunity as deleted in room {room_id}"
                            )
                            return {"success": True}
                
        return {"success": False, "error": "Failed to mark as deleted"}
        
    except Exception as e:
        opportunity_logger.error(f"Error deleting opportunity room data: {e}")
        return {"success": False, "error": str(e)}
