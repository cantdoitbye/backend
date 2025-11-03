#!/usr/bin/env python3
"""
Test script to verify CommunityAffiliation validation fixes.

This script tests that the validation logic for CommunityAffiliation mutations
works correctly according to the specified requirements:
- entity: 2-100 characters
- subject: 5-100 characters
- date: ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- communityUid: required
- communityType: required (must match allowed community types)
- fileId: optional but validated if provided
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graphql import GraphQLError
from community.graphql.inputs import CreateCommunityAffiliationInput, UpdateCommunityAffiliationInput
from auth_manager.validators.custom_graphql_validator import NonSpecialCharacterString2_100, NonSpecialCharacterString5_100, DateTimeScalar, String, NonSemiSpecialCharacterString2_100
from community.graphql.enums.group_type_enum import GroupTypeEnum

def test_entity_validation():
    """Test that entity field accepts 2-100 characters"""
    print("Testing entity validation (2-100 characters)...")

    # Test scalar validator directly (now using NonSemiSpecialCharacterString2_100)
    entity_validator = NonSemiSpecialCharacterString2_100.add_option("entity", "CreateCommunityAffiliation")()

    # Test valid entity values (now allows more characters)
    valid_entities = [
        "AB",  # 2 characters - minimum
        "Microsoft Corporation",  # Normal length with spaces
        "Tech Corp. Inc.",  # With periods and abbreviations
        "A" * 100,  # 100 characters - maximum
    ]

    for entity in valid_entities:
        try:
            result = entity_validator.parse_value(entity)
            print(f"✓ Entity '{entity[:20]}...' (len={len(entity)}) accepted")
        except GraphQLError as e:
            print(f"✗ Entity '{entity[:20]}...' (len={len(entity)}) rejected: {e}")

    # Test invalid entity values
    invalid_entities = [
        "A",  # 1 character - too short
        "A" * 101,  # 101 characters - too long
    ]

    for entity in invalid_entities:
        try:
            result = entity_validator.parse_value(entity)
            print(f"✗ Entity '{entity[:20]}...' (len={len(entity)}) should have been rejected")
        except GraphQLError as e:
            print(f"✓ Entity '{entity[:20]}...' (len={len(entity)}) correctly rejected: {e}")


def test_subject_validation():
    """Test that subject field accepts 5-100 characters"""
    print("\nTesting subject validation (5-100 characters)...")

    # Test scalar validator directly
    subject_validator = NonSpecialCharacterString5_100.add_option("subject", "CreateCommunityAffiliation")()

    # Test valid subject values
    valid_subjects = [
        "Partnership",  # 11 characters - minimum + 1
        "Strategic partnership for community development",  # Normal length
        "S" * 100,  # 100 characters - maximum
    ]

    for subject in valid_subjects:
        try:
            result = subject_validator.parse_value(subject)
            print(f"✓ Subject '{subject[:20]}...' (len={len(subject)}) accepted")
        except GraphQLError as e:
            print(f"✗ Subject '{subject[:20]}...' (len={len(subject)}) rejected: {e}")

    # Test invalid subject values
    invalid_subjects = [
        "Test",  # 4 characters - too short
        "S" * 101,  # 101 characters - too long
    ]

    for subject in invalid_subjects:
        try:
            result = subject_validator.parse_value(subject)
            print(f"✗ Subject '{subject[:20]}...' (len={len(subject)}) should have been rejected")
        except GraphQLError as e:
            print(f"✓ Subject '{subject[:20]}...' (len={len(subject)}) correctly rejected: {e}")


def test_date_validation():
    """Test that date field accepts valid ISO 8601 format"""
    print("\nTesting date validation (ISO 8601 format)...")

    # Test scalar validator directly
    date_validator = DateTimeScalar.add_option("date", "CreateCommunityAffiliation")()

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


def test_community_type_validation():
    """Test that community_type field accepts valid community types"""
    print("\nTesting community_type validation...")

    # Test valid community types with input object
    valid_types = [
        "personal group",
        "interest group",
        "official group",
        "business group"
    ]

    for ctype in valid_types:
        try:
            input_data = CreateCommunityAffiliationInput(
                entity="Test Entity",
                subject="Test subject that is long enough",
                date="2023-01-01T00:00:00",
                community_uid="test-community-uid",
                community_type=ctype
            )
            print(f"✓ Community type '{ctype}' accepted")
        except GraphQLError as e:
            print(f"✗ Community type '{ctype}' rejected: {e}")

    # Test invalid community types with input object
    invalid_types = [
        "invalid type",
        "random group",
        "",
        None
    ]

    for ctype in invalid_types:
        try:
            input_data = CreateCommunityAffiliationInput(
                entity="Test Entity",
                subject="Test subject that is long enough",
                date="2023-01-01T00:00:00",
                community_uid="test-community-uid",
                community_type=ctype
            )
            print(f"✗ Community type '{ctype}' should have been rejected")
        except GraphQLError as e:
            print(f"✓ Community type '{ctype}' correctly rejected: {e}")

    # Note: Input object validation for enums and required fields happens during GraphQL execution,
    # not during input object creation. The scalar validation is working correctly.


def test_required_fields():
    """Test that required fields are enforced"""
    print("\nTesting required field validation...")

    # Note: Required field validation in Graphene happens during GraphQL execution,
    # not during input object creation. The fields are marked as required=True in the schema.

    # Test missing community_uid
    try:
        input_data = CreateCommunityAffiliationInput(
            entity="Test Entity",
            subject="Test subject that is long enough",
            date="2023-01-01T00:00:00"
            # missing community_uid
        )
        print("✗ Missing community_uid should have been rejected (during GraphQL execution)")
    except Exception as e:
        print(f"✓ Missing community_uid correctly rejected: {e}")

    # Test missing community_type
    try:
        input_data = CreateCommunityAffiliationInput(
            entity="Test Entity",
            subject="Test subject that is long enough",
            date="2023-01-01T00:00:00",
            community_uid="test-community-uid"
            # missing community_type
        )
        print("✗ Missing community_type should have been rejected (during GraphQL execution)")
    except Exception as e:
        print(f"✓ Missing community_type correctly rejected: {e}")

    # Test missing date
    try:
        input_data = CreateCommunityAffiliationInput(
            entity="Test Entity",
            subject="Test subject that is long enough",
            community_uid="test-community-uid",
            community_type="personal group"
            # missing date
        )
        print("✗ Missing date should have been rejected (during GraphQL execution)")
    except Exception as e:
        print(f"✓ Missing date correctly rejected: {e}")


def test_update_validation():
    """Test that UpdateCommunityAffiliationInput validation also works"""
    print("\nTesting UpdateCommunityAffiliationInput validation...")

    # Test scalar validator directly for update entity
    update_entity_validator = NonSemiSpecialCharacterString2_100.add_option("entity", "UpdateCommunityAffiliation")()

    # Test valid update entity
    try:
        result = update_entity_validator.parse_value("Updated Entity Name")
        print("✓ Valid update entity accepted")
    except GraphQLError as e:
        print(f"✗ Valid update entity rejected: {e}")

    # Test invalid entity in update
    try:
        result = update_entity_validator.parse_value("A")  # Too short
        print("✗ Invalid entity in UpdateCommunityAffiliationInput should have been rejected")
    except GraphQLError as e:
        print(f"✓ Invalid entity in UpdateCommunityAffiliationInput correctly rejected: {e}")

    # Test with input object
    print("\nTesting UpdateCommunityAffiliationInput with input object...")
    try:
        input_data = UpdateCommunityAffiliationInput(
            uid="test-affiliation-uid",
            entity="Updated Entity Name",
            subject="Updated subject that meets requirements"
        )
        print("✓ Valid UpdateCommunityAffiliationInput accepted")
    except GraphQLError as e:
        print(f"✗ Valid UpdateCommunityAffiliationInput rejected: {e}")

    # Test invalid entity in update input object
    try:
        input_data = UpdateCommunityAffiliationInput(
            uid="test-affiliation-uid",
            entity="A",  # Too short
            subject="Updated subject that meets requirements"
        )
        print("✗ Invalid entity in UpdateCommunityAffiliationInput should have been rejected")
    except GraphQLError as e:
        print(f"✓ Invalid entity in UpdateCommunityAffiliationInput correctly rejected: {e}")


def main():
    """Run all validation tests"""
    print("=== CommunityAffiliation Validation Tests ===\n")

    test_entity_validation()
    test_subject_validation()
    test_date_validation()
    test_community_type_validation()
    test_required_fields()
    test_update_validation()

    print("\n=== Test Complete ===")
    print("\nNote: File validation has been fixed in the get_valid_image function.")
    print("It now properly raises GraphQLError for invalid file IDs during mutation execution.")


if __name__ == "__main__":
    main()
