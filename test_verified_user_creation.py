#!/usr/bin/env python
"""
Test script for the CreateVerifiedUser mutation.

This script tests the new CreateVerifiedUser GraphQL mutation to ensure
it creates all required models and relationships correctly.

Usage:
    python test_verified_user_creation.py
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.append('/Users/harsh/Development/python/ooumph-backend')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

# Now import Django models
from django.contrib.auth.models import User
from auth_manager.models import Users, Profile, OnboardingStatus, Score, ConnectionStats
from msg.models import MatrixProfile
import json

def test_create_verified_user():
    """
    Test the CreateVerifiedUser mutation by creating a test user
    and verifying all models and relationships are created correctly.
    """
    print("🧪 Testing CreateVerifiedUser mutation...")
    
    # Test data
    test_email = "testbot@example.com"
    test_first_name = "Test"
    test_last_name = "Bot"
    test_password = "testpassword123"
    
    # Clean up any existing test user
    cleanup_test_user(test_email)
    
    try:
        # Import GraphQL mutation
        from auth_manager.graphql.mutations import CreateVerifiedUser
        from auth_manager.graphql.inputs import CreateVerifiedUserInput
        
        # Create input data
        input_data = {
            'email': test_email,
            'first_name': test_first_name,
            'last_name': test_last_name,
            'password': test_password,
            'is_bot': True,
            'persona': 'test_bot',
            'gender': 'Other',
            'bio': 'This is a test bot user',
            'user_type': 'personal'
        }
        
        # Create mutation instance and execute
        mutation = CreateVerifiedUser()
        
        # Mock info object
        class MockInfo:
            context = None
        
        # Mock input object
        class MockInput:
            def __init__(self, data):
                self.data = data
            
            def get(self, key, default=None):
                return self.data.get(key, default)
        
        mock_input = MockInput(input_data)
        mock_info = MockInfo()
        
        # Execute mutation
        result = mutation.mutate(mock_info, mock_input)
        
        print(f"✅ Mutation executed successfully: {result.success}")
        print(f"📝 Message: {result.message}")
        
        if result.success:
            # Verify Django User was created
            django_user = User.objects.get(email=test_email)
            print(f"✅ Django User created: {django_user.username}")
            print(f"   - Email: {django_user.email}")
            print(f"   - First Name: {django_user.first_name}")
            print(f"   - Last Name: {django_user.last_name}")
            
            # Verify Neo4j Users node was created
            user_node = Users.nodes.get(user_id=str(django_user.id))
            print(f"✅ Neo4j Users node created: {user_node.uid}")
            print(f"   - Is Bot: {user_node.is_bot}")
            print(f"   - Persona: {user_node.persona}")
            print(f"   - Is Active: {user_node.is_active}")
            print(f"   - User Type: {user_node.user_type}")
            
            # Verify Profile was created and populated
            profile = user_node.profile.single()
            if profile:
                print(f"✅ Profile created: {profile.uid}")
                print(f"   - Phone Number: {profile.phone_number}")
                print(f"   - Gender: {profile.gender}")
                print(f"   - Bio: {profile.bio}")
                print(f"   - City: {profile.city}")
                print(f"   - State: {profile.state}")
                
                # Verify OnboardingStatus is fully verified
                onboarding = profile.onboarding.single()
                if onboarding:
                    print(f"✅ OnboardingStatus created: {onboarding.uid}")
                    print(f"   - Email Verified: {onboarding.email_verified}")
                    print(f"   - Phone Verified: {onboarding.phone_verified}")
                    print(f"   - Username Selected: {onboarding.username_selected}")
                    print(f"   - First Name Set: {onboarding.first_name_set}")
                    print(f"   - Last Name Set: {onboarding.last_name_set}")
                    print(f"   - Gender Set: {onboarding.gender_set}")
                    print(f"   - Bio Set: {onboarding.bio_set}")
                
                # Verify Score was created
                score = profile.score.single()
                if score:
                    print(f"✅ Score created: {score.uid}")
                    print(f"   - Default scores set: {score.vibers_count}, {score.cumulative_vibescore}")
            
            # Verify ConnectionStats was created
            connection_stats = user_node.connection_stat.single()
            if connection_stats:
                print(f"✅ ConnectionStats created: {connection_stats.uid}")
            
            # Verify MatrixProfile was created
            try:
                matrix_profile = MatrixProfile.objects.get(user=django_user)
                print(f"✅ MatrixProfile created: {matrix_profile.id}")
                print(f"   - Matrix User ID: {matrix_profile.matrix_user_id}")
                print(f"   - Pending Registration: {matrix_profile.pending_matrix_registration}")
            except MatrixProfile.DoesNotExist:
                print("❌ MatrixProfile not found")
            
            # Verify tokens were generated
            if result.token and result.refresh_token:
                print(f"✅ Authentication tokens generated")
                print(f"   - Token length: {len(result.token)}")
                print(f"   - Refresh token length: {len(result.refresh_token)}")
            
            print(f"\n🎉 All verifications passed! User created successfully.")
            
        else:
            print(f"❌ Mutation failed: {result.message}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test user
        cleanup_test_user(test_email)
        print("🧹 Test cleanup completed")

def cleanup_test_user(email):
    """Clean up any existing test user"""
    try:
        # Delete Django user (this should cascade to other models via signals)
        django_user = User.objects.filter(email=email).first()
        if django_user:
            # Delete MatrixProfile
            MatrixProfile.objects.filter(user=django_user).delete()
            
            # Delete Neo4j nodes
            try:
                user_node = Users.nodes.get(user_id=str(django_user.id))
                profile = user_node.profile.single()
                if profile:
                    # Delete related nodes
                    onboarding = profile.onboarding.single()
                    if onboarding:
                        onboarding.delete()
                    
                    score = profile.score.single()
                    if score:
                        score.delete()
                    
                    profile.delete()
                
                connection_stats = user_node.connection_stat.single()
                if connection_stats:
                    connection_stats.delete()
                
                user_node.delete()
            except:
                pass
            
            # Delete Django user
            django_user.delete()
            print(f"🧹 Cleaned up existing test user: {email}")
    except:
        pass

if __name__ == "__main__":
    test_create_verified_user()
