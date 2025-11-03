"""
Example usage of the education validation system.

This script demonstrates how to use the education validation functions
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

from auth_manager.validators.rules.education_validation import (
    validate_education_input,
    validate_school_name,
    validate_degree,
    validate_field_of_study
)


def example_1_basic_validation():
    """
    Example 1: Basic validation with JSON response
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Validation")
    print("="*80)
    
    # Valid input
    result = validate_education_input("Delhi University", "Bachelor of Science", "Computer Science")
    print(f"Input: schoolName='Delhi University', degree='Bachelor of Science', fieldOfStudy='Computer Science'")
    print(f"Result: {result}")
    print()
    
    # Invalid input - schoolName too short
    result = validate_education_input("A", "B.Tech", "CS")
    print(f"Input: schoolName='A', degree='B.Tech', fieldOfStudy='CS'")
    print(f"Result: {result}")
    print()
    
    # Invalid input - degree too short
    result = validate_education_input("MIT", "B", "Physics")
    print(f"Input: schoolName='MIT', degree='B', fieldOfStudy='Physics'")
    print(f"Result: {result}")
    print()
    
    # Invalid input - fieldOfStudy too short
    result = validate_education_input("IIT Bombay", "M.Tech", "A")
    print(f"Input: schoolName='IIT Bombay', degree='M.Tech', fieldOfStudy='A'")
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
        "schoolName": "Stanford University",
        "degree": "Master's Degree",
        "fieldOfStudy": "Data Science"
    }
    
    result = validate_education_input(
        form_data["schoolName"],
        form_data["degree"],
        form_data["fieldOfStudy"]
    )
    
    if result["valid"]:
        print(f"✓ Form validation passed!")
        print(f"  Message: {result['message']}")
        print(f"  Ready to save:")
        print(f"    - School: {form_data['schoolName']}")
        print(f"    - Degree: {form_data['degree']}")
        print(f"    - Field: {form_data['fieldOfStudy']}")
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
        "what": "PhD",
        "field_of_study": "Physics"
    }
    
    # Validate the input
    result = validate_education_input(
        api_request.get("from_source", ""),
        api_request.get("what", ""),
        api_request.get("field_of_study", "")
    )
    
    # Prepare API response
    if result["valid"]:
        api_response = {
            "status": "success",
            "data": {
                "education": {
                    "school": api_request["from_source"],
                    "degree": api_request["what"],
                    "field": api_request["field_of_study"]
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
    
    # Validate School Name
    try:
        validate_school_name("Harvard University")
        print("✓ School Name 'Harvard University' is valid")
    except ValueError as e:
        print(f"✗ School Name validation failed: {e}")
    
    # Validate Degree
    try:
        validate_degree("Bachelor of Arts")
        print("✓ Degree 'Bachelor of Arts' is valid")
    except ValueError as e:
        print(f"✗ Degree validation failed: {e}")
    
    # Validate Field of Study
    try:
        validate_field_of_study("Computer Science")
        print("✓ Field of Study 'Computer Science' is valid")
    except ValueError as e:
        print(f"✗ Field of Study validation failed: {e}")
    
    # Try with invalid input
    try:
        validate_school_name("123")
        print("✓ School Name '123' is valid")
    except ValueError as e:
        print(f"✗ School Name validation failed: {e}")


def example_5_batch_validation():
    """
    Example 5: Validating multiple education records at once
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Batch Validation")
    print("="*80)
    
    education_records = [
        {
            "schoolName": "Harvard",
            "degree": "MBA",
            "fieldOfStudy": "Business"
        },
        {
            "schoolName": "MIT",
            "degree": "B.Tech",
            "fieldOfStudy": "Computer Science"
        },
        {
            "schoolName": "A",
            "degree": "PhD",
            "fieldOfStudy": "Physics"
        },  # Invalid
        {
            "schoolName": "Stanford",
            "degree": "Master's",
            "fieldOfStudy": "Economics"
        },
        {
            "schoolName": "12345",
            "degree": "B.Sc",
            "fieldOfStudy": "Mathematics"
        },  # Invalid
    ]
    
    valid_records = []
    invalid_records = []
    
    for i, record in enumerate(education_records, 1):
        result = validate_education_input(
            record["schoolName"],
            record["degree"],
            record["fieldOfStudy"]
        )
        
        if result["valid"]:
            valid_records.append(record)
            print(f"{i}. ✓ Valid: {record['schoolName']} - {record['degree']} - {record['fieldOfStudy']}")
        else:
            invalid_records.append({
                "record": record,
                "error": result["error"]
            })
            print(f"{i}. ✗ Invalid: {record} - {result['error']}")
    
    print(f"\nSummary: {len(valid_records)} valid, {len(invalid_records)} invalid")


def example_6_graphql_context():
    """
    Example 6: How it's used in GraphQL mutations
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: GraphQL Mutation Context")
    print("="*80)
    
    print("""
In the GraphQL mutations (CreateEducation and UpdateEducation), the validation is used like this:

```python
from auth_manager.validators.rules import education_validation
from graphql import GraphQLError

def mutate(self, info, input):
    try:
        # Extract fields from input
        # Note the field mapping:
        # - from_source = school/institution name
        # - what = degree/qualification
        # - field_of_study = academic field/major
        school_name = input.get('from_source', '')
        degree = input.get('what', '')
        field_of_study = input.get('field_of_study', '')
        
        # Validate using the validator
        validation_result = education_validation.validate_education_input(
            school_name, degree, field_of_study
        )
        
        # Check if validation failed
        if not validation_result.get('valid'):
            raise GraphQLError(validation_result.get('error'))
        
        # Continue with creating/updating the education record...
        education = Education(
            from_source=school_name,
            what=degree,
            field_of_study=field_of_study
        )
        education.save()
        
        return CreateEducation(education=education, success=True, message="Success")
        
    except Exception as error:
        return CreateEducation(education=None, success=False, message=str(error))
```

**Field Mapping in GraphQL:**
- `fromSource` (GraphQL input) → `from_source` (model) → School Name
- `what` (GraphQL input) → `what` (model) → Degree
- `fieldOfStudy` (GraphQL input) → `field_of_study` (model) → Field of Study

This ensures that all education data is validated before being saved to the database.
""")


def example_7_real_world_scenarios():
    """
    Example 7: Real-world education scenarios
    """
    print("\n" + "="*80)
    print("EXAMPLE 7: Real-World Education Scenarios")
    print("="*80)
    
    scenarios = [
        {
            "name": "Indian University",
            "data": {
                "schoolName": "IIT Delhi",
                "degree": "B.Tech",
                "fieldOfStudy": "Computer Science"
            }
        },
        {
            "name": "US University",
            "data": {
                "schoolName": "Stanford University",
                "degree": "Master of Science",
                "fieldOfStudy": "Artificial Intelligence"
            }
        },
        {
            "name": "UK University",
            "data": {
                "schoolName": "Oxford University",
                "degree": "Doctor of Philosophy",
                "fieldOfStudy": "Quantum Physics"
            }
        },
        {
            "name": "Professional Certification",
            "data": {
                "schoolName": "Google",
                "degree": "Professional Certificate",
                "fieldOfStudy": "Cloud Computing"
            }
        },
    ]
    
    for scenario in scenarios:
        result = validate_education_input(
            scenario["data"]["schoolName"],
            scenario["data"]["degree"],
            scenario["data"]["fieldOfStudy"]
        )
        
        status = "✓" if result["valid"] else "✗"
        print(f"{status} {scenario['name']}: {scenario['data']}")
        if not result["valid"]:
            print(f"   Error: {result['error']}")


def main():
    """
    Run all examples
    """
    print("\n" + "#"*80)
    print("# EDUCATION VALIDATION USAGE EXAMPLES")
    print("#"*80)
    
    example_1_basic_validation()
    example_2_form_validation()
    example_3_api_endpoint()
    example_4_individual_field_validation()
    example_5_batch_validation()
    example_6_graphql_context()
    example_7_real_world_scenarios()
    
    print("\n" + "#"*80)
    print("# END OF EXAMPLES")
    print("#"*80)
    print()


if __name__ == "__main__":
    main()

