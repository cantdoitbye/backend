import asyncio
from nio import AsyncClient, LoginResponse
from django.conf import settings

async def register_user_on_matrix(username, password):
    # Initialize the Matrix client for admin login
    admin_client = AsyncClient(settings.MATRIX_SERVER_URL)
    
    # Log in as an admin to create the new user
    admin_login = await admin_client.login(settings.MATRIX_ADMIN_USER, settings.MATRIX_ADMIN_PASSWORD)
    if isinstance(admin_login, LoginResponse):
        user_id = f"@{username}:{admin_client.homeserver}"
        try:
            # Register the new user
            await admin_client.register_with_password(user_id=user_id, password=password)
            await admin_client.logout()  # Log out the admin session
            return user_id  # Return the registered Matrix user ID
        except Exception as e:
            pass
            #add above to logger
            #print(f"Matrix registration error: {e}")
    else:
        pass
        # add to loger file
        # print("Admin login failed.")

    await admin_client.close()
    return None