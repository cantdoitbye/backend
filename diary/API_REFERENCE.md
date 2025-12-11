# Diary Module - API Reference

Quick reference for all GraphQL mutations and queries.

---

## 🔧 Mutations (12 Total)

### Folder Mutations (3)

#### createDiaryFolder
Create a new folder for organizing notes or documents.

**Input:**
```graphql
{
  name: String!           # Folder name
  folder_type: String!    # "notes" or "documents"
  color: String           # Hex color (optional)
}
```

**Returns:** `{ folder, success, message }`

---

#### updateDiaryFolder
Update folder name or color.

**Input:**
```graphql
{
  uid: String!      # Folder UID
  name: String      # New name (optional)
  color: String     # New color (optional)
}
```

**Returns:** `{ folder, success, message }`

**Note:** Cannot change folder_type after creation.

---

#### deleteDiaryFolder
Delete a folder (fails if folder contains items).

**Input:**
```graphql
{
  uid: String!      # Folder UID
}
```

**Returns:** `{ success, message }`

---

### Note Mutations (3)

#### createDiaryNote
Create a new note in a folder.

**Input:**
```graphql
{
  title: String!          # Note title
  content: String         # Note content (optional)
  folder_uid: String!     # Folder UID (required)
  privacy_level: String   # "private", "inner", "outer", "universe" (optional)
}
```

**Returns:** `{ note, success, message }`

---

#### updateDiaryNote
Update note content or move to different folder.

**Input:**
```graphql
{
  uid: String!            # Note UID
  title: String           # New title (optional)
  content: String         # New content (optional)
  folder_uid: String      # Move to new folder (optional)
  privacy_level: String   # Change privacy (optional)
}
```

**Returns:** `{ note, success, message }`

---

#### deleteDiaryNote
Delete a note.

**Input:**
```graphql
{
  uid: String!      # Note UID
}
```

**Returns:** `{ success, message }`

---

### Document Mutations (3)

#### createDiaryDocument
Create a new document with file attachments.

**Input:**
```graphql
{
  title: String!          # Document title
  description: String     # Description (optional)
  folder_uid: String!     # Folder UID (required)
  document_ids: [String!]!  # File IDs (required, min 1)
  privacy_level: String   # Privacy level (optional)
}
```

**Returns:** `{ document, success, message }`

---

#### updateDiaryDocument
Update document metadata or files.

**Input:**
```graphql
{
  uid: String!            # Document UID
  title: String           # New title (optional)
  description: String     # New description (optional)
  folder_uid: String      # Move to new folder (optional)
  document_ids: [String]  # Replace files (optional)
  privacy_level: String   # Change privacy (optional)
}
```

**Returns:** `{ document, success, message }`

---

#### deleteDiaryDocument
Delete a document.

**Input:**
```graphql
{
  uid: String!      # Document UID
}
```

**Returns:** `{ success, message }`

---

### Todo Mutations (3)

#### createDiaryTodo
Create a new todo item.

**Input:**
```graphql
{
  title: String!        # Todo title
  description: String   # Description (optional)
  date: Date            # Due date (optional)
  time: DateTime        # Specific time (optional)
}
```

**Returns:** `{ todo, success, message }`

**Note:** Todos are independent, not in folders.

---

#### updateDiaryTodo
Update todo details or status.

**Input:**
```graphql
{
  uid: String!          # Todo UID
  title: String         # New title (optional)
  description: String   # New description (optional)
  status: String        # "pending" or "completed" (optional)
  date: Date            # Change date (optional)
  time: DateTime        # Change time (optional)
}
```

**Returns:** `{ todo, success, message }`

---

#### deleteDiaryTodo
Delete a todo.

**Input:**
```graphql
{
  uid: String!      # Todo UID
}
```

**Returns:** `{ success, message }`

---

## 🔍 Queries (9 Total)

### Folder Queries (2)

#### myDiaryFolders
Get all folders created by the authenticated user.

**Arguments:**
- `folder_type: String` (optional) - Filter by "notes" or "documents"

**Returns:**
```graphql
[{
  uid: String
  name: String
  folder_type: String
  color: String
  created_by: UserType
  created_on: DateTime
  updated_on: DateTime
  notes_count: Int
  documents_count: Int
  notes: [DiaryNoteType]      # If folder_type='notes'
  documents: [DiaryDocumentType]  # If folder_type='documents'
}]
```

---

#### diaryFolderByUid
Get a specific folder with nested items.

**Arguments:**
- `uid: String!` (required) - Folder UID

**Returns:** Single `DiaryFolderType` with nested notes/documents

---

### Note Queries (2)

#### myDiaryNotes
Get all notes created by the authenticated user.

**Arguments:**
- `folder_uid: String` (optional) - Filter by folder

**Returns:**
```graphql
[{
  uid: String
  title: String
  content: String
  privacy_level: String
  folder: DiaryFolderType
  created_by: UserType
  created_on: DateTime
  updated_on: DateTime
}]
```

**Sorted by:** `updated_on` DESC

---

#### diaryNoteByUid
Get a specific note by UID.

**Arguments:**
- `uid: String!` (required) - Note UID

**Returns:** Single `DiaryNoteType`

---

### Document Queries (2)

#### myDiaryDocuments
Get all documents created by the authenticated user.

**Arguments:**
- `folder_uid: String` (optional) - Filter by folder

**Returns:**
```graphql
[{
  uid: String
  title: String
  description: String
  document_ids: [String]
  document_urls: [String]  # Presigned URLs
  privacy_level: String
  folder: DiaryFolderType
  created_by: UserType
  created_on: DateTime
  updated_on: DateTime
}]
```

**Sorted by:** `updated_on` DESC

---

#### diaryDocumentByUid
Get a specific document with file URLs.

**Arguments:**
- `uid: String!` (required) - Document UID

**Returns:** Single `DiaryDocumentType` with presigned URLs

---

### Todo Queries (3)

#### myDiaryTodos
Get all todos created by the authenticated user.

**Arguments:**
- `status: String` (optional) - Filter by "pending" or "completed"
- `date: Date` (optional) - Filter by specific date

**Returns:**
```graphql
[{
  uid: String
  title: String
  description: String
  status: String
  date: Date
  time: DateTime
  created_by: UserType
  created_on: DateTime
  updated_on: DateTime
}]
```

**Sorted by:** `date` ASC, then `created_on` DESC

---

#### diaryTodoByUid
Get a specific todo by UID.

**Arguments:**
- `uid: String!` (required) - Todo UID

**Returns:** Single `DiaryTodoType`

---

#### diaryTodosByDate
Get all todos for a specific date (calendar view).

**Arguments:**
- `date: Date!` (required) - Date to filter by

**Returns:** List of `DiaryTodoType` for that date

**Sorted by:** `time` if available, otherwise `created_on`

---

## 📝 Complete Examples

### Full Workflow: Create Folder → Note → Update → Delete

```graphql
# 1. Create a notes folder
mutation {
  createDiaryFolder(input: {
    name: "Work Notes"
    folder_type: "notes"
    color: "#4A90E2"
  }) {
    folder { uid name }
    success
  }
}

# 2. Create a note in that folder
mutation {
  createDiaryNote(input: {
    title: "Sprint Planning"
    content: "Goals for next sprint..."
    folder_uid: "folder-uid-from-step-1"
    privacy_level: "private"
  }) {
    note { uid title }
    success
  }
}

# 3. Update the note
mutation {
  updateDiaryNote(input: {
    uid: "note-uid-from-step-2"
    content: "Updated sprint goals..."
  }) {
    note { uid title content }
    success
  }
}

# 4. Query all notes
query {
  myDiaryNotes {
    uid
    title
    folder { name color }
  }
}

# 5. Delete the note
mutation {
  deleteDiaryNote(input: {
    uid: "note-uid"
  }) {
    success
    message
  }
}
```

---

### Todo Workflow: Create → Update Status → Query by Date

```graphql
# 1. Create todo
mutation {
  createDiaryTodo(input: {
    title: "Code Review"
    description: "Review PR #123"
    date: "2025-12-01"
    time: "2025-12-01T14:00:00"
  }) {
    todo { uid title status }
    success
  }
}

# 2. Mark as completed
mutation {
  updateDiaryTodo(input: {
    uid: "todo-uid"
    status: "completed"
  }) {
    todo { uid status }
    success
  }
}

# 3. Get all todos for a date
query {
  diaryTodosByDate(date: "2025-12-01") {
    uid
    title
    time
    status
  }
}

# 4. Get pending todos
query {
  myDiaryTodos(status: "pending") {
    uid
    title
    date
  }
}
```

---

## 🎨 Privacy Levels

| Level | Description |
|-------|-------------|
| `private` | Only visible to creator |
| `inner` | Visible to inner circle |
| `outer` | Visible to outer circle |
| `universe` | Visible to all connections |

**Usage:**
```graphql
createDiaryNote(input: {
  title: "..."
  privacy_level: "inner"  # Share with inner circle
})
```

---

## ⚠️ Validation Rules

### Folder Validation
- ✅ `folder_type` must be "notes" or "documents"
- ✅ `name` is required
- ✅ Cannot change `folder_type` after creation
- ✅ Cannot delete folder with items

### Note Validation
- ✅ `title` is required
- ✅ `folder_uid` is required
- ✅ Folder must be of type "notes"
- ✅ User must own the folder

### Document Validation
- ✅ `title` is required
- ✅ `folder_uid` is required
- ✅ `document_ids` must have at least 1 file
- ✅ Folder must be of type "documents"
- ✅ User must own the folder

### Todo Validation
- ✅ `title` is required
- ✅ `status` must be "pending" or "completed"
- ✅ No folder relationship (independent)

---

## 🔐 Authentication

All mutations and queries require authentication via JWT token.

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Error if not authenticated:**
```json
{
  "errors": [{
    "message": "Authentication is required for this operation."
  }]
}
```

---

## 📊 Response Format

### Success Response
```json
{
  "data": {
    "createDiaryFolder": {
      "folder": {
        "uid": "abc123",
        "name": "My Folder"
      },
      "success": true,
      "message": "Your diary folder has been successfully created."
    }
  }
}
```

### Error Response
```json
{
  "data": {
    "createDiaryFolder": {
      "folder": null,
      "success": false,
      "message": "Invalid folder type. Must be 'notes' or 'documents'."
    }
  }
}
```

---

## 🚀 Quick Start

```graphql
# 1. Create a notes folder
mutation { createDiaryFolder(input: {name: "Personal", folder_type: "notes"}) { folder { uid } success } }

# 2. Create a note
mutation { createDiaryNote(input: {title: "Test", folder_uid: "YOUR_FOLDER_UID"}) { note { uid } success } }

# 3. List your notes
query { myDiaryNotes { uid title folder { name } } }

# 4. Create a todo
mutation { createDiaryTodo(input: {title: "Buy milk"}) { todo { uid } success } }

# 5. List pending todos
query { myDiaryTodos(status: "pending") { uid title } }
```

---

**Version:** 1.0.0  
**Last Updated:** November 30, 2025
