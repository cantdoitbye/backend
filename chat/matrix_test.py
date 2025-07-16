import asyncio
import json
from nio import AsyncClient, LoginResponse, RegisterResponse

# Matrix server configuration
MATRIX_SERVER_URL = "http://192.168.194.8:8008"  # Replace with your Matrix server URL
TEST_USER = "testuser6"  # Desired username for the test
TEST_PASSWORD = "testpassword3"  # Desired password for the test

# File to store access token
TOKEN_FILE = "test_user_token.json"

async def register_user():
    client = AsyncClient(MATRIX_SERVER_URL)
    try:
        response = await client.register(
            username=TEST_USER,
            password=TEST_PASSWORD,
            device_name="Test Device"
        )
        if isinstance(response, RegisterResponse):
            print(f"User '{TEST_USER}' registered successfully.")
            return True
        else:
            print(f"Failed to register user: {response}")
            return False
    except Exception as e:
        print(f"Error during registration: {e}")
        return False
    finally:
        await client.close()

async def login_user():
    client = AsyncClient(MATRIX_SERVER_URL, TEST_USER)
    try:
        response = await client.login(
            password=TEST_PASSWORD,
            device_name="Test Device"
        )
        if isinstance(response, LoginResponse):
            print(f"User '{TEST_USER}' logged in successfully.")
            # Save access token to a file
            with open(TOKEN_FILE, "w") as f:
                json.dump({
                    "access_token": response.access_token,
                    "device_id": response.device_id,
                    "user_id": response.user_id
                }, f)
            return True
        else:
            print(f"Failed to log in: {response}")
            return False
    except Exception as e:
        print(f"Error during login: {e}")
        return False
    finally:
        await client.close()

async def main():
    # Register the user
    print("Testing user registration...")
    registered = await register_user()
    if not registered:
        print("Registration test failed.")
        return

    # Log in the user
    print("Testing user login...")
    logged_in = await login_user()
    if not logged_in:
        print("Login test failed.")
        return

    print("Matrix connectivity, registration, and login test completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())