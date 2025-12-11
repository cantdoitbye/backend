# Diary Module

## Overview

The **Diary Module** is a comprehensive personal organization system for the Ooumph platform that allows users to organize their thoughts, documents, and tasks efficiently. It provides a flexible folder-based structure for notes and documents, along with an independent todo system.

---

## Features

### 📁 Folder Organization
- Create colored folders for notes and documents
- Two folder types: `notes` and `documents`
- Visual color coding for easy identification
- Organize items within folders

### 📝 Notes
- Rich text notes with title and content
- Store notes in organized folders
- Privacy levels for sharing (private, inner, outer, universe)
- Update and move notes between folders

### 📄 Documents
- Upload and organize multiple document files
- Support for PDFs, Word docs, and other file types
- Folder-based organization
- Privacy controls for sharing

### ✅ Todos
- Independent todo items (not in folders)
- Calendar integration with dates and times
- Status tracking (pending/completed)
- Date-based organization for calendar views

---

## Architecture

### Models

#### `DiaryFolder`
Container for organizing notes or documents.

**Fields:**
- `uid`: Unique identifier
- `name`: Folder name
- `folder_type`: 'notes' or 'documents'
- `color`: Hex color code for UI
- `created_on`: Creation timestamp
- `updated_on`: Last update timestamp

**Relationships:**
- `created_by` → Users
- `notes` → DiaryNote (if folder_type='notes')
- `documents` → DiaryDocument (if folder_type='documents')

---

#### `DiaryNote`
Individual notes stored in notes folders.

**Fields:**
- `uid`: Unique identifier
- `title`: Note title (required)
- `content`: Rich text content
- `privacy_level`: 'private', 'inner', 'outer', 'universe'
- `created_on`: Creation timestamp
- `updated_on`: Last update timestamp

**Relationships:**
- `created_by` → Users
- `folder` → DiaryFolder (required, must be type='notes')

---

#### `DiaryDocument`
Documents stored in documents folders.

**Fields:**
- `uid`: Unique identifier
- `title`: Document title (required)
- `description`: Optional description
- `document_ids`: Array of uploaded file IDs
- `privacy_level`: 'private', 'inner', 'outer', 'universe'
- `created_on`: Creation timestamp
- `updated_on`: Last update timestamp

**Relationships:**
- `created_by` → Users
- `folder` → DiaryFolder (required, must be type='documents')

---

#### `DiaryTodo`
Independent todo items with calendar integration.

**Fields:**
- `uid`: Unique identifier
- `title`: Todo title (required)
- `description`: Optional description
- `status`: 'pending' or 'completed'
- `date`: Optional due date
- `time`: Optional due time
- `created_on`: Creation timestamp
- `updated_on`: Last update timestamp

**Relationships:**
- `created_by` → Users

---

## GraphQL API

### Mutations

#### Folder Mutations

**createDiaryFolder**
```graphql
mutation {
  createDiaryFolder(input: {
    name: "Work Notes"
    folder_type: NOTES  # Select from: NOTES or DOCUMENTS
    color: "#FF6B6B"
  }) {
    folder {
      uid
      name
      folder_type
      color
    }
    success
    message
  }
}
```

**updateDiaryFolder**
```graphql
mutation {
  updateDiaryFolder(input: {
    uid: "folder-uid"
    name: "Updated Name"
    color: "#42A5F5"
  }) {
    folder {
      uid
      name
      color
    }
    success
    message
  }
}
```

**deleteDiaryFolder**
```graphql
mutation {
  deleteDiaryFolder(input: {
    uid: "folder-uid"
  }) {
    success
    message
  }
}
```

---

#### Note Mutations

**createDiaryNote**
```graphql
mutation {
  createDiaryNote(input: {
    title: "Meeting Notes"
    content: "Discussed project timeline..."
    folder_uid: "folder-uid"
    privacy_level: PRIVATE  # Select from: PRIVATE, INNER, OUTER, UNIVERSE
  }) {
    note {
      uid
      title
      content
      privacy_level
      folder {
        uid
        name
      }
    }
    success
    message
  }
}
```

**updateDiaryNote**
```graphql
mutation {
  updateDiaryNote(input: {
    uid: "note-uid"
    title: "Updated Title"
    content: "Updated content..."
    folder_uid: "new-folder-uid"  # Optional: move to different folder
    privacy_level: "inner"
  }) {
    note {
      uid
      title
      content
    }
    success
    message
  }
}
```

**deleteDiaryNote**
```graphql
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

#### Document Mutations

**createDiaryDocument**
```graphql
mutation {
  createDiaryDocument(input: {
    title: "Onboarding Flow"
    description: "Company onboarding process"
    folder_uid: "folder-uid"
    document_ids: ["file-id-1", "file-id-2"]
    privacy_level: "private"
  }) {
    document {
      uid
      title
      description
      document_ids
    }
    success
    message
  }
}
```

**updateDiaryDocument**
```graphql
mutation {
  updateDiaryDocument(input: {
    uid: "document-uid"
    title: "Updated Title"
    document_ids: ["new-file-id-1"]
  }) {
    document {
      uid
      title
    }
    success
    message
  }
}
```

**deleteDiaryDocument**
```graphql
mutation {
  deleteDiaryDocument(input: {
    uid: "document-uid"
  }) {
    success
    message
  }
}
```

---

#### Todo Mutations

**createDiaryTodo**
```graphql
mutation {
  createDiaryTodo(input: {
    title: "Finish project report"
    description: "Complete quarterly report"
    date: "2025-12-01"
    time: "2025-12-01T14:00:00Z"
  }) {
    todo {
      uid
      title
      description
      status
      date
      time
    }
    success
    message
  }
}
```

**updateDiaryTodo**
```graphql
mutation {
  updateDiaryTodo(input: {
    uid: "todo-uid"
    title: "Updated task"
    status: COMPLETED  # Select from: PENDING or COMPLETED
    date: "2025-12-02"
  }) {
    todo {
      uid
      status
    }
    success
    message
  }
}
```

**deleteDiaryTodo**
```graphql
mutation {
  deleteDiaryTodo(input: {
    uid: "todo-uid"
  }) {
    success
    message
  }
}
```

---

### Queries

#### Folder Queries

**myDiaryFolders**
```graphql
query {
  myDiaryFolders(folder_type: "notes") {
    uid
    name
    folder_type
    color
    notes_count
    created_on
  }
}
```

**diaryFolderByUid**
```graphql
query {
  diaryFolderByUid(uid: "folder-uid") {
    uid
    name
    folder_type
    notes {
      uid
      title
    }
    documents {
      uid
      title
    }
  }
}
```

---

#### Note Queries

**myDiaryNotes**
```graphql
query {
  myDiaryNotes(folder_uid: "folder-uid") {
    uid
    title
    content
    privacy_level
    folder {
      uid
      name
    }
    created_on
    updated_on
  }
}
```

**diaryNoteByUid**
```graphql
query {
  diaryNoteByUid(uid: "note-uid") {
    uid
    title
    content
    privacy_level
    folder {
      uid
      name
      color
    }
  }
}
```

---

#### Document Queries

**myDiaryDocuments**
```graphql
query {
  myDiaryDocuments(folder_uid: "folder-uid") {
    uid
    title
    description
    document_ids
    privacy_level
    folder {
      uid
      name
    }
  }
}
```

**diaryDocumentByUid**
```graphql
query {
  diaryDocumentByUid(uid: "document-uid") {
    uid
    title
    description
    document_ids
    folder {
      uid
      name
    }
  }
}
```

---

#### Todo Queries

**myDiaryTodos**
```graphql
query {
  myDiaryTodos(status: "pending") {
    uid
    title
    description
    status
    date
    time
    created_on
  }
}
```

**diaryTodoByUid**
```graphql
query {
  diaryTodoByUid(uid: "todo-uid") {
    uid
    title
    description
    status
    date
    time
  }
}
```

**diaryTodosByDate**
```graphql
query {
  diaryTodosByDate(date: "2025-12-01") {
    uid
    title
    description
    status
    time
  }
}
```

---

## Integration Guide

### Step 1: Add to Django Settings

```python
# settings/base.py

INSTALLED_APPS = [
    # ... existing apps
    'diary',  # Add this
]
```

### Step 2: Update Users Model

Add relationships in `auth_manager/models.py`:

```python
class Users(DjangoNode, StructuredNode):
    # ... existing fields
    
    # Add diary relationships
    diary_folders = RelationshipTo('diary.models.DiaryFolder', 'HAS_DIARY_FOLDER')
    diary_notes = RelationshipTo('diary.models.DiaryNote', 'HAS_DIARY_NOTE')
    diary_documents = RelationshipTo('diary.models.DiaryDocument', 'HAS_DIARY_DOCUMENT')
    diary_todos = RelationshipTo('diary.models.DiaryTodo', 'HAS_DIARY_TODO')
```

### Step 3: Update GraphQL Schema

In `schema/schema.py`:

```python
from diary.graphql.query import Query as DiaryQuery
from diary.graphql.mutations import Mutation as DiaryMutation

class Query(
    # ... existing queries
    DiaryQuery,
    graphene.ObjectType
):
    pass

class Mutation(
    # ... existing mutations
    DiaryMutation,
    graphene.ObjectType
):
    pass
```

### Step 4: Create Neo4j Indexes

```bash
# In Django shell or management command
from diary.models import DiaryFolder, DiaryNote, DiaryDocument, DiaryTodo

# Create indexes for better query performance
DiaryFolder.install_all_labels()
DiaryNote.install_all_labels()
DiaryDocument.install_all_labels()
DiaryTodo.install_all_labels()
```

Or run in Neo4j directly:

```cypher
CREATE INDEX diary_folder_uid IF NOT EXISTS FOR (f:DiaryFolder) ON (f.uid);
CREATE INDEX diary_note_uid IF NOT EXISTS FOR (n:DiaryNote) ON (n.uid);
CREATE INDEX diary_document_uid IF NOT EXISTS FOR (d:DiaryDocument) ON (d.uid);
CREATE INDEX diary_todo_uid IF NOT EXISTS FOR (t:DiaryTodo) ON (t.uid);
```

### Step 5: Restart Server

```bash
docker-compose restart django_backend
```

---

## Business Rules

### Folder Rules
- Users can create unlimited folders
- Folder type ('notes' or 'documents') cannot be changed after creation
- Folder names can be duplicated
- Deleting a folder deletes all items within it

### Note Rules
- Notes MUST belong to a folder of type 'notes'
- Notes can be moved between notes folders
- Privacy levels control sharing with circles

### Document Rules
- Documents MUST belong to a folder of type 'documents'
- Documents require at least one file upload
- Documents can be moved between documents folders
- Privacy levels control sharing with circles

### Todo Rules
- Todos are INDEPENDENT (not in folders)
- Todos have status: 'pending' or 'completed'
- Todos can have optional date/time for calendar integration
- Todos are sorted by date, then creation time

---

## Privacy Levels

All notes and documents support four privacy levels:

- **private**: Only visible to the creator
- **inner**: Visible to inner circle connections
- **outer**: Visible to outer circle connections
- **universe**: Visible to all connections

---

## File Structure

```
diary/
├── __init__.py
├── apps.py
├── models.py
├── graphql/
│   ├── __init__.py
│   ├── types.py
│   ├── inputs.py
│   ├── mutations.py
│   ├── query.py
│   └── messages.py
└── README.md
```

---

## Testing

### Example Test Cases

```python
# Test creating a folder
mutation = """
mutation {
  createDiaryFolder(input: {
    name: "Test Folder"
    folder_type: "notes"
  }) {
    folder { uid }
    success
  }
}
"""

# Test creating a note
mutation = """
mutation {
  createDiaryNote(input: {
    title: "Test Note"
    content: "Content"
    folder_uid: "folder-uid"
  }) {
    note { uid }
    success
  }
}
"""

# Test creating a todo
mutation = """
mutation {
  createDiaryTodo(input: {
    title: "Test Todo"
    date: "2025-12-01"
  }) {
    todo { uid }
    success
  }
}
"""
```

---

## Future Enhancements

- [ ] AI-assisted note creation
- [ ] Note templates
- [ ] Collaborative folders
- [ ] Document versioning
- [ ] Full-text search
- [ ] Note linking/backlinking
- [ ] Recurring todos
- [ ] Todo reminders/notifications
- [ ] Export to PDF/Word
- [ ] Saved posts integration

---

## Support

For issues or questions, please contact the Ooumph development team.

---

## Version

**Version:** 1.0.0  
**Last Updated:** November 30, 2025
