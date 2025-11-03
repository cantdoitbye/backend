# Skill Validation Implementation

## Overview

This document describes the implementation of the skill validation system for the "create skill" and "update skill" forms in the backend.

## Validation Rules

### 1. From (Source/Institution) Field

- **Type**: String
- **Minimum Length**: 2 characters
- **Maximum Length**: 100 characters
- **Content Rules**: Must contain at least one letter (A-Z, a-z). Should not contain only numbers or symbols.
- **Allowed Characters**: Letters, numbers, spaces, hyphens, apostrophes, periods, ampersands, commas, and parentheses

**Valid Examples:**
- "Harvard University"
- "Google"
- "MIT"
- "Stanford University, USA"
- "Company123"

**Invalid Examples:**
- "A" (too short)
- "12345" (only numbers)
- "@@@###" (only symbols)
- "" (empty)
- "   " (only whitespace)

### 2. What (Skill/Expertise) Field

- **Type**: String
- **Minimum Length**: 2 characters
- **Maximum Length**: 100 characters
- **Content Rules**: Should describe a real skill, expertise, or knowledge area
- **Allowed Characters**: Letters, numbers, spaces, hyphens, apostrophes, periods, ampersands, commas, and parentheses

**Valid Examples:**
- "Machine Learning"
- "Software Engineering"
- "Data Science"
- "Full-Stack Development"
- "AI Research"

**Invalid Examples:**
- "A" (too short)
- "" (empty)
- "   " (only whitespace)

## Response Format

The validation function returns a JSON object with one of two formats:

### Success Response
```json
{
  "valid": true,
  "message": "Skill input is valid."
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

Added two new regex patterns:
- `SKILL_FROM_PATTERN`: Validates the "From" field (requires at least one letter)
- `SKILL_WHAT_PATTERN`: Validates the "What" field

### 2. Validation Functions
**File**: `auth_manager/validators/rules/skill_validation.py`

Contains three functions:

#### `validate_skill_input(from_field, what_field)`
Main validation function that validates both fields and returns a JSON response.

**Parameters:**
- `from_field` (str): Source/Institution field
- `what_field` (str): Skill/Expertise field

**Returns:**
- dict: JSON response with validation result

**Example Usage:**
```python
from auth_manager.validators.rules.skill_validation import validate_skill_input

result = validate_skill_input("Harvard University", "Machine Learning")
# Returns: {"valid": True, "message": "Skill input is valid."}

result = validate_skill_input("A", "ML")
# Returns: {"valid": False, "error": "From must be at least 2 characters long."}
```

#### `validate_skill_from(from_field)`
Validates only the From field. Raises ValueError on validation failure.

#### `validate_skill_what(what_field)`
Validates only the What field. Raises ValueError on validation failure.

### 3. GraphQL Mutations
**File**: `auth_manager/graphql/mutations.py`

Updated two mutations to include validation:

#### CreateSkill Mutation
Validates both `from_source` and `what` fields before creating a new skill record.

```graphql
mutation {
  createSkill(input: {
    fromSource: "Harvard University"
    what: "Machine Learning"
  }) {
    skill {
      uid
      what
      fromSource
    }
    success
    message
  }
}
```

#### UpdateSkill Mutation
Validates `from_source` and `what` fields when they are being updated.

```graphql
mutation {
  updateSkill(input: {
    uid: "skill-uid-here"
    fromSource: "Stanford University"
    what: "Data Science"
  }) {
    skill {
      uid
      what
      fromSource
    }
    success
    message
  }
}
```

## Testing

### Test File
**File**: `test_skill_validation.py`

Comprehensive test suite with 18 test cases covering:
- Valid inputs with various formats
- Invalid inputs (too short, too long, empty, whitespace-only)
- Edge cases (minimum/maximum length, special characters)
- Number-only and symbol-only From fields

### Running Tests
```bash
python test_skill_validation.py
```

**Expected Output:**
```
================================================================================
SKILL VALIDATION TEST SUITE
================================================================================
...
================================================================================
TEST SUMMARY
================================================================================
Total Tests: 18
Passed: 18 ✓
Failed: 0 ✗
Success Rate: 100.0%
================================================================================
```

## Error Messages

The validation system provides clear, user-friendly error messages:

| Error Condition | Error Message |
|----------------|---------------|
| From field empty | "From field must not be empty." |
| What field empty | "What field must not be empty." |
| From too short | "From must be at least 2 characters long." |
| What too short | "What must be at least 2 characters long." |
| From too long | "From must not exceed 100 characters." |
| What too long | "What must not exceed 100 characters." |
| From only numbers/symbols | "From should not contain only numbers or symbols." |
| What invalid characters | "What contains invalid characters." |
| From not a string | "From must be a string." |
| What not a string | "What must be a string." |

## Integration with Backend

The validation is automatically applied when:
1. Creating a new skill via the `createSkill` GraphQL mutation
2. Updating an existing skill via the `updateSkill` GraphQL mutation

If validation fails, the mutation returns:
- `skill`: null
- `success`: false
- `message`: The specific error message

If validation succeeds, the skill is created/updated and the mutation returns:
- `skill`: The created/updated skill object
- `success`: true
- `message`: Success message

## Example API Responses

### Valid Skill Creation
**Request:**
```graphql
mutation {
  createSkill(input: {
    fromSource: "Harvard University"
    what: "Machine Learning"
  }) {
    skill {
      uid
      what
      fromSource
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
    "createSkill": {
      "skill": {
        "uid": "generated-uid",
        "what": "Machine Learning",
        "fromSource": "Harvard University"
      },
      "success": true,
      "message": "Skill created successfully"
    }
  }
}
```

### Invalid Skill Creation
**Request:**
```graphql
mutation {
  createSkill(input: {
    fromSource: "A"
    what: "ML"
  }) {
    skill {
      uid
      what
      fromSource
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
    "createSkill": {
      "skill": null,
      "success": false,
      "message": "From must be at least 2 characters long."
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

## Future Enhancements

Potential improvements to consider:
1. Add validation for skill categories/tags
2. Implement skill deduplication
3. Add proficiency level validation
4. Implement skill verification system
5. Add support for skill endorsements
6. Implement skill matching for networking

## Maintenance

When updating validation rules:
1. Update regex patterns in `regex_patterns.py`
2. Update validation functions in `skill_validation.py`
3. Update test cases in `test_skill_validation.py`
4. Run tests to ensure nothing breaks
5. Update this documentation

## Support

For questions or issues with skill validation:
1. Check the test file for examples
2. Review error messages carefully
3. Ensure input data matches the required format
4. Contact the backend team for assistance

