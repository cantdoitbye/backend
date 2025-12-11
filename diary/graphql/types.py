"""
GraphQL Types for Diary module.

Defines GraphQL object types for DiaryFolder, DiaryNote, DiaryDocument, and DiaryTodo.
Also exports enums for type-safe inputs.
"""

import graphene
from graphene import ObjectType
from auth_manager.graphql.types import UserType
from post.graphql.types import FileDetailType
from auth_manager.Utils.generate_presigned_url import generate_file_info


# ========================================
# Enums for GraphQL Schema
# ========================================

class FolderTypeEnum(graphene.Enum):
    """Enum for folder types."""
    NOTES = 'notes'
    DOCUMENTS = 'documents'


class PrivacyLevelEnum(graphene.Enum):
    """Enum for privacy levels."""
    PRIVATE = 'private'
    INNER = 'inner'
    OUTER = 'outer'
    UNIVERSE = 'universe'


class TodoStatusEnum(graphene.Enum):
    """Enum for todo status."""
    PENDING = 'pending'
    COMPLETED = 'completed'


# ========================================
# GraphQL Object Types
# ========================================


class DiaryFolderType(ObjectType):
    """
    GraphQL type for DiaryFolder.
    
    Represents a folder that contains either notes or documents.
    """
    uid = graphene.String()
    name = graphene.String()
    folder_type = graphene.String()
    color = graphene.String()
    created_by = graphene.Field(UserType)
    created_on = graphene.DateTime()
    updated_on = graphene.DateTime()
    notes_count = graphene.Int()
    documents_count = graphene.Int()
    notes = graphene.List(lambda: DiaryNoteType)
    documents = graphene.List(lambda: DiaryDocumentType)
    
    def resolve_notes(self, info):
        """
        Resolver for notes field - fetches notes from database.
        Only returns notes if folder_type is 'notes'.
        """
        if self.folder_type != 'notes':
            return []
        
        try:
            from diary.models import DiaryFolder
            folder = DiaryFolder.nodes.get(uid=self.uid)
            notes = list(folder.notes.all())
            # Sort by updated_on descending
            notes.sort(key=lambda x: x.updated_on, reverse=True)
            return [DiaryNoteType.from_neomodel(note, include_folder=False) for note in notes]
        except Exception as e:
            print(f"Error fetching notes: {e}")
            return []
    
    def resolve_documents(self, info):
        """
        Resolver for documents field - fetches documents from database.
        Only returns documents if folder_type is 'documents'.
        """
        if self.folder_type != 'documents':
            return []
        
        try:
            from diary.models import DiaryFolder
            folder = DiaryFolder.nodes.get(uid=self.uid)
            documents = list(folder.documents.all())
            # Sort by updated_on descending
            documents.sort(key=lambda x: x.updated_on, reverse=True)
            return [DiaryDocumentType.from_neomodel(doc, include_folder=False) for doc in documents]
        except Exception as e:
            print(f"Error fetching documents: {e}")
            return []
    
    @classmethod
    def from_neomodel(cls, folder):
        """
        Convert neomodel DiaryFolder instance to GraphQL type.
        
        Args:
            folder: DiaryFolder neomodel instance
        """
        return cls(
            uid=folder.uid,
            name=folder.name,
            folder_type=folder.folder_type,
            color=folder.color,
            created_by=UserType.from_neomodel(folder.created_by.single()) if folder.created_by.single() else None,
            created_on=folder.created_on,
            updated_on=folder.updated_on,
            notes_count=len(folder.notes.all()) if folder.folder_type == 'notes' else 0,
            documents_count=len(folder.documents.all()) if folder.folder_type == 'documents' else 0
        )


class DiaryNoteType(ObjectType):
    """
    GraphQL type for DiaryNote.
    
    Represents a note entry within a notes folder.
    """
    uid = graphene.String()
    title = graphene.String()
    content = graphene.String()
    privacy_level = graphene.String()
    folder = graphene.Field(lambda: DiaryFolderType)
    created_by = graphene.Field(UserType)
    created_on = graphene.DateTime()
    updated_on = graphene.DateTime()
    
    @classmethod
    def from_neomodel(cls, note, include_folder=True):
        """
        Convert neomodel DiaryNote instance to GraphQL type.
        
        Args:
            note: DiaryNote neomodel instance
            include_folder: If True, include folder details (default: True)
        """
        folder_data = None
        if include_folder and note.folder.single():
            # Don't include items in folder to avoid recursion
            folder_data = DiaryFolderType.from_neomodel(note.folder.single())
        
        return cls(
            uid=note.uid,
            title=note.title,
            content=note.content,
            privacy_level=note.privacy_level,
            folder=folder_data,
            created_by=UserType.from_neomodel(note.created_by.single()) if note.created_by.single() else None,
            created_on=note.created_on,
            updated_on=note.updated_on
        )


class DiaryDocumentType(ObjectType):
    """
    GraphQL type for DiaryDocument.
    
    Represents a document entry within a documents folder.
    Includes presigned URLs for document files.
    """
    uid = graphene.String()
    title = graphene.String()
    description = graphene.String()
    document_ids = graphene.List(graphene.String)
    document_urls = graphene.List(FileDetailType)  # Presigned URLs for documents
    privacy_level = graphene.String()
    folder = graphene.Field(lambda: DiaryFolderType)
    created_by = graphene.Field(UserType)
    created_on = graphene.DateTime()
    updated_on = graphene.DateTime()
    
    @classmethod
    def from_neomodel(cls, document, include_folder=True):
        """
        Convert neomodel DiaryDocument instance to GraphQL type.
        Generates presigned URLs for all document files.
        
        Args:
            document: DiaryDocument neomodel instance
            include_folder: If True, include folder details (default: True)
        """
        # Generate presigned URLs for documents
        document_urls = None
        if document.document_ids:
            try:
                document_urls = [
                    FileDetailType(**generate_file_info(doc_id)) 
                    for doc_id in document.document_ids
                ]
            except Exception as e:
                print(f"Error generating document URLs: {e}")
                document_urls = []
        
        folder_data = None
        if include_folder and document.folder.single():
            # Don't include items in folder to avoid recursion
            folder_data = DiaryFolderType.from_neomodel(document.folder.single())
        
        return cls(
            uid=document.uid,
            title=document.title,
            description=document.description,
            document_ids=document.document_ids or [],
            document_urls=document_urls,
            privacy_level=document.privacy_level,
            folder=folder_data,
            created_by=UserType.from_neomodel(document.created_by.single()) if document.created_by.single() else None,
            created_on=document.created_on,
            updated_on=document.updated_on
        )


class DiaryTodoType(ObjectType):
    """
    GraphQL type for DiaryTodo.
    
    Represents a todo item (not stored in folders).
    """
    uid = graphene.String()
    title = graphene.String()
    description = graphene.String()
    status = graphene.String()
    date = graphene.Date()
    time = graphene.DateTime()
    created_by = graphene.Field(UserType)
    created_on = graphene.DateTime()
    updated_on = graphene.DateTime()
    
    @classmethod
    def from_neomodel(cls, todo):
        """Convert neomodel DiaryTodo instance to GraphQL type."""
        return cls(
            uid=todo.uid,
            title=todo.title,
            description=todo.description,
            status=todo.status,
            date=todo.date,
            time=todo.time,
            created_by=UserType.from_neomodel(todo.created_by.single()) if todo.created_by.single() else None,
            created_on=todo.created_on,
            updated_on=todo.updated_on
        )
