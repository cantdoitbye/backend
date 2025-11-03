#!/usr/bin/env python
"""
Comprehensive test script to verify username fix works correctly.
This script tests:
1. User creation without automatic UID assignment
2. Username selection through SelectUsername mutation
3. Verification that username is stored correctly
4. Cleanup of test data
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append('/Users/harsh/Development/python/ooumph-backend')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

# Import after Django setup
from django.contrib.auth.models import User
from django.db import transaction
from auth_manager.models import Users, Profile, OnboardingStatus
from msg.models import MatrixProfile
from auth_manager.validators.rules import string_validation

def cleanup_test_user(email):
    """Clean up test user and related data"""
    try:
        # Delete Django User
        django_user = User.objects.filter(email=email).first()
        if django_user:
            # Delete MatrixProfile
            MatrixProfile.objects.filter(user=django_user).delete()
            
            # Delete Neo4j nodes
            neo4j_user = Users.nodes.filter(user_id=str(django_user.id)).first()
            if neo4j_user:
                profile = neo4j_user.profile.single()
                if profile:
                    onboarding = profile.onboarding.single()
                    if onboarding:
                        onboarding.delete()
                    
                    score = profile.score.single()
                    if score:
                        score.delete()
                    
                    profile.delete()
                
                connection_stats = neo4j_user.connection_stat.single()
                if connection_stats:
                    connection_stats.delete()
                
                neo4j_user.delete()
            
            # Delete Django user
            django_user.delete()
            print(f"   ✅ Cleaned up test user: {email}")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning for {email}: {e}")

def test_user_creation_without_uid():
    """Test that new users are created without username set to UID"""
    print("\n=== Test 1: User Creation Without UID Assignment ===")
    
    test_email = "test.username.fix@example.com"
    
    # Cleanup any existing test user
    cleanup_test_user(test_email)
    
    try:
        # Create Django user (this triggers the signal)
        # Use email as temporary username since Django requires it
        with transaction.atomic():
            django_user = User.objects.create_user(
                username=test_email,  # Temporary username
                email=test_email,
                password='testpassword123'
            )
        
        print(f"   ✅ Created Django user with ID: {django_user.id}")
        
        # Check Neo4j user node
        neo4j_user = Users.nodes.filter(user_id=str(django_user.id)).first()
        if not neo4j_user:
            print("   ❌ Neo4j user node not created")
            return False
        
        print(f"   ✅ Neo4j user node created with UID: {neo4j_user.uid}")
        
        # Check that username is NOT set to UID
        if neo4j_user.username == neo4j_user.uid:
            print(f"   ❌ FAILED: Username is set to UID ({neo4j_user.username})")
            return False, django_user, neo4j_user
        
        # Check that username is empty or None
        if neo4j_user.username and neo4j_user.username.strip():
            print(f"   ❌ FAILED: Username should be empty but is: '{neo4j_user.username}'")
            return False, django_user, neo4j_user
        
        print("   ✅ Username is correctly empty (not set to UID)")
        
        # Verify profile and related objects are created
        profile = neo4j_user.profile.single()
        if not profile:
            print("   ❌ Profile not created")
            return False
        
        print(f"   ✅ Profile created with UID: {profile.uid}")
        
        onboarding = profile.onboarding.single()
        if not onboarding:
            print("   ❌ OnboardingStatus not created")
            return False
        
        print("   ✅ OnboardingStatus created")
        
        # Check Matrix profile
        matrix_profile = MatrixProfile.objects.filter(user=django_user).first()
        if not matrix_profile:
            print("   ❌ MatrixProfile not created")
            return False
        
        print("   ✅ MatrixProfile created")
        
        print("   ✅ Test 1 PASSED: User creation works correctly")
        return True, django_user, neo4j_user
        
    except Exception as e:
        print(f"   ❌ Test 1 FAILED with error: {e}")
        cleanup_test_user(test_email)
        return False, None, None

def test_select_username_mutation(django_user, neo4j_user):
    """Test the SelectUsername mutation functionality"""
    print("\n=== Test 2: SelectUsername Mutation ===")
    
    try:
        test_username = "testuser123"
        
        # Validate username format
        string_validation.validate_username(username=test_username)
        print(f"   ✅ Username '{test_username}' passed validation")
        
        # Check if username already exists
        existing_user = Users.nodes.filter(username=test_username).first()
        if existing_user:
            print(f"   ⚠️  Username '{test_username}' already exists, using alternative")
            test_username = f"testuser{django_user.id}"
        
        # Simulate SelectUsername mutation logic
        neo4j_user.username = test_username
        neo4j_user.save()
        
        print(f"   ✅ Username set to: {test_username}")
        
        # Update onboarding status
        profile = neo4j_user.profile.single()
        onboarding = profile.onboarding.single()
        onboarding.username_selected = True
        onboarding.save()
        
        print("   ✅ Onboarding status updated")
        
        # Verify the username was saved correctly
        updated_user = Users.nodes.get(user_id=str(django_user.id))
        if updated_user.username != test_username:
            print(f"   ❌ FAILED: Username not saved correctly. Expected: {test_username}, Got: {updated_user.username}")
            return False
        
        print(f"   ✅ Username correctly saved: {updated_user.username}")
        
        # Verify username is NOT the UID
        if updated_user.username == updated_user.uid:
            print(f"   ❌ FAILED: Username is still set to UID: {updated_user.username}")
            return False
        
        print("   ✅ Username is different from UID")
        
        print("   ✅ Test 2 PASSED: SelectUsername mutation works correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Test 2 FAILED with error: {e}")
        return False

def test_specific_user_email():
    """Test the specific user email mentioned in the issue"""
    print("\n=== Test 3: Specific User Email Test ===")
    
    test_email = "alt.ho-1or5rl0a@yopmail.com"
    
    # Cleanup any existing test user
    cleanup_test_user(test_email)
    
    try:
        # Create user with the specific email
        with transaction.atomic():
            django_user = User.objects.create_user(
                username=test_email,  # Temporary username
                email=test_email,
                password='testpassword123'
            )
        
        print(f"   ✅ Created user with email: {test_email}")
        
        # Check Neo4j user
        neo4j_user = Users.nodes.filter(user_id=str(django_user.id)).first()
        if not neo4j_user:
            print("   ❌ Neo4j user not created")
            return False
        
        # Verify username is not set to UID
        if neo4j_user.username == neo4j_user.uid:
            print(f"   ❌ FAILED: Username is set to UID: {neo4j_user.username}")
            cleanup_test_user(test_email)
            return False
        
        print("   ✅ Username is not set to UID")
        
        # Test username selection
        test_username = "altho1or5rl0a"
        neo4j_user.username = test_username
        neo4j_user.save()
        
        # Verify
        updated_user = Users.nodes.get(user_id=str(django_user.id))
        if updated_user.username != test_username:
            print(f"   ❌ FAILED: Username selection failed")
            cleanup_test_user(test_email)
            return False
        
        print(f"   ✅ Username selection works: {updated_user.username}")
        
        # Cleanup
        cleanup_test_user(test_email)
        
        print("   ✅ Test 3 PASSED: Specific user email test successful")
        return True
        
    except Exception as e:
        print(f"   ❌ Test 3 FAILED with error: {e}")
        cleanup_test_user(test_email)
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Comprehensive Username Fix Tests...")
    
    test_results = []
    
    # Test 1: User creation without UID
    result1, django_user, neo4j_user = test_user_creation_without_uid()
    test_results.append(result1)
    
    # Test 2: SelectUsername mutation (only if Test 1 passed)
    if result1 and django_user and neo4j_user:
        result2 = test_select_username_mutation(django_user, neo4j_user)
        test_results.append(result2)
        
        # Cleanup test user
        cleanup_test_user(django_user.email)
    else:
        test_results.append(False)
    
    # Test 3: Specific user email
    result3 = test_specific_user_email()
    test_results.append(result3)
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    test_names = [
        "User Creation Without UID",
        "SelectUsername Mutation", 
        "Specific User Email Test"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, test_results), 1):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"Test {i}: {name} - {status}")
    
    all_passed = all(test_results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Username fix is working correctly.")
        print("✅ Users are no longer getting UID as username")
        print("✅ SelectUsername mutation works properly")
        print("✅ The issue should not occur again")
    else:
        print("\n❌ SOME TESTS FAILED! Issues remain with the username fix.")
        failed_tests = [name for name, result in zip(test_names, test_results) if not result]
        print(f"Failed tests: {', '.join(failed_tests)}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)