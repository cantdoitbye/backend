# Agent Matrix Integration Utilities
# This module provides utilities for creating and managing Matrix profiles for AI agents.
# It handles agent registration, login, and profile management on the Matrix server.

import asyncio
import logging
import time
from typing import Optional, Tuple
from nio import AsyncClient, LoginResponse, RegisterResponse
from django.conf import settings

# Configure logging for Matrix operations
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

matrix_logger = logging.getLogger("agent_matrix_logger")

# Matrix operation error types
class MatrixRegistrationError(Exception):
    """Raised when agent Matrix registration fails"""
    pass

class MatrixLoginError(Exception):
    """Raised when agent Matrix login fails"""
    pass

class MatrixProfileUpdateError(Exception):
    """Raised when agent Matrix profile update fails"""
    pass


async def register_agent_on_matrix(agent_name: str, agent_uid: str, max_retries: int = 1, timeout: int = 2) -> Optional[Tuple[str, str]]:
    """
    Registers an AI agent on the Matrix server with retry and timeout logic.
    
    Args:
        agent_name (str): The display name for the agent.
        agent_uid (str): The unique identifier for the agent (used as username).
        max_retries (int): Maximum number of retries in case of failure.
        timeout (int): Timeout duration (in seconds) for each registration attempt.

    Returns:
        tuple: (access_token, user_id) if successful, None otherwise.
    """
    # Create a unique username for the agent using the agent_uid
    username = f"agent_{agent_uid}"
    # Use agent_uid as password for simplicity (can be enhanced with proper password generation)
    password = agent_uid
    
    for attempt in range(max_retries):
        client = AsyncClient(settings.MATRIX_SERVER_URL)
        try:
            response = await asyncio.wait_for(
                client.register(username=username, password=password), 
                timeout=timeout
            )
            if isinstance(response, RegisterResponse) and response.user_id:
                matrix_logger.info(f"Agent {agent_name} ({username}) successfully registered on Matrix.")
                
                # Set the display name for the agent
                if response.access_token:
                    await update_agent_matrix_profile(
                        access_token=response.access_token,
                        user_id=response.user_id,
                        display_name=agent_name
                    )
                
                return response.access_token, response.user_id
        except asyncio.TimeoutError:
            matrix_logger.warning(f"Matrix registration timed out for agent {agent_name} (attempt {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise MatrixRegistrationError(f"Registration timeout for agent {agent_name} after {max_retries} attempts")
        except Exception as e:
            matrix_logger.error(f"Matrix registration error for agent {agent_name} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise MatrixRegistrationError(f"Registration failed for agent {agent_name}: {str(e)}")
        finally:
            await client.close()

        # Exponential backoff delay before retrying
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)

    # If all attempts fail, return None
    matrix_logger.error(f"Failed to register agent {agent_name} after {max_retries} attempts.")
    return None


async def login_agent_on_matrix(agent_uid: str, max_retries: int = 1, timeout: int = 2) -> Optional[Tuple[str, str]]:
    """
    Logs in an AI agent to the Matrix server with retry and timeout logic.

    Args:
        agent_uid (str): The unique identifier for the agent.
        max_retries (int): Maximum number of retries in case of failure.
        timeout (int): Timeout duration (in seconds) for each login attempt.

    Returns:
        tuple: (access_token, user_id) if successful, (None, None) otherwise.
    """
    username = f"agent_{agent_uid}"
    password = agent_uid
    
    for attempt in range(max_retries):
        client = AsyncClient(settings.MATRIX_SERVER_URL, username)
        try:
            response = await asyncio.wait_for(client.login(password=password), timeout=timeout)
            if isinstance(response, LoginResponse):
                matrix_logger.info(f"Agent {username} successfully logged in to Matrix.")
                return response.access_token, response.user_id
        except asyncio.TimeoutError:
            matrix_logger.warning(f"Matrix login timed out for agent {username}, retrying ({attempt + 1}/{max_retries})...")
        except Exception as e:
            matrix_logger.error(f"Matrix login error for agent {username}: {e}")
        finally:
            await client.close()

        # Exponential backoff delay before retrying
        await asyncio.sleep(2 ** attempt)

    # If login fails, try to register the agent as a fallback
    matrix_logger.warning(f"Failed to login agent {username} after {max_retries} attempts. Attempting registration as fallback...")
    try:
        # Get agent name from the database for registration
        from .models import Agent
        try:
            agent = Agent.nodes.get(uid=agent_uid)
            registration_result = await register_agent_on_matrix(agent.name, agent_uid)
            if registration_result and registration_result[0]:
                matrix_logger.info(f"Successfully registered and logged in agent {username} as fallback.")
                return registration_result
        except Agent.DoesNotExist:
            matrix_logger.error(f"Agent {agent_uid} not found in database for fallback registration.")
        
    except Exception as e:
        matrix_logger.error(f"Fallback registration failed for agent {username}: {e}")
    
    # If all attempts fail, raise MatrixLoginError
    error_msg = f"All login and registration attempts failed for agent {username}."
    matrix_logger.error(error_msg)
    raise MatrixLoginError(error_msg)


async def update_agent_matrix_profile(access_token: str, user_id: str, display_name: str = None, avatar_url: str = None, timeout: int = 10) -> dict:
    """
    Updates an agent's profile on the Matrix server.

    Args:
        access_token (str): The access token for authenticating the agent.
        user_id (str): The Matrix user ID of the agent to update.
        display_name (str, optional): The new display name for the agent.
        avatar_url (str, optional): The new avatar URL for the agent.
        timeout (int): Timeout duration (in seconds) for each update attempt.

    Returns:
        dict: A dictionary containing the status of the updates (success or error).
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = access_token
    client.user_id = user_id

    results = {"display_name": None, "avatar_url": None}

    try:
        if display_name:
            # Update display name
            matrix_logger.info(f"Updating display name for agent {user_id}")
            response = await asyncio.wait_for(
                client.set_displayname(display_name), timeout=timeout
            )
            if response and response.transport_response.status == 200:
                matrix_logger.info(f"Successfully updated display name to '{display_name}' for agent {user_id}.")
                results["display_name"] = "success"
            else:
                matrix_logger.error(f"Failed to update display name for agent {user_id}: {response}")
                results["display_name"] = "error"

        if avatar_url:
            # Update avatar URL
            response = await asyncio.wait_for(
                client.set_avatar(avatar_url), timeout=timeout
            )
            if response and response.transport_response.status == 200:
                matrix_logger.info(f"Successfully updated avatar URL for agent {user_id}.")
                results["avatar_url"] = "success"
            else:
                matrix_logger.error(f"Failed to update avatar URL for agent {user_id}: {response}")
                results["avatar_url"] = "error"

    except asyncio.TimeoutError:
        error_msg = f"Profile update timed out for agent {user_id}."
        matrix_logger.error(error_msg)
        raise MatrixProfileUpdateError(error_msg)
    except Exception as e:
        error_msg = f"Error updating profile for agent {user_id}: {e}"
        matrix_logger.error(error_msg)
        raise MatrixProfileUpdateError(error_msg)
    finally:
        await client.close()

    # Check if any updates failed and raise exception if so
    if "error" in results.values():
        error_msg = f"One or more profile updates failed for agent {user_id}: {results}"
        matrix_logger.error(error_msg)
        raise MatrixProfileUpdateError(error_msg)

    return results


def create_agent_matrix_profile(agent):
    """
    Synchronous wrapper to create Matrix profile for an agent.
    
    Args:
        agent: Agent instance to create Matrix profile for
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        matrix_logger.info(f"Starting Matrix profile creation for agent {agent.name} ({agent.uid})")
        
        # Create Matrix profile for the agent
        matrix_result = asyncio.run(register_agent_on_matrix(agent.name, agent.uid))
        
        if matrix_result and matrix_result[0]:
            # Update agent with Matrix credentials
            agent.access_token = matrix_result[0]
            agent.matrix_user_id = matrix_result[1]
            agent.pending_matrix_registration = False
            agent.save()
            
            matrix_logger.info(f"Successfully created Matrix profile for agent {agent.name} ({agent.uid}) - Matrix ID: {matrix_result[1]}")
            return True
        else:
            # Mark as pending registration
            agent.pending_matrix_registration = True
            agent.save()
            
            matrix_logger.warning(f"Failed to create Matrix profile for agent {agent.name} ({agent.uid}), marked as pending")
            return False
            
    except MatrixRegistrationError as e:
        matrix_logger.error(f"Matrix registration error for agent {agent.name} ({agent.uid}): {e}")
        agent.pending_matrix_registration = True
        agent.save()
        return False
    except Exception as e:
        matrix_logger.error(f"Unexpected error creating Matrix profile for agent {agent.name} ({agent.uid}): {e}")
        # Mark as pending registration on error
        agent.pending_matrix_registration = True
        agent.save()
        return False


def retry_agent_matrix_registration(agent):
    """
    Retry Matrix registration for an agent with pending registration.
    
    Args:
        agent: Agent instance with pending Matrix registration
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not agent.pending_matrix_registration:
        matrix_logger.info(f"Agent {agent.name} ({agent.uid}) does not have pending Matrix registration")
        return True
        
    return create_agent_matrix_profile(agent)


async def join_agent_to_matrix_room(agent_matrix_id: str, agent_access_token: str, room_id: str, timeout: int = 10) -> bool:
    """
    Join an agent to a Matrix room.
    
    Args:
        agent_matrix_id (str): The Matrix user ID of the agent
        agent_access_token (str): The access token of the agent
        room_id (str): The Matrix room ID to join
        timeout (int): Timeout for the join operation
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixProfileUpdateError: If the join operation fails after retries
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = agent_access_token
    client.user_id = agent_matrix_id
    
    try:
        matrix_logger.info(f"Joining agent {agent_matrix_id} to Matrix room {room_id}")
        
        response = await asyncio.wait_for(
            client.join(room_id),
            timeout=timeout
        )
        
        if hasattr(response, 'room_id'):
            matrix_logger.info(f"Successfully joined agent {agent_matrix_id} to room {room_id}")
            return True
        else:
            matrix_logger.error(f"Failed to join agent {agent_matrix_id} to room {room_id}: {response}")
            raise MatrixProfileUpdateError(f"Failed to join agent to room {room_id}: {response}")
            
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout joining agent {agent_matrix_id} to room {room_id}")
        raise MatrixProfileUpdateError(f"Timeout joining agent to room {room_id}")
    except Exception as e:
        matrix_logger.error(f"Error joining agent {agent_matrix_id} to room {room_id}: {e}")
        raise MatrixProfileUpdateError(f"Error joining agent to room {room_id}: {e}")
    finally:
        await client.close()


async def set_agent_power_level(admin_access_token: str, admin_matrix_id: str, room_id: str, agent_matrix_id: str, power_level: int = 50, timeout: int = 10) -> bool:
    """
    Set power level for an agent in a Matrix room to grant admin privileges.
    
    Args:
        admin_access_token (str): Access token of the room admin
        admin_matrix_id (str): Matrix user ID of the room admin
        room_id (str): Matrix room ID
        agent_matrix_id (str): Matrix user ID of the agent
        power_level (int): Power level to set (50 = moderator, 100 = admin)
        timeout (int): Timeout for the operation
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixProfileUpdateError: If the power level setting fails
    """
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    client.access_token = admin_access_token
    client.user_id = admin_matrix_id
    
    try:
        matrix_logger.info(f"Setting power level {power_level} for agent {agent_matrix_id} in room {room_id}")
        
        # Get current room power levels
        response = await asyncio.wait_for(
            client.room_get_state_event(room_id, "m.room.power_levels"),
            timeout=timeout
        )
        
        if hasattr(response, 'content'):
            power_levels = response.content
            matrix_logger.info(f"Current power levels retrieved: {power_levels}")
        else:
            matrix_logger.warning(f"No existing power levels found, creating default structure")
            # If no power levels exist, create default structure
            power_levels = {
                "users": {},
                "users_default": 0,
                "events": {},
                "events_default": 0,
                "state_default": 50,
                "ban": 50,
                "kick": 50,
                "redact": 50,
                "invite": 50
            }
        
        # Verify admin has sufficient power level
        admin_power = power_levels.get("users", {}).get(admin_matrix_id, 0)
        matrix_logger.info(f"Admin {admin_matrix_id} current power level: {admin_power}")
        
        if admin_power < power_level:
            matrix_logger.error(f"Admin power level ({admin_power}) is insufficient to grant power level {power_level}")
            return False
        
        # Check if agent already has the required power level
        current_agent_power = power_levels.get("users", {}).get(agent_matrix_id, 0)
        if current_agent_power >= power_level:
            matrix_logger.info(f"Agent {agent_matrix_id} already has sufficient power level ({current_agent_power})")
            return True
        
        # Set the agent's power level
        if "users" not in power_levels:
            power_levels["users"] = {}
        power_levels["users"][agent_matrix_id] = power_level
        
        matrix_logger.info(f"Updating power levels to grant {agent_matrix_id} power level {power_level}")
        
        # Send the updated power levels
        response = await asyncio.wait_for(
            client.room_put_state(room_id, "m.room.power_levels", power_levels),
            timeout=timeout
        )
        
        if hasattr(response, 'event_id'):
            matrix_logger.info(f"Successfully set power level {power_level} for agent {agent_matrix_id} in room {room_id}")
            
            # Verify the change was applied by re-fetching power levels
            verify_response = await asyncio.wait_for(
                client.room_get_state_event(room_id, "m.room.power_levels"),
                timeout=timeout
            )
            
            if hasattr(verify_response, 'content'):
                new_power_levels = verify_response.content
                actual_agent_power = new_power_levels.get("users", {}).get(agent_matrix_id, 0)
                if actual_agent_power >= power_level:
                    matrix_logger.info(f"Verified: Agent {agent_matrix_id} now has power level {actual_agent_power}")
                    return True
                else:
                    matrix_logger.warning(f"Power level verification failed: expected {power_level}, got {actual_agent_power}")
                    return False
            else:
                matrix_logger.warning(f"Could not verify power level change")
                return True  # Assume success if we can't verify
            
        else:
            matrix_logger.error(f"Failed to set power level for agent {agent_matrix_id} in room {room_id}: {response}")
            return False
            
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout setting power level for agent {agent_matrix_id} in room {room_id}")
        raise MatrixProfileUpdateError(f"Timeout setting power level for agent in room {room_id}")
    except Exception as e:
        matrix_logger.error(f"Error setting power level for agent {agent_matrix_id} in room {room_id}: {e}")
        raise MatrixProfileUpdateError(f"Error setting power level for agent in room {room_id}: {e}")
    finally:
        await client.close()


async def set_power_level_with_server_admin_http(room_id: str, user_matrix_id: str, power_level: int = 100, timeout: int = 10) -> bool:
    """
    Set power level for a user in a Matrix room using server admin privileges via HTTP API.
    This function uses direct HTTP API calls to bypass matrix-nio compatibility issues.
    
    Args:
        room_id (str): Matrix room ID
        user_matrix_id (str): Matrix user ID of the user to grant power level to
        power_level (int): Power level to set (50 = moderator, 100 = admin)
        timeout (int): Timeout for the operation
        
    Returns:
        bool: True if successful, False otherwise
    """
    import aiohttp
    import json
    
    if not settings.MATRIX_ADMIN_USER or not settings.MATRIX_ADMIN_PASSWORD:
        matrix_logger.warning("Matrix server admin credentials not configured, skipping server admin power level setting")
        return False
    
    try:
        matrix_logger.info(f"Attempting HTTP API login as server admin to set power level {power_level} for user {user_matrix_id} in room {room_id}")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # Step 1: Login via HTTP API
            login_data = {
                "type": "m.login.password",
                "user": settings.MATRIX_ADMIN_USER,
                "password": settings.MATRIX_ADMIN_PASSWORD
            }
            
            login_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/login"
            
            async with session.post(login_url, json=login_data) as response:
                if response.status == 429:
                    matrix_logger.warning(f"HTTP API login rate limited (429), this is expected after multiple attempts")
                    return False
                elif response.status != 200:
                    response_text = await response.text()
                    matrix_logger.error(f"HTTP API login failed: {response.status} - {response_text}")
                    return False
                
                login_result = await response.json()
                access_token = login_result.get('access_token')
                admin_user_id = login_result.get('user_id')
                
                if not access_token:
                    matrix_logger.error("No access token received from login")
                    return False
                
                matrix_logger.info(f"Successfully logged in via HTTP API as {admin_user_id}")
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                # Step 2: Get current power levels
                state_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/m.room.power_levels"
                
                async with session.get(state_url, headers=headers) as state_response:
                    if state_response.status == 403:
                        matrix_logger.warning(f"Admin user {admin_user_id} is not in room {room_id}")
                        matrix_logger.info("Admin user would need to be invited to the room first")
                        return False
                    elif state_response.status != 200:
                        matrix_logger.error(f"Failed to get room state: {state_response.status}")
                        return False
                    
                    power_levels = await state_response.json()
                    matrix_logger.info(f"Retrieved current power levels via HTTP API")
                    
                    # Check if user already has sufficient power level
                    current_power = power_levels.get("users", {}).get(user_matrix_id, 0)
                    if current_power >= power_level:
                        matrix_logger.info(f"User {user_matrix_id} already has sufficient power level ({current_power})")
                        return True
                    
                    # Step 3: Update power levels
                    if "users" not in power_levels:
                        power_levels["users"] = {}
                    power_levels["users"][user_matrix_id] = power_level
                    
                    matrix_logger.info(f"Updating power levels via HTTP API to grant {user_matrix_id} power level {power_level}")
                    
                    async with session.put(state_url, headers=headers, json=power_levels) as update_response:
                        if update_response.status == 200:
                            update_result = await update_response.json()
                            event_id = update_result.get('event_id')
                            matrix_logger.info(f"Successfully updated power levels via HTTP API (event: {event_id})")
                            
                            # Verify the change
                            await asyncio.sleep(1)  # Give server time to process
                            
                            async with session.get(state_url, headers=headers) as verify_response:
                                if verify_response.status == 200:
                                    new_power_levels = await verify_response.json()
                                    new_power = new_power_levels.get("users", {}).get(user_matrix_id, 0)
                                    matrix_logger.info(f"Verified: User {user_matrix_id} now has power level {new_power}")
                                    
                                    if new_power >= power_level:
                                        matrix_logger.info(f"Successfully set power level {power_level} for user {user_matrix_id} via HTTP API")
                                        return True
                                    else:
                                        matrix_logger.warning(f"Power level verification failed: expected {power_level}, got {new_power}")
                                        return False
                                else:
                                    matrix_logger.warning("Could not verify power level change via HTTP API")
                                    return True  # Assume success
                        else:
                            update_text = await update_response.text()
                            matrix_logger.error(f"Failed to update power levels via HTTP API: {update_response.status} - {update_text}")
                            return False
                            
    except Exception as e:
        matrix_logger.error(f"Error in HTTP API power level setting: {e}")
        return False


async def set_power_level_with_server_admin(room_id: str, user_matrix_id: str, power_level: int = 100, timeout: int = 10) -> bool:
    """
    Set power level for a user in a Matrix room using server admin privileges.
    This function uses the server admin credentials to bypass room-level permission restrictions.
    
    Args:
        room_id (str): Matrix room ID
        user_matrix_id (str): Matrix user ID of the user to grant power level to
        power_level (int): Power level to set (50 = moderator, 100 = admin)
        timeout (int): Timeout for the operation
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixProfileUpdateError: If the power level setting fails
    """
    if not settings.MATRIX_ADMIN_USER or not settings.MATRIX_ADMIN_PASSWORD:
        matrix_logger.warning("Matrix server admin credentials not configured, skipping server admin power level setting")
        return False
    
    client = AsyncClient(settings.MATRIX_SERVER_URL)
    
    try:
        matrix_logger.info(f"Attempting to login as server admin to set power level {power_level} for user {user_matrix_id} in room {room_id}")
        
        # Try multiple login formats with simple username approach
        login_attempts = [
            settings.MATRIX_ADMIN_USER,
            "matrixadmin", 
            f"@{settings.MATRIX_ADMIN_USER}:{settings.MATRIX_SERVER_URL.replace('https://', '').replace('http://', '')}",
            f"@matrixadmin:chat.ooumph.com"
        ]
        
        login_successful = False
        for username in login_attempts:
            try:
                matrix_logger.info(f"Trying login with username: {username}")
                
                # Add delay between attempts to avoid rate limiting
                if username != login_attempts[0]:
                    await asyncio.sleep(1)
                
                login_response = await asyncio.wait_for(
                    client.login(username, settings.MATRIX_ADMIN_PASSWORD),
                    timeout=timeout
                )
                
                if hasattr(login_response, 'access_token') and login_response.access_token:
                    matrix_logger.info(f"Successfully logged in as server admin: {client.user_id}")
                    login_successful = True
                    break
                else:
                    matrix_logger.warning(f"Login failed for {username}: {login_response}")
            except Exception as login_error:
                matrix_logger.warning(f"Login attempt failed for {username}: {login_error}")
                continue
        
        if not login_successful:
            matrix_logger.error("All server admin login attempts failed")
            return False
        
        # Get current room power levels
        response = await asyncio.wait_for(
            client.room_get_state_event(room_id, "m.room.power_levels"),
            timeout=timeout
        )
        
        if hasattr(response, 'content'):
            power_levels = response.content
        else:
            # If no power levels exist, create default structure
            power_levels = {
                "users": {},
                "users_default": 0,
                "events": {},
                "events_default": 0,
                "state_default": 50,
                "ban": 50,
                "kick": 50,
                "redact": 50,
                "invite": 50
            }
        
        # Set the user's power level
        if "users" not in power_levels:
            power_levels["users"] = {}
        power_levels["users"][user_matrix_id] = power_level
        
        # Send the updated power levels
        response = await asyncio.wait_for(
            client.room_put_state(room_id, "m.room.power_levels", power_levels),
            timeout=timeout
        )
        
        if hasattr(response, 'event_id'):
            matrix_logger.info(f"Successfully set power level {power_level} for user {user_matrix_id} in room {room_id} using server admin")
            return True
        else:
            matrix_logger.error(f"Failed to set power level for user {user_matrix_id} in room {room_id}: {response}")
            return False
            
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout setting power level for user {user_matrix_id} in room {room_id} using server admin")
        return False
    except Exception as e:
        matrix_logger.error(f"Error setting power level for user {user_matrix_id} in room {room_id} using server admin: {e}")
        return False
    finally:
        await client.close()


async def invite_and_join_agent_to_matrix_room(admin_matrix_id, admin_access_token, agent_matrix_id, agent_access_token, room_id, timeout=10):
    """
    Invite an agent to a Matrix room and then have them join.
    
    Args:
        admin_matrix_id (str): Matrix user ID of the room admin
        admin_access_token (str): Access token of the room admin
        agent_matrix_id (str): Matrix user ID of the agent
        agent_access_token (str): Access token of the agent
        room_id (str): Matrix room ID to join
        timeout (int): Timeout for operations
        
    Returns:
        bool: True if both invite and join were successful
        
    Raises:
        MatrixProfileUpdateError: If either operation fails
    """
    from community.utils.matrix_invites import invite_user_to_room, auto_join_room
    
    try:
        matrix_logger.info(f"Inviting agent {agent_matrix_id} to room {room_id}")
        
        # First, invite the agent to the room using admin credentials
        invite_success = await invite_user_to_room(
            admin_access_token=admin_access_token,
            admin_user_id=admin_matrix_id,
            room_id=room_id,
            user_id=agent_matrix_id,
            timeout=timeout
        )
        
        if not invite_success:
            raise MatrixProfileUpdateError(f"Failed to invite agent to room {room_id}")
        
        matrix_logger.info(f"Successfully invited agent {agent_matrix_id}, now joining room {room_id}")
        
        # Then, have the agent join the room
        join_success = await auto_join_room(
            user_access_token=agent_access_token,
            user_matrix_id=agent_matrix_id,
            room_id=room_id,
            timeout=timeout
        )
        
        if not join_success:
            raise MatrixProfileUpdateError(f"Agent was invited but failed to join room {room_id}")
        
        matrix_logger.info(f"Successfully joined agent {agent_matrix_id} to room {room_id}")
        return True
        
    except asyncio.TimeoutError:
        matrix_logger.error(f"Timeout inviting/joining agent {agent_matrix_id} to room {room_id}")
        raise MatrixProfileUpdateError(f"Timeout inviting/joining agent to room {room_id}")
    except Exception as e:
        matrix_logger.error(f"Error inviting/joining agent {agent_matrix_id} to room {room_id}: {e}")
        raise MatrixProfileUpdateError(f"Error inviting/joining agent to room {room_id}: {e}")


async def invite_join_and_grant_admin_to_agent(admin_matrix_id, admin_access_token, agent_matrix_id, agent_access_token, room_id, power_level=50, timeout=10):
    """
    Invite an agent to a Matrix room, have them join, and grant admin privileges.
    
    Args:
        admin_matrix_id (str): Matrix user ID of the room admin
        admin_access_token (str): Access token of the room admin
        agent_matrix_id (str): Matrix user ID of the agent
        agent_access_token (str): Access token of the agent
        room_id (str): Matrix room ID to join
        power_level (int): Power level to grant (50 = moderator, 100 = admin)
        timeout (int): Timeout for operations
        
    Returns:
        bool: True if invite, join, and admin grant were all successful
        
    Raises:
        MatrixProfileUpdateError: If any operation fails
    """
    try:
        # First, invite and join the agent to the room
        join_success = await invite_and_join_agent_to_matrix_room(
            admin_matrix_id=admin_matrix_id,
            admin_access_token=admin_access_token,
            agent_matrix_id=agent_matrix_id,
            agent_access_token=agent_access_token,
            room_id=room_id,
            timeout=timeout
        )
        
        if not join_success:
            raise MatrixProfileUpdateError(f"Failed to invite/join agent to room {room_id}")
        
        # Then, grant admin privileges to the agent
        matrix_logger.info(f"Granting admin privileges (power level {power_level}) to agent {agent_matrix_id} in room {room_id}")
        admin_success = await set_agent_power_level(
            admin_access_token=admin_access_token,
            admin_matrix_id=admin_matrix_id,
            room_id=room_id,
            agent_matrix_id=agent_matrix_id,
            power_level=power_level,
            timeout=timeout
        )
        
        if not admin_success:
            matrix_logger.warning(f"Agent {agent_matrix_id} joined room {room_id} but failed to get admin privileges")
            # Don't raise an error here as the agent is still in the room
            return False
        
        matrix_logger.info(f"Successfully invited, joined, and granted admin privileges to agent {agent_matrix_id} in room {room_id}")
        return True
        
    except Exception as e:
        matrix_logger.error(f"Error in invite/join/admin process for agent {agent_matrix_id} in room {room_id}: {e}")
        raise MatrixProfileUpdateError(f"Error in invite/join/admin process for agent in room {room_id}: {e}")


def grant_agent_admin_rights_to_existing_room(agent_uid: str, community_uid: str, power_level: int = 50) -> bool:
    """
    Grant admin rights to an agent that's already in a Matrix room.
    
    This function is useful for fixing agents that were added to rooms without proper permissions.
    It attempts to set the power level using community admin credentials first, then falls back
    to server admin credentials if needed.
    
    Args:
        agent_uid (str): UID of the agent to grant admin rights to
        community_uid (str): UID of the community containing the Matrix room
        power_level (int): Power level to grant (50 = moderator, 100 = admin). Default: 50
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixProfileUpdateError: If the operation fails
    """
    from agentic.models import Agent
    from community.models import Community
    from msg.models import MatrixProfile
    from neomodel import DoesNotExist
    
    matrix_logger.info(f"Granting admin rights (power level {power_level}) to agent {agent_uid} in community {community_uid}")
    
    try:
        # Get agent and community
        try:
            agent = Agent.nodes.get(uid=agent_uid)
        except DoesNotExist:
            raise MatrixProfileUpdateError(f"Agent {agent_uid} not found")
            
        try:
            community = Community.nodes.get(uid=community_uid)
        except DoesNotExist:
            raise MatrixProfileUpdateError(f"Community {community_uid} not found")
        
        # Validate agent has Matrix credentials
        if not agent.matrix_user_id or not agent.access_token:
            raise MatrixProfileUpdateError(f"Agent {agent.name} does not have Matrix credentials")
        
        # Validate community has Matrix room
        if not community.room_id:
            raise MatrixProfileUpdateError(f"Community {community.name} does not have a Matrix room")
        
        matrix_logger.info(f"Agent: {agent.name} ({agent.matrix_user_id})")
        matrix_logger.info(f"Community: {community.name} ({community.room_id})")
        
        # First try using community admin credentials - prioritize those with Matrix room privileges
        admin_matrix_profile = None
        potential_admins = []
        
        # Collect all potential admins with Matrix credentials
        for membership in community.members.all():
            if membership.is_admin:
                try:
                    user_node = membership.user.single()
                    if user_node and hasattr(user_node, 'user_id'):
                        profile = MatrixProfile.objects.get(user=user_node.user_id)
                        if profile.matrix_user_id and profile.access_token:
                            potential_admins.append(profile)
                except (MatrixProfile.DoesNotExist, AttributeError):
                    continue
        
        if potential_admins:
            matrix_logger.info(f"Found {len(potential_admins)} potential admins, checking Matrix room privileges...")
            
            # Check which admin has actual Matrix room privileges
            async def check_admin_privileges(profile):
                try:
                    client = AsyncClient(settings.MATRIX_SERVER_URL)
                    client.access_token = profile.access_token
                    client.user_id = profile.matrix_user_id
                    
                    response = await asyncio.wait_for(
                        client.room_get_state_event(community.room_id, "m.room.power_levels"),
                        timeout=5
                    )
                    
                    await client.close()
                    
                    if hasattr(response, 'content'):
                        power_levels = response.content
                        admin_power = power_levels.get("users", {}).get(profile.matrix_user_id, 0)
                        return admin_power
                    else:
                        return -1
                except Exception:
                    return -1
            
            for profile in potential_admins:
                try:
                    admin_power = asyncio.run(check_admin_privileges(profile))
                    matrix_logger.info(f"Admin {profile.matrix_user_id} has power level {admin_power} in Matrix room")
                    
                    if admin_power >= 100:
                        admin_matrix_profile = profile
                        matrix_logger.info(f"Selected admin with Matrix room privileges: {profile.matrix_user_id}")
                        break
                    elif admin_power >= 0:
                        matrix_logger.warning(f"Admin {profile.matrix_user_id} has insufficient Matrix room privileges ({admin_power})")
                except Exception as check_error:
                    matrix_logger.warning(f"Error checking Matrix privileges for {profile.matrix_user_id}: {check_error}")
                    continue
            
            # If no admin has sufficient privileges, use the first one
            if not admin_matrix_profile and potential_admins:
                admin_matrix_profile = potential_admins[0]
                matrix_logger.warning(f"No admin has sufficient Matrix room privileges, using {admin_matrix_profile.matrix_user_id} anyway")
        
        if admin_matrix_profile:
            try:
                matrix_logger.info(f"Attempting to set power level using community admin {admin_matrix_profile.matrix_user_id}")
                success = asyncio.run(set_agent_power_level(
                    admin_access_token=admin_matrix_profile.access_token,
                    admin_matrix_id=admin_matrix_profile.matrix_user_id,
                    room_id=community.room_id,
                    agent_matrix_id=agent.matrix_user_id,
                    power_level=power_level
                ))
                
                if success:
                    matrix_logger.info(f"Successfully set power level {power_level} for agent using community admin")
                    return True
                else:
                    matrix_logger.warning(f"Failed to set power level using community admin, trying server admin")
            except Exception as e:
                matrix_logger.warning(f"Community admin power level setting failed: {e}, trying server admin")
        else:
            matrix_logger.warning(f"No community admin with Matrix credentials found, trying server admin")
        
        # Fallback to server admin credentials
        try:
            matrix_logger.info(f"Attempting to set power level using server admin credentials (matrix-nio)")
            success = asyncio.run(set_power_level_with_server_admin(
                room_id=community.room_id,
                user_matrix_id=agent.matrix_user_id,
                power_level=power_level
            ))
            
            if success:
                matrix_logger.info(f"Successfully set power level {power_level} for agent using server admin (matrix-nio)")
                return True
            else:
                matrix_logger.warning(f"Server admin (matrix-nio) failed, trying HTTP API")
                
                # Try HTTP API approach
                http_success = asyncio.run(set_power_level_with_server_admin_http(
                    room_id=community.room_id,
                    user_matrix_id=agent.matrix_user_id,
                    power_level=power_level
                ))
                
                if http_success:
                    matrix_logger.info(f"Successfully set power level {power_level} for agent using server admin (HTTP API)")
                    return True
                else:
                    matrix_logger.error(f"Both server admin approaches failed")
                    return False
                
        except Exception as e:
            matrix_logger.warning(f"Server admin (matrix-nio) failed with error: {e}")
            
            # Try HTTP API as fallback
            try:
                matrix_logger.info(f"Trying HTTP API as fallback")
                http_success = asyncio.run(set_power_level_with_server_admin_http(
                    room_id=community.room_id,
                    user_matrix_id=agent.matrix_user_id,
                    power_level=power_level
                ))
                
                if http_success:
                    matrix_logger.info(f"Successfully set power level {power_level} for agent using HTTP API fallback")
                    return True
                else:
                    matrix_logger.error(f"HTTP API fallback also failed")
                    return False
                    
            except Exception as http_error:
                matrix_logger.error(f"HTTP API fallback failed: {http_error}")
                return False
            
    except Exception as e:
        matrix_logger.error(f"Error granting admin rights to agent {agent_uid} in community {community_uid}: {e}")
        raise MatrixProfileUpdateError(f"Error granting admin rights: {e}")


def join_agent_to_community_matrix_room(agent, community):
    """
    Join an agent to their assigned community's Matrix room.
    First invites the agent using community admin credentials, then has agent join.
    
    Args:
        agent: Agent instance with Matrix credentials
        community: Community instance with room_id
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        MatrixProfileUpdateError: If the join operation fails
    """
    from msg.models import MatrixProfile
    from community.models import Membership
    
    matrix_logger.info(f"Attempting to join agent {agent.name} ({agent.uid}) to community {community.name} Matrix room")
    
    # Check if agent has Matrix credentials
    if not agent.matrix_user_id or not agent.access_token:
        matrix_logger.error(f"Agent {agent.name} ({agent.uid}) does not have Matrix credentials")
        raise MatrixProfileUpdateError(f"Agent {agent.name} does not have Matrix credentials")
    
    # Check if community has a Matrix room
    if not community.room_id:
        matrix_logger.warning(f"Community {community.name} ({community.uid}) does not have a Matrix room")
        return False
    
    try:
        # Find a community admin with Matrix credentials AND Matrix room privileges
        admin_matrix_profile = None
        potential_admins = []
        
        # Collect all potential admins with Matrix credentials
        for membership in community.members.all():
            if membership.is_admin:
                try:
                    user_node = membership.user.single()
                    if user_node and hasattr(user_node, 'user_id'):
                        profile = MatrixProfile.objects.get(user=user_node.user_id)
                        if profile.matrix_user_id and profile.access_token:
                            potential_admins.append(profile)
                except (MatrixProfile.DoesNotExist, AttributeError):
                    continue
        
        if not potential_admins:
            matrix_logger.error(f"No community admin found with Matrix credentials for community {community.name}")
            raise MatrixProfileUpdateError(f"No community admin with Matrix credentials found")
        
        # Check which admin has actual Matrix room privileges
        matrix_logger.info(f"Found {len(potential_admins)} potential admins, checking Matrix room privileges...")
        
        async def check_admin_privileges(profile):
            """Check if an admin has Matrix room privileges."""
            try:
                client = AsyncClient(settings.MATRIX_SERVER_URL)
                client.access_token = profile.access_token
                client.user_id = profile.matrix_user_id
                
                response = await asyncio.wait_for(
                    client.room_get_state_event(community.room_id, "m.room.power_levels"),
                    timeout=5
                )
                
                await client.close()
                
                if hasattr(response, 'content'):
                    power_levels = response.content
                    admin_power = power_levels.get("users", {}).get(profile.matrix_user_id, 0)
                    return admin_power
                else:
                    return -1  # Could not determine
                    
            except Exception:
                return -1  # Error occurred
        
        for profile in potential_admins:
            try:
                admin_power = asyncio.run(check_admin_privileges(profile))
                matrix_logger.info(f"Admin {profile.matrix_user_id} has power level {admin_power} in Matrix room")
                
                if admin_power >= 100:  # Has sufficient privileges
                    admin_matrix_profile = profile
                    matrix_logger.info(f"Selected admin with Matrix room privileges: {profile.matrix_user_id}")
                    break
                elif admin_power >= 0:
                    matrix_logger.warning(f"Admin {profile.matrix_user_id} has insufficient Matrix room privileges ({admin_power})")
                else:
                    matrix_logger.warning(f"Could not check Matrix room privileges for {profile.matrix_user_id}")
                    
            except Exception as check_error:
                matrix_logger.warning(f"Error checking Matrix privileges for {profile.matrix_user_id}: {check_error}")
                continue
        
        # If no admin has sufficient Matrix privileges, use the first one and log the issue
        if not admin_matrix_profile and potential_admins:
            admin_matrix_profile = potential_admins[0]
            matrix_logger.warning(f"No admin has sufficient Matrix room privileges, using {admin_matrix_profile.matrix_user_id} anyway")
            matrix_logger.warning(f"This may cause power level setting to fail - the room creator might not be a community admin")
        
        if not admin_matrix_profile:
            matrix_logger.error(f"No community admin found with Matrix credentials for community {community.name}")
            raise MatrixProfileUpdateError(f"No community admin with Matrix credentials found")
        
        # First try to invite and join the agent using community admin credentials
        try:
            # Invite and join the agent to the room
            join_success = asyncio.run(invite_and_join_agent_to_matrix_room(
                admin_matrix_id=admin_matrix_profile.matrix_user_id,
                admin_access_token=admin_matrix_profile.access_token,
                agent_matrix_id=agent.matrix_user_id,
                agent_access_token=agent.access_token,
                room_id=community.room_id
            ))
            
            if not join_success:
                matrix_logger.error(f"Failed to invite/join agent to room {community.room_id}")
                return False
            
            matrix_logger.info(f"Agent {agent.name} successfully joined room")
            
            # Try to set power level using community admin first with retries
            max_retries = 3
            retry_delay = 2  # seconds
            power_success = False
            
            for attempt in range(max_retries):
                try:
                    matrix_logger.info(f"Attempt {attempt + 1}/{max_retries}: Setting agent power level using community admin")
                    
                    # Add a small delay to ensure room state has propagated
                    if attempt > 0:
                        time.sleep(retry_delay)
                    
                    power_success = asyncio.run(set_agent_power_level(
                        admin_access_token=admin_matrix_profile.access_token,
                        admin_matrix_id=admin_matrix_profile.matrix_user_id,
                        room_id=community.room_id,
                        agent_matrix_id=agent.matrix_user_id,
                        power_level=100
                    ))
                    
                    if power_success:
                        matrix_logger.info(f"Successfully set agent power level using community admin on attempt {attempt + 1}")
                        return True
                    else:
                        matrix_logger.warning(f"Attempt {attempt + 1} failed to set power level using community admin")
                        if attempt < max_retries - 1:
                            matrix_logger.info(f"Retrying in {retry_delay} seconds...")
                        
                except Exception as power_error:
                    matrix_logger.warning(f"Attempt {attempt + 1} failed with error: {power_error}")
                    if attempt < max_retries - 1:
                        matrix_logger.info(f"Retrying in {retry_delay} seconds...")
            
            if not power_success:
                matrix_logger.warning(f"All {max_retries} attempts failed, trying server admin")
            
            # Fallback: Use server admin to set power level (bypasses room-level permission restrictions)
            try:
                # First try the matrix-nio approach
                power_success = asyncio.run(set_power_level_with_server_admin(
                    room_id=community.room_id,
                    user_matrix_id=agent.matrix_user_id,
                    power_level=100  # Full admin level
                ))
                
                if power_success:
                    matrix_logger.info(f"Successfully set agent power level using server admin (matrix-nio)")
                    return True
                else:
                    matrix_logger.warning(f"Server admin (matrix-nio) failed, trying HTTP API approach")
                    
                    # Fallback to HTTP API approach
                    http_success = asyncio.run(set_power_level_with_server_admin_http(
                        room_id=community.room_id,
                        user_matrix_id=agent.matrix_user_id,
                        power_level=100
                    ))
                    
                    if http_success:
                        matrix_logger.info(f"Successfully set agent power level using server admin (HTTP API)")
                        return True
                    else:
                        matrix_logger.warning(f"Server admin (HTTP API) also failed")
                        
            except Exception as server_admin_error:
                matrix_logger.warning(f"Server admin approach failed: {server_admin_error}")
                
                # Try HTTP API as final fallback
                try:
                    matrix_logger.info(f"Trying HTTP API as final fallback")
                    http_success = asyncio.run(set_power_level_with_server_admin_http(
                        room_id=community.room_id,
                        user_matrix_id=agent.matrix_user_id,
                        power_level=100
                    ))
                    
                    if http_success:
                        matrix_logger.info(f"Successfully set agent power level using HTTP API fallback")
                        return True
                except Exception as http_error:
                    matrix_logger.warning(f"HTTP API fallback also failed: {http_error}")
            
            # Final fallback: Agent is in room but without admin privileges
            matrix_logger.warning(f"Agent {agent.name} is in the room but without admin privileges")
            matrix_logger.info(f"You can fix this later using: python manage.py fix_agent_matrix_admin_rights --agent-id {agent.uid} --community-id {community.uid}")
            
            # Still return True because the agent successfully joined the room
            return True
            
        except Exception as e:
            matrix_logger.error(f"Failed to join agent to room: {e}")
            return False
        
    except Exception as e:
        matrix_logger.error(f"Error joining agent to community Matrix room: {e}")
        return False