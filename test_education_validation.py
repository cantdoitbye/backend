"""
Test suite for education validation functionality.

This script tests the validate_education_input function with various inputs
to ensure it properly validates the "create education" form according to the
specified requirements.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

import django
django.setup()

from auth_manager.validators.rules.education_validation import validate_education_input


def test_education_validation():
    """
    Test the education validation function with various inputs.
    """
    
    print("=" * 80)
    print("EDUCATION VALIDATION TEST SUITE")
    print("=" * 80)
    print()
    
    # Test cases based on user requirements
    test_cases = [
        # Valid inputs
        {
            "name": "Valid: Delhi University + Bachelor of Science + Computer Science",
            "input": {
                "schoolName": "Delhi University",
                "degree": "Bachelor of Science",
                "fieldOfStudy": "Computer Science"
            },
            "expected": {"valid": True, "message": "Education input is valid."}
        },
        {
            "name": "Valid: MIT + PhD + Physics",
            "input": {
                "schoolName": "MIT",
                "degree": "PhD",
                "fieldOfStudy": "Physics"
            },
            "expected": {"valid": True}
        },
        {
            "name": "Valid: Stanford University + Master's + Data Science",
            "input": {
                "schoolName": "Stanford University",
                "degree": "Master's Degree",
                "fieldOfStudy": "Data Science"
            },
            "expected": {"valid": True}
        },
        
        # Invalid: schoolName too short
        {
            "name": "Invalid: schoolName too short (1 character)",
            "input": {
                "schoolName": "A",
                "degree": "B.Tech",
                "fieldOfStudy": "CS"
            },
            "expected": {"valid": False, "error": "schoolName must be at least 2 characters long."}
        },
        
        # Invalid: degree too short
        {
            "name": "Invalid: degree too short (1 character)",
            "input": {
                "schoolName": "MIT",
                "degree": "B",
                "fieldOfStudy": "Physics"
            },
            "expected": {"valid": False, "error": "degree must be at least 2 characters long."}
        },
        
        # Invalid: fieldOfStudy too short
        {
            "name": "Invalid: fieldOfStudy too short (1 character)",
            "input": {
                "schoolName": "IIT Bombay",
                "degree": "M.Tech",
                "fieldOfStudy": "A"
            },
            "expected": {"valid": False, "error": "fieldOfStudy must be at least 2 characters long."}
        },
        
        # Invalid: schoolName only numbers
        {
            "name": "Invalid: schoolName only numbers",
            "input": {
                "schoolName": "12345",
                "degree": "B.Tech",
                "fieldOfStudy": "Engineering"
            },
            "expected": {"valid": False, "error": "schoolName should not contain only numbers or symbols."}
        },
        
        # Invalid: schoolName only symbols
        {
            "name": "Invalid: schoolName only symbols",
            "input": {
                "schoolName": "@@@###",
                "degree": "B.Tech",
                "fieldOfStudy": "Engineering"
            },
            "expected": {"valid": False, "error": "schoolName should not contain only numbers or symbols."}
        },
        
        # Invalid: Empty schoolName
        {
            "name": "Invalid: Empty schoolName",
            "input": {
                "schoolName": "",
                "degree": "B.Tech",
                "fieldOfStudy": "Engineering"
            },
            "expected": {"valid": False, "error": "schoolName field must not be empty."}
        },
        
        # Invalid: Empty degree
        {
            "name": "Invalid: Empty degree",
            "input": {
                "schoolName": "MIT",
                "degree": "",
                "fieldOfStudy": "Physics"
            },
            "expected": {"valid": False, "error": "degree field must not be empty."}
        },
        
        # Invalid: Empty fieldOfStudy
        {
            "name": "Invalid: Empty fieldOfStudy",
            "input": {
                "schoolName": "Harvard",
                "degree": "MBA",
                "fieldOfStudy": ""
            },
            "expected": {"valid": False, "error": "fieldOfStudy field must not be empty."}
        },
        
        # Invalid: schoolName too long
        {
            "name": "Invalid: schoolName exceeds 100 characters",
            "input": {
                "schoolName": "A" * 101,
                "degree": "B.Tech",
                "fieldOfStudy": "CS"
            },
            "expected": {"valid": False, "error": "schoolName must not exceed 100 characters."}
        },
        
        # Invalid: degree too long
        {
            "name": "Invalid: degree exceeds 100 characters",
            "input": {
                "schoolName": "MIT",
                "degree": "B" * 101,
                "fieldOfStudy": "Physics"
            },
            "expected": {"valid": False, "error": "degree must not exceed 100 characters."}
        },
        
        # Invalid: fieldOfStudy too long (max 50 characters)
        {
            "name": "Invalid: fieldOfStudy exceeds 50 characters",
            "input": {
                "schoolName": "Harvard",
                "degree": "PhD",
                "fieldOfStudy": "A" * 51
            },
            "expected": {"valid": False, "error": "fieldOfStudy must not exceed 50 characters."}
        },
        
        # Valid: Minimum valid length (2 characters each)
        {
            "name": "Valid: Minimum length fields (2 characters each)",
            "input": {
                "schoolName": "AB",
                "degree": "CD",
                "fieldOfStudy": "EF"
            },
            "expected": {"valid": True}
        },
        
        # Valid: Maximum valid length (100, 100, 50 characters)
        {
            "name": "Valid: Maximum length fields",
            "input": {
                "schoolName": "A" * 100,
                "degree": "B" * 100,
                "fieldOfStudy": "C" * 50
            },
            "expected": {"valid": True}
        },
        
        # Valid: schoolName with spaces and special characters
        {
            "name": "Valid: schoolName with spaces and special characters",
            "input": {
                "schoolName": "Indian Institute of Technology, Delhi",
                "degree": "B.Tech",
                "fieldOfStudy": "Computer Science"
            },
            "expected": {"valid": True}
        },
        
        # Valid: degree with dots and spaces
        {
            "name": "Valid: degree with dots and spaces",
            "input": {
                "schoolName": "Harvard",
                "degree": "M.B.A.",
                "fieldOfStudy": "Business"
            },
            "expected": {"valid": True}
        },
        
        # Valid: fieldOfStudy with hyphens
        {
            "name": "Valid: fieldOfStudy with hyphens",
            "input": {
                "schoolName": "Stanford",
                "degree": "Master's",
                "fieldOfStudy": "Computer Science & Engineering"
            },
            "expected": {"valid": True}
        },
        
        # Valid: schoolName with numbers and letters
        {
            "name": "Valid: schoolName with numbers and letters",
            "input": {
                "schoolName": "University123",
                "degree": "Bachelor's",
                "fieldOfStudy": "Mathematics"
            },
            "expected": {"valid": True}
        },
        
        # Invalid: Whitespace only in schoolName
        {
            "name": "Invalid: schoolName with only whitespace",
            "input": {
                "schoolName": "   ",
                "degree": "B.Tech",
                "fieldOfStudy": "CS"
            },
            "expected": {"valid": False, "error": "schoolName field must not be empty."}
        },
        
        # Invalid: Whitespace only in degree
        {
            "name": "Invalid: degree with only whitespace",
            "input": {
                "schoolName": "MIT",
                "degree": "   ",
                "fieldOfStudy": "Physics"
            },
            "expected": {"valid": False, "error": "degree field must not be empty."}
        },
        
        # Invalid: Whitespace only in fieldOfStudy
        {
            "name": "Invalid: fieldOfStudy with only whitespace",
            "input": {
                "schoolName": "Harvard",
                "degree": "MBA",
                "fieldOfStudy": "   "
            },
            "expected": {"valid": False, "error": "fieldOfStudy field must not be empty."}
        },
        
        # Valid: Real-world examples
        {
            "name": "Valid: IIT Delhi + B.Tech + Computer Science",
            "input": {
                "schoolName": "IIT Delhi",
                "degree": "B.Tech",
                "fieldOfStudy": "Computer Science"
            },
            "expected": {"valid": True}
        },
        {
            "name": "Valid: Oxford University + Master of Arts + Economics",
            "input": {
                "schoolName": "Oxford University",
                "degree": "Master of Arts",
                "fieldOfStudy": "Economics"
            },
            "expected": {"valid": True}
        },
        {
            "name": "Valid: Cambridge + PhD + Quantum Physics",
            "input": {
                "schoolName": "Cambridge",
                "degree": "PhD",
                "fieldOfStudy": "Quantum Physics"
            },
            "expected": {"valid": True}
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        # Run validation
        result = validate_education_input(
            test_case['input']['schoolName'],
            test_case['input']['degree'],
            test_case['input']['fieldOfStudy']
        )
        
        print(f"Result: {result}")
        
        # Check if result matches expected
        expected = test_case['expected']
        
        if expected.get('valid') == result.get('valid'):
            if result.get('valid'):
                # For valid cases, just check that valid is True
                print("✓ PASSED")
                passed += 1
            else:
                # For invalid cases, check the error message
                if expected.get('error') == result.get('error'):
                    print("✓ PASSED")
                    passed += 1
                else:
                    print(f"✗ FAILED - Expected error: '{expected.get('error')}', Got: '{result.get('error')}'")
                    failed += 1
        else:
            print(f"✗ FAILED - Expected valid={expected.get('valid')}, Got valid={result.get('valid')}")
            failed += 1
        
        print("-" * 80)
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success Rate: {(passed / len(test_cases) * 100):.1f}%")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_education_validation()
    sys.exit(0 if success else 1)

