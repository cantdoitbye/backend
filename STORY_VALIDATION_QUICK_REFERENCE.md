# Story Validation Quick Reference

## 🚀 Quick Start

### Import the Validator
```python
from auth_manager.validators.rules.story_validation import validate_story_input
```

### Validate Story Input
```python
result = validate_story_input("My First Story", "This is a fun story!", "Adventure and learning.")

if result["isValid"]:
    # Use validated (trimmed) data
    story_data = result["validatedData"]
    print(f"Title: {story_data['title']}")
    print(f"Content: {story_data['content']}")
    print(f"Captions: {story_data['captions']}")
else:
    # Check individual field errors
    errors = result["errors"]
    if errors["title"]:
        print(f"Title error: {errors['title']}")
    if errors["content"]:
        print(f"Content error: {errors['content']}")
    if errors["captions"]:
        print(f"Captions error: {errors['captions']}")
```

## ✅ Validation Rules

| Field | Type | Min Length | Max Length | Auto-Trim |
|-------|------|------------|------------|-----------|
| **title** | String | 1 | 50 | ✅ Yes |
| **content** | String | 1 | 50 | ✅ Yes |
| **captions** | String | 1 | 100 | ✅ Yes |

**Note:** Minimum length is 1 character (most flexible validator!)

## 📝 Valid Examples

```python
✅ {"title": "My First Story", "content": "This is a fun story!", "captions": "Adventure and learning go hand in hand."}
✅ {"title": "A", "content": "B", "captions": "C"}  # Minimum length (1 char each)
✅ {"title": "  Trimmed  ", "content": "  Spaces  ", "captions": "  Removed  "}  # Auto-trimmed
✅ {"title": "Story 🌟", "content": "Hello! 👋", "captions": "Life & happiness ❤️"}  # Emojis OK
✅ {"title": "Story #1", "content": "2024...", "captions": "Chapter 1 (Part 1)"}  # Special chars OK
```

## ❌ Invalid Examples

```python
❌ {"title": "", "content": "Valid", "captions": "Valid"}           # Empty title
❌ {"title": "Valid", "content": "", "captions": "Valid"}           # Empty content
❌ {"title": "Valid", "content": "Valid", "captions": ""}           # Empty captions
❌ {"title": "A"*51, "content": "Valid", "captions": "Valid"}       # Title too long (>50)
❌ {"title": "Valid", "content": "B"*51, "captions": "Valid"}       # Content too long (>50)
❌ {"title": "Valid", "content": "Valid", "captions": "C"*101}      # Captions too long (>100)
❌ {"title": "   ", "content": "Valid", "captions": "Valid"}        # Only whitespace
```

## 🎯 Response Format

### Success Response
```json
{
  "isValid": true,
  "errors": {
    "title": "",
    "content": "",
    "captions": ""
  },
  "validatedData": {
    "title": "My First Story",
    "content": "This is a fun story!",
    "captions": "Adventure and learning go hand in hand."
  }
}
```

### Error Response
```json
{
  "isValid": false,
  "errors": {
    "title": "Title must not be empty.",
    "content": "",
    "captions": "Captions must not exceed 100 characters."
  },
  "validatedData": {
    "title": "",
    "content": "Valid content",
    "captions": "Very long captions that exceed the limit..."
  }
}
```

## 💡 Key Features

1. **Custom Format** - Returns `isValid`, `errors` object, and `validatedData`
2. **Auto-Trimming** - Automatically trims whitespace from all inputs
3. **Field-Specific Errors** - Easy to display individual field errors in UI
4. **Validated Data** - Returns trimmed, validated values ready for storage
5. **Very Permissive** - Accepts all characters (emojis, unicode, special chars)
6. **Minimum 1 Char** - Most flexible validator (other validators require 2+ chars)

## 🔍 All Error Messages

| Error Condition | Message |
|----------------|---------|
| Empty title | "Title must not be empty." |
| Empty content | "Content must not be empty." |
| Empty captions | "Captions must not be empty." |
| Title too long | "Title must not exceed 50 characters." |
| Content too long | "Content must not exceed 50 characters." |
| Captions too long | "Captions must not exceed 100 characters." |
| Title not string | "Title must be a string." |
| Content not string | "Content must be a string." |
| Captions not string | "Captions must be a string." |

## 🧪 Test the Validator

```bash
# Run all tests (17 tests)
python test_story_validation.py

# Expected: 17/17 passing (100%)
```

## 📖 Individual Field Validation

You can also validate fields individually:

```python
from auth_manager.validators.rules.story_validation import (
    validate_title,
    validate_content,
    validate_captions
)

# These raise ValueError on failure
try:
    validate_title("My Story Title")
    validate_content("Story content here")
    validate_captions("Some captions for the story")
    print("All fields valid!")
except ValueError as e:
    print(f"Validation error: {e}")
```

## 🎨 Usage in Forms

Perfect for form validation with field-specific error display:

```python
def validate_story_form(title, content, captions):
    result = validate_story_input(title, content, captions)
    
    if result["isValid"]:
        # Save story with trimmed data
        save_story(result["validatedData"])
        return {"success": True}
    else:
        # Return field-specific errors for UI
        return {
            "success": False,
            "errors": result["errors"]  # Can map directly to form fields
        }
```

## ✅ Status

- ✅ All tests passing (17/17)
- ✅ No linter errors
- ✅ Production ready
- ✅ Custom response format
- ✅ 100% test coverage

## 🔄 Comparison with Other Validators

| Feature | Other Validators | Story Validator |
|---------|-----------------|-----------------|
| Min Length | 2-5 chars | 1 char ✨ |
| Response | `{"valid": true}` | `{"isValid": true, "errors": {}, "validatedData": {}}` |
| Errors | Single string | Object with per-field errors |
| Trimmed Data | Not returned | Returned in `validatedData` |
| Char Restrictions | Some limits | Very permissive ✨ |

## 📚 Integration Example

```python
from auth_manager.validators.rules.story_validation import validate_story_input

class CreateStoryAPI:
    def post(self, request):
        # Get form data
        title = request.data.get('title', '')
        content = request.data.get('content', '')
        captions = request.data.get('captions', '')
        
        # Validate
        result = validate_story_input(title, content, captions)
        
        if not result["isValid"]:
            # Return errors for each field
            return Response({
                "success": False,
                "errors": result["errors"]
            }, status=400)
        
        # Use validated (trimmed) data
        story = Story.objects.create(**result["validatedData"])
        
        return Response({
            "success": True,
            "story_id": story.id
        }, status=201)
```

## 🎯 Perfect For

- ✅ Form validation with per-field error display
- ✅ APIs that need structured error responses
- ✅ Frontend frameworks (React, Vue, etc.)
- ✅ REST APIs requiring JSON error format
- ✅ Any system needing trimmed, validated data

---

**Quick Import:**
```python
from auth_manager.validators.rules.story_validation import validate_story_input
```

**Quick Test:**
```python
result = validate_story_input("Title", "Content", "Captions")
if result["isValid"]:
    use_data(result["validatedData"])
else:
    show_errors(result["errors"])
```

