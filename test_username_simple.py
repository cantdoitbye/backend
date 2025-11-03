#!/usr/bin/env python
"""
Simple test script to verify username fix
"""

import os
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local')
    django.setup()
    
    from django.contrib.auth.models import User
    from auth_manager.models import Users
    
    # Test email
    test_email = "test.username.fix@yopmail.com"
    test_username = "testuser123"
    
    print("=== Testing Username Fix ===")
    
    # Clean up any existing test user
    try:
        existing_user = User.objects.get(email=test_email)
        existing_user.delete()
        print(f"Cleaned up existing user: {test_email}")
    except User.DoesNotExist:
        pass
    
    # Create a new Django user (this triggers the signal)
    print(f"\n1. Creating Django user with email: {test_email}")
    django_user = User.objects.create_user(
        username=test_email,
        email=test_email,
        password='testpassword123'
    )
    print(f"   Django user created with ID: {django_user.id}")
    
    # Check the Neo4j Users node
    print("\n2. Checking Neo4j Users node...")
    try:
        neo4j_user = Users.nodes.get(user_id=str(django_user.id))
        print(f"   Neo4j user found with UID: {neo4j_user.uid}")
        print(f"   Neo4j user username: '{neo4j_user.username}'")
        print(f"   Neo4j user email: {neo4j_user.email}")
        
        # Verify username is not set to UID
        if neo4j_user.username == neo4j_user.uid:
            print("   ❌ ERROR: Username was set to UID! Fix failed.")
            success = False
        elif not neo4j_user.username or neo4j_user.username == test_email:
            print("   ✅ SUCCESS: Username is not set to UID")
            success = True
        else:
            print(f"   ✅ SUCCESS: Username is set to: {neo4j_user.username}")
            success = True
        
        # Simulate username selection
        print(f"\n3. Simulating username selection: {test_username}")
        neo4j_user.username = test_username
        neo4j_user.save()
        print(f"   Username updated to: {neo4j_user.username}")
        
        # Verify the username is stored correctly
        print("\n4. Verifying username storage...")
        updated_user = Users.nodes.get(user_id=str(django_user.id))
        if updated_user.username == test_username:
            print(f"   ✅ SUCCESS: Username correctly stored as: {updated_user.username}")
        else:
            print(f"   ❌ ERROR: Username not stored correctly. Expected: {test_username}, Got: {updated_user.username}")
            success = False
        
        print("\n=== Test Complete ===")
        if success:
            print("✅ Username fix is working correctly!")
        else:
            print("❌ Username fix has issues!")
            
    except Exception as e:
        print(f"   ❌ ERROR: Could not find Neo4j user: {e}")
        success = False
    
    # Clean up
    django_user.delete()
    print(f"\nCleaned up test user: {test_email}")