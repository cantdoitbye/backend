"""
Quick Test: Verify myProfile User Field Fix
===========================================

This script quickly tests if the myProfile query returns user data correctly.

Usage:
    python test_myprofile_user.py <user_id>
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialooumph.settings')
django.setup()

from auth_manager.models import Profile, Users
from auth_manager.graphql.types import ProfileInfoType
from auth_manager.graphql.raw_queries import profile_details_query
from neomodel import db


def test_myprofile(user_id):
    """Test myProfile query for a specific user_id"""
    
    print(f"\n{'='*80}")
    print(f" Testing myProfile for user_id: {user_id}")
    print('='*80)
    
    try:
        # Step 1: Get profile
        print("\n1. Fetching Profile...")
        profile = Profile.nodes.get(user_id=user_id)
        print(f"   ✅ Profile found: {profile.uid}")
        
        # Step 2: Execute Cypher query (same as resolve_my_profile)
        print("\n2. Executing Cypher Query...")
        params = {"log_in_user_profile_uid": profile.uid}
        results, _ = db.cypher_query(profile_details_query.get_profile_details_query, params)
        
        profile_node = results[0][0] if results[0][0] else None
        user_node = results[0][1] if results[0][1] else None
        
        print(f"   Profile Node: {'✅ Found' if profile_node else '❌ Not Found'}")
        print(f"   User Node: {'✅ Found' if user_node else '❌ Not Found (will use fallback)'}")
        
        # Step 3: Apply fallback if needed
        if not user_node:
            print("\n3. Applying Fallback Logic...")
            try:
                user_obj = Users.nodes.get(user_id=user_id)
                user_node = {
                    'uid': user_obj.uid,
                    'user_id': user_obj.user_id,
                    'username': user_obj.username,
                    'email': user_obj.email,
                    'first_name': user_obj.first_name,
                    'last_name': user_obj.last_name,
                    'user_type': user_obj.user_type,
                    'created_at': user_obj.created_at.timestamp() if user_obj.created_at else None,
                    'updated_at': user_obj.updated_at.timestamp() if user_obj.updated_at else None,
                    'created_by': user_obj.created_by,
                    'updated_by': user_obj.updated_by,
                    'is_bot': user_obj.is_bot,
                    'persona': user_obj.persona,
                }
                print(f"   ✅ Fallback successful: {user_obj.username}")
            except Exception as e:
                print(f"   ❌ Fallback failed: {str(e)}")
                user_node = None
        else:
            print("\n3. Fallback Not Needed ✅")
        
        # Step 4: Create ProfileInfoType
        print("\n4. Creating ProfileInfoType...")
        onboardingStatus_node = results[0][2] if results[0][2] else None
        score_node = results[0][3] if results[0][3] else None
        interest_node = results[0][4] if results[0][4] else None
        achievement_node = results[0][5] if results[0][5] else None
        education_node = results[0][6] if results[0][6] else None
        skill_node = results[0][7] if results[0][7] else None
        experience_node = results[0][8] if results[0][8] else None
        post_count = results[0][9] if len(results[0]) > 9 and results[0][9] is not None else 0
        community_count = results[0][10] if len(results[0]) > 10 and results[0][10] is not None else 0
        connection_count = results[0][11] if len(results[0]) > 11 and results[0][11] is not None else 0
        
        profile_info = ProfileInfoType.from_neomodel(
            profile_node, user_node, onboardingStatus_node, score_node,
            interest_node, achievement_node, education_node, skill_node,
            experience_node, post_count, community_count, connection_count
        )
        
        print(f"   ✅ ProfileInfoType created")
        
        # Step 5: Check results
        print("\n5. Results:")
        print(f"   Profile UID: {profile_info.uid}")
        print(f"   Profile Name: {profile_info.name or 'null'}")
        print(f"   User Object: {'✅ Present' if profile_info.user else '❌ null'}")
        
        if profile_info.user:
            print(f"   User UID: {profile_info.user.uid}")
            print(f"   Username: {profile_info.user.username}")
            print(f"   User Name: {profile_info.user.name or 'null'}")
            print(f"   Email: {profile_info.user.email}")
        
        # Step 6: Final verdict
        print("\n" + "="*80)
        if profile_info.user:
            print(" ✅ SUCCESS: User field is populated correctly!")
            print(" ✅ The fix is working!")
        else:
            print(" ❌ FAILED: User field is still null")
            print(" ⚠️  This needs further investigation")
        print("="*80 + "\n")
        
        return profile_info.user is not None
        
    except Profile.DoesNotExist:
        print(f"\n❌ ERROR: Profile not found for user_id: {user_id}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_myprofile_user.py <user_id>")
        print("\nExample: python test_myprofile_user.py 123456")
        sys.exit(1)
    
    user_id = sys.argv[1]
    success = test_myprofile(user_id)
    sys.exit(0 if success else 1)

