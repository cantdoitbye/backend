"""
Test suite for story validation functionality.

This script tests the validate_story_input function with various inputs
to ensure it properly validates the "create story" form according to the
specified requirements.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

import django
django.setup()

from auth_manager.validators.rules.story_validation import validate_story_input


def test_story_validation():
    """
    Test the story validation function with various inputs.
    """
    
    print("=" * 80)
    print("STORY VALIDATION TEST SUITE")
    print("=" * 80)
    print()
    
    # Test cases
    test_cases = [
        # Valid input - User's example
        {
            "name": "Valid: User's example input",
            "input": {
                "title": "My First Story",
                "content": "This is a fun story!",
                "captions": "Adventure and learning go hand in hand."
            },
            "expected": {
                "isValid": True,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": ""
                }
            }
        },
        
        # Valid inputs with various lengths
        {
            "name": "Valid: Minimum length (1 character each)",
            "input": {
                "title": "A",
                "content": "B",
                "captions": "C"
            },
            "expected": {
                "isValid": True,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": ""
                }
            }
        },
        
        # Valid: Maximum length for title and content (50 chars)
        {
            "name": "Valid: Maximum length title and content (50 chars)",
            "input": {
                "title": "A" * 50,
                "content": "B" * 50,
                "captions": "Short caption"
            },
            "expected": {
                "isValid": True,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": ""
                }
            }
        },
        
        # Valid: Maximum length captions (100 chars)
        {
            "name": "Valid: Maximum length captions (100 chars)",
            "input": {
                "title": "Story Title",
                "content": "Story Content",
                "captions": "C" * 100
            },
            "expected": {
                "isValid": True,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": ""
                }
            }
        },
        
        # Valid: With extra spaces (should be trimmed)
        {
            "name": "Valid: With leading/trailing spaces (trimmed)",
            "input": {
                "title": "  My Title  ",
                "content": "  My Content  ",
                "captions": "  My Captions  "
            },
            "expected": {
                "isValid": True,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": ""
                },
                "validatedData": {
                    "title": "My Title",
                    "content": "My Content",
                    "captions": "My Captions"
                }
            }
        },
        
        # Invalid: Empty title
        {
            "name": "Invalid: Empty title",
            "input": {
                "title": "",
                "content": "Valid content",
                "captions": "Valid captions"
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "Title must not be empty.",
                    "content": "",
                    "captions": ""
                }
            }
        },
        
        # Invalid: Empty content
        {
            "name": "Invalid: Empty content",
            "input": {
                "title": "Valid title",
                "content": "",
                "captions": "Valid captions"
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "",
                    "content": "Content must not be empty.",
                    "captions": ""
                }
            }
        },
        
        # Invalid: Empty captions
        {
            "name": "Invalid: Empty captions",
            "input": {
                "title": "Valid title",
                "content": "Valid content",
                "captions": ""
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": "Captions must not be empty."
                }
            }
        },
        
        # Invalid: Title too long (51 characters)
        {
            "name": "Invalid: Title exceeds 50 characters",
            "input": {
                "title": "A" * 51,
                "content": "Valid content",
                "captions": "Valid captions"
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "Title must not exceed 50 characters.",
                    "content": "",
                    "captions": ""
                }
            }
        },
        
        # Invalid: Content too long (51 characters)
        {
            "name": "Invalid: Content exceeds 50 characters",
            "input": {
                "title": "Valid title",
                "content": "B" * 51,
                "captions": "Valid captions"
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "",
                    "content": "Content must not exceed 50 characters.",
                    "captions": ""
                }
            }
        },
        
        # Invalid: Captions too long (101 characters)
        {
            "name": "Invalid: Captions exceeds 100 characters",
            "input": {
                "title": "Valid title",
                "content": "Valid content",
                "captions": "C" * 101
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": "Captions must not exceed 100 characters."
                }
            }
        },
        
        # Invalid: Only whitespace in title
        {
            "name": "Invalid: Title with only whitespace",
            "input": {
                "title": "   ",
                "content": "Valid content",
                "captions": "Valid captions"
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "Title must not be empty.",
                    "content": "",
                    "captions": ""
                }
            }
        },
        
        # Invalid: Only whitespace in content
        {
            "name": "Invalid: Content with only whitespace",
            "input": {
                "title": "Valid title",
                "content": "   ",
                "captions": "Valid captions"
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "",
                    "content": "Content must not be empty.",
                    "captions": ""
                }
            }
        },
        
        # Invalid: Only whitespace in captions
        {
            "name": "Invalid: Captions with only whitespace",
            "input": {
                "title": "Valid title",
                "content": "Valid content",
                "captions": "   "
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": "Captions must not be empty."
                }
            }
        },
        
        # Invalid: Multiple fields invalid
        {
            "name": "Invalid: All three fields empty",
            "input": {
                "title": "",
                "content": "",
                "captions": ""
            },
            "expected": {
                "isValid": False,
                "errors": {
                    "title": "Title must not be empty.",
                    "content": "Content must not be empty.",
                    "captions": "Captions must not be empty."
                }
            }
        },
        
        # Valid: With numbers and special characters
        {
            "name": "Valid: With numbers and special characters",
            "input": {
                "title": "Story #1: The Beginning!",
                "content": "Once upon a time, in 2024...",
                "captions": "Chapter 1 - Introduction (Part 1)"
            },
            "expected": {
                "isValid": True,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": ""
                }
            }
        },
        
        # Valid: With emojis and unicode
        {
            "name": "Valid: With emojis and unicode",
            "input": {
                "title": "My Story 🌟",
                "content": "Hello World! 👋",
                "captions": "A story about life, love & happiness ❤️"
            },
            "expected": {
                "isValid": True,
                "errors": {
                    "title": "",
                    "content": "",
                    "captions": ""
                }
            }
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Input: {json.dumps(test_case['input'], indent=2)}")
        
        # Run validation
        result = validate_story_input(
            test_case['input']['title'],
            test_case['input']['content'],
            test_case['input']['captions']
        )
        
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Check if result matches expected
        expected = test_case['expected']
        
        # Check isValid
        if expected['isValid'] != result['isValid']:
            print(f"✗ FAILED - Expected isValid={expected['isValid']}, Got isValid={result['isValid']}")
            failed += 1
        # Check errors
        elif expected['errors'] != result['errors']:
            print(f"✗ FAILED - Errors don't match")
            print(f"  Expected: {expected['errors']}")
            print(f"  Got: {result['errors']}")
            failed += 1
        # Check validatedData if specified in expected
        elif 'validatedData' in expected and expected['validatedData'] != result['validatedData']:
            print(f"✗ FAILED - ValidatedData doesn't match")
            print(f"  Expected: {expected['validatedData']}")
            print(f"  Got: {result['validatedData']}")
            failed += 1
        else:
            print("✓ PASSED")
            passed += 1
        
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
    success = test_story_validation()
    sys.exit(0 if success else 1)

