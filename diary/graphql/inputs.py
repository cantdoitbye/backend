"""
GraphQL Input Types for Diary module.

Defines input types for creating and updating diary folders, notes, documents, and todos.
"""

import graphene


# ========================================
# Enums for Type Safety
# ========================================

class FolderTypeEnum(graphene.Enum):
    """
    Enum for folder types.
    Ensures users can only select valid folder types.
    """
    NOTES = 'notes'
    DOCUMENTS = 'documents'


class PrivacyLevelEnum(graphene.Enum):
    """
    Enum for privacy levels.
    Ensures users can only select valid privacy levels.
    """
    PRIVATE = 'private'
    INNER = 'inner'
    OUTER = 'outer'
    UNIVERSE = 'universe'


class TodoStatusEnum(graphene.Enum):
    """
    Enum for todo status.
    Ensures users can only select valid status values.
    """
    PENDING = 'pending'
    COMPLETED = 'completed'


# ========================================
# Folder Input Types
# ========================================

class CreateDiaryFolderInput(graphene.InputObjectType):
    """
    Input for creating a new diary folder.
    
    Args:
        name: Folder name (required)
        folder_type: Type of folder - select 'notes' or 'documents' (required)
        color: Hex color code (optional, defaults to '#FF6B6B')
    """
    name = graphene.String(required=True)
    folder_type = graphene.Field(FolderTypeEnum, required=True)
    color = graphene.String()


class UpdateDiaryFolderInput(graphene.InputObjectType):
    """
    Input for updating an existing diary folder.
    
    Args:
        uid: Folder UID (required)
        name: New folder name (optional)
        color: New hex color code (optional)
    
    Note: folder_type cannot be changed after creation
    """
    uid = graphene.String(required=True)
    name = graphene.String()
    color = graphene.String()


class DeleteDiaryFolderInput(graphene.InputObjectType):
    """
    Input for deleting a diary folder.
    
    Args:
        uid: Folder UID (required)
    """
    uid = graphene.String(required=True)


# ========================================
# Note Input Types
# ========================================

class CreateDiaryNoteInput(graphene.InputObjectType):
    """
    Input for creating a new diary note.
    
    Args:
        title: Note title (required)
        content: Note content (optional)
        folder_uid: UID of the folder to store this note (required)
        privacy_level: Privacy setting - select from dropdown (optional, defaults to 'private')
    """
    title = graphene.String(required=True)
    content = graphene.String()
    folder_uid = graphene.String(required=True)
    privacy_level = graphene.Field(PrivacyLevelEnum)


class UpdateDiaryNoteInput(graphene.InputObjectType):
    """
    Input for updating an existing diary note.
    
    Args:
        uid: Note UID (required)
        title: New title (optional)
        content: New content (optional)
        folder_uid: New folder UID to move note to (optional)
        privacy_level: New privacy level - select from dropdown (optional)
    """
    uid = graphene.String(required=True)
    title = graphene.String()
    content = graphene.String()
    folder_uid = graphene.String()
    privacy_level = graphene.Field(PrivacyLevelEnum)


class DeleteDiaryNoteInput(graphene.InputObjectType):
    """
    Input for deleting a diary note.
    
    Args:
        uid: Note UID (required)
    """
    uid = graphene.String(required=True)


# ========================================
# Document Input Types
# ========================================

class CreateDiaryDocumentInput(graphene.InputObjectType):
    """
    Input for creating a new diary document.
    
    Args:
        title: Document title (required)
        description: Document description (optional)
        folder_uid: UID of the folder to store this document (required)
        document_ids: List of uploaded file IDs (required, at least one)
        privacy_level: Privacy setting - select from dropdown (optional, defaults to 'private')
    """
    title = graphene.String(required=True)
    description = graphene.String()
    folder_uid = graphene.String(required=True)
    document_ids = graphene.List(graphene.String, required=True)
    privacy_level = graphene.Field(PrivacyLevelEnum)


class UpdateDiaryDocumentInput(graphene.InputObjectType):
    """
    Input for updating an existing diary document.
    
    Args:
        uid: Document UID (required)
        title: New title (optional)
        description: New description (optional)
        folder_uid: New folder UID to move document to (optional)
        document_ids: New list of file IDs (optional)
        privacy_level: New privacy level - select from dropdown (optional)
    """
    uid = graphene.String(required=True)
    title = graphene.String()
    description = graphene.String()
    folder_uid = graphene.String()
    document_ids = graphene.List(graphene.String)
    privacy_level = graphene.Field(PrivacyLevelEnum)


class DeleteDiaryDocumentInput(graphene.InputObjectType):
    """
    Input for deleting a diary document.
    
    Args:
        uid: Document UID (required)
    """
    uid = graphene.String(required=True)


# ========================================
# Todo Input Types
# ========================================

class CreateDiaryTodoInput(graphene.InputObjectType):
    """
    Input for creating a new diary todo.
    
    Args:
        title: Todo title (required)
        description: Todo description (optional)
        date: Due date (optional)
        time: Due time (optional)
    """
    title = graphene.String(required=True)
    description = graphene.String()
    date = graphene.Date()
    time = graphene.DateTime()


class UpdateDiaryTodoInput(graphene.InputObjectType):
    """
    Input for updating an existing diary todo.
    
    Args:
        uid: Todo UID (required)
        title: New title (optional)
        description: New description (optional)
        status: New status - select 'pending' or 'completed' (optional)
        date: New due date (optional)
        time: New due time (optional)
    """
    uid = graphene.String(required=True)
    title = graphene.String()
    description = graphene.String()
    status = graphene.Field(TodoStatusEnum)
    date = graphene.Date()
    time = graphene.DateTime()


class DeleteDiaryTodoInput(graphene.InputObjectType):
    """
    Input for deleting a diary todo.
    
    Args:
        uid: Todo UID (required)
    """
    uid = graphene.String(required=True)
