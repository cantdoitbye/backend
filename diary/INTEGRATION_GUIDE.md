# 🚀 Diary Module - Complete Integration Guide

This guide provides step-by-step instructions to integrate the Diary module into your Ooumph platform.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [File Installation](#file-installation)
3. [Django Settings Updates](#django-settings-updates)
4. [Users Model Update](#users-model-update)
5. [GraphQL Schema Integration](#graphql-schema-integration)
6. [Neo4j Indexes](#neo4j-indexes)
7. [Testing](#testing)
8. [API Examples](#api-examples)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Django project is set up and running
- Neo4j database is configured
- GraphQL (Graphene) is configured
- Auth manager module is working
- User authentication is functional

---

## 1. File Installation

### Copy All Files

Copy the entire `diary/` directory to your Django project root:

```bash
# From where you downloaded the module
cp -r diary/ /path/to/your/project/
```

### Verify Structure

```bash
ls -R diary/

# Should show:
# diary/:
# __init__.py  apps.py  models.py  tests.py  README.md  graphql/
#
# diary/graphql:
# __init__.py  types.py  inputs.py  mutations.py  query.py  messages.py
```

---

## 2. Django Settings Updates

### Add to INSTALLED_APPS

**File:** `settings/base.py` or `settings.py`

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'diary',  # ← Add this line
]
```

---

## 3. Users Model Update

### Update auth_manager/models.py

Add diary relationships to the Users model:

**File:** `auth_manager/models.py`

```python
class Users(DjangoNode, StructuredNode):
    # ... existing fields ...
    
    # ✅ ADD THESE DIARY RELATIONSHIPS
    diary_folders = RelationshipTo('diary.models.DiaryFolder', 'HAS_DIARY_FOLDER')
    diary_notes = RelationshipTo('diary.models.DiaryNote', 'HAS_DIARY_NOTE')
    diary_documents = RelationshipTo('diary.models.DiaryDocument', 'HAS_DIARY_DOCUMENT')
    diary_todos = RelationshipTo('diary.models.DiaryTodo', 'HAS_DIARY_TODO')
```

---

## 4. GraphQL Schema Integration

### Update schema/schema.py

**File:** `schema/schema.py`

```python
# ✅ ADD THESE IMPORTS
from diary.graphql.query import Query as DiaryQuery
from diary.graphql.mutations import Mutation as DiaryMutation


# Update Query class
class Query(
    # ... other query classes ...
    DiaryQuery,  # ✅ Add this
    graphene.ObjectType
):
    pass


# Update Mutation class  
class Mutation(
    # ... other mutation classes ...
    DiaryMutation,  # ✅ Add this
    graphene.ObjectType
):
    pass
```

---

## 5. Neo4j Indexes

### Django Shell Method

```bash
python manage.py shell
# Or: docker-compose exec django_backend python manage.py shell
```

```python
from diary.models import DiaryFolder, DiaryNote, DiaryDocument, DiaryTodo

DiaryFolder.install_all_labels()
DiaryNote.install_all_labels()
DiaryDocument.install_all_labels()
DiaryTodo.install_all_labels()

print("✅ Indexes created!")
```

### Direct Cypher Method

```cypher
CREATE INDEX diary_folder_uid IF NOT EXISTS FOR (f:DiaryFolder) ON (f.uid);
CREATE INDEX diary_note_uid IF NOT EXISTS FOR (n:DiaryNote) ON (n.uid);
CREATE INDEX diary_document_uid IF NOT EXISTS FOR (d:DiaryDocument) ON (d.uid);
CREATE INDEX diary_todo_uid IF NOT EXISTS FOR (t:DiaryTodo) ON (t.uid);
```

---

## 6. Testing

### Run Tests

```bash
python manage.py test diary
```

### Manual Test via Shell

```python
from auth_manager.models import Users
from diary.models import DiaryFolder, DiaryNote, DiaryTodo

user = Users.nodes.first()

# Create folder
folder = DiaryFolder(name='Test', folder_type='notes', color='#FF6B6B')
folder.save()
folder.created_by.connect(user)

# Create note
note = DiaryNote(title='Test Note', content='Content')
note.save()
note.created_by.connect(user)
note.folder.connect(folder)

# Create todo
todo = DiaryTodo(title='Test Todo')
todo.save()
todo.created_by.connect(user)

print("✅ All working!")
```

---

## 7. Restart Server

```bash
docker-compose restart django_backend
```

---

## 8. API Examples

### Create Folder

```graphql
mutation {
  createDiaryFolder(input: {
    name: "Work Notes"
    folder_type: "notes"
    color: "#FF6B6B"
  }) {
    folder { uid name }
    success
    message
  }
}
```

### Create Note

```graphql
mutation {
  createDiaryNote(input: {
    title: "Meeting Notes"
    content: "Discussed integration..."
    folder_uid: "FOLDER_UID"
  }) {
    note { uid title }
    success
  }
}
```

### Create Todo

```graphql
mutation {
  createDiaryTodo(input: {
    title: "Review module"
    date: "2025-12-01"
  }) {
    todo { uid title status }
    success
  }
}
```

### Query Folders

```graphql
query {
  myDiaryFolders {
    uid
    name
    folder_type
    notes_count
  }
}
```

---

## 9. Troubleshooting

### Common Issues

**Import Error:**
- Verify diary is in INSTALLED_APPS
- Restart Django server

**Relationship Not Found:**
- Add diary relationships to Users model
- Restart server

**GraphQL Schema Error:**
- Check schema.py imports
- Ensure DiaryQuery and DiaryMutation are imported

---

## ✅ Integration Checklist

- [ ] Copy diary module files
- [ ] Add to INSTALLED_APPS
- [ ] Update Users model
- [ ] Update GraphQL schema
- [ ] Create Neo4j indexes
- [ ] Run tests
- [ ] Restart server
- [ ] Test API endpoints

---

## 📊 Module Summary

**Files:** 8  
**Models:** 4 (DiaryFolder, DiaryNote, DiaryDocument, DiaryTodo)  
**Mutations:** 12 (3 per model)  
**Queries:** 9  
**Integration Time:** ~30 minutes

---

**Version:** 1.0.0  
**Date:** November 30, 2025
