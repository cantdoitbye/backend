#!/usr/bin/env python3
"""
Debug script to check what's actually stored in the username field
"""

import os
import sys
import django
from django.conf import settings
from neomodel import config, db

# Add the project root to Python path
sys.path.append('/Users/harsh/Development/python/ooumph-backend')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

# Import the Users model
from auth_manager.models import Users

def debug_username_storage():
    """
    Debug function to check what's stored in the username field
    """
    try:
        # Set up database connection using Django settings
        from django.conf import settings
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL') and settings.NEOMODEL_NEO4J_BOLT_URL:
            config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL
        else:
            config.DATABASE_URL = os.getenv('NEOMODEL_NEO4J_BOLT_URL', 'bolt://neo4j:password@localhost:7687')
        
        print("=== Username Debug Report ===")
        print()
        
        # Get all users to see what's in the username field
        print("1. Checking all users in database:")
        all_users = Users.nodes.all()
        
        if not all_users:
            print("   No users found in database")
            return
            
        for i, user in enumerate(all_users[:10]):  # Limit to first 10 users
            print(f"   User {i+1}:")
            print(f"     UID: {user.uid}")
            print(f"     Username: {user.username}")
            print(f"     User ID: {getattr(user, 'user_id', 'N/A')}")
            print(f"     Created: {getattr(user, 'created_at', 'N/A')}")
            print()
            
        # Check for users where username looks like a UID
        print("2. Checking for users with UID-like usernames:")
        uid_like_usernames = []
        for user in all_users:
            if user.username and len(user.username) == 32 and user.username.replace('-', '').isalnum():
                uid_like_usernames.append(user)
                
        if uid_like_usernames:
            print(f"   Found {len(uid_like_usernames)} users with UID-like usernames:")
            for user in uid_like_usernames[:5]:  # Show first 5
                print(f"     UID: {user.uid}")
                print(f"     Username: {user.username}")
                print(f"     Match: {user.uid == user.username}")
                print()
        else:
            print("   No users found with UID-like usernames")
            
        # Check recent username updates
        print("3. Running raw Cypher query to check username field:")
        query = """
        MATCH (u:Users)
        RETURN u.uid as uid, u.username as username, u.user_id as user_id
        ORDER BY u.created_at DESC
        LIMIT 10
        """
        
        results, meta = db.cypher_query(query)
        
        if results:
            print("   Raw query results:")
            for row in results:
                uid, username, user_id = row
                print(f"     UID: {uid}")
                print(f"     Username: {username}")
                print(f"     User ID: {user_id}")
                print(f"     Username == UID: {username == uid}")
                print()
        else:
            print("   No results from raw query")
            
        # Check for the specific test user
        print("4. Looking for 'test' username:")
        test_users = Users.nodes.filter(username='test')
        if test_users:
            for user in test_users:
                print(f"   Found user with username 'test':")
                print(f"     UID: {user.uid}")
                print(f"     Username: {user.username}")
                print()
        else:
            print("   No user found with username 'test'")
            
        # Check for users with UID as username
        print("5. Checking for users where username equals UID:")
        matching_users = []
        for user in all_users:
            if user.username == user.uid:
                matching_users.append(user)
                
        if matching_users:
            print(f"   Found {len(matching_users)} users where username == UID:")
            for user in matching_users[:3]:  # Show first 3
                print(f"     UID: {user.uid}")
                print(f"     Username: {user.username}")
                print()
        else:
            print("   No users found where username == UID")
            
    except Exception as e:
        print(f"Error during debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_username_storage()