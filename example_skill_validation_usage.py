"""
Example usage of the skill validation system.

This script demonstrates how to use the skill validation functions
in different contexts within your application.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

import django
django.setup()

from auth_manager.validators.rules.skill_validation import (
    validate_skill_input,
    validate_skill_from,
    validate_skill_what
)


def example_1_basic_validation():
    """
    Example 1: Basic validation with JSON response
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Validation")
    print("="*80)
    
    # Valid input
    result = validate_skill_input("Harvard University", "Machine Learning")
    print(f"Input: From='Harvard University', What='Machine Learning'")
    print(f"Result: {result}")
    print()
    
    # Invalid input - From too short
    result = validate_skill_input("A", "Machine Learning")
    print(f"Input: From='A', What='Machine Learning'")
    print(f"Result: {result}")
    print()
    
    # Invalid input - What too short
    result = validate_skill_input("Google", "A")
    print(f"Input: From='Google', What='A'")
    print(f"Result: {result}")


def example_2_form_validation():
    """
    Example 2: Using in a form validation context
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Form Validation Context")
    print("="*80)
    
    # Simulate form data
    form_data = {
        "From": "Stanford University",
        "What": "Data Science"
    }
    
    result = validate_skill_input(form_data["From"], form_data["What"])
    
    if result["valid"]:
        print(f"✓ Form validation passed!")
        print(f"  Message: {result['message']}")
        print(f"  Ready to save: From='{form_data['From']}', What='{form_data['What']}'")
    else:
        print(f"✗ Form validation failed!")
        print(f"  Error: {result['error']}")


def example_3_api_endpoint():
    """
    Example 3: Using in an API endpoint context
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: API Endpoint Context")
    print("="*80)
    
    # Simulate API request data
    api_request = {
        "from_source": "MIT",
        "what": "Artificial Intelligence"
    }
    
    # Validate the input
    result = validate_skill_input(
        api_request.get("from_source", ""),
        api_request.get("what", "")
    )
    
    # Prepare API response
    if result["valid"]:
        api_response = {
            "status": "success",
            "data": {
                "skill": {
                    "from": api_request["from_source"],
                    "what": api_request["what"]
                }
            },
            "message": result["message"]
        }
        print("API Response:")
        print(api_response)
    else:
        api_response = {
            "status": "error",
            "error": result["error"],
            "data": None
        }
        print("API Response:")
        print(api_response)


def example_4_individual_field_validation():
    """
    Example 4: Validating individual fields with exception handling
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Individual Field Validation")
    print("="*80)
    
    # Validate From field
    try:
        validate_skill_from("Google Inc.")
        print("✓ From field 'Google Inc.' is valid")
    except ValueError as e:
        print(f"✗ From field validation failed: {e}")
    
    # Validate What field
    try:
        validate_skill_what("Machine Learning")
        print("✓ What field 'Machine Learning' is valid")
    except ValueError as e:
        print(f"✗ What field validation failed: {e}")
    
    # Try with invalid input
    try:
        validate_skill_from("123")
        print("✓ From field '123' is valid")
    except ValueError as e:
        print(f"✗ From field validation failed: {e}")


def example_5_batch_validation():
    """
    Example 5: Validating multiple skills at once
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Batch Validation")
    print("="*80)
    
    skills = [
        {"From": "Harvard", "What": "Economics"},
        {"From": "Google", "What": "Software Engineering"},
        {"From": "A", "What": "Programming"},  # Invalid
        {"From": "MIT", "What": "Physics"},
        {"From": "12345", "What": "Coding"},  # Invalid
    ]
    
    valid_skills = []
    invalid_skills = []
    
    for i, skill in enumerate(skills, 1):
        result = validate_skill_input(skill["From"], skill["What"])
        
        if result["valid"]:
            valid_skills.append(skill)
            print(f"{i}. ✓ Valid: {skill}")
        else:
            invalid_skills.append({
                "skill": skill,
                "error": result["error"]
            })
            print(f"{i}. ✗ Invalid: {skill} - {result['error']}")
    
    print(f"\nSummary: {len(valid_skills)} valid, {len(invalid_skills)} invalid")


def example_6_graphql_context():
    """
    Example 6: How it's used in GraphQL mutations
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: GraphQL Mutation Context")
    print("="*80)
    
    print("""
In the GraphQL mutations (CreateSkill and UpdateSkill), the validation is used like this:

```python
from auth_manager.validators.rules import skill_validation
from graphql import GraphQLError

def mutate(self, info, input):
    try:
        # Extract fields from input
        from_source = input.get('from_source', '')
        what = input.get('what', '')
        
        # Validate using the validator
        validation_result = skill_validation.validate_skill_input(from_source, what)
        
        # Check if validation failed
        if not validation_result.get('valid'):
            raise GraphQLError(validation_result.get('error'))
        
        # Continue with creating/updating the skill...
        skill = Skill(what=what, from_source=from_source)
        skill.save()
        
        return CreateSkill(skill=skill, success=True, message="Success")
        
    except Exception as error:
        return CreateSkill(skill=None, success=False, message=str(error))
```

This ensures that all skill data is validated before being saved to the database.
""")


def main():
    """
    Run all examples
    """
    print("\n" + "#"*80)
    print("# SKILL VALIDATION USAGE EXAMPLES")
    print("#"*80)
    
    example_1_basic_validation()
    example_2_form_validation()
    example_3_api_endpoint()
    example_4_individual_field_validation()
    example_5_batch_validation()
    example_6_graphql_context()
    
    print("\n" + "#"*80)
    print("# END OF EXAMPLES")
    print("#"*80)
    print()


if __name__ == "__main__":
    main()

