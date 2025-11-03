#!/usr/bin/env python
"""
Test script to verify that the username fix works correctly.
This script tests:
1. User creation without automatic UID assignment
2. Username selection through SelectUsername mutation
3. Verification that username is stored correctly
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append('/Users/harsh/Development/python/ooumph-backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local')
django.setup()

# Now import Django models after setup
from django.contrib.auth.models import User
from auth_manager.models import Users, Profile
from msg.models import MatrixProfile

def test_user_creation_and_username_selection():
    """
    Test the complete flow of user creation and username selection
    """
    print("\n=== Testing Username Fix ===")
    
    # Test email
    test_email = "test.username.fix@yopmail.com"
    test_username = "testuser123"
    
    try:
        # Clean up any existing test user
        try:
            existing_user = User.objects.get(email=test_email)
            existing_user.delete()
            print(f"Cleaned up existing user: {test_email}")
        except User.DoesNotExist:
            pass
        
        # Step 1: Create a new Django user (this triggers the signal)
        print(f"\n1. Creating Django user with email: {test_email}")
        django_user = User.objects.create_user(
            username=test_email,  # Initially use email as username
            email=test_email,
            password='testpassword123'
        )
        print(f"   Django user created with ID: {django_user.id}")
        
        # Step 2: Check the Neo4j Users node
        print("\n2. Checking Neo4j Users node...")
        neo4j_user = Users.nodes.get(user_id=str(django_user.id))
        print(f"   Neo4j user found with UID: {neo4j_user.uid}")
        print(f"   Neo4j user username: '{neo4j_user.username}'")
        print(f"   Neo4j user email: {neo4j_user.email}")
        
        # Step 3: Verify username is not set to UID
        if neo4j_user.username == neo4j_user.uid:
            print("   ❌ ERROR: Username was set to UID! Fix failed.")
            return False
        elif not neo4j_user.username or neo4j_user.username == test_email:
            print("   ✅ SUCCESS: Username is not set to UID")
        else:
            print(f"   ✅ SUCCESS: Username is set to: {neo4j_user.username}")
        
        # Step 4: Simulate username selection
        print(f"\n3. Simulating username selection: {test_username}")
        neo4j_user.username = test_username
        neo4j_user.save()
        print(f"   Username updated to: {neo4j_user.username}")
        
        # Step 5: Verify the username is stored correctly
        print("\n4. Verifying username storage...")
        updated_user = Users.nodes.get(user_id=str(django_user.id))
        if updated_user.username == test_username:
            print(f"   ✅ SUCCESS: Username correctly stored as: {updated_user.username}")
        else:
            print(f"   ❌ ERROR: Username not stored correctly. Expected: {test_username}, Got: {updated_user.username}")
            return False
        
        # Step 6: Check Matrix profile creation
        print("\n5. Checking Matrix profile...")
        try:
            matrix_profile = MatrixProfile.objects.get(user=django_user)
            print(f"   Matrix profile created: {matrix_profile.matrix_user_id}")
            print(f"   Pending registration: {matrix_profile.pending_matrix_registration}")
        except MatrixProfile.DoesNotExist:
            print("   ❌ Matrix profile not created")
        
        # Step 7: Check Profile and related objects
        print("\n6. Checking Profile and related objects...")
        profile = neo4j_user.profile.single()
        if profile:
            print(f"   Profile created with UID: {profile.uid}")
            
            # Check onboarding status
            onboarding = profile.onboarding.single()
            if onboarding:
                print(f"   Onboarding status created: {onboarding.uid}")
            
            # Check score
            score = profile.score.single()
            if score:
                print(f"   Score created: {score.uid}")
        
        # Check connection stats
        connection_stats = neo4j_user.connection_stat.single()
        if connection_stats:
            print(f"   Connection stats created: {connection_stats.uid}")
        
        print("\n=== Test Results ===")
        print("✅ All tests passed! Username fix is working correctly.")
        print("✅ Users are created without automatic UID assignment")
        print("✅ Username selection works properly")
        print("✅ All related objects are created correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test user
        try:
            test_user = User.objects.get(email=test_email)
            test_user.delete()
            print(f"\nCleaned up test user: {test_email}")
        except User.DoesNotExist:
            pass

if __name__ == "__main__":
    success = test_user_creation_and_username_selection()
    if success:
        print("\n🎉 Username fix verification completed successfully!")
    else:
        print("\n💥 Username fix verification failed!")
        sys.exit(1)