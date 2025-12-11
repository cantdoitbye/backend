"""
Tests for Diary module.

Comprehensive test suite for diary folders, notes, documents, and todos.
"""

from django.test import TestCase
from neomodel import db
from diary.models import DiaryFolder, DiaryNote, DiaryDocument, DiaryTodo
from auth_manager.models import Users
from datetime import datetime, date


class DiaryFolderTests(TestCase):
    """Test cases for DiaryFolder model and operations."""
    
    def setUp(self):
        """Set up test data."""
        db.begin()
        # Create test user
        self.user = Users(
            user_id='test_user_123',
            username='testuser',
            email='test@example.com'
        )
        self.user.save()
    
    def tearDown(self):
        """Clean up test data."""
        db.rollback()
    
    def test_create_notes_folder(self):
        """Test creating a notes folder."""
        folder = DiaryFolder(
            name='Test Notes Folder',
            folder_type='notes',
            color='#FF6B6B'
        )
        folder.save()
        folder.created_by.connect(self.user)
        
        self.assertIsNotNone(folder.uid)
        self.assertEqual(folder.name, 'Test Notes Folder')
        self.assertEqual(folder.folder_type, 'notes')
        self.assertEqual(folder.color, '#FF6B6B')
    
    def test_create_documents_folder(self):
        """Test creating a documents folder."""
        folder = DiaryFolder(
            name='Test Documents Folder',
            folder_type='documents',
            color='#42A5F5'
        )
        folder.save()
        folder.created_by.connect(self.user)
        
        self.assertEqual(folder.folder_type, 'documents')
    
    def test_folder_user_relationship(self):
        """Test folder to user relationship."""
        folder = DiaryFolder(
            name='My Folder',
            folder_type='notes'
        )
        folder.save()
        folder.created_by.connect(self.user)
        
        self.assertTrue(folder.created_by.is_connected(self.user))


class DiaryNoteTests(TestCase):
    """Test cases for DiaryNote model and operations."""
    
    def setUp(self):
        """Set up test data."""
        db.begin()
        self.user = Users(
            user_id='test_user_123',
            username='testuser',
            email='test@example.com'
        )
        self.user.save()
        
        self.folder = DiaryFolder(
            name='Notes Folder',
            folder_type='notes'
        )
        self.folder.save()
        self.folder.created_by.connect(self.user)
    
    def tearDown(self):
        """Clean up test data."""
        db.rollback()
    
    def test_create_note(self):
        """Test creating a note."""
        note = DiaryNote(
            title='Test Note',
            content='This is test content',
            privacy_level='private'
        )
        note.save()
        note.created_by.connect(self.user)
        note.folder.connect(self.folder)
        
        self.assertIsNotNone(note.uid)
        self.assertEqual(note.title, 'Test Note')
        self.assertEqual(note.privacy_level, 'private')
    
    def test_note_folder_relationship(self):
        """Test note to folder relationship."""
        note = DiaryNote(
            title='Test Note',
            content='Content'
        )
        note.save()
        note.created_by.connect(self.user)
        note.folder.connect(self.folder)
        
        self.assertTrue(note.folder.is_connected(self.folder))
        self.assertTrue(self.folder.notes.is_connected(note))
    
    def test_note_privacy_levels(self):
        """Test different privacy levels."""
        privacy_levels = ['private', 'inner', 'outer', 'universe']
        
        for level in privacy_levels:
            note = DiaryNote(
                title=f'Note {level}',
                content='Content',
                privacy_level=level
            )
            note.save()
            self.assertEqual(note.privacy_level, level)


class DiaryDocumentTests(TestCase):
    """Test cases for DiaryDocument model and operations."""
    
    def setUp(self):
        """Set up test data."""
        db.begin()
        self.user = Users(
            user_id='test_user_123',
            username='testuser',
            email='test@example.com'
        )
        self.user.save()
        
        self.folder = DiaryFolder(
            name='Documents Folder',
            folder_type='documents'
        )
        self.folder.save()
        self.folder.created_by.connect(self.user)
    
    def tearDown(self):
        """Clean up test data."""
        db.rollback()
    
    def test_create_document(self):
        """Test creating a document."""
        document = DiaryDocument(
            title='Test Document',
            description='Test description',
            document_ids=['file-1', 'file-2'],
            privacy_level='private'
        )
        document.save()
        document.created_by.connect(self.user)
        document.folder.connect(self.folder)
        
        self.assertIsNotNone(document.uid)
        self.assertEqual(document.title, 'Test Document')
        self.assertEqual(len(document.document_ids), 2)
    
    def test_document_folder_relationship(self):
        """Test document to folder relationship."""
        document = DiaryDocument(
            title='Test Document',
            document_ids=['file-1']
        )
        document.save()
        document.created_by.connect(self.user)
        document.folder.connect(self.folder)
        
        self.assertTrue(document.folder.is_connected(self.folder))
        self.assertTrue(self.folder.documents.is_connected(document))


class DiaryTodoTests(TestCase):
    """Test cases for DiaryTodo model and operations."""
    
    def setUp(self):
        """Set up test data."""
        db.begin()
        self.user = Users(
            user_id='test_user_123',
            username='testuser',
            email='test@example.com'
        )
        self.user.save()
    
    def tearDown(self):
        """Clean up test data."""
        db.rollback()
    
    def test_create_todo(self):
        """Test creating a todo."""
        todo = DiaryTodo(
            title='Test Todo',
            description='Test description',
            status='pending'
        )
        todo.save()
        todo.created_by.connect(self.user)
        
        self.assertIsNotNone(todo.uid)
        self.assertEqual(todo.title, 'Test Todo')
        self.assertEqual(todo.status, 'pending')
    
    def test_todo_with_date(self):
        """Test creating a todo with date."""
        test_date = date(2025, 12, 1)
        todo = DiaryTodo(
            title='Scheduled Todo',
            status='pending',
            date=test_date
        )
        todo.save()
        todo.created_by.connect(self.user)
        
        self.assertEqual(todo.date, test_date)
    
    def test_todo_status_change(self):
        """Test changing todo status."""
        todo = DiaryTodo(
            title='Test Todo',
            status='pending'
        )
        todo.save()
        todo.created_by.connect(self.user)
        
        self.assertEqual(todo.status, 'pending')
        
        todo.status = 'completed'
        todo.save()
        
        self.assertEqual(todo.status, 'completed')
    
    def test_todo_user_relationship(self):
        """Test todo to user relationship."""
        todo = DiaryTodo(
            title='Test Todo',
            status='pending'
        )
        todo.save()
        todo.created_by.connect(self.user)
        
        self.assertTrue(todo.created_by.is_connected(self.user))


class DiaryIntegrationTests(TestCase):
    """Integration tests for diary module."""
    
    def setUp(self):
        """Set up test data."""
        db.begin()
        self.user = Users(
            user_id='test_user_123',
            username='testuser',
            email='test@example.com'
        )
        self.user.save()
    
    def tearDown(self):
        """Clean up test data."""
        db.rollback()
    
    def test_folder_with_multiple_notes(self):
        """Test folder containing multiple notes."""
        folder = DiaryFolder(
            name='Test Folder',
            folder_type='notes'
        )
        folder.save()
        folder.created_by.connect(self.user)
        
        # Create multiple notes
        for i in range(3):
            note = DiaryNote(
                title=f'Note {i}',
                content=f'Content {i}'
            )
            note.save()
            note.created_by.connect(self.user)
            note.folder.connect(folder)
            folder.notes.connect(note)
        
        # Verify folder has 3 notes
        self.assertEqual(len(folder.notes.all()), 3)
    
    def test_user_with_multiple_folders(self):
        """Test user with multiple folders."""
        # Create notes folder
        notes_folder = DiaryFolder(
            name='Notes',
            folder_type='notes'
        )
        notes_folder.save()
        notes_folder.created_by.connect(self.user)
        self.user.diary_folders.connect(notes_folder)
        
        # Create documents folder
        docs_folder = DiaryFolder(
            name='Documents',
            folder_type='documents'
        )
        docs_folder.save()
        docs_folder.created_by.connect(self.user)
        self.user.diary_folders.connect(docs_folder)
        
        # Verify user has 2 folders
        self.assertEqual(len(self.user.diary_folders.all()), 2)
    
    def test_move_note_between_folders(self):
        """Test moving a note from one folder to another."""
        # Create two folders
        folder1 = DiaryFolder(name='Folder 1', folder_type='notes')
        folder1.save()
        folder1.created_by.connect(self.user)
        
        folder2 = DiaryFolder(name='Folder 2', folder_type='notes')
        folder2.save()
        folder2.created_by.connect(self.user)
        
        # Create note in folder1
        note = DiaryNote(title='Test Note', content='Content')
        note.save()
        note.created_by.connect(self.user)
        note.folder.connect(folder1)
        
        # Verify note is in folder1
        self.assertTrue(note.folder.is_connected(folder1))
        
        # Move note to folder2
        note.folder.disconnect(folder1)
        note.folder.connect(folder2)
        
        # Verify note is now in folder2
        self.assertTrue(note.folder.is_connected(folder2))
        self.assertFalse(note.folder.is_connected(folder1))


# Run tests with: python manage.py test diary
