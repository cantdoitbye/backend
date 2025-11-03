# Education Validation Implementation

## Overview

This document describes the implementation of the education validation system for the "create education" and "update education" forms in the backend.

## Validation Rules

### 1. School Name (From/Source/Institution) Field

- **Type**: String
- **Minimum Length**: 2 characters
- **Maximum Length**: 100 characters
- **Content Rules**: Must contain at least one letter (A-Z, a-z). Should not contain only numbers or symbols. Should represent an educational institution (e.g., school, college, university).
- **Allowed Characters**: Letters, numbers, spaces, hyphens, apostrophes, periods, ampersands, commas, and parentheses

**Valid Examples:**
- "Delhi University"
- "MIT"
- "Indian Institute of Technology, Delhi"
- "Stanford University"
- "University123"

**Invalid Examples:**
- "A" (too short)
- "12345" (only numbers)
- "@@@###" (only symbols)
- "" (empty)
- "   " (only whitespace)

### 2. Degree (What/Experience/Learning) Field

- **Type**: String
- **Minimum Length**: 2 characters
- **Maximum Length**: 100 characters
- **Content Rules**: Should represent a valid academic degree, diploma, or learning title
- **Allowed Characters**: Letters, numbers, spaces, hyphens, apostrophes, periods, ampersands, commas, and parentheses

**Valid Examples:**
- "Bachelor of Science"
- "B.Tech"
- "Master's Degree"
- "PhD"
- "M.B.A."

**Invalid Examples:**
- "B" (too short)
- "" (empty)
- "   " (only whitespace)

### 3. Field of Study

- **Type**: String
- **Minimum Length**: 2 characters
- **Maximum Length**: 50 characters (note: shorter than other fields)
- **Content Rules**: Should describe a subject, specialization, or study area
- **Allowed Characters**: Letters, numbers, spaces, hyphens, apostrophes, periods, ampersands, commas, and parentheses

**Valid Examples:**
- "Computer Science"
- "Physics"
- "Economics"
- "Computer Science & Engineering"
- "Quantum Physics"

**Invalid Examples:**
- "A" (too short)
- "" (empty)
- "   " (only whitespace)
- (51+ characters - exceeds maximum)

## Response Format

The validation function returns a JSON object with one of two formats:

### Success Response
```json
{
  "valid": true,
  "message": "Education input is valid."
}
```

### Error Response
```json
{
  "valid": false,
  "error": "<specific reason for invalidation>"
}
```

## Implementation Files

### 1. Regex Patterns
**File**: `auth_manager/validators/rules/regex_patterns.py`

Added three new regex patterns:
- `EDUCATION_SCHOOL_NAME_PATTERN`: Validates the school name (requires at least one letter)
- `EDUCATION_DEGREE_PATTERN`: Validates the degree field
- `EDUCATION_FIELD_OF_STUDY_PATTERN`: Validates the field of study (max 50 chars)

### 2. Validation Functions
**File**: `auth_manager/validators/rules/education_validation.py`

Contains four functions:

#### `validate_education_input(school_name, degree, field_of_study)`
Main validation function that validates all three fields and returns a JSON response.

**Parameters:**
- `school_name` (str): School/Institution name
- `degree` (str): Degree/Diploma/Learning title
- `field_of_study` (str): Subject/Specialization/Study area

**Returns:**
- dict: JSON response with validation result

**Example Usage:**
```python
from auth_manager.validators.rules.education_validation import validate_education_input

result = validate_education_input("Delhi University", "Bachelor of Science", "Computer Science")
# Returns: {"valid": True, "message": "Education input is valid."}

result = validate_education_input("A", "B.Tech", "CS")
# Returns: {"valid": False, "error": "schoolName must be at least 2 characters long."}
```

#### `validate_school_name(school_name)`
Validates only the School Name field. Raises ValueError on validation failure.

#### `validate_degree(degree)`
Validates only the Degree field. Raises ValueError on validation failure.

#### `validate_field_of_study(field_of_study)`
Validates only the Field of Study field. Raises ValueError on validation failure.

### 3. GraphQL Mutations
**File**: `auth_manager/graphql/mutations.py`

Updated two mutations to include validation:

#### CreateEducation Mutation
Validates `from_source` (school name), `what` (degree), and `field_of_study` before creating a new education record.

**Field Mapping:**
- `from_source` → School Name (institution/school name)
- `what` → Degree (degree/qualification)
- `field_of_study` → Field of Study (academic field/major)

```graphql
mutation {
  createEducation(input: {
    fromSource: "Delhi University"
    what: "Bachelor of Science"
    fieldOfStudy: "Computer Science"
    fromDate: "2020-01-01"
  }) {
    education {
      uid
      what
      fromSource
      fieldOfStudy
    }
    success
    message
  }
}
```

#### UpdateEducation Mutation
Validates the three key fields when they are being updated.

```graphql
mutation {
  updateEducation(input: {
    uid: "education-uid-here"
    fromSource: "Stanford University"
    what: "Master's Degree"
    fieldOfStudy: "Data Science"
  }) {
    education {
      uid
      what
      fromSource
      fieldOfStudy
    }
    success
    message
  }
}
```

## Testing

### Test File
**File**: `test_education_validation.py`

Comprehensive test suite with 26 test cases covering:
- Valid inputs with various formats
- Invalid inputs (too short, too long, empty, whitespace-only)
- Edge cases (minimum/maximum length, special characters)
- Number-only and symbol-only school names
- Real-world education examples

### Running Tests
```bash
python test_education_validation.py
```

**Expected Output:**
```
================================================================================
EDUCATION VALIDATION TEST SUITE
================================================================================
...
================================================================================
TEST SUMMARY
================================================================================
Total Tests: 26
Passed: 26 ✓
Failed: 0 ✗
Success Rate: 100.0%
================================================================================
```

## Error Messages

The validation system provides clear, user-friendly error messages:

| Error Condition | Error Message |
|----------------|---------------|
| schoolName empty | "schoolName field must not be empty." |
| degree empty | "degree field must not be empty." |
| fieldOfStudy empty | "fieldOfStudy field must not be empty." |
| schoolName too short | "schoolName must be at least 2 characters long." |
| degree too short | "degree must be at least 2 characters long." |
| fieldOfStudy too short | "fieldOfStudy must be at least 2 characters long." |
| schoolName too long | "schoolName must not exceed 100 characters." |
| degree too long | "degree must not exceed 100 characters." |
| fieldOfStudy too long | "fieldOfStudy must not exceed 50 characters." |
| schoolName only numbers/symbols | "schoolName should not contain only numbers or symbols." |
| degree invalid characters | "degree contains invalid characters." |
| fieldOfStudy invalid characters | "fieldOfStudy contains invalid characters." |
| schoolName not a string | "schoolName must be a string." |
| degree not a string | "degree must be a string." |
| fieldOfStudy not a string | "fieldOfStudy must be a string." |

## Integration with Backend

The validation is automatically applied when:
1. Creating a new education record via the `createEducation` GraphQL mutation
2. Updating an existing education record via the `updateEducation` GraphQL mutation

If validation fails, the mutation returns:
- `education`: null
- `success`: false
- `message`: The specific error message

If validation succeeds, the education record is created/updated and the mutation returns:
- `education`: The created/updated education object
- `success`: true
- `message`: Success message

## Example API Responses

### Valid Education Creation
**Request:**
```graphql
mutation {
  createEducation(input: {
    fromSource: "Delhi University"
    what: "Bachelor of Science"
    fieldOfStudy: "Computer Science"
    fromDate: "2020-01-01"
    toDate: "2024-01-01"
  }) {
    education {
      uid
      what
      fromSource
      fieldOfStudy
    }
    success
    message
  }
}
```

**Response:**
```json
{
  "data": {
    "createEducation": {
      "education": {
        "uid": "generated-uid",
        "what": "Bachelor of Science",
        "fromSource": "Delhi University",
        "fieldOfStudy": "Computer Science"
      },
      "success": true,
      "message": "Education created successfully"
    }
  }
}
```

### Invalid Education Creation
**Request:**
```graphql
mutation {
  createEducation(input: {
    fromSource: "A"
    what: "B.Tech"
    fieldOfStudy: "CS"
    fromDate: "2020-01-01"
  }) {
    education {
      uid
      what
      fromSource
      fieldOfStudy
    }
    success
    message
  }
}
```

**Response:**
```json
{
  "data": {
    "createEducation": {
      "education": null,
      "success": false,
      "message": "schoolName must be at least 2 characters long."
    }
  }
}
```

## Best Practices

1. **Always validate on the backend**: Never rely solely on frontend validation
2. **Provide clear error messages**: Help users understand what went wrong
3. **Test thoroughly**: Use the test suite to verify validation works correctly
4. **Keep validation consistent**: Use the same rules for create and update operations
5. **Handle edge cases**: Test with empty strings, whitespace, special characters, etc.
6. **Be mindful of field lengths**: Note that fieldOfStudy has a max length of 50, not 100

## Field Mapping Reference

In the Neo4j Education model and GraphQL:
- **`from_source`** → School/Institution Name (the "From" field)
- **`what`** → Degree/Qualification (the "What" field)
- **`field_of_study`** → Academic Field/Major (the "Field of Study" field)

This mapping is important when working with the database models and GraphQL inputs.

## Future Enhancements

Potential improvements to consider:
1. Add validation for degree types/categories
2. Implement institution verification
3. Add GPA/grade validation
4. Implement credential verification system
5. Add support for multiple majors/minors
6. Implement education matching for alumni networking

## Maintenance

When updating validation rules:
1. Update regex patterns in `regex_patterns.py`
2. Update validation functions in `education_validation.py`
3. Update test cases in `test_education_validation.py`
4. Run tests to ensure nothing breaks
5. Update this documentation

## Support

For questions or issues with education validation:
1. Check the test file for examples
2. Review error messages carefully
3. Ensure input data matches the required format
4. Contact the backend team for assistance

