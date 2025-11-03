#!/usr/bin/env python3
"""
Test script to verify CommunityActivity validation fixes.

This script tests that the validation logic for CommunityActivity mutations
works correctly according to the specified requirements:
- name: 2-100 characters
- description: 5-200 characters
- community_uid: required
- date: ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graphql import GraphQLError
from community.graphql.inputs import CreateCommunityActivityInput, UpdateCommunityActivityInput
from auth_manager.validators.custom_graphql_validator import NonSpecialCharacterString2_100, NonSpecialCharacterString5_200, DateTimeScalar, String

def test_name_validation():
    """Test that name field accepts 2-100 characters"""
    print("Testing name validation (2-100 characters)...")

    # Test scalar validator directly
    name_validator = NonSpecialCharacterString2_100.add_option("name", "CreateCommunityActivity")()

    # Test valid name values
    valid_names = [
        "AB",  # 2 characters - minimum
        "Community Activity",  # Normal length
        "A" * 100,  # 100 characters - maximum
    ]

    for name in valid_names:
        try:
            result = name_validator.parse_value(name)
            print(f"✓ Name '{name[:20]}...' (len={len(name)}) accepted")
        except GraphQLError as e:
            print(f"✗ Name '{name[:20]}...' (len={len(name)}) rejected: {e}")

    # Test invalid name values
    invalid_names = [
        "A",  # 1 character - too short
        "A" * 101,  # 101 characters - too long
    ]

    for name in invalid_names:
        try:
            result = name_validator.parse_value(name)
            print(f"✗ Name '{name[:20]}...' (len={len(name)}) should have been rejected")
        except GraphQLError as e:
            print(f"✓ Name '{name[:20]}...' (len={len(name)}) correctly rejected: {e}")

    # Also test with input object
    print("\nTesting name validation with input object...")
    for name in valid_names:
        try:
            input_data = CreateCommunityActivityInput(
                name=name,
                description="Test description that is long enough for validation",
                community_uid="test-community-uid"
            )
            print(f"✓ Input object with name '{name[:20]}...' (len={len(name)}) accepted")
        except GraphQLError as e:
            print(f"✗ Input object with name '{name[:20]}...' (len={len(name)}) rejected: {e}")


def test_description_validation():
    """Test that description field accepts 5-200 characters"""
    print("\nTesting description validation (5-200 characters)...")

    # Test scalar validator directly
    description_validator = NonSpecialCharacterString5_200.add_option("description", "CreateCommunityActivity")()

    # Test valid description values
    valid_descriptions = [
        "Test description",  # 16 characters - minimum + 1
        "This is a longer description that should be accepted for community activities",  # Normal length
        "D" * 200,  # 200 characters - maximum
    ]

    for description in valid_descriptions:
        try:
            result = description_validator.parse_value(description)
            print(f"✓ Description '{description[:20]}...' (len={len(description)}) accepted")
        except GraphQLError as e:
            print(f"✗ Description '{description[:20]}...' (len={len(description)}) rejected: {e}")

    # Test invalid description values
    invalid_descriptions = [
        "Test",  # 4 characters - too short
        "D" * 201,  # 201 characters - too long
    ]

    for description in invalid_descriptions:
        try:
            result = description_validator.parse_value(description)
            print(f"✗ Description '{description[:20]}...' (len={len(description)}) should have been rejected")
        except GraphQLError as e:
            print(f"✓ Description '{description[:20]}...' (len={len(description)}) correctly rejected: {e}")


def test_date_validation():
    """Test that date field accepts valid ISO 8601 format"""
    print("\nTesting date validation (ISO 8601 format)...")

    # Test scalar validator directly
    date_validator = DateTimeScalar.add_option("date", "CreateCommunityActivity")()

    # Test valid date values
    valid_dates = [
        "2023-01-01T00:00:00",  # Valid ISO format
        "2025-10-22T15:30:45",  # Current date/time format
        "1990-12-31T23:59:59",  # End of day
    ]

    for date in valid_dates:
        try:
            result = date_validator.parse_value(date)
            print(f"✓ Date '{date}' accepted")
        except GraphQLError as e:
            print(f"✗ Date '{date}' rejected: {e}")

    # Test invalid date values
    invalid_dates = [
        "2023-01-01",  # Missing time part
        "01/01/2023",  # Wrong format
        "2023-13-01T00:00:00",  # Invalid month
        "2023-01-32T00:00:00",  # Invalid day
        "2023-01-01T25:00:00",  # Invalid hour
        "invalid-date",  # Completely wrong format
    ]

    for date in invalid_dates:
        try:
            result = date_validator.parse_value(date)
            print(f"✗ Date '{date}' should have been rejected")
        except GraphQLError as e:
            print(f"✓ Date '{date}' correctly rejected: {e}")


def test_community_uid_required():
    """Test that community_uid is required"""
    print("\nTesting community_uid required validation...")

    # Test scalar validator directly
    uid_validator = String.add_option("communityUid", "CreateCommunityActivity")()

    # Test valid community_uid values
    valid_uids = [
        "test-community-uid",
        "community-123",
        "subcommunity-abc-def"
    ]

    for uid in valid_uids:
        try:
            result = uid_validator.parse_value(uid)
            print(f"✓ Community UID '{uid}' accepted")
        except GraphQLError as e:
            print(f"✗ Community UID '{uid}' rejected: {e}")

    # Test missing/None community_uid
    try:
        result = uid_validator.parse_value(None)
        print("✗ None community_uid should have been rejected")
    except GraphQLError as e:
        print(f"✓ None community_uid correctly rejected: {e}")

    # Test with input object
    print("\nTesting community_uid with input object...")
    try:
        input_data = CreateCommunityActivityInput(
            name="Test Activity",
            description="Test description that is long enough"
            # missing community_uid
        )
        print("✗ Missing community_uid should have been rejected")
    except Exception as e:
        print(f"✓ Missing community_uid correctly rejected: {e}")


def test_update_validation():
    """Test that UpdateCommunityActivityInput validation also works"""
    print("\nTesting UpdateCommunityActivityInput validation...")

    # Test scalar validator directly for update name
    update_name_validator = NonSpecialCharacterString2_100.add_option("name", "UpdateCommunityActivity")()

    # Test valid update name
    try:
        result = update_name_validator.parse_value("Updated Activity Name")
        print("✓ Valid update name accepted")
    except GraphQLError as e:
        print(f"✗ Valid update name rejected: {e}")

    # Test invalid name in update
    try:
        result = update_name_validator.parse_value("A")  # Too short
        print("✗ Invalid name in UpdateCommunityActivityInput should have been rejected")
    except GraphQLError as e:
        print(f"✓ Invalid name in UpdateCommunityActivityInput correctly rejected: {e}")

    # Test with input object
    print("\nTesting UpdateCommunityActivityInput with input object...")
    try:
        input_data = UpdateCommunityActivityInput(
            uid="test-activity-uid",
            name="Updated Activity Name",
            description="Updated description that meets requirements"
        )
        print("✓ Valid UpdateCommunityActivityInput accepted")
    except GraphQLError as e:
        print(f"✗ Valid UpdateCommunityActivityInput rejected: {e}")

    # Test invalid name in update input object
    try:
        input_data = UpdateCommunityActivityInput(
            uid="test-activity-uid",
            name="A",  # Too short
            description="Updated description that meets requirements"
        )
        print("✗ Invalid name in UpdateCommunityActivityInput should have been rejected")
    except GraphQLError as e:
        print(f"✓ Invalid name in UpdateCommunityActivityInput correctly rejected: {e}")


def main():
    """Run all validation tests"""
    print("=== CommunityActivity Validation Tests ===\n")

    test_name_validation()
    test_description_validation()
    test_date_validation()
    test_community_uid_required()
    test_update_validation()

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()

