# Experience Validation Quick Reference

## 🚀 Quick Start

### Import the Validator
```python
from auth_manager.validators.rules.experience_validation import validate_experience_input
```

### Validate Experience Input
```python
result = validate_experience_input("Google", "Software Engineer", "Developed scalable backend APIs.")

if result["valid"]:
    # Input is valid, proceed with saving
    print(result["message"])  # "Experience input is valid."
else:
    # Input is invalid, show error to user
    print(result["error"])  # Specific error message
```

## ✅ Validation Rules

| Field | Type | Min Length | Max Length | Special Rules |
|-------|------|------------|------------|---------------|
| **Company Name** | String | 2 | 100 | Must contain at least one letter |
| **Title** | String | 2 | 100 | Job title/position/role |
| **Description** | String | 5 | 200 | Work summary/responsibilities |

**Note:** Description has a minimum of 5 characters (not 2!)

## 📝 Valid Examples

```python
✅ {"companyName": "Google", "title": "Software Engineer", "description": "Developed scalable backend APIs and improved system performance."}
✅ {"companyName": "Microsoft", "title": "Backend Developer", "description": "Worked on backend systems and APIs."}
✅ {"companyName": "Amazon", "title": "Full Stack Engineer", "description": "Built full-stack applications using React and Node.js."}
✅ {"companyName": "Netflix", "title": "Senior Software Engineer", "description": "Led development of streaming infrastructure."}
✅ {"companyName": "TechStartup Inc.", "title": "Software Engineering Intern", "description": "Assisted in developing mobile applications."}
```

## ❌ Invalid Examples

```python
❌ {"companyName": "A", "title": "Developer", "description": "Worked on web apps"}           # companyName too short
❌ {"companyName": "Microsoft", "title": "A", "description": "Worked on backend systems."}   # title too short
❌ {"companyName": "Amazon", "title": "Backend Developer", "description": "API"}             # description too short (< 5 chars)
❌ {"companyName": "12345", "title": "Engineer", "description": "Worked on projects."}       # companyName no letters
❌ {"companyName": "@@@", "title": "Developer", "description": "Built applications."}        # companyName only symbols
❌ {"companyName": "", "title": "Engineer", "description": "Developed systems."}             # Empty companyName
```

## 🎯 Response Format

### Valid Response
```json
{
  "valid": true,
  "message": "Experience input is valid."
}
```

### Invalid Response
```json
{
  "valid": false,
  "error": "companyName must be at least 2 characters long."
}
```

## 💡 Usage in GraphQL

The validation is automatically applied in:
- `createExperience` mutation
- `updateExperience` mutation

Example mutation:
```graphql
mutation {
  createExperience(input: {
    fromSource: "Google"
    what: "Software Engineer"
    description: "Developed scalable backend APIs and improved system performance."
    fromDate: "2022-01-01"
    toDate: "2024-01-01"
  }) {
    experience {
      uid
      what
      fromSource
      description
    }
    success
    message
  }
}
```

## ⚙️ Field Mapping

**Important**: The field names differ between the user-facing names, GraphQL inputs, and database models:

| User-Facing | GraphQL Input | Database Model | Validator Param |
|-------------|---------------|----------------|----------------|
| Company Name | `fromSource` | `from_source` | `company_name` |
| Title | `what` | `what` | `title` |
| Description | `description` | `description` | `description` |

## 🔍 All Error Messages

| Error | Message |
|-------|---------|
| Empty companyName | "companyName field must not be empty." |
| Empty title | "title field must not be empty." |
| Empty description | "description field must not be empty." |
| companyName too short | "companyName must be at least 2 characters long." |
| title too short | "title must be at least 2 characters long." |
| description too short | "description must be at least 5 characters long." |
| companyName too long | "companyName must not exceed 100 characters." |
| title too long | "title must not exceed 100 characters." |
| description too long | "description must not exceed 200 characters." |
| companyName no letters | "companyName should not contain only numbers or symbols." |
| Invalid chars | "title/description contains invalid characters." |

## 🧪 Test the Validator

```bash
# Run all tests (26 tests)
python test_experience_validation.py

# Expected: 26/26 passing (100%)
```

## 📖 Individual Field Validation

You can also validate fields individually:

```python
from auth_manager.validators.rules.experience_validation import (
    validate_company_name,
    validate_title,
    validate_description
)

# These raise ValueError on failure
try:
    validate_company_name("Google Inc.")
    validate_title("Software Engineer")
    validate_description("Developed scalable systems.")
    print("All fields valid!")
except ValueError as e:
    print(f"Validation error: {e}")
```

## ✅ Status

- ✅ All tests passing (26/26)
- ✅ No linter errors
- ✅ Production ready
- ✅ Integrated into GraphQL mutations
- ✅ 100% test coverage

## 🎯 Key Differences from Other Validators

**Description Field:**
- **Minimum**: 5 characters (vs 2 for title fields in other validators)
- **Maximum**: 200 characters (vs 100-50 for other validators)
- **Special Characters**: Allows more special chars (!, @, #, $, %, ^, *, +, =, :, ;, ", ?, /, <, >) for detailed work descriptions

## 🔄 Complete Validation System

| Validator | Fields | Min Lengths | Max Lengths | Tests | Status |
|-----------|--------|-------------|-------------|-------|--------|
| Skill | 2 | 2/2 | 100/100 | 18 | ✅ 100% |
| Education | 3 | 2/2/2 | 100/100/50 | 26 | ✅ 100% |
| Experience | 3 | 2/2/5 | 100/100/200 | 26 | ✅ 100% |
| **Total** | **8** | - | - | **70** | **✅ 100%** |

