# Diary Module - Testing Guide

## Test These Queries in Postman

### 1. Create a Folder (Notes)
```graphql
mutation CreateNotesFolder {
  createDiaryFolder(input: {
    name: "Personal Notes"
    folderType: NOTES
    color: "#FF6B6B"
  }) {
    success
    message
    folder {
      uid
      name
      folderType
      color
      notesCount
    }
  }
}
```

### 2. Create a Folder (Documents)
```graphql
mutation CreateDocumentsFolder {
  createDiaryFolder(input: {
    name: "Work Documents"
    folderType: DOCUMENTS
    color: "#4ECDC4"
  }) {
    success
    message
    folder {
      uid
      name
      folderType
      color
      documentsCount
    }
  }
}
```

### 3. Query All Folders
```graphql
query GetMyFolders {
  myDiaryFolders {
    uid
    name
    folderType
    color
    notesCount
    documentsCount
    createdOn
    updatedOn
    createdBy {
      uid
      username
    }
  }
}
```

### 4. Create a Note
```graphql
mutation CreateNote {
  createDiaryNote(input: {
    title: "My First Note"
    content: "This is the content of my note"
    folderUid: "FOLDER_UID_FROM_STEP_1"
    privacyLevel: PRIVATE
  }) {
    success
    message
    note {
      uid
      title
      content
      privacyLevel
      folder {
        uid
        name
        folderType
      }
      createdOn
    }
  }
}
```

### 5. Query All Notes
```graphql
query GetMyNotes {
  myDiaryNotes {
    uid
    title
    content
    privacyLevel
    folder {
      uid
      name
      folderType
      color
    }
    createdBy {
      uid
      username
    }
    createdOn
    updatedOn
  }
}
```

### 6. Create a Document (with file IDs)
**Note:** First upload files to your storage server to get document IDs

```graphql
mutation CreateDocument {
  createDiaryDocument(input: {
    title: "Project Specifications"
    description: "Technical specifications for the project"
    folderUid: "FOLDER_UID_FROM_STEP_2"
    documentIds: ["doc_abc123", "doc_xyz789"]
    privacyLevel: PRIVATE
  }) {
    success
    message
    document {
      uid
      title
      description
      documentIds
      documentUrls {
        fileId
        url
        fileName
        fileType
        fileSize
      }
      folder {
        uid
        name
      }
      createdOn
    }
  }
}
```

### 7. Query All Documents
```graphql
query GetMyDocuments {
  myDiaryDocuments {
    uid
    title
    description
    documentIds
    documentUrls {
      fileId
      url
      fileName
      fileType
      fileSize
    }
    privacyLevel
    folder {
      uid
      name
      folderType
    }
    createdOn
  }
}
```

### 8. Create a Todo
```graphql
mutation CreateTodo {
  createDiaryTodo(input: {
    title: "Complete project documentation"
    description: "Finish writing all technical docs"
    date: "2024-12-15"
  }) {
    success
    message
    todo {
      uid
      title
      description
      status
      date
      createdOn
    }
  }
}
```

### 9. Query All Todos
```graphql
query GetMyTodos {
  myDiaryTodos {
    uid
    title
    description
    status
    date
    time
    createdBy {
      uid
      username
    }
    createdOn
  }
}
```

### 10. Update a Note
```graphql
mutation UpdateNote {
  updateDiaryNote(input: {
    uid: "NOTE_UID_HERE"
    title: "Updated Title"
    content: "Updated content"
    privacyLevel: INNER
  }) {
    success
    message
    note {
      uid
      title
      content
      privacyLevel
      updatedOn
    }
  }
}
```

### 11. Update a Todo Status
```graphql
mutation CompleteTodo {
  updateDiaryTodo(input: {
    uid: "TODO_UID_HERE"
    status: COMPLETED
  }) {
    success
    message
    todo {
      uid
      title
      status
      updatedOn
    }
  }
}
```

### 12. Delete a Note
```graphql
mutation DeleteNote {
  deleteDiaryNote(input: {
    uid: "NOTE_UID_HERE"
  }) {
    success
    message
  }
}
```

## Expected Results

All queries should return data without any recursion errors. The key improvements:

1. ✅ **No "maximum recursion depth exceeded" errors**
2. ✅ **Folders show counts** (notesCount, documentsCount)
3. ✅ **Notes/Documents include folder info** (but folder doesn't include items back)
4. ✅ **Document URLs are generated** (presigned URLs for file access)
5. ✅ **Enums work correctly** (NOTES, DOCUMENTS, PRIVATE, etc.)

## Common Issues

### Issue: "Invalid folder type"
**Solution:** Use enum values: `NOTES` or `DOCUMENTS` (not strings)

### Issue: "Document files required"
**Solution:** Provide at least one document ID in the `documentIds` array

### Issue: "Folder not found"
**Solution:** Make sure you're using the correct folder UID from the create folder response

### Issue: "Note can only be added to folders of type 'notes'"
**Solution:** Make sure you're using a NOTES folder UID, not a DOCUMENTS folder UID

## Authentication

All queries require authentication. Make sure to include your JWT token in the headers:

```
Authorization: JWT your_token_here
```

Or in Postman GraphQL:
- Set the token in the Authorization tab
- Type: Bearer Token
- Token: your_jwt_token
