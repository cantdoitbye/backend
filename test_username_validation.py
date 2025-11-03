#!/usr/bin/env python3
"""
Test script to verify username validation fix.
This script tests the validate_username function with various inputs
to ensure the bug is fixed and validation works correctly.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_manager.validators.rules.string_validation import validate_username
from graphql import GraphQLError

def test_username_validation():
    """
    Test the username validation function with various inputs.
    """
    print("🧪 Testing Username Validation Fix...\n")
    
    # Test cases: (username, expected_result, description)
    test_cases = [
        # Valid usernames (3-9 characters)
        ("abc", True, "3 characters - minimum boundary"),
        ("test", True, "4 characters - should pass"),
        ("user1", True, "5 characters - should pass"),
        ("abcdef", True, "6 characters - should pass"),
        ("user123", True, "7 characters - should pass"),
        ("testuser", True, "8 characters - should pass"),
        ("test_user", True, "9 characters with underscore - maximum boundary"),
        
        # Invalid usernames (too short)
        ("ab", False, "2 characters - too short"),
        ("a", False, "1 character - too short"),
        ("", False, "Empty string - too short"),
        
        # Invalid usernames (too long)
        ("nitinooump", False, "Original failing case - 10 characters - too long"),
        ("a1b2c3d4e5", False, "10 characters mixed - too long"),
        ("verylongusername", False, "16 characters - too long"),
        ("a1b2c3d4e5f", False, "11 characters - too long"),
        ("toolongusername123", False, "18 characters - too long"),
        
        # Invalid characters (should fail regardless of length)
        ("user@name", False, "Contains @ symbol"),
        ("user name", False, "Contains space"),
        ("user-name", False, "Contains hyphen"),
        ("user.name", False, "Contains dot"),
        ("user#name", False, "Contains hash"),
    ]
    
    passed = 0
    failed = 0
    
    for username, expected_valid, description in test_cases:
        try:
            result = validate_username(username)
            if expected_valid:
                print(f"✅ PASS: '{username}' - {description}")
                passed += 1
            else:
                print(f"❌ FAIL: '{username}' - {description} (Expected to fail but passed)")
                failed += 1
        except GraphQLError as e:
            if not expected_valid:
                print(f"✅ PASS: '{username}' - {description} (Correctly rejected: {str(e)})")
                passed += 1
            else:
                print(f"❌ FAIL: '{username}' - {description} (Expected to pass but failed: {str(e)})")
                failed += 1
        except Exception as e:
            print(f"❌ ERROR: '{username}' - {description} (Unexpected error: {str(e)})")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Username validation is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the validation logic.")
        return False

def test_original_failing_case():
    """
    Specifically test the original failing case from the GraphQL mutation.
    """
    print("\n🎯 Testing Original Failing Case...")
    
    username = "nitinooump"
    print(f"Testing username: '{username}' (length: {len(username)})")
    
    try:
        result = validate_username(username)
        print(f"❌ FAILED: Username '{username}' should be invalid (too long)!")
        print(f"   Length: {len(username)} characters (exceeds 3-9 range)")
        return False
    except GraphQLError as e:
        print(f"✅ SUCCESS: Username '{username}' correctly rejected: {str(e)}")
        print(f"   Length: {len(username)} characters (exceeds 3-9 range)")
        return True
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("USERNAME VALIDATION FIX TEST")
    print("=" * 60)
    
    # Test the original failing case first
    original_case_passed = test_original_failing_case()
    
    # Run comprehensive tests
    all_tests_passed = test_username_validation()
    
    print("\n" + "=" * 60)
    if original_case_passed and all_tests_passed:
        print("🎉 OVERALL RESULT: ALL TESTS PASSED - BUG IS FIXED!")
        sys.exit(0)
    else:
        print("❌ OVERALL RESULT: SOME TESTS FAILED - BUG NOT FULLY FIXED")
        sys.exit(1)
    print("=" * 60)