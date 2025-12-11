"""
GraphQL Queries for Diary module.

Implements queries for fetching diary folders, notes, documents, and todos.
"""

import graphene
from graphql_jwt.decorators import login_required

from diary.models import DiaryFolder, DiaryNote, DiaryDocument, DiaryTodo
from diary.graphql.types import DiaryFolderType, DiaryNoteType, DiaryDocumentType, DiaryTodoType
from auth_manager.models import Users


class Query(graphene.ObjectType):
    """Root query class for Diary module."""
    
    # ========================================
    # Folder Queries
    # ========================================
    
    my_diary_folders = graphene.List(
        DiaryFolderType,
        folder_type=graphene.String(
            description="Filter by folder type. Options: 'notes' (for note folders), 'documents' (for document folders). Leave empty to get all folders."
        )
    )
    
    @login_required
    def resolve_my_diary_folders(self, info, folder_type=None):
        """
        Get all folders created by the authenticated user.
        
        Args:
            folder_type: Optional filter by folder type ('notes' or 'documents')
        
        Returns:
            List of DiaryFolderType
        """
        try:
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get all folders
            folders = list(user_node.diary_folders.all())
            
            # Filter by folder_type if provided
            if folder_type:
                folders = [f for f in folders if f.folder_type == folder_type]
            
            # Sort by created_on descending (newest first)
            folders.sort(key=lambda x: x.created_on, reverse=True)
            
            return [DiaryFolderType.from_neomodel(folder) for folder in folders]
        except Exception as e:
            raise Exception(f"Error fetching folders: {str(e)}")
    
    
    diary_folder_by_uid = graphene.Field(
        DiaryFolderType,
        uid=graphene.String(
            required=True,
            description="Unique identifier of the folder to retrieve."
        )
    )
    
    @login_required
    def resolve_diary_folder_by_uid(self, info, uid):
        """
        Get a single folder by UID.
        
        Args:
            uid: Folder UID
        
        Returns:
            DiaryFolderType or None
        """
        try:
            folder = DiaryFolder.nodes.get(uid=uid)
            
            # Verify user has access
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            if not folder.created_by.is_connected(user_node):
                return None
            
            return DiaryFolderType.from_neomodel(folder)
        except DiaryFolder.DoesNotExist:
            return None
        except Exception as e:
            raise Exception(f"Error fetching folder: {str(e)}")
    
    
    # ========================================
    # Note Queries
    # ========================================
    
    my_diary_notes = graphene.List(
        DiaryNoteType,
        folder_uid=graphene.String(
            description="Filter by folder UID. Provide a folder UID to get notes only from that folder. Leave empty to get all notes."
        )
    )
    
    @login_required
    def resolve_my_diary_notes(self, info, folder_uid=None):
        """
        Get all notes created by the authenticated user.
        
        Args:
            folder_uid: Optional filter by folder UID
        
        Returns:
            List of DiaryNoteType
        """
        try:
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get all notes
            notes = list(user_node.diary_notes.all())
            
            # Filter by folder_uid if provided
            if folder_uid:
                notes = [n for n in notes if n.folder.single() and n.folder.single().uid == folder_uid]
            
            # Sort by updated_on descending (most recently updated first)
            notes.sort(key=lambda x: x.updated_on, reverse=True)
            
            return [DiaryNoteType.from_neomodel(note) for note in notes]
        except Exception as e:
            raise Exception(f"Error fetching notes: {str(e)}")
    
    
    diary_note_by_uid = graphene.Field(
        DiaryNoteType,
        uid=graphene.String(
            required=True,
            description="Unique identifier of the note to retrieve."
        )
    )
    
    @login_required
    def resolve_diary_note_by_uid(self, info, uid):
        """
        Get a single note by UID.
        
        Args:
            uid: Note UID
        
        Returns:
            DiaryNoteType or None
        """
        try:
            note = DiaryNote.nodes.get(uid=uid)
            
            # Verify user has access (owns the note or has privacy access)
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # For now, only owner can access
            # TODO: Implement privacy level access checking
            if not note.created_by.is_connected(user_node):
                return None
            
            return DiaryNoteType.from_neomodel(note)
        except DiaryNote.DoesNotExist:
            return None
        except Exception as e:
            raise Exception(f"Error fetching note: {str(e)}")
    
    
    # ========================================
    # Document Queries
    # ========================================
    
    my_diary_documents = graphene.List(
        DiaryDocumentType,
        folder_uid=graphene.String(
            description="Filter by folder UID. Provide a folder UID to get documents only from that folder. Leave empty to get all documents."
        )
    )
    
    @login_required
    def resolve_my_diary_documents(self, info, folder_uid=None):
        """
        Get all documents created by the authenticated user.
        
        Args:
            folder_uid: Optional filter by folder UID
        
        Returns:
            List of DiaryDocumentType
        """
        try:
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get all documents
            documents = list(user_node.diary_documents.all())
            
            # Filter by folder_uid if provided
            if folder_uid:
                documents = [d for d in documents if d.folder.single() and d.folder.single().uid == folder_uid]
            
            # Sort by updated_on descending (most recently updated first)
            documents.sort(key=lambda x: x.updated_on, reverse=True)
            
            return [DiaryDocumentType.from_neomodel(doc) for doc in documents]
        except Exception as e:
            raise Exception(f"Error fetching documents: {str(e)}")
    
    
    diary_document_by_uid = graphene.Field(
        DiaryDocumentType,
        uid=graphene.String(
            required=True,
            description="Unique identifier of the document to retrieve."
        )
    )
    
    @login_required
    def resolve_diary_document_by_uid(self, info, uid):
        """
        Get a single document by UID.
        
        Args:
            uid: Document UID
        
        Returns:
            DiaryDocumentType or None
        """
        try:
            document = DiaryDocument.nodes.get(uid=uid)
            
            # Verify user has access
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # For now, only owner can access
            # TODO: Implement privacy level access checking
            if not document.created_by.is_connected(user_node):
                return None
            
            return DiaryDocumentType.from_neomodel(document)
        except DiaryDocument.DoesNotExist:
            return None
        except Exception as e:
            raise Exception(f"Error fetching document: {str(e)}")
    
    
    # ========================================
    # Todo Queries
    # ========================================
    
    my_diary_todos = graphene.List(
        DiaryTodoType,
        status=graphene.String(
            description="Filter by status. Options: 'pending' (not completed), 'completed' (finished). Leave empty to get all todos."
        ),
        date=graphene.Date(
            description="Filter by specific date (YYYY-MM-DD format). Leave empty to get all todos."
        )
    )
    
    @login_required
    def resolve_my_diary_todos(self, info, status=None, date=None):
        """
        Get all todos created by the authenticated user.
        
        Args:
            status: Optional filter by status ('pending' or 'completed')
            date: Optional filter by specific date
        
        Returns:
            List of DiaryTodoType
        """
        try:
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get all todos
            todos = list(user_node.diary_todos.all())
            
            # Filter by status if provided
            if status:
                todos = [t for t in todos if t.status == status]
            
            # Filter by date if provided
            if date:
                todos = [t for t in todos if t.date == date]
            
            # Sort by date (if available) ascending, then by created_on descending
            def sort_key(todo):
                if todo.date:
                    return (0, todo.date, -todo.created_on.timestamp())
                else:
                    return (1, None, -todo.created_on.timestamp())
            
            todos.sort(key=sort_key)
            
            return [DiaryTodoType.from_neomodel(todo) for todo in todos]
        except Exception as e:
            raise Exception(f"Error fetching todos: {str(e)}")
    
    
    diary_todo_by_uid = graphene.Field(
        DiaryTodoType,
        uid=graphene.String(
            required=True,
            description="Unique identifier of the todo to retrieve."
        )
    )
    
    @login_required
    def resolve_diary_todo_by_uid(self, info, uid):
        """
        Get a single todo by UID.
        
        Args:
            uid: Todo UID
        
        Returns:
            DiaryTodoType or None
        """
        try:
            todo = DiaryTodo.nodes.get(uid=uid)
            
            # Verify user has access
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            if not todo.created_by.is_connected(user_node):
                return None
            
            return DiaryTodoType.from_neomodel(todo)
        except DiaryTodo.DoesNotExist:
            return None
        except Exception as e:
            raise Exception(f"Error fetching todo: {str(e)}")
    
    
    diary_todos_by_date = graphene.List(
        DiaryTodoType,
        date=graphene.Date(
            required=True,
            description="Date to get todos for (YYYY-MM-DD format). Returns all todos scheduled for this date."
        )
    )
    
    @login_required
    def resolve_diary_todos_by_date(self, info, date):
        """
        Get all todos for a specific date (for calendar view).
        
        Args:
            date: Date to get todos for
        
        Returns:
            List of DiaryTodoType
        """
        try:
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get all todos for this date
            todos = list(user_node.diary_todos.all())
            todos = [t for t in todos if t.date == date]
            
            # Sort by time if available
            def sort_key(todo):
                if todo.time:
                    return (0, todo.time)
                else:
                    return (1, todo.created_on)
            
            todos.sort(key=sort_key)
            
            return [DiaryTodoType.from_neomodel(todo) for todo in todos]
        except Exception as e:
            raise Exception(f"Error fetching todos by date: {str(e)}")
