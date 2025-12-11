# Diary Module - Integration Checklist

Use this checklist to ensure proper integration of the diary module.

---

## Pre-Integration Checklist

- [ ] Django 4.2+ installed
- [ ] Neo4j database running
- [ ] neomodel package installed
- [ ] graphene-django package installed
- [ ] Existing modules (post, story, etc.) working
- [ ] GraphQL endpoint accessible

---

## Integration Steps

### Step 1: File Setup
- [ ] Copy `diary/` directory to project root
- [ ] Verify all 13 files are present
- [ ] Check file permissions are correct

### Step 2: Django Configuration
- [ ] Add `'diary'` to INSTALLED_APPS in settings.py
- [ ] Verify settings.py has no syntax errors
- [ ] Check INSTALLED_APPS order (diary should be after auth_manager)

### Step 3: Users Model Update
- [ ] Open `auth_manager/models.py`
- [ ] Locate the `Users` class
- [ ] Add `diary_folders` relationship
- [ ] Add `diary_notes` relationship
- [ ] Add `diary_documents` relationship
- [ ] Add `diary_todos` relationship
- [ ] Save file and check for syntax errors

### Step 4: Neo4j Indexes
- [ ] Open Neo4j Browser (http://localhost:7474)
- [ ] Run index creation command for DiaryFolder (uid)
- [ ] Run index creation command for DiaryFolder (folder_type)
- [ ] Run index creation command for DiaryNote (uid)
- [ ] Run index creation command for DiaryDocument (uid)
- [ ] Run index creation command for DiaryTodo (uid)
- [ ] Run index creation command for DiaryTodo (date)
- [ ] Run index creation command for DiaryTodo (status)
- [ ] Verify all 7 indexes with `SHOW INDEXES`

### Step 5: GraphQL Schema Update
- [ ] Open `schema/schema.py`
- [ ] Import DiaryQuery from diary.graphql.query
- [ ] Import DiaryMutation from diary.graphql.mutations
- [ ] Add DiaryQuery to Query class
- [ ] Add DiaryMutation to Mutation class
- [ ] Save file and check for syntax errors

### Step 6: Server Restart
- [ ] Stop Django server (Ctrl+C or docker-compose stop)
- [ ] Clear any cached files
- [ ] Restart Django server
- [ ] Check logs for errors
- [ ] Verify server starts successfully

---

## Testing Checklist

### GraphQL Schema Verification
- [ ] Open GraphiQL/GraphQL Playground
- [ ] Query `myDiaryFolders` returns empty array (not error)
- [ ] Schema shows all 12 mutations
- [ ] Schema shows all 9 queries
- [ ] No GraphQL errors in console

### Folder Operations
- [ ] Create notes folder (returns success)
- [ ] Create documents folder (returns success)
- [ ] List folders shows both (returns 2 folders)
- [ ] Get folder by UID (returns folder details)
- [ ] Update folder name (returns updated folder)
- [ ] Update folder color (returns new color)
- [ ] Try delete folder with items (fails as expected)
- [ ] Delete empty folder (returns success)

### Note Operations
- [ ] Create note in notes folder (returns success)
- [ ] Note shows in folder query
- [ ] Get note by UID (returns note details)
- [ ] Update note title (returns updated note)
- [ ] Update note content (returns new content)
- [ ] Move note to different notes folder (returns success)
- [ ] Try create note in documents folder (fails as expected)
- [ ] Delete note (returns success)

### Document Operations
- [ ] Upload file (get file ID)
- [ ] Create document in documents folder (returns success)
- [ ] Document shows in folder query
- [ ] Get document by UID (returns document with URLs)
- [ ] Update document title (returns updated document)
- [ ] Add more document files (returns updated list)
- [ ] Move document to different documents folder (returns success)
- [ ] Try create document in notes folder (fails as expected)
- [ ] Delete document (returns success)

### Todo Operations
- [ ] Create simple todo (returns success)
- [ ] Create todo with date (returns success with date)
- [ ] Create todo with time (returns success with time)
- [ ] List all todos (returns all created)
- [ ] Filter by status pending (returns only pending)
- [ ] Update todo status to completed (returns success)
- [ ] Filter by status completed (returns completed todo)
- [ ] Get todos by date (returns todos for that date)
- [ ] Update todo date (returns new date)
- [ ] Delete todo (returns success)

---

## Database Verification

### Neo4j Queries
- [ ] Run: `MATCH (f:DiaryFolder) RETURN count(f)` (should show folders created)
- [ ] Run: `MATCH (n:DiaryNote) RETURN count(n)` (should show notes created)
- [ ] Run: `MATCH (d:DiaryDocument) RETURN count(d)` (should show documents created)
- [ ] Run: `MATCH (t:DiaryTodo) RETURN count(t)` (should show todos created)

### Relationship Verification
- [ ] Run: `MATCH (u:Users)-[:HAS_DIARY_FOLDER]->(f) RETURN count(f)`
- [ ] Run: `MATCH (u:Users)-[:HAS_DIARY_NOTE]->(n) RETURN count(n)`
- [ ] Run: `MATCH (u:Users)-[:HAS_DIARY_DOCUMENT]->(d) RETURN count(d)`
- [ ] Run: `MATCH (u:Users)-[:HAS_DIARY_TODO]->(t) RETURN count(t)`
- [ ] Run: `MATCH (f:DiaryFolder)-[:CONTAINS_NOTE]->(n) RETURN count(n)`
- [ ] Run: `MATCH (f:DiaryFolder)-[:CONTAINS_DOCUMENT]->(d) RETURN count(d)`
- [ ] Run: `MATCH (n:DiaryNote)-[:IN_FOLDER]->(f) RETURN count(n)`
- [ ] Run: `MATCH (d:DiaryDocument)-[:IN_FOLDER]->(f) RETURN count(d)`

---

## Edge Cases Testing

### Validation Tests
- [ ] Try create folder with invalid type (fails with proper message)
- [ ] Try create note without folder_uid (fails with proper message)
- [ ] Try create document with empty document_ids (fails with proper message)
- [ ] Try update folder_type (check if prevented)
- [ ] Try create note in non-existent folder (fails with proper message)
- [ ] Try access another user's folder (fails with proper message)

### Ownership Tests
- [ ] Create items as User A
- [ ] Try update User A's items as User B (fails with proper message)
- [ ] Try delete User A's items as User B (fails with proper message)
- [ ] Try query User A's items as User B (returns empty or fails)

---

## Performance Checks

- [ ] Create 10 folders (all succeed)
- [ ] Create 50 notes across folders (all succeed)
- [ ] Query myDiaryNotes (returns quickly)
- [ ] Query folder with 50 notes (returns quickly)
- [ ] Delete folder with items (check cascade or prevention)
- [ ] Indexes are being used (check query plans)

---

## Documentation Review

- [ ] Read README.md completely
- [ ] Understand all 4 models
- [ ] Understand all 12 mutations
- [ ] Understand all 9 queries
- [ ] Review API_REFERENCE.md examples
- [ ] Follow INTEGRATION_GUIDE.md steps
- [ ] Review MODULE_SUMMARY.md

---

## Production Readiness

- [ ] All tests passing
- [ ] No errors in Django logs
- [ ] No errors in Neo4j logs
- [ ] GraphQL schema validated
- [ ] Sample data created successfully
- [ ] Can query, create, update, delete all entities
- [ ] Relationships working correctly
- [ ] Privacy levels stored correctly
- [ ] Timestamps updating properly

---

## Common Issues Solved

If you encounter issues, check these:

**Import Error:**
- [ ] diary/ in correct location
- [ ] 'diary' in INSTALLED_APPS
- [ ] Django restarted

**GraphQL Error:**
- [ ] DiaryQuery imported in schema.py
- [ ] DiaryMutation imported in schema.py
- [ ] Added to Query/Mutation classes
- [ ] Django restarted

**Relationship Error:**
- [ ] Users model has all 4 relationships
- [ ] Relationship syntax correct
- [ ] Import path correct

**Index Error:**
- [ ] All 7 indexes created
- [ ] Index names unique
- [ ] Neo4j restarted if needed

**Authentication Error:**
- [ ] JWT token valid
- [ ] Token in Authorization header
- [ ] User exists in database

---

## Final Verification

### Smoke Test
Run this complete workflow:

```graphql
# 1. Create folder
mutation { 
  createDiaryFolder(input: {name: "Test", folder_type: "notes"}) 
  { folder { uid } success } 
}

# 2. Create note (use folder uid from step 1)
mutation { 
  createDiaryNote(input: {title: "Test Note", folder_uid: "FOLDER_UID"}) 
  { note { uid } success } 
}

# 3. Create todo
mutation { 
  createDiaryTodo(input: {title: "Test Todo"}) 
  { todo { uid } success } 
}

# 4. Query all
query { 
  myDiaryFolders { uid name }
  myDiaryNotes { uid title }
  myDiaryTodos { uid title }
}
```

**All 4 operations should succeed!**

---

## Completion

- [ ] All checklist items completed
- [ ] Module fully integrated
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Ready for frontend integration

---

**Integration Status:** ___ / 100 items completed

**Date Completed:** _______________

**Integrated By:** _______________

---

**Congratulations! The Diary Module is now integrated! 🎉**
