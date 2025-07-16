import logging
import asyncio
from nio import AsyncClient, LoginResponse, RegisterResponse
from django.conf import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

matrix_logger = logging.getLogger("matrix_logger")


async def register_user_on_matrix(username, password, max_retries=1, timeout=2):
    """
    Registers a user on the Matrix server with retry and timeout logic.
    
    Args:
        username (str): The username for Matrix registration.
        password (str): The password for Matrix registration.
        max_retries (int): Maximum number of retries in case of failure.
        timeout (int): Timeout duration (in seconds) for each registration attempt.

    Returns:
        tuple: (access_token, user_id) if successful, None otherwise.
    """
    for attempt in range(max_retries):
        # matrix_logger.info("Matrix Server :- ", settings.MATRIX_SERVER_URL)
        client = AsyncClient(settings.MATRIX_SERVER_URL)
        try:
            response = await asyncio.wait_for(client.register(username=username, password=password), timeout=timeout)
            if isinstance(response, RegisterResponse) and response.user_id:
                matrix_logger.info(f"User {username} successfully registered on Matrix.")
                return response.access_token, response.user_id
        except asyncio.TimeoutError:
            matrix_logger.warning(f"Matrix registration timed out for {username}, retrying ({attempt + 1}/{max_retries})...")
        except Exception as e:
            matrix_logger.error(f"Matrix registration error for {username}: {e}")
        finally:
            await client.close()

        # Exponential backoff delay before retrying
        await asyncio.sleep(2 ** attempt)

    # If all attempts fail, return None
    matrix_logger.error(f"Failed to register user {username} after {max_retries} attempts.")
    return None

# async def login_user_on_matrix(username, password, max_retries=1, timeout=2):
#     """
#     Logs in a user to the Matrix server with retry and timeout logic.

#     Args:
#         username (str): The username for Matrix login.
#         password (str): The password for Matrix login.
#         max_retries (int): Maximum number of retries in case of failure.
#         timeout (int): Timeout duration (in seconds) for each login attempt.

#     Returns:
#         tuple: (access_token, user_id) if successful, (None, None) otherwise.
#     """
#     for attempt in range(max_retries):
#         client = AsyncClient(settings.MATRIX_SERVER_URL, username)
#         try:
#             response = await asyncio.wait_for(client.login(password=password), timeout=timeout)
#             if isinstance(response, LoginResponse):
#                 matrix_logger.info(f"User {username} successfully logged in to Matrix.")
#                 return response.access_token, response.user_id
#         except asyncio.TimeoutError:
#             # Print statement will be replace by loger
#             matrix_logger.warning(f"Matrix login timed out for {username}, retrying ({attempt + 1}/{max_retries})...")
#         except Exception as e:
#             matrix_logger.error(f"Matrix login error for {username}: {e}")
#         finally:
#             await client.close()

#         # Exponential backoff delay before retrying
#         await asyncio.sleep(2 ** attempt)

#     # If all attempts fail, return None values
#     matrix_logger.error(f"Failed to login user {username} after {max_retries} attempts.")
#     return None, None


async def login_user_on_matrix(username, password, max_retries=1, timeout=2):
    """
    Logs in a user to the Matrix server with retry and timeout logic.

    Args:
        username (str): The username for Matrix login.
        password (str): The password for Matrix login.
        max_retries (int): Maximum number of retries in case of failure.
        timeout (int): Timeout duration (in seconds) for each login attempt.

    Returns:
        tuple: (access_token, user_id) if successful, (None, None) otherwise.
    """
    for attempt in range(max_retries):
        client = AsyncClient(settings.MATRIX_SERVER_URL, username)
        try:
            response = await asyncio.wait_for(client.login(password=password), timeout=timeout)
            if isinstance(response, LoginResponse):
                matrix_logger.info(f"User {username} successfully logged in to Matrix.")
                return response.access_token, response.user_id
        except asyncio.TimeoutError:
            matrix_logger.warning(f"Matrix login timed out for {username}, retrying ({attempt + 1}/{max_retries})...")
        except Exception as e:
            matrix_logger.error(f"Matrix login error for {username}: {e}")
        finally:
            await client.close()

        # Exponential backoff delay before retrying
        await asyncio.sleep(2 ** attempt)

    # If login fails, try to register the user as a fallback
    matrix_logger.warning(f"Failed to login user {username} after {max_retries} attempts. Attempting registration as fallback...")
    try:
        # Try to register the user
        registration_result = await register_user_on_matrix(username, password)
        if registration_result and registration_result[0]:
            matrix_logger.info(f"Successfully registered and logged in user {username} as fallback.")
            return registration_result
        
    except Exception as e:
        matrix_logger.error(f"Fallback registration failed for {username}: {e}")
    
    # If all attempts fail, return None values
    matrix_logger.error(f"All login and registration attempts failed for {username}.")
    return None, None





async def update_matrix_profile(access_token, user_id, display_name=None, avatar_url=None, timeout=10):
    """
    Updates a user's profile on the Matrix server.

    Args:
        access_token (str): The access token for authenticating the user.
        user_id (str): The Matrix user ID of the user to update.
        display_name (str, optional): The new display name for the user.
        avatar_url (str, optional): The new avatar URL for the user.
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
            print("Updating for the display name")
            response = await asyncio.wait_for(
                client.set_displayname(display_name), timeout=timeout
            )
            if response and response.transport_response.status == 200:
                matrix_logger.info(f"Successfully updated display name to '{display_name}' for user {user_id}.")
                results["display_name"] = "success"
            else:
                matrix_logger.error(f"Failed to update display name for user {user_id}: {response}")
                results["display_name"] = "error"

        if avatar_url:
            # Update avatar URL
            response = await asyncio.wait_for(
                client.set_avatar(avatar_url), timeout=timeout
            )
            if response and response.transport_response.status == 200:
                matrix_logger.info(f"Successfully updated avatar URL for user {user_id}.")
                results["avatar_url"] = "success"
            else:
                matrix_logger.error(f"Failed to update avatar URL for user {user_id}: {response}")
                results["avatar_url"] = "error"

    except asyncio.TimeoutError:
        matrix_logger.error(f"Profile update timed out for user {user_id}.")
    except Exception as e:
        matrix_logger.error(f"Error updating profile for user {user_id}: {e}")
    finally:
        await client.close()

    return results