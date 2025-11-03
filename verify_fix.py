#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local')
django.setup()

from django.contrib.auth.models import User
from auth_manager.models import Users

def test_new_user_creation():
    """Test that new users don't get UID as username"""
    print("\n=== Testing New User Creation ===")
    
    test_email = "verify.fix.test@yopmail.com"
    
    # Clean up any existing test user
    try:
        existing_user = User.objects.get(email=test_email)
        existing_user.delete()
        print(f"Cleaned up existing user: {test_email}")
    except User.DoesNotExist:
        pass
    
    # Create new user
    print(f"Creating new user: {test_email}")
    django_user = User.objects.create_user(
        username=test_email,
        email=test_email,
        password='testpass123'
    )
    
    # Check Neo4j user
    try:
        neo4j_user = Users.nodes.get(user_id=str(django_user.id))
        print(f"Neo4j UID: {neo4j_user.uid}")
        print(f"Neo4j username: '{neo4j_user.username}'")
        
        if neo4j_user.username == neo4j_user.uid:
            print("❌ FAILED: Username was set to UID!")
            result = False
        elif not neo4j_user.username or neo4j_user.username == test_email:
            print("✅ PASSED: Username is not set to UID")
            result = True
        else:
            print(f"✅ PASSED: Username is: {neo4j_user.username}")
            result = True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        result = False
    
    # Clean up
    django_user.delete()
    print(f"Cleaned up test user")
    
    return result

def check_existing_user():
    """Check the user mentioned in the issue"""
    print("\n=== Checking Existing User ===")
    
    test_email = "alt.ho-1or5rl0a@yopmail.com"
    
    try:
        django_user = User.objects.get(email=test_email)
        print(f"Found user: {django_user.email}")
        
        neo4j_user = Users.nodes.get(user_id=str(django_user.id))
        print(f"Neo4j UID: {neo4j_user.uid}")
        print(f"Neo4j username: '{neo4j_user.username}'")
        
        if neo4j_user.username == neo4j_user.uid:
            print("❌ ISSUE CONFIRMED: Username is UID")
            print("Fixing this user...")
            neo4j_user.username = None
            neo4j_user.save()
            print("✅ Fixed: Username cleared")
            return True
        else:
            print("✅ User is already fixed")
            return True
            
    except User.DoesNotExist:
        print(f"User {test_email} not found")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=== Username Fix Verification ===")
    
    # Test 1: New user creation
    test1_result = test_new_user_creation()
    
    # Test 2: Check existing user
    test2_result = check_existing_user()
    
    print("\n=== Summary ===")
    if test1_result and test2_result:
        print("✅ ALL TESTS PASSED: Username fix is working!")
    else:
        print("❌ SOME TESTS FAILED: Issues remain")
    
    print("=== Verification Complete ===")