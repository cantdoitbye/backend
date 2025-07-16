import asyncio
import os
import sys
from nio import AsyncClient
import aiohttp

async def test_matrix_connection(server_url):
    """Test connection to a Matrix server."""
    print(f"Testing connection to Matrix server: {server_url}")
    
    # Try using aiohttp directly to test the connection
    try:
        async with aiohttp.ClientSession() as session:
            versions_url = f"{server_url}/_matrix/client/versions"
            print(f"Requesting: {versions_url}")
            async with session.get(versions_url) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"Connection successful! Server response: {result}")
                    return True
                else:
                    print(f"Server returned status code: {response.status}")
                    print(f"Response: {await response.text()}")
                    return False
    except Exception as e:
        print(f"Error connecting to Matrix server: {e}")
        return False
    
    # Also try with the matrix-nio client
    client = AsyncClient(server_url)
    try:
        # Just try to connect and close
        print("Testing with matrix-nio client...")
        await client.sync(timeout=5000, full_state=True)
        print("Matrix-nio client connection successful!")
        return True
    except Exception as e:
        print(f"Error connecting with matrix-nio client: {e}")
        return False
    finally:
        await client.close()

if __name__ == "__main__":
    # Get the Matrix server URL from environment or use a default
    matrix_server_url = os.environ.get("MATRIX_SERVER_URL", "https://chat.ooumph.com")
    
    print(f"Using Matrix server URL: {matrix_server_url}")
    
    # Run the test
    try:
        result = asyncio.run(test_matrix_connection(matrix_server_url))
        if result:
            print("Connection test passed!")
            sys.exit(0)
        else:
            print("Connection test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"Error running test: {e}")
        sys.exit(1) 