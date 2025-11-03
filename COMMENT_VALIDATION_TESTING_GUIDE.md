# Comment Validation Testing Guide

## GraphQL Mutation Examples

### Post Comment Creation

#### ✅ Valid Comment (Should Succeed)

```graphql
mutation CreatePostComment {
  createComment(input: {
    postUid: "post-123"
    content: "Great post! Thanks for sharing."
  }) {
    success
    message
    comment {
      uid
      content
    }
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "createComment": {
      "success": true,
      "message": "Comment created successfully",
      "comment": {
        "uid": "comment-456",
        "content": "Great post! Thanks for sharing."
      }
    }
  }
}
```

---

#### ❌ Empty Comment (Should Fail)

```graphql
mutation CreateEmptyComment {
  createComment(input: {
    postUid: "post-123"
    content: ""
  }) {
    success
    message
    comment {
      uid
    }
  }
}
```

**Expected Response**:
```json
{
  "errors": [
    {
      "message": "content cannot be empty or contain only whitespace.",
      "extensions": {
        "code": "BAD_REQUEST",
        "status_code": 400
      },
      "path": ["createComment", "content"]
    }
  ]
}
```

---

#### ❌ Whitespace-Only Comment (Should Fail)

```graphql
mutation CreateWhitespaceComment {
  createComment(input: {
    postUid: "post-123"
    content: "     "
  }) {
    success
    message
  }
}
```

**Expected Response**:
```json
{
  "errors": [
    {
      "message": "content cannot be empty or contain only whitespace.",
      "extensions": {
        "code": "BAD_REQUEST",
        "status_code": 400
      },
      "path": ["createComment", "content"]
    }
  ]
}
```

---

#### ❌ Comment Too Long (Should Fail)

```graphql
mutation CreateLongComment {
  createComment(input: {
    postUid: "post-123"
    content: "Lorem ipsum dolor sit amet, consectetur adipiscing elit... (201+ characters)"
  }) {
    success
    message
  }
}
```

**Expected Response**:
```json
{
  "errors": [
    {
      "message": "content must be between 1 and 200 characters.",
      "extensions": {
        "code": "BAD_REQUEST",
        "status_code": 400
      },
      "path": ["createComment", "content"]
    }
  ]
}
```

---

#### ❌ HTML Tags (Should Fail)

```graphql
mutation CreateHTMLComment {
  createComment(input: {
    postUid: "post-123"
    content: "<script>alert('XSS')</script>"
  }) {
    success
    message
  }
}
```

**Expected Response**:
```json
{
  "errors": [
    {
      "message": "HTML tags are not allowed.",
      "extensions": {
        "code": "BAD_REQUEST",
        "status_code": 400
      },
      "path": ["createComment", "content"]
    }
  ]
}
```

---

#### ✅ Minimum Length (Should Succeed)

```graphql
mutation CreateMinComment {
  createComment(input: {
    postUid: "post-123"
    content: "A"
  }) {
    success
    message
    comment {
      content
    }
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "createComment": {
      "success": true,
      "message": "Comment created successfully",
      "comment": {
        "content": "A"
      }
    }
  }
}
```

---

#### ✅ Maximum Length (Should Succeed)

```graphql
mutation CreateMaxComment {
  createComment(input: {
    postUid: "post-123"
    content: "A very long comment with exactly 200 characters... (fill to 200)"
  }) {
    success
    message
    comment {
      content
    }
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "createComment": {
      "success": true,
      "message": "Comment created successfully",
      "comment": {
        "content": "A very long comment with exactly 200 characters..."
      }
    }
  }
}
```

---

#### ✅ Whitespace Trimming (Should Trim and Succeed)

```graphql
mutation CreateTrimmedComment {
  createComment(input: {
    postUid: "post-123"
    content: "   Trimmed comment   "
  }) {
    success
    message
    comment {
      content
    }
  }
}
```

**Expected Response** (note trimmed content):
```json
{
  "data": {
    "createComment": {
      "success": true,
      "message": "Comment created successfully",
      "comment": {
        "content": "Trimmed comment"
      }
    }
  }
}
```

---

### Story Comment Creation

#### ✅ Valid Story Comment

```graphql
mutation CreateStoryComment {
  createStoryComment(input: {
    storyUid: "story-789"
    content: "Nice story!"
  }) {
    success
    message
  }
}
```

**Note**: Story comments use `NonSpecialCharacterString1_200` which:
- ✅ Allows letters, numbers, spaces, basic punctuation (.,!?;:'")
- ❌ Blocks special symbols like `@#$%^&*`

---

### Profile Comment Creation

#### ✅ Valid Profile Comment

```graphql
mutation CreateProfileComment {
  createProfileCommentV2(input: {
    uid: "user-profile-123"
    category: ACHIEVEMENT
    content: "Congratulations on your achievement!"
  }) {
    success
    message
  }
}
```

---

## Python Unit Test Examples

### Test Post Comment Validator

```python
import pytest
from graphql import GraphQLError
from auth_manager.validators.custom_graphql_validator import SpecialCharacterString1_200

def test_valid_comment():
    validator = SpecialCharacterString1_200()
    result = validator.parse_value("Great post!")
    assert result == "Great post!"

def test_empty_comment():
    validator = SpecialCharacterString1_200()
    with pytest.raises(GraphQLError) as exc_info:
        validator.parse_value("")
    assert "cannot be empty or contain only whitespace" in str(exc_info.value)

def test_whitespace_only_comment():
    validator = SpecialCharacterString1_200()
    with pytest.raises(GraphQLError) as exc_info:
        validator.parse_value("     ")
    assert "cannot be empty or contain only whitespace" in str(exc_info.value)

def test_comment_too_long():
    validator = SpecialCharacterString1_200()
    long_comment = "A" * 201
    with pytest.raises(GraphQLError) as exc_info:
        validator.parse_value(long_comment)
    assert "must be between 1 and 200 characters" in str(exc_info.value)

def test_html_tags_blocked():
    validator = SpecialCharacterString1_200()
    with pytest.raises(GraphQLError) as exc_info:
        validator.parse_value("<script>alert('xss')</script>")
    assert "HTML tags are not allowed" in str(exc_info.value)

def test_whitespace_trimming():
    validator = SpecialCharacterString1_200()
    result = validator.parse_value("   Trimmed   ")
    assert result == "Trimmed"

def test_minimum_length():
    validator = SpecialCharacterString1_200()
    result = validator.parse_value("A")
    assert result == "A"

def test_maximum_length():
    validator = SpecialCharacterString1_200()
    max_comment = "A" * 200
    result = validator.parse_value(max_comment)
    assert result == max_comment
```

---

## Manual Testing Steps

### 1. Test via GraphQL Playground

1. Open your GraphQL playground (e.g., `http://localhost:8000/graphql`)
2. Ensure you're authenticated (add auth token to headers)
3. Run each mutation example above
4. Verify error messages match expected responses

### 2. Test via cURL

```bash
# Valid comment
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "mutation { createComment(input: {postUid: \"post-123\", content: \"Great!\"}) { success message } }"
  }'

# Empty comment (should fail)
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "mutation { createComment(input: {postUid: \"post-123\", content: \"\"}) { success message } }"
  }'

# Whitespace-only (should fail)
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "mutation { createComment(input: {postUid: \"post-123\", content: \"     \"}) { success message } }"
  }'
```

### 3. Test via Python Requests

```python
import requests

GRAPHQL_URL = "http://localhost:8000/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}

# Valid comment
valid_query = """
mutation {
  createComment(input: {
    postUid: "post-123"
    content: "Great post!"
  }) {
    success
    message
    comment {
      uid
      content
    }
  }
}
"""

response = requests.post(GRAPHQL_URL, json={"query": valid_query}, headers=HEADERS)
print(response.json())

# Empty comment (should fail)
empty_query = """
mutation {
  createComment(input: {
    postUid: "post-123"
    content: ""
  }) {
    success
    message
  }
}
"""

response = requests.post(GRAPHQL_URL, json={"query": empty_query}, headers=HEADERS)
print(response.json())
# Expected: Error with message "cannot be empty or contain only whitespace"
```

---

## Integration Test Checklist

- [ ] Test valid comment creation (1-200 chars)
- [ ] Test empty comment rejection
- [ ] Test whitespace-only comment rejection
- [ ] Test comment > 200 chars rejection
- [ ] Test HTML tag rejection
- [ ] Test whitespace trimming
- [ ] Test minimum length (1 char)
- [ ] Test maximum length (200 chars)
- [ ] Test update comment validation
- [ ] Test story comment validation
- [ ] Test profile comment validation
- [ ] Test error message format
- [ ] Test error code (400 BAD_REQUEST)

---

## Frontend Validation Recommendations

To provide better UX, implement client-side validation that matches backend rules:

```javascript
// Frontend validation function
function validateComment(content) {
  // Trim whitespace
  const trimmed = content.trim();
  
  // Check if empty
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: "Comment cannot be empty or contain only whitespace."
    };
  }
  
  // Check length
  if (trimmed.length < 1 || trimmed.length > 200) {
    return {
      valid: false,
      error: "Comment must be between 1 and 200 characters."
    };
  }
  
  // Check for HTML tags
  if (/<[^>]+>/.test(trimmed)) {
    return {
      valid: false,
      error: "HTML tags are not allowed."
    };
  }
  
  return {
    valid: true,
    content: trimmed
  };
}

// Usage example
const userInput = document.getElementById('commentInput').value;
const validation = validateComment(userInput);

if (!validation.valid) {
  showError(validation.error);
} else {
  submitComment(validation.content);
}
```

---

## Common Edge Cases

| Case | Input | Expected Behavior |
|------|-------|-------------------|
| Empty string | `""` | ❌ Rejected |
| Single space | `" "` | ❌ Rejected (after trim) |
| Multiple spaces | `"     "` | ❌ Rejected (after trim) |
| Newlines only | `"\n\n\n"` | ❌ Rejected (after trim) |
| Tabs only | `"\t\t\t"` | ❌ Rejected (after trim) |
| Single char | `"A"` | ✅ Accepted |
| 200 chars | `"A" * 200` | ✅ Accepted |
| 201 chars | `"A" * 201` | ❌ Rejected |
| Emoji | `"Great! 😊"` | ✅ Accepted (post comments) |
| Emoji | `"Great! 😊"` | ❌ Rejected (story/profile comments) |
| HTML | `"<b>Bold</b>"` | ❌ Rejected |
| With spaces | `"  Hello  "` | ✅ Accepted, trimmed to `"Hello"` |

---

## Monitoring & Logging

### Track Validation Failures

Monitor these metrics in production:
- Count of empty comment attempts
- Count of too-long comment attempts
- Count of HTML injection attempts
- Count of whitespace-only attempts

### Example Log Format

```json
{
  "event": "comment_validation_failed",
  "user_id": "user-123",
  "mutation": "createComment",
  "field": "content",
  "error": "content cannot be empty or contain only whitespace",
  "input_length": 5,
  "timestamp": "2025-10-27T10:30:00Z"
}
```

---

## Summary

✅ All comment types now have consistent validation:
- **Min**: 1 character
- **Max**: 200 characters
- **Whitespace**: Trimmed and rejected if only whitespace
- **HTML**: Blocked
- **Error Messages**: Clear and user-friendly

🧪 Test thoroughly before deploying to production!

