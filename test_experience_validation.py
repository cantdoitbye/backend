"""
Test suite for experience validation functionality.

This script tests the validate_experience_input function with various inputs
to ensure it properly validates the "create experience" form according to the
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

from auth_manager.validators.rules.experience_validation import validate_experience_input


def test_experience_validation():
    """
    Test the experience validation function with various inputs.
    """
    
    print("=" * 80)
    print("EXPERIENCE VALIDATION TEST SUITE")
    print("=" * 80)
    print()
    
    # Test cases based on user requirements
    test_cases = [
        # Valid inputs
        {
            "name": "Valid: Google + Software Engineer + Full description",
            "input": {
                "companyName": "Google",
                "title": "Software Engineer",
                "description": "Developed scalable backend APIs and improved system performance."
            },
            "expected": {"valid": True, "message": "Experience input is valid."}
        },
        {
            "name": "Valid: Microsoft + Backend Developer + Description",
            "input": {
                "companyName": "Microsoft",
                "title": "Backend Developer",
                "description": "Worked on backend systems and APIs."
            },
            "expected": {"valid": True}
        },
        {
            "name": "Valid: Amazon + Full Stack Engineer + Description",
            "input": {
                "companyName": "Amazon",
                "title": "Full Stack Engineer",
                "description": "Built full-stack applications using React and Node.js."
            },
            "expected": {"valid": True}
        },
        
        # Invalid: companyName too short
        {
            "name": "Invalid: companyName too short (1 character)",
            "input": {
                "companyName": "A",
                "title": "Developer",
                "description": "Worked on web apps"
            },
            "expected": {"valid": False, "error": "companyName must be at least 2 characters long."}
        },
        
        # Invalid: title too short
        {
            "name": "Invalid: title too short (1 character)",
            "input": {
                "companyName": "Microsoft",
                "title": "A",
                "description": "Worked on backend systems."
            },
            "expected": {"valid": False, "error": "title must be at least 2 characters long."}
        },
        
        # Invalid: description too short
        {
            "name": "Invalid: description too short (3 characters)",
            "input": {
                "companyName": "Amazon",
                "title": "Backend Developer",
                "description": "API"
            },
            "expected": {"valid": False, "error": "description must be at least 5 characters long."}
        },
        
        # Invalid: companyName only numbers
        {
            "name": "Invalid: companyName only numbers",
            "input": {
                "companyName": "12345",
                "title": "Engineer",
                "description": "Worked on various projects."
            },
            "expected": {"valid": False, "error": "companyName should not contain only numbers or symbols."}
        },
        
        # Invalid: companyName only symbols
        {
            "name": "Invalid: companyName only symbols",
            "input": {
                "companyName": "@@@###",
                "title": "Developer",
                "description": "Built software applications."
            },
            "expected": {"valid": False, "error": "companyName should not contain only numbers or symbols."}
        },
        
        # Invalid: Empty companyName
        {
            "name": "Invalid: Empty companyName",
            "input": {
                "companyName": "",
                "title": "Engineer",
                "description": "Developed systems."
            },
            "expected": {"valid": False, "error": "companyName field must not be empty."}
        },
        
        # Invalid: Empty title
        {
            "name": "Invalid: Empty title",
            "input": {
                "companyName": "Google",
                "title": "",
                "description": "Worked on projects."
            },
            "expected": {"valid": False, "error": "title field must not be empty."}
        },
        
        # Invalid: Empty description
        {
            "name": "Invalid: Empty description",
            "input": {
                "companyName": "Amazon",
                "title": "Developer",
                "description": ""
            },
            "expected": {"valid": False, "error": "description field must not be empty."}
        },
        
        # Invalid: companyName too long
        {
            "name": "Invalid: companyName exceeds 100 characters",
            "input": {
                "companyName": "A" * 101,
                "title": "Engineer",
                "description": "Built software."
            },
            "expected": {"valid": False, "error": "companyName must not exceed 100 characters."}
        },
        
        # Invalid: title too long
        {
            "name": "Invalid: title exceeds 100 characters",
            "input": {
                "companyName": "Google",
                "title": "B" * 101,
                "description": "Worked on projects."
            },
            "expected": {"valid": False, "error": "title must not exceed 100 characters."}
        },
        
        # Invalid: description too long
        {
            "name": "Invalid: description exceeds 200 characters",
            "input": {
                "companyName": "Microsoft",
                "title": "Engineer",
                "description": "A" * 201
            },
            "expected": {"valid": False, "error": "description must not exceed 200 characters."}
        },
        
        # Valid: Minimum valid length (2, 2, 5 characters)
        {
            "name": "Valid: Minimum length fields",
            "input": {
                "companyName": "AB",
                "title": "CD",
                "description": "EFGHI"
            },
            "expected": {"valid": True}
        },
        
        # Valid: Maximum valid length (100, 100, 200 characters)
        {
            "name": "Valid: Maximum length fields",
            "input": {
                "companyName": "A" * 100,
                "title": "B" * 100,
                "description": "C" * 200
            },
            "expected": {"valid": True}
        },
        
        # Valid: companyName with spaces and special characters
        {
            "name": "Valid: companyName with spaces and special characters",
            "input": {
                "companyName": "Google Inc., USA",
                "title": "Software Engineer",
                "description": "Developed scalable systems."
            },
            "expected": {"valid": True}
        },
        
        # Valid: title with spaces and hyphens
        {
            "name": "Valid: title with spaces and hyphens",
            "input": {
                "companyName": "Microsoft",
                "title": "Senior Full-Stack Developer",
                "description": "Built web applications using modern technologies."
            },
            "expected": {"valid": True}
        },
        
        # Valid: description with special characters
        {
            "name": "Valid: description with special characters",
            "input": {
                "companyName": "Amazon",
                "title": "Backend Engineer",
                "description": "Developed RESTful APIs, worked with AWS services, and improved performance by 50%."
            },
            "expected": {"valid": True}
        },
        
        # Valid: companyName with numbers and letters
        {
            "name": "Valid: companyName with numbers and letters",
            "input": {
                "companyName": "Company123",
                "title": "Developer",
                "description": "Worked on software projects."
            },
            "expected": {"valid": True}
        },
        
        # Invalid: Whitespace only in companyName
        {
            "name": "Invalid: companyName with only whitespace",
            "input": {
                "companyName": "   ",
                "title": "Engineer",
                "description": "Built systems."
            },
            "expected": {"valid": False, "error": "companyName field must not be empty."}
        },
        
        # Invalid: Whitespace only in title
        {
            "name": "Invalid: title with only whitespace",
            "input": {
                "companyName": "Google",
                "title": "   ",
                "description": "Developed applications."
            },
            "expected": {"valid": False, "error": "title field must not be empty."}
        },
        
        # Invalid: Whitespace only in description
        {
            "name": "Invalid: description with only whitespace",
            "input": {
                "companyName": "Microsoft",
                "title": "Developer",
                "description": "     "
            },
            "expected": {"valid": False, "error": "description field must not be empty."}
        },
        
        # Valid: Real-world examples
        {
            "name": "Valid: Netflix + Senior Engineer + Description",
            "input": {
                "companyName": "Netflix",
                "title": "Senior Software Engineer",
                "description": "Led development of streaming infrastructure and improved system reliability."
            },
            "expected": {"valid": True}
        },
        {
            "name": "Valid: Startup + Intern + Description",
            "input": {
                "companyName": "TechStartup Inc.",
                "title": "Software Engineering Intern",
                "description": "Assisted in developing mobile applications and wrote unit tests."
            },
            "expected": {"valid": True}
        },
        {
            "name": "Valid: Freelance + Consultant + Description",
            "input": {
                "companyName": "Self Employed",
                "title": "Freelance Consultant",
                "description": "Provided technical consulting services to various clients and organizations."
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
        result = validate_experience_input(
            test_case['input']['companyName'],
            test_case['input']['title'],
            test_case['input']['description']
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
    success = test_experience_validation()
    sys.exit(0 if success else 1)

