import asyncio
import logging
import threading
from nio import AsyncClient, RoomInviteResponse
from msg.models import MatrixProfile
from auth_manager.models import Users
from django.conf import settings
from asgiref.sync import sync_to_async

matrix_logger = logging.getLogger("matrix_logger")

async def invite_user_to_room(admin_access_token, admin_user_id, room_id, user_id, timeout=10):
    """
    Invite a user to a Matrix room.
    
    Args:
        admin_access_token (str): The access token of the room admin
        admin_user_id (str): The Matrix user ID of the room admin
        room_id (str): The ID of the room to invite to
        user_id (str): The Matrix user ID of the user to invite
        timeout (int, optional): Timeout for the invite API call
        
    Returns:
        bool: True if invitation was successful, False otherwise
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = admin_access_token
    client.user_id = admin_user_id
    
    try:
        matrix_logger.info(f"Inviting user {user_id} to room {room_id}")
        response = await asyncio.wait_for(
            client.room_invite(room_id, user_id),
            timeout=timeout
        )
        
        if isinstance(response, RoomInviteResponse):
            matrix_logger.info(f"Successfully invited {user_id} to room {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to invite {user_id} to room {room_id}: {response}")
            return False
    except Exception as e:
        matrix_logger.error(f"Error inviting {user_id} to room {room_id}: {e}")
        return False
    finally:
        await client.close()

async def auto_join_room(user_access_token, user_matrix_id, room_id, timeout=10):
    """
    Auto-join a Matrix room on behalf of a user.
    
    Args:
        user_access_token (str): The access token of the user
        user_matrix_id (str): The Matrix user ID of the user
        room_id (str): The ID of the room to join
        timeout (int, optional): Timeout for the join API call
        
    Returns:
        bool: True if join was successful, False otherwise
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = user_access_token
    client.user_id = user_matrix_id
    
    try:
        matrix_logger.info(f"Auto-joining user {user_matrix_id} to room {room_id}")
        response = await asyncio.wait_for(
            client.join(room_id),
            timeout=timeout
        )
        
        if hasattr(response, "room_id"):
            matrix_logger.info(f"Successfully joined {user_matrix_id} to room {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to join {user_matrix_id} to room {room_id}: {response}")
            return False
    except Exception as e:
        matrix_logger.error(f"Error joining {user_matrix_id} to room {room_id}: {e}")
        return False
    finally:
        await client.close()

def process_matrix_invites(admin_user_id, room_id, member_ids):
    """
    Process Matrix room invitations in a separate thread.
    This function should be called from synchronous code.
    
    Args:
        admin_user_id (str): The user ID of the community creator/admin
        room_id (str): The ID of the Matrix room
        member_ids (list): List of user IDs to invite to the room
    """
    def _run_async_invites():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(_invite_and_join_members(admin_user_id, room_id, member_ids))
            matrix_logger.info(
                f"Matrix room invitation results: "
                f"Total={results['total']}, "
                f"Invited={results['invite_success_count']}, "
                f"Joined={results['join_success_count']}, "
                f"Failed={len(results['failed'])}"
            )
            
            if results['failed']:
                matrix_logger.warning(f"Failed Matrix invites: {results['failed']}")
        except Exception as e:
            matrix_logger.error(f"Error processing Matrix invites: {e}")
        finally:
            loop.close()
    
    # Start processing in a separate thread to not block the main request
    thread = threading.Thread(target=_run_async_invites)
    thread.daemon = True
    thread.start()
    
    return {
        "status": "processing_started",
        "message": f"Started processing {len(member_ids)} Matrix invites in background"
    }

# Helper function to get Django user_id from Neo4j user_uid
async def get_django_user_id(neo4j_user_uid):
    """Get the Django user ID from a Neo4j user UID"""
    get_neo4j_user = sync_to_async(Users.nodes.get)
    try:
        user_node = await get_neo4j_user(uid=neo4j_user_uid)
        return user_node.user_id  # This is the Django user ID
    except Exception as e:
        matrix_logger.error(f"Error getting Django user ID for Neo4j user {neo4j_user_uid}: {e}")
        return None

async def _invite_and_join_members(admin_user_id, room_id, member_ids):
    """
    Internal async function to invite members to a Matrix room and auto-join them.
    
    Args:
        admin_user_id (str): The user ID of the community creator/admin
        room_id (str): The ID of the Matrix room
        member_ids (list): List of user IDs to invite to the room
        
    Returns:
        dict: Summary of invite and join operations
    """
    results = {
        "success": [],
        "failed": [],
        "total": len(member_ids),
        "invite_success_count": 0,
        "join_success_count": 0
    }
    
    try:
        # Get admin Matrix credentials using Django user_id (numeric)
        # No need to convert admin_user_id since it's already the numeric ID
        get_matrix_profile = sync_to_async(MatrixProfile.objects.get)
        try:
            admin_matrix = await get_matrix_profile(user=admin_user_id)
            admin_matrix_id = admin_matrix.matrix_user_id
            admin_access_token = admin_matrix.access_token
            
            if not admin_matrix_id or not admin_access_token:
                matrix_logger.error(f"Admin user {admin_user_id} doesn't have valid Matrix credentials")
                return results
        except Exception as e:
            matrix_logger.error(f"Error getting admin Matrix profile: {e}")
            return results
        
        # Process each member
        for member_uid in member_ids:
            try:
                # Convert Neo4j UID to Django user ID
                django_user_id = await get_django_user_id(member_uid)
                if not django_user_id:
                    results["failed"].append({
                        "user_id": member_uid,
                        "reason": "Could not find Django user ID"
                    })
                    continue
                
                # Get member Matrix credentials using Django user_id
                try:
                    member_matrix = await get_matrix_profile(user=django_user_id)
                    member_matrix_id = member_matrix.matrix_user_id
                    member_access_token = member_matrix.access_token
                    
                    if not member_matrix_id or not member_access_token:
                        matrix_logger.warning(f"Member {member_uid} doesn't have valid Matrix credentials")
                        results["failed"].append({
                            "user_id": member_uid,
                            "reason": "No valid Matrix credentials"
                        })
                        continue
                except Exception as e:
                    matrix_logger.warning(f"No Matrix profile found for user {member_uid}: {e}")
                    results["failed"].append({
                        "user_id": member_uid,
                        "reason": f"No Matrix profile found: {str(e)}"
                    })
                    continue
                
                # Invite member to room
                invite_success = await invite_user_to_room(
                    admin_access_token, 
                    admin_matrix_id,
                    room_id, 
                    member_matrix_id
                )
                
                if invite_success:
                    results["invite_success_count"] += 1
                    
                    # Auto-join the room for the member
                    join_success = await auto_join_room(
                        member_access_token,
                        member_matrix_id,
                        room_id
                    )
                    
                    if join_success:
                        results["join_success_count"] += 1
                        results["success"].append(member_uid)
                    else:
                        results["failed"].append({
                            "user_id": member_uid,
                            "reason": "Invited but failed to auto-join"
                        })
                else:
                    results["failed"].append({
                        "user_id": member_uid,
                        "reason": "Failed to invite"
                    })
            except Exception as e:
                matrix_logger.error(f"Error processing member {member_uid}: {e}")
                results["failed"].append({
                    "user_id": member_uid,
                    "reason": str(e)
                })
                
    except Exception as e:
        matrix_logger.error(f"Error in _invite_and_join_members: {e}")
    
    return results 