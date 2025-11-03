# Skill Validation Quick Reference

## 🚀 Quick Start

### Import the Validator
```python
from auth_manager.validators.rules.skill_validation import validate_skill_input
```

### Validate Skill Input
```python
result = validate_skill_input("Harvard University", "Machine Learning")

if result["valid"]:
    # Input is valid, proceed with saving
    print(result["message"])  # "Skill input is valid."
else:
    # Input is invalid, show error to user
    print(result["error"])  # Specific error message
```

## ✅ Validation Rules

| Field | Type | Min Length | Max Length | Special Rules |
|-------|------|------------|------------|---------------|
| **From** | String | 2 | 100 | Must contain at least one letter |
| **What** | String | 2 | 100 | Must describe a skill/expertise |

## 📝 Valid Examples

```python
✅ {"From": "Harvard University", "What": "Machine Learning"}
✅ {"From": "Google", "What": "Software Engineering"}
✅ {"From": "MIT", "What": "Data Science"}
✅ {"From": "Company123", "What": "Full-Stack Development"}
✅ {"From": "Stanford, USA", "What": "AI Research"}
```

## ❌ Invalid Examples

```python
❌ {"From": "A", "What": "ML"}           # From too short
❌ {"From": "Google", "What": "A"}       # What too short
❌ {"From": "12345", "What": "Coding"}   # From has no letters
❌ {"From": "@@@", "What": "Coding"}     # From only symbols
❌ {"From": "", "What": "Coding"}        # Empty From
❌ {"From": "MIT", "What": ""}           # Empty What
```

## 🎯 Response Format

### Valid Response
```json
{
  "valid": true,
  "message": "Skill input is valid."
}
```

### Invalid Response
```json
{
  "valid": false,
  "error": "From must be at least 2 characters long."
}
```

## 💡 Usage in GraphQL

The validation is automatically applied in:
- `createSkill` mutation
- `updateSkill` mutation

Example mutation:
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

## 🔍 All Error Messages

| Error | Message |
|-------|---------|
| Empty From | "From field must not be empty." |
| Empty What | "What field must not be empty." |
| From too short | "From must be at least 2 characters long." |
| What too short | "What must be at least 2 characters long." |
| From too long | "From must not exceed 100 characters." |
| What too long | "What must not exceed 100 characters." |
| From no letters | "From should not contain only numbers or symbols." |
| Invalid chars | "What contains invalid characters." |

## 🧪 Test the Validator

```bash
# Run all tests
python test_skill_validation.py

# Run usage examples
python example_skill_validation_usage.py
```

## 📚 Full Documentation

For complete documentation, see:
- `SKILL_VALIDATION_DOCUMENTATION.md` - Full technical documentation
- `SKILL_VALIDATION_SUMMARY.md` - Implementation summary
- `example_skill_validation_usage.py` - 6 practical examples

## 🛠️ Files Modified

**Created:**
- `auth_manager/validators/rules/skill_validation.py`
- `test_skill_validation.py`
- `example_skill_validation_usage.py`

**Modified:**
- `auth_manager/validators/rules/regex_patterns.py`
- `auth_manager/graphql/mutations.py`

## ✅ Status

- ✅ All tests passing (18/18)
- ✅ No linter errors
- ✅ Production ready
- ✅ Integrated into GraphQL mutations

