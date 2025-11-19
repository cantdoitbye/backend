import asyncio
import aiohttp
from django.conf import settings
from asgiref.sync import sync_to_async
from msg.models import MatrixProfile
from auth_manager.models import Users
from auth_manager.Utils import generate_presigned_url
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


async def generate_avatar_url_async(image_id):
    """
    Generate presigned avatar URL asynchronously (same approach as matrix_avatar_manager.py).
    
    Args:
        image_id: Profile image ID from database
    
    Returns:
        str: Avatar URL or empty string if failed
    """
    if not image_id:
        return ''
    
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            file_info = await loop.run_in_executor(
                executor,
                generate_presigned_url.generate_file_info,
                image_id
            )
        
        if file_info and file_info.get('url'):
            logger.info(f"Generated avatar URL for image_id: {image_id}")
            return file_info['url']
        else:
            logger.warning(f"No URL in file_info for image_id: {image_id}")
            return ''
    except Exception as e:
        logger.warning(f"Could not generate avatar URL for image_id {image_id}: {e}")
        return ''


async def update_dm_room_by_room_id(room_id, current_user_id, access_token, current_user_matrix_id):
    """
    Update DM room data by room_id.
    
    Args:
        room_id (str): Matrix room ID (e.g., "!abc123:chat.ooumph.com")
        current_user_id (int): Django user ID of current user
        access_token (str): Matrix access token
        current_user_matrix_id (str): Matrix ID of current user
    
    Returns:
        dict: {
            'success': bool,
            'message': str (if success),
            'error': str (if failed),
            'user1_name': str,
            'user2_name': str,
            'relation': str,
            'has_user1_avatar': bool,
            'has_user2_avatar': bool
        }
    
    Flow:
        1. Get room members from Matrix API
        2. Find the other user's Matrix ID
        3. Get both users' data from database (including avatars)
        4. Find connection relation between users
        5. Update Matrix room state event with both users' data
    """
    try:
        # Step 1: Get room members
        room_members = await get_room_members(room_id, access_token)
        
        if not room_members or len(room_members) == 0:
            return {
                'success': False,
                'error': f'Room has no members. Cannot update DM room data.'
            }
        
        # Step 2: Get current user's data from database
        current_user_data = await get_user_data_from_matrix_id(current_user_matrix_id)
        
        if not current_user_data:
            return {
                'success': False,
                'error': 'Could not find your user data in database'
            }
        
        # Step 3: Generate avatar URLs asynchronously (same approach as matrix_avatar_manager.py)
        current_user_profile_image_id = current_user_data.get('profile_image_id')
        logger.info(f"Current user profile_image_id: {current_user_profile_image_id}")
        
        current_user_avatar_url = await generate_avatar_url_async(current_user_profile_image_id)
        current_user_data['avatar_url'] = current_user_avatar_url
        
        logger.info(f"Current user avatar_url generated: {current_user_avatar_url[:50] if current_user_avatar_url else 'None'}...")
        logger.info(f"Current user has avatar: {bool(current_user_avatar_url)}")
        
        # Step 4: Handle different cases based on member count
        if len(room_members) == 1:
            # Self-DM room (only 1 member) - store just current user's profile
            logger.info(f"Room {room_id} has 1 member - treating as self-DM for profile storage")
            
            update_result = await update_room_state_event_single_user(
                access_token=access_token,
                room_id=room_id,
                user_matrix_id=current_user_matrix_id,
                user_data=current_user_data
            )
            
            if update_result['success']:
                return {
                    'success': True,
                    'message': 'DM room data updated successfully (self-DM)',
                    'user1_name': current_user_data.get('name'),
                    'user2_name': None,
                    'relation': None,
                    'has_user1_avatar': bool(current_user_data.get('avatar_url')),
                    'has_user2_avatar': False
                }
            else:
                return update_result
        
        else:
            # Regular DM room (2+ members) - store both users' profiles
            # Step 4: Find the other user
            other_user_matrix_id = None
            for member_id in room_members:
                if member_id != current_user_matrix_id:
                    other_user_matrix_id = member_id
                    break
            
            if not other_user_matrix_id:
                return {
                    'success': False,
                    'error': 'Could not find the other user in this room'
                }
            
            # Step 5: Get other user's data from database
            other_user_data = await get_user_data_from_matrix_id(other_user_matrix_id)
            
            if not other_user_data:
                return {
                    'success': False,
                    'error': 'Could not find other user data in database'
                }
            
            # Step 6: Generate avatar URL for other user asynchronously
            other_user_profile_image_id = other_user_data.get('profile_image_id')
            logger.info(f"Other user profile_image_id: {other_user_profile_image_id}")
            
            other_user_avatar_url = await generate_avatar_url_async(other_user_profile_image_id)
            other_user_data['avatar_url'] = other_user_avatar_url
            
            logger.info(f"Other user avatar_url generated: {other_user_avatar_url[:50] if other_user_avatar_url else 'None'}...")
            logger.info(f"Other user has avatar: {bool(other_user_avatar_url)}")
            
            relation = await get_connection_relation(
                current_user_data['user_node'],
                other_user_data['user_node']
            )
            
            update_result = await update_room_state_event(
                access_token=access_token,
                room_id=room_id,
                user1_matrix_id=current_user_matrix_id,
                user1_data=current_user_data,
                user2_matrix_id=other_user_matrix_id,
                user2_data=other_user_data,
                relation=relation
            )
            
            if update_result['success']:
                return {
                    'success': True,
                    'message': 'DM room data updated successfully',
                    'user1_name': current_user_data.get('name'),
                    'user2_name': other_user_data.get('name'),
                    'relation': relation,
                    'has_user1_avatar': bool(current_user_data.get('avatar_url')),
                    'has_user2_avatar': bool(other_user_data.get('avatar_url'))
                }
            else:
                return update_result
            
    except Exception as e:
        logger.error(f"Error in update_dm_room_by_room_id: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


async def get_room_members(room_id, access_token):
    """
    Get list of member Matrix IDs in a room.
    
    Returns: 
        List of Matrix user IDs (e.g., ['@user1:chat.ooumph.com', '@user2:chat.ooumph.com'])
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        members_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/joined_members"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(members_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    members = list(data.get('joined', {}).keys())
                    logger.info(f"Found {len(members)} members in room {room_id}")
                    return members
                else:
                    logger.error(f"Failed to get room members: HTTP {response.status}")
                    return []
                    
    except Exception as e:
        logger.error(f"Error getting room members: {e}")
        return []


@sync_to_async
def get_user_data_from_matrix_id(matrix_user_id):
    """
    Get user data from database using Matrix ID.
    
    Returns:
        dict: {
            'user_node': Users node object,
            'uid': user uid,
            'name': full name or email,
            'email': email,
            'avatar_url': avatar URL or empty string
        }
    """
    try:
        matrix_profile = MatrixProfile.objects.filter(
            matrix_user_id=matrix_user_id
        ).first()
        
        if not matrix_profile:
            logger.warning(f"No MatrixProfile found for {matrix_user_id}")
            return None
        
        user_node = Users.nodes.get(user_id=matrix_profile.user.id)
        
        # Get profile_image_id from Profile node (not Users node)
        # The profile_pic_id is stored in the Profile relationship
        profile_image_id = None
        try:
            profile_node = user_node.profile.single()
            if profile_node:
                profile_image_id = getattr(profile_node, 'profile_pic_id', None)
                logger.info(f"Retrieved profile_pic_id from Profile node for {matrix_user_id}: {profile_image_id}")
            else:
                logger.warning(f"No Profile node found for user {matrix_user_id}")
        except Exception as e:
            logger.warning(f"Error accessing Profile node for {matrix_user_id}: {e}")
        
        # Fallback: Try direct attribute on Users node (in case it's stored there)
        if not profile_image_id:
            profile_image_id = (
                getattr(user_node, 'profile_image_id', None) or
                getattr(user_node, 'profileImageId', None) or
                getattr(user_node, 'profile_picture_id', None) or
                getattr(user_node, 'profilePictureId', None) or
                getattr(user_node, 'avatar_id', None) or
                getattr(user_node, 'avatarId', None)
            )
            if profile_image_id:
                logger.info(f"Retrieved profile_image_id from Users node for {matrix_user_id}: {profile_image_id}")
        
        logger.info(f"Final profile_image_id for {matrix_user_id}: {profile_image_id}")
        
        user_data = {
            'user_node': user_node,
            'uid': user_node.uid,
            'name': getattr(user_node, 'full_name', '') or getattr(user_node, 'username', '') or user_node.email,
            'email': user_node.email,
            'avatar_url': '',
            'overall_score': '4.0',
            'profile_image_id': profile_image_id  # Store image_id for async processing
        }
        
        return user_data
        
    except Exception as e:
        logger.error(f"Error getting user data for {matrix_user_id}: {e}")
        return None


@sync_to_async
def get_connection_relation(user1_node, user2_node):
    """
    Find connection between two users and return the relation.
    
    Returns: 
        str: Relation name (e.g., "Friend", "Professional") or "Connection" as default
    """
    try:
        # Check connections from user1 to user2
        connections = user1_node.connection.filter(connection_status='Accepted')
        
        for connection in connections:
            receiver = connection.receiver.single()
            created_by = connection.created_by.single()
            
            # Check if this connection involves user2
            if (receiver and receiver.uid == user2_node.uid) or \
               (created_by and created_by.uid == user2_node.uid):
                
                # Get relation from circle
                circle = connection.circle.single()
                if circle and circle.relation:
                    return circle.relation
        
        return "Connection"
        
    except Exception as e:
        logger.warning(f"Error finding connection relation: {e}")
        return "Connection"


async def set_standard_room_avatar(session, headers, room_id, avatar_url, timeout):
    """
    Also set the standard Matrix room avatar state for client compatibility.
    Same approach as in matrix_avatar_manager.py
    """
    try:
        avatar_state_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/m.room.avatar"
        avatar_data = {"url": avatar_url}
        
        async with session.put(avatar_state_url, json=avatar_data, headers=headers, timeout=timeout) as response:
            if response.status == 200:
                logger.info(f"✓ Standard room avatar also set for {room_id}")
            else:
                logger.warning(f"Failed to set standard room avatar: HTTP {response.status}")
    except Exception as e:
        logger.warning(f"Error setting standard room avatar: {e}")


async def update_room_state_event_single_user(access_token, room_id, user_matrix_id, user_data):
    """
    Update the Matrix room state event with a single user's profile data.
    Used for self-DM rooms where only one user's profile needs to be stored.
    
    State event type: com.ooumph.user.profile (for consistency with user profile storage)
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Store user profile data in room state (similar to community room data)
        user_node = user_data.get('user_node')
        avatar_url = user_data.get('avatar_url', '')
        
        profile_data = {
            "user_id": str(user_node.user_id) if user_node else '',
            "user_uid": user_data['uid'],
            "overall_score": user_data.get('overall_score', '4.0'),
            "room_type": "dm",
            "updated_at": str(int(asyncio.get_event_loop().time())),
            "avatar_url": avatar_url,
            "name": user_data.get('name', ''),
            "email": user_data.get('email', '')
        }
        
        # Set room state event using user profile event type
        # Using user_uid as state_key to make it unique
        profile_data_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.user.profile/{user_data['uid']}"
        
        async with aiohttp.ClientSession() as session:
            async with session.put(profile_data_url, json=profile_data, headers=headers, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"✓ Updated single user profile in DM room {room_id}")
                    
                    # Also set the standard Matrix room avatar if avatar is provided
                    if avatar_url:
                        await set_standard_room_avatar(
                            session, headers, room_id, avatar_url, 10
                        )
                    
                    return {'success': True}
                else:
                    response_text = await response.text()
                    logger.error(f"Failed to update single user room state: HTTP {response.status} - {response_text}")
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}: {response_text}"
                    }
                    
    except Exception as e:
        logger.error(f"Error updating single user room state event: {e}")
        return {'success': False, 'error': str(e)}


async def update_room_state_event(access_token, room_id, user1_matrix_id, user1_data,
                                  user2_matrix_id, user2_data, relation):
    """
    Update the Matrix room state event with both users' complete data.
    This makes the data accessible to both users in frontend via Matrix events.
    
    State event type: com.ooumph.dm.data
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        dm_data = {
            "relation": relation,
            "room_type": "dm",
            "updated_at": str(int(asyncio.get_event_loop().time())),
            "users": {
                user1_matrix_id: {
                    "user_id": str(user1_data['user_node'].user_id) if user1_data.get('user_node') else '',
                    "matrix_id": user1_matrix_id,
                    "uid": user1_data['uid'],
                    "name": user1_data['name'],
                    "email": user1_data['email'],
                    "avatar_url": user1_data.get('avatar_url', ''),
                    "overall_score": user1_data.get('overall_score', '4.0')
                },
                user2_matrix_id: {
                    "user_id": str(user2_data['user_node'].user_id) if user2_data.get('user_node') else '',
                    "matrix_id": user2_matrix_id,
                    "uid": user2_data['uid'],
                    "name": user2_data['name'],
                    "email": user2_data['email'],
                    "avatar_url": user2_data.get('avatar_url', ''),
                    "overall_score": user2_data.get('overall_score', '4.0')
                }
            }
        }
        
        # Set room state event
        dm_data_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.dm.data"
        
        async with aiohttp.ClientSession() as session:
            async with session.put(dm_data_url, json=dm_data, headers=headers, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"✓ Updated DM room data for {room_id}")
                    
                    # Also set the standard Matrix room avatar using the other user's avatar
                    # (the person you're chatting with, not yourself)
                    other_user_avatar = user2_data.get('avatar_url', '')
                    if other_user_avatar:
                        await set_standard_room_avatar(
                            session, headers, room_id, other_user_avatar, 10
                        )
                    
                    return {'success': True}
                else:
                    response_text = await response.text()
                    logger.error(f"Failed to update room state: HTTP {response.status} - {response_text}")
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}: {response_text}"
                    }
                    
    except Exception as e:
        logger.error(f"Error updating room state event: {e}")
        return {'success': False, 'error': str(e)}