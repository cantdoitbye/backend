import asyncio
import os
import sys
from nio import AsyncClient, RoomCreateResponse, RoomVisibility, RoomPreset

async def test_room_creation(server_url, access_token, user_id):
    """Test room creation on a Matrix server."""
    print(f"Testing room creation on Matrix server: {server_url}")
    print(f"Using user_id: {user_id}")
    
    # Initialize the AsyncClient with the homeserver URL
    client = AsyncClient(server_url)
    client.access_token = access_token
    client.user_id = user_id
    
    room_name = "Test Room Creation"
    topic = "Testing room creation functionality"
    
    try:
        print("Attempting to create room...")
        response = await client.room_create(
            name=room_name,
            topic=topic,
            visibility=RoomVisibility.private,
            preset=RoomPreset.private_chat
        )
        
        if isinstance(response, RoomCreateResponse) and response.room_id:
            print(f"Room created successfully! Room ID: {response.room_id}")
            return True
        else:
            print(f"Failed to create room. Response: {response}")
            return False
    except Exception as e:
        print(f"Error creating room: {e}")
        return False
    finally:
        await client.close()

if __name__ == "__main__":
    # Get the Matrix server URL and credentials from environment or use defaults
    matrix_server_url = os.environ.get("MATRIX_SERVER_URL", "https://chat.ooumph.com")
    
    # These need to be provided
    access_token = input("Enter your Matrix access token: ")
    user_id = input("Enter your Matrix user ID: ")
    
    # Run the test
    try:
        result = asyncio.run(test_room_creation(matrix_server_url, access_token, user_id))
        if result:
            print("Room creation test passed!")
            sys.exit(0)
        else:
            print("Room creation test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"Error running test: {e}")
        sys.exit(1) 