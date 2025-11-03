"""
Test Script for Sub-Community Content Section Creation Fix
==========================================================

This script tests the fix for creating content sections (goals, activities, 
achievements, affiliations) in sibling-child sub-communities.

Bug: "Failed to create achievement, goal, activity, and affiliation"
Fix: Use correct member relationship (sub_community_members) for SubCommunity instances

Usage:
    python test_subcommunity_content_sections.py

Prerequisites:
    - Django environment must be configured
    - Test user must exist and have admin rights in a test sub-community
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialooumph.settings')
django.setup()

from datetime import datetime
from community.models import Community, SubCommunity, SubCommunityMembership
from auth_manager.models import Users
from community.graphql.mutations import (
    CreateCommunityGoal,
    CreateCommunityActivity,
    CreateCommunityAffiliation,
    CreateCommunityAchievement
)


class TestContext:
    """Mock GraphQL context for testing"""
    def __init__(self, user, user_id):
        self.user = user
        self.payload = {'user_id': user_id}


class TestInfo:
    """Mock GraphQL info object for testing"""
    def __init__(self, user, user_id):
        self.context = TestContext(user, user_id)


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 80}")
    print(f" {title}")
    print('=' * 80)


def print_result(test_name, success, message=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} | {test_name}")
    if message:
        print(f"     └─ {message}")


def setup_test_data():
    """
    Setup test data: community, sub-community, and test user
    Returns: (community, subcommunity, user)
    """
    print_section("Setting Up Test Data")
    
    # Get or create test user
    try:
        user = Users.nodes.get(username="test_admin")
        print(f"✓ Found test user: {user.username} (ID: {user.user_id})")
    except Users.DoesNotExist:
        print("❌ Test user 'test_admin' not found. Please create a test user first.")
        return None, None, None
    
    # Get or create test community
    try:
        community = Community.nodes.get(name="Test Community")
        print(f"✓ Found test community: {community.name} (UID: {community.uid})")
    except Community.DoesNotExist:
        print("❌ Test community not found. Please create a test community first.")
        return None, None, None
    
    # Get or create test sub-community
    try:
        subcommunity = SubCommunity.nodes.get(name="Test Sub-Community")
        print(f"✓ Found test sub-community: {subcommunity.name} (UID: {subcommunity.uid})")
    except SubCommunity.DoesNotExist:
        print("Creating test sub-community...")
        subcommunity = SubCommunity(
            name="Test Sub-Community",
            description="Test sub-community for content section testing",
            sub_community_type="sibling community",
            sub_community_group_type="test",
            sub_community_circle="outer circle",
            category="test"
        )
        subcommunity.save()
        subcommunity.created_by.connect(user)
        subcommunity.parent_community.connect(community)
        community.sibling_communities.connect(subcommunity)
        print(f"✓ Created test sub-community: {subcommunity.name} (UID: {subcommunity.uid})")
    
    # Ensure user is admin of sub-community
    membership = None
    for mem in subcommunity.sub_community_members.all():
        if mem.user.is_connected(user):
            membership = mem
            break
    
    if not membership:
        print("Creating admin membership for test user...")
        membership = SubCommunityMembership(
            is_admin=True,
            can_message=True,
            is_notification_muted=False
        )
        membership.save()
        membership.user.connect(user)
        membership.sub_community.connect(subcommunity)
        subcommunity.sub_community_members.connect(membership)
        print("✓ Created admin membership")
    elif not membership.is_admin:
        print("Updating membership to admin...")
        membership.is_admin = True
        membership.save()
        print("✓ Updated membership to admin")
    else:
        print("✓ User is already admin of sub-community")
    
    return community, subcommunity, user


def test_create_goal_in_subcommunity(subcommunity, user):
    """Test creating a goal in a sub-community"""
    print_section("Test 1: Create Goal in Sub-Community")
    
    try:
        from types import SimpleNamespace
        
        # Mock input
        input_data = SimpleNamespace(
            community_uid=subcommunity.uid,
            name="Test Goal for Sub-Community",
            description="This is a test goal created in a sub-community",
            file_id=[]
        )
        
        # Mock info object
        info = TestInfo(user, user.user_id)
        
        # Create mutation instance and execute
        mutation = CreateCommunityGoal()
        result = mutation.mutate(info, input_data)
        
        if result.success:
            print_result("Create Goal", True, f"Goal UID: {result.goal.uid}")
            return True
        else:
            print_result("Create Goal", False, f"Error: {result.message}")
            return False
            
    except Exception as e:
        print_result("Create Goal", False, f"Exception: {str(e)}")
        return False


def test_create_activity_in_subcommunity(subcommunity, user):
    """Test creating an activity in a sub-community"""
    print_section("Test 2: Create Activity in Sub-Community")
    
    try:
        from types import SimpleNamespace
        
        # Mock input
        input_data = SimpleNamespace(
            community_uid=subcommunity.uid,
            name="Test Activity for Sub-Community",
            description="This is a test activity created in a sub-community",
            activity_type="meetup",
            file_id=[]
        )
        
        # Mock info object
        info = TestInfo(user, user.user_id)
        
        # Create mutation instance and execute
        mutation = CreateCommunityActivity()
        result = mutation.mutate(info, input_data)
        
        if result.success:
            print_result("Create Activity", True, f"Activity UID: {result.activity.uid}")
            return True
        else:
            print_result("Create Activity", False, f"Error: {result.message}")
            return False
            
    except Exception as e:
        print_result("Create Activity", False, f"Exception: {str(e)}")
        return False


def test_create_affiliation_in_subcommunity(subcommunity, user):
    """Test creating an affiliation in a sub-community"""
    print_section("Test 3: Create Affiliation in Sub-Community")
    
    try:
        from types import SimpleNamespace
        
        # Mock input
        input_data = SimpleNamespace(
            community_uid=subcommunity.uid,
            entity="Test Partner Organization",
            date=datetime.now(),
            subject="Partnership agreement for testing",
            file_id=[]
        )
        
        # Mock info object
        info = TestInfo(user, user.user_id)
        
        # Create mutation instance and execute
        mutation = CreateCommunityAffiliation()
        result = mutation.mutate(info, input_data)
        
        if result.success:
            print_result("Create Affiliation", True, f"Affiliation UID: {result.affiliation.uid}")
            return True
        else:
            print_result("Create Affiliation", False, f"Error: {result.message}")
            return False
            
    except Exception as e:
        print_result("Create Affiliation", False, f"Exception: {str(e)}")
        return False


def test_create_achievement_in_subcommunity(subcommunity, user):
    """Test creating an achievement in a sub-community"""
    print_section("Test 4: Create Achievement in Sub-Community")
    
    try:
        from types import SimpleNamespace
        
        # Mock input
        input_data = SimpleNamespace(
            community_uid=subcommunity.uid,
            entity="Test Achievement Award",
            date=datetime.now(),
            subject="Won an award for testing excellence",
            file_id=[]
        )
        
        # Mock info object
        info = TestInfo(user, user.user_id)
        
        # Create mutation instance and execute
        mutation = CreateCommunityAchievement()
        result = mutation.mutate(info, input_data)
        
        if result.success:
            print_result("Create Achievement", True, f"Achievement UID: {result.achievement.uid}")
            return True
        else:
            print_result("Create Achievement", False, f"Error: {result.message}")
            return False
            
    except Exception as e:
        print_result("Create Achievement", False, f"Exception: {str(e)}")
        return False


def test_create_goal_in_regular_community(community, user):
    """Test creating a goal in a regular community (regression test)"""
    print_section("Test 5: Create Goal in Regular Community (Regression)")
    
    try:
        from types import SimpleNamespace
        
        # Mock input
        input_data = SimpleNamespace(
            community_uid=community.uid,
            name="Test Goal for Community",
            description="This is a test goal created in a regular community",
            file_id=[]
        )
        
        # Mock info object
        info = TestInfo(user, user.user_id)
        
        # Create mutation instance and execute
        mutation = CreateCommunityGoal()
        result = mutation.mutate(info, input_data)
        
        if result.success:
            print_result("Create Goal (Regular Community)", True, f"Goal UID: {result.goal.uid}")
            return True
        else:
            print_result("Create Goal (Regular Community)", False, f"Error: {result.message}")
            return False
            
    except Exception as e:
        print_result("Create Goal (Regular Community)", False, f"Exception: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print_section("Sub-Community Content Section Creation Tests")
    print("Testing fix for bug: 'Failed to create achievement, goal, activity, and affiliation'")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup test data
    community, subcommunity, user = setup_test_data()
    
    if not all([community, subcommunity, user]):
        print("\n❌ Test setup failed. Cannot proceed with tests.")
        return
    
    # Run tests
    results = []
    
    results.append(("Goal in Sub-Community", test_create_goal_in_subcommunity(subcommunity, user)))
    results.append(("Activity in Sub-Community", test_create_activity_in_subcommunity(subcommunity, user)))
    results.append(("Affiliation in Sub-Community", test_create_affiliation_in_subcommunity(subcommunity, user)))
    results.append(("Achievement in Sub-Community", test_create_achievement_in_subcommunity(subcommunity, user)))
    results.append(("Goal in Regular Community", test_create_goal_in_regular_community(community, user)))
    
    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Tests Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The fix is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        print("\nFailed tests:")
        for name, result in results:
            if not result:
                print(f"  - {name}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test execution failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

