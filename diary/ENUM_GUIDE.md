# 🎯 Enum Types Guide - Type-Safe Inputs

## ✅ What Changed

The Diary module now uses **GraphQL Enums** instead of String fields for type selection. This ensures users can **only select valid options** from dropdowns, preventing invalid data entry.

---

## 📊 Available Enums

### 1. **FolderTypeEnum**
Used when creating folders to select the folder type.

**Values:**
- `NOTES` - For storing notes
- `DOCUMENTS` - For storing documents

**Usage:**
```graphql
mutation {
  createDiaryFolder(input: {
    name: "My Folder"
    folder_type: NOTES  # ← Select from dropdown: NOTES or DOCUMENTS
  }) {
    folder { uid }
    success
  }
}
```

---

### 2. **PrivacyLevelEnum**
Used when creating/updating notes and documents to set privacy.

**Values:**
- `PRIVATE` - Only visible to you
- `INNER` - Visible to inner circle
- `OUTER` - Visible to outer circle
- `UNIVERSE` - Visible to all connections

**Usage:**
```graphql
mutation {
  createDiaryNote(input: {
    title: "Private Note"
    folder_uid: "abc123"
    privacy_level: PRIVATE  # ← Select from dropdown
  }) {
    note { uid }
    success
  }
}
```

---

### 3. **TodoStatusEnum**
Used when updating todos to change status.

**Values:**
- `PENDING` - Todo is not completed
- `COMPLETED` - Todo is done

**Usage:**
```graphql
mutation {
  updateDiaryTodo(input: {
    uid: "todo-123"
    status: COMPLETED  # ← Select from dropdown: PENDING or COMPLETED
  }) {
    todo { uid status }
    success
  }
}
```

---

## 🎨 Frontend Benefits

### **Before (String):**
```javascript
// User could type anything - error prone!
const folderType = "note";  // ❌ Typo! Should be "notes"
const folderType = "NOTES"; // ❌ Wrong case!
const folderType = "anything"; // ❌ Invalid value!
```

### **After (Enum):**
```javascript
// User must select from dropdown - type safe!
const folderType = "NOTES";  // ✅ Valid
const folderType = "DOCUMENTS";  // ✅ Valid
// User cannot enter invalid values
```

---

## 📱 How It Appears in GraphQL Clients

### **GraphiQL / Apollo Studio:**
When you use the mutation, you'll see a **dropdown** for enum fields:

```graphql
mutation {
  createDiaryFolder(input: {
    name: "Test"
    folder_type: [NOTES ▼]  # ← Dropdown with: NOTES, DOCUMENTS
  })
}
```

### **Frontend Code (Apollo/URQL):**
```typescript
// TypeScript gets automatic type checking!
const CREATE_FOLDER = gql`
  mutation CreateFolder($input: CreateDiaryFolderInput!) {
    createDiaryFolder(input: $input) {
      folder { uid }
      success
    }
  }
`;

// TypeScript knows folderType must be "NOTES" or "DOCUMENTS"
const variables = {
  input: {
    name: "My Folder",
    folder_type: "NOTES"  // ✅ TypeScript validates this
  }
};
```

---

## 🔧 Complete Usage Examples

### **Creating a Notes Folder:**
```graphql
mutation {
  createDiaryFolder(input: {
    name: "Work Notes"
    folder_type: NOTES  # Enum - select from dropdown
    color: "#FF6B6B"
  }) {
    folder {
      uid
      name
      folder_type  # Returns: "notes"
    }
    success
    message
  }
}
```

### **Creating a Documents Folder:**
```graphql
mutation {
  createDiaryFolder(input: {
    name: "Important Docs"
    folder_type: DOCUMENTS  # Enum - select from dropdown
    color: "#42A5F5"
  }) {
    folder {
      uid
      name
      folder_type  # Returns: "documents"
    }
    success
    message
  }
}
```

### **Creating a Private Note:**
```graphql
mutation {
  createDiaryNote(input: {
    title: "Secret Ideas"
    content: "My brilliant ideas..."
    folder_uid: "folder-123"
    privacy_level: PRIVATE  # Enum - select from dropdown
  }) {
    note {
      uid
      privacy_level  # Returns: "private"
    }
    success
  }
}
```

### **Creating a Shared Document:**
```graphql
mutation {
  createDiaryDocument(input: {
    title: "Team Document"
    folder_uid: "folder-456"
    document_ids: ["file-1"]
    privacy_level: INNER  # Enum - share with inner circle
  }) {
    document {
      uid
      privacy_level  # Returns: "inner"
    }
    success
  }
}
```

### **Completing a Todo:**
```graphql
mutation {
  updateDiaryTodo(input: {
    uid: "todo-789"
    status: COMPLETED  # Enum - mark as done
  }) {
    todo {
      uid
      status  # Returns: "completed"
    }
    success
  }
}
```

---

## 🎯 Validation Rules

### **FolderTypeEnum:**
- ✅ Must be exactly `NOTES` or `DOCUMENTS`
- ❌ Cannot be `"notes"` (lowercase) - GraphQL will reject
- ❌ Cannot be `"note"` (typo) - GraphQL will reject
- ❌ Cannot be empty or null when required

### **PrivacyLevelEnum:**
- ✅ Must be `PRIVATE`, `INNER`, `OUTER`, or `UNIVERSE`
- ❌ Cannot be `"public"` - not a valid option
- ✅ Optional fields default to `PRIVATE` if not specified

### **TodoStatusEnum:**
- ✅ Must be `PENDING` or `COMPLETED`
- ❌ Cannot be `"done"` or `"finished"`
- ✅ New todos default to `PENDING`

---

## 🚨 Error Examples

### **Invalid Folder Type:**
```graphql
# ❌ This will fail:
mutation {
  createDiaryFolder(input: {
    name: "Test"
    folder_type: "notes"  # Wrong! Must be NOTES (enum)
  })
}

# Error: "notes" is not a valid value for FolderTypeEnum
```

### **Invalid Privacy Level:**
```graphql
# ❌ This will fail:
mutation {
  createDiaryNote(input: {
    title: "Note"
    folder_uid: "123"
    privacy_level: "public"  # Wrong! Not a valid enum value
  })
}

# Error: "public" is not a valid value for PrivacyLevelEnum
```

---

## ✅ Migration from String Version

If you had the old string-based version, here's what changed:

### **Old Way (String):**
```graphql
mutation {
  createDiaryFolder(input: {
    folder_type: "notes"  # String - lowercase
  })
}
```

### **New Way (Enum):**
```graphql
mutation {
  createDiaryFolder(input: {
    folder_type: NOTES  # Enum - uppercase, no quotes
  })
}
```

**Note:** The database still stores lowercase values ("notes", "documents", etc.), but the GraphQL API now enforces type safety.

---

## 🎨 Frontend Dropdown Example

### **React Example:**
```jsx
import { useMutation } from '@apollo/client';

function CreateFolderForm() {
  const [createFolder] = useMutation(CREATE_FOLDER_MUTATION);
  
  return (
    <form onSubmit={handleSubmit}>
      <input name="name" placeholder="Folder name" />
      
      {/* Dropdown for folder type */}
      <select name="folder_type">
        <option value="NOTES">Notes</option>
        <option value="DOCUMENTS">Documents</option>
      </select>
      
      {/* Dropdown for privacy level */}
      <select name="privacy_level">
        <option value="PRIVATE">Private</option>
        <option value="INNER">Inner Circle</option>
        <option value="OUTER">Outer Circle</option>
        <option value="UNIVERSE">Everyone</option>
      </select>
      
      <button type="submit">Create Folder</button>
    </form>
  );
}
```

---

## 📝 Summary

**Benefits of Enums:**
- ✅ Type safety - no invalid values
- ✅ Auto-complete in GraphQL clients
- ✅ Better developer experience
- ✅ Frontend dropdowns work perfectly
- ✅ Clear API documentation
- ✅ Prevents typos and errors

**What You Need to Know:**
- Use `NOTES` or `DOCUMENTS` for folder_type (uppercase, no quotes)
- Use `PRIVATE`, `INNER`, `OUTER`, or `UNIVERSE` for privacy_level
- Use `PENDING` or `COMPLETED` for todo status
- GraphQL will validate all inputs automatically

---

**Version:** 1.0.1 (with Enums)  
**Updated:** November 30, 2025
