"""
Test suite for skill validation functionality.

This script tests the validate_skill_input function with various inputs
to ensure it properly validates the "create skill" form according to the
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

from auth_manager.validators.rules.skill_validation import validate_skill_input


def test_skill_validation():
    """
    Test the skill validation function with various inputs.
    """
    
    print("=" * 80)
    print("SKILL VALIDATION TEST SUITE")
    print("=" * 80)
    print()
    
    # Test cases based on user requirements
    test_cases = [
        # Valid inputs
        {
            "name": "Valid: Harvard University + Machine Learning",
            "input": {"From": "Harvard University", "What": "Machine Learning"},
            "expected": {"valid": True, "message": "Skill input is valid."}
        },
        {
            "name": "Valid: Google + Software Engineering",
            "input": {"From": "Google", "What": "Software Engineering"},
            "expected": {"valid": True}
        },
        {
            "name": "Valid: MIT + Data Science",
            "input": {"From": "MIT", "What": "Data Science"},
            "expected": {"valid": True}
        },
        
        # Invalid: From field too short
        {
            "name": "Invalid: From field too short (1 character)",
            "input": {"From": "A", "What": "ML"},
            "expected": {"valid": False, "error": "From must be at least 2 characters long."}
        },
        
        # Invalid: What field too short
        {
            "name": "Invalid: What field too short (1 character)",
            "input": {"From": "Google", "What": "A"},
            "expected": {"valid": False, "error": "What must be at least 2 characters long."}
        },
        
        # Invalid: From field only numbers
        {
            "name": "Invalid: From field only numbers",
            "input": {"From": "12345", "What": "Programming"},
            "expected": {"valid": False, "error": "From should not contain only numbers or symbols."}
        },
        
        # Invalid: From field only symbols
        {
            "name": "Invalid: From field only symbols",
            "input": {"From": "@@@###", "What": "Programming"},
            "expected": {"valid": False, "error": "From should not contain only numbers or symbols."}
        },
        
        # Invalid: Empty From field
        {
            "name": "Invalid: Empty From field",
            "input": {"From": "", "What": "Programming"},
            "expected": {"valid": False, "error": "From field must not be empty."}
        },
        
        # Invalid: Empty What field
        {
            "name": "Invalid: Empty What field",
            "input": {"From": "Stanford", "What": ""},
            "expected": {"valid": False, "error": "What field must not be empty."}
        },
        
        # Invalid: From field too long
        {
            "name": "Invalid: From field exceeds 100 characters",
            "input": {
                "From": "A" * 101,
                "What": "Programming"
            },
            "expected": {"valid": False, "error": "From must not exceed 100 characters."}
        },
        
        # Invalid: What field too long
        {
            "name": "Invalid: What field exceeds 100 characters",
            "input": {
                "From": "Stanford",
                "What": "A" * 101
            },
            "expected": {"valid": False, "error": "What must not exceed 100 characters."}
        },
        
        # Valid: Minimum valid length (2 characters)
        {
            "name": "Valid: Minimum length fields (2 characters each)",
            "input": {"From": "AB", "What": "CD"},
            "expected": {"valid": True}
        },
        
        # Valid: Maximum valid length (100 characters)
        {
            "name": "Valid: Maximum length fields (100 characters each)",
            "input": {
                "From": "A" * 100,
                "What": "B" * 100
            },
            "expected": {"valid": True}
        },
        
        # Valid: From with spaces and special characters
        {
            "name": "Valid: From with spaces and special characters",
            "input": {"From": "Stanford University, USA", "What": "AI Research"},
            "expected": {"valid": True}
        },
        
        # Valid: What with spaces and special characters
        {
            "name": "Valid: What with spaces and hyphens",
            "input": {"From": "Google", "What": "Full-Stack Development"},
            "expected": {"valid": True}
        },
        
        # Valid: From with numbers and letters
        {
            "name": "Valid: From with numbers and letters",
            "input": {"From": "Company123", "What": "Web Development"},
            "expected": {"valid": True}
        },
        
        # Invalid: Whitespace only
        {
            "name": "Invalid: From with only whitespace",
            "input": {"From": "   ", "What": "Programming"},
            "expected": {"valid": False, "error": "From field must not be empty."}
        },
        
        # Invalid: What with only whitespace
        {
            "name": "Invalid: What with only whitespace",
            "input": {"From": "Stanford", "What": "   "},
            "expected": {"valid": False, "error": "What field must not be empty."}
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        # Run validation
        result = validate_skill_input(
            test_case['input']['From'],
            test_case['input']['What']
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
    success = test_skill_validation()
    sys.exit(0 if success else 1)

