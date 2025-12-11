# Diary Module - Recursion Fix Summary

## Problem
The diary module was experiencing "maximum recursion depth exceeded" errors when querying folders, notes, or documents. This was caused by circular references in the GraphQL types.

## Root Cause
The circular reference chain was:
1. `DiaryFolderType.from_neomodel()` → loads all notes/documents
2. For each note, calls `DiaryNoteType.from_neomodel()`
3. `DiaryNoteType.from_neomodel()` → loads the folder
4. Calls `DiaryFolderType.from_neomodel()` again
5. **Infinite loop** → recursion error

## Solution
Added optional parameters to control nested relationship loading:

### DiaryFolderType
```python
@classmethod
def from_neomodel(cls, folder, include_items=False):
    # Only includes notes_count and documents_count
    # Does NOT include full notes/documents list by default
```

### DiaryNoteType
```python
@classmethod
def from_neomodel(cls, note, include_folder=True):
    # Includes folder info by default
    # But folder is loaded WITHOUT items (include_items=False)
```

### DiaryDocumentType
```python
@classmethod
def from_neomodel(cls, document, include_folder=True):
    # Includes folder info by default
    # But folder is loaded WITHOUT items (include_items=False)
```

## How It Works Now

### Query: myDiaryFolders
```graphql
query {
  myDiaryFolders {
    uid
    name
    folderType
    notesCount      # ✅ Shows count
    documentsCount  # ✅ Shows count
    # notes list is NOT included to avoid recursion
  }
}
```

### Query: myDiaryNotes
```graphql
query {
  myDiaryNotes {
    uid
    title
    content
    folder {        # ✅ Folder info included
      uid
      name
      folderType
      notesCount    # ✅ Count included
      # But notes list is NOT included
    }
  }
}
```

### Query: myDiaryDocuments
```graphql
query {
  myDiaryDocuments {
    uid
    title
    documentUrls {
      url
      fileName
    }
    folder {        # ✅ Folder info included
      uid
      name
      folderType
      documentsCount  # ✅ Count included
      # But documents list is NOT included
    }
  }
}
```

## Benefits

1. **No More Recursion Errors** - Circular references are broken
2. **Better Performance** - Only loads necessary data
3. **Flexible** - Can extend with `include_items=True` if needed in future
4. **Consistent** - Follows same pattern across all types

## Testing

All queries should now work without recursion errors:
- ✅ `myDiaryFolders`
- ✅ `myDiaryNotes`
- ✅ `myDiaryDocuments`
- ✅ `myDiaryTodos`
- ✅ `createDiaryFolder`
- ✅ `createDiaryNote`
- ✅ `createDiaryDocument`
- ✅ `createDiaryTodo`

## Future Enhancement (Optional)

If you need to query folders WITH their items, you can add a separate query:

```python
diary_folder_with_items = graphene.Field(
    DiaryFolderType,
    uid=graphene.String(required=True)
)

@login_required
def resolve_diary_folder_with_items(self, info, uid):
    folder = DiaryFolder.nodes.get(uid=uid)
    # Use include_items=True for this specific query
    return DiaryFolderType.from_neomodel(folder, include_items=True)
```

But for now, the current implementation avoids recursion and provides all necessary data.
