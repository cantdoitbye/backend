"""
GraphQL Mutations for Diary module.

Implements create, update, and delete mutations for diary folders, notes, documents, and todos.
"""

import graphene
from graphene import Mutation
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from diary.models import DiaryFolder, DiaryNote, DiaryDocument, DiaryTodo
from diary.graphql.types import DiaryFolderType, DiaryNoteType, DiaryDocumentType, DiaryTodoType
from diary.graphql.inputs import (
    CreateDiaryFolderInput, UpdateDiaryFolderInput, DeleteDiaryFolderInput,
    CreateDiaryNoteInput, UpdateDiaryNoteInput, DeleteDiaryNoteInput,
    CreateDiaryDocumentInput, UpdateDiaryDocumentInput, DeleteDiaryDocumentInput,
    CreateDiaryTodoInput, UpdateDiaryTodoInput, DeleteDiaryTodoInput
)
from diary.graphql.messages import DiaryMessages
from auth_manager.models import Users


# ========================================
# Helper Functions
# ========================================

def extract_enum_value(enum_value):
    """
    Extract the actual string value from a GraphQL enum.
    
    Handles different enum formats:
    - enum.value (graphene enum with value attribute)
    - enum.name (graphene enum with name attribute)
    - plain string
    
    Returns lowercase string value.
    """
    if enum_value is None:
        return None
    
    # Try to get .value attribute first (most reliable)
    if hasattr(enum_value, 'value'):
        return str(enum_value.value).lower()
    
    # Try to get .name attribute
    if hasattr(enum_value, 'name'):
        return str(enum_value.name).lower()
    
    # Fallback to string conversion
    return str(enum_value).lower()


# ========================================
# Folder Mutations
# ========================================

class CreateDiaryFolder(Mutation):
    """
    Create a new diary folder.
    
    Creates a folder for organizing notes or documents. The folder type
    ('notes' or 'documents') determines what kind of items can be stored in it.
    """
    folder = graphene.Field(DiaryFolderType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = CreateDiaryFolderInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Extract string value from enum
            folder_type_value = extract_enum_value(input.folder_type)
            
            # Validate folder_type
            if folder_type_value not in ['notes', 'documents']:
                raise GraphQLError(DiaryMessages.FOLDER_TYPE_INVALID)
            
            # Create folder
            folder = DiaryFolder(
                name=input.name,
                folder_type=folder_type_value,
                color=input.color if input.color else '#FF6B6B'
            )
            folder.save()
            
            # Connect to user
            folder.created_by.connect(user_node)
            user_node.diary_folders.connect(folder)
            
            return CreateDiaryFolder(
                folder=DiaryFolderType.from_neomodel(folder),
                success=True,
                message=DiaryMessages.FOLDER_CREATED
            )
        except Exception as e:
            return CreateDiaryFolder(
                folder=None,
                success=False,
                message=str(e)
            )


class UpdateDiaryFolder(Mutation):
    """
    Update an existing diary folder.
    
    Allows updating folder name and color. The folder_type cannot be changed
    after creation.
    """
    folder = graphene.Field(DiaryFolderType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = UpdateDiaryFolderInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get folder
            folder = DiaryFolder.nodes.get(uid=input.uid)
            
            # Verify ownership
            if not folder.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.FOLDER_NOT_OWNED)
            
            # Update fields
            if input.name is not None:
                folder.name = input.name
            
            if input.color is not None:
                folder.color = input.color
            
            folder.save()
            
            return UpdateDiaryFolder(
                folder=DiaryFolderType.from_neomodel(folder),
                success=True,
                message=DiaryMessages.FOLDER_UPDATED
            )
        except DiaryFolder.DoesNotExist:
            return UpdateDiaryFolder(
                folder=None,
                success=False,
                message=DiaryMessages.FOLDER_NOT_FOUND
            )
        except Exception as e:
            return UpdateDiaryFolder(
                folder=None,
                success=False,
                message=str(e)
            )


class DeleteDiaryFolder(Mutation):
    """
    Delete a diary folder.
    
    Deletes the folder and all items within it. This action cannot be undone.
    """
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = DeleteDiaryFolderInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get folder
            folder = DiaryFolder.nodes.get(uid=input.uid)
            
            # Verify ownership
            if not folder.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.FOLDER_NOT_OWNED)
            
            # Delete folder (cascade delete items)
            folder.delete()
            
            return DeleteDiaryFolder(
                success=True,
                message=DiaryMessages.FOLDER_DELETED
            )
        except DiaryFolder.DoesNotExist:
            return DeleteDiaryFolder(
                success=False,
                message=DiaryMessages.FOLDER_NOT_FOUND
            )
        except Exception as e:
            return DeleteDiaryFolder(
                success=False,
                message=str(e)
            )


# ========================================
# Note Mutations
# ========================================

class CreateDiaryNote(Mutation):
    """
    Create a new diary note.
    
    Creates a note entry within a specified notes folder.
    """
    note = graphene.Field(DiaryNoteType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = CreateDiaryNoteInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get and validate folder
            folder = DiaryFolder.nodes.get(uid=input.folder_uid)
            
            # Verify folder is type 'notes'
            if folder.folder_type != 'notes':
                raise GraphQLError(DiaryMessages.NOTE_FOLDER_INVALID)
            
            # Verify user owns folder
            if not folder.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.FOLDER_NOT_OWNED)
            
            # Extract privacy_level value from enum (default to 'private')
            privacy_level = extract_enum_value(input.privacy_level) if input.privacy_level else 'private'
            
            # Create note
            note = DiaryNote(
                title=input.title,
                content=input.content if input.content else '',
                privacy_level=privacy_level
            )
            note.save()
            
            # Connect relationships
            note.created_by.connect(user_node)
            note.folder.connect(folder)
            folder.notes.connect(note)
            user_node.diary_notes.connect(note)
            
            return CreateDiaryNote(
                note=DiaryNoteType.from_neomodel(note),
                success=True,
                message=DiaryMessages.NOTE_CREATED
            )
        except DiaryFolder.DoesNotExist:
            return CreateDiaryNote(
                note=None,
                success=False,
                message=DiaryMessages.FOLDER_NOT_FOUND
            )
        except Exception as e:
            return CreateDiaryNote(
                note=None,
                success=False,
                message=str(e)
            )


class UpdateDiaryNote(Mutation):
    """
    Update an existing diary note.
    
    Allows updating note content, moving to different folder, or changing privacy level.
    """
    note = graphene.Field(DiaryNoteType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = UpdateDiaryNoteInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get note
            note = DiaryNote.nodes.get(uid=input.uid)
            
            # Verify ownership
            if not note.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.NOTE_NOT_OWNED)
            
            # Update fields
            if input.title is not None:
                note.title = input.title
            
            if input.content is not None:
                note.content = input.content
            
            if input.privacy_level is not None:
                note.privacy_level = extract_enum_value(input.privacy_level)
            
            # Move to different folder if requested
            if input.folder_uid is not None:
                new_folder = DiaryFolder.nodes.get(uid=input.folder_uid)
                
                # Verify new folder is type 'notes'
                if new_folder.folder_type != 'notes':
                    raise GraphQLError(DiaryMessages.NOTE_FOLDER_INVALID)
                
                # Verify user owns new folder
                if not new_folder.created_by.is_connected(user_node):
                    raise GraphQLError(DiaryMessages.FOLDER_NOT_OWNED)
                
                # Disconnect from old folder and connect to new
                note.folder.disconnect_all()
                note.folder.connect(new_folder)
            
            note.save()
            
            return UpdateDiaryNote(
                note=DiaryNoteType.from_neomodel(note),
                success=True,
                message=DiaryMessages.NOTE_UPDATED
            )
        except DiaryNote.DoesNotExist:
            return UpdateDiaryNote(
                note=None,
                success=False,
                message=DiaryMessages.NOTE_NOT_FOUND
            )
        except DiaryFolder.DoesNotExist:
            return UpdateDiaryNote(
                note=None,
                success=False,
                message=DiaryMessages.FOLDER_NOT_FOUND
            )
        except Exception as e:
            return UpdateDiaryNote(
                note=None,
                success=False,
                message=str(e)
            )


class DeleteDiaryNote(Mutation):
    """
    Delete a diary note.
    
    Permanently deletes the note. This action cannot be undone.
    """
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = DeleteDiaryNoteInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get note
            note = DiaryNote.nodes.get(uid=input.uid)
            
            # Verify ownership
            if not note.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.NOTE_NOT_OWNED)
            
            # Delete note
            note.delete()
            
            return DeleteDiaryNote(
                success=True,
                message=DiaryMessages.NOTE_DELETED
            )
        except DiaryNote.DoesNotExist:
            return DeleteDiaryNote(
                success=False,
                message=DiaryMessages.NOTE_NOT_FOUND
            )
        except Exception as e:
            return DeleteDiaryNote(
                success=False,
                message=str(e)
            )


# ========================================
# Document Mutations
# ========================================

class CreateDiaryDocument(Mutation):
    """
    Create a new diary document.
    
    Creates a document entry within a specified documents folder.
    """
    document = graphene.Field(DiaryDocumentType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = CreateDiaryDocumentInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Validate document_ids
            if not input.document_ids or len(input.document_ids) == 0:
                raise GraphQLError(DiaryMessages.DOCUMENT_FILES_REQUIRED)
            
            # Get and validate folder
            folder = DiaryFolder.nodes.get(uid=input.folder_uid)
            
            # Verify folder is type 'documents'
            if folder.folder_type != 'documents':
                raise GraphQLError(DiaryMessages.DOCUMENT_FOLDER_INVALID)
            
            # Verify user owns folder
            if not folder.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.FOLDER_NOT_OWNED)
            
            # Extract privacy_level value from enum (default to 'private')
            privacy_level = extract_enum_value(input.privacy_level) if input.privacy_level else 'private'
            
            # Create document
            document = DiaryDocument(
                title=input.title,
                description=input.description if input.description else '',
                document_ids=input.document_ids,
                privacy_level=privacy_level
            )
            document.save()
            
            # Connect relationships
            document.created_by.connect(user_node)
            document.folder.connect(folder)
            folder.documents.connect(document)
            user_node.diary_documents.connect(document)
            
            return CreateDiaryDocument(
                document=DiaryDocumentType.from_neomodel(document),
                success=True,
                message=DiaryMessages.DOCUMENT_CREATED
            )
        except DiaryFolder.DoesNotExist:
            return CreateDiaryDocument(
                document=None,
                success=False,
                message=DiaryMessages.FOLDER_NOT_FOUND
            )
        except Exception as e:
            return CreateDiaryDocument(
                document=None,
                success=False,
                message=str(e)
            )


class UpdateDiaryDocument(Mutation):
    """
    Update an existing diary document.
    
    Allows updating document details, moving to different folder, or changing privacy level.
    """
    document = graphene.Field(DiaryDocumentType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = UpdateDiaryDocumentInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get document
            document = DiaryDocument.nodes.get(uid=input.uid)
            
            # Verify ownership
            if not document.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.DOCUMENT_NOT_OWNED)
            
            # Update fields
            if input.title is not None:
                document.title = input.title
            
            if input.description is not None:
                document.description = input.description
            
            if input.document_ids is not None:
                if len(input.document_ids) == 0:
                    raise GraphQLError(DiaryMessages.DOCUMENT_FILES_REQUIRED)
                document.document_ids = input.document_ids
            
            if input.privacy_level is not None:
                document.privacy_level = extract_enum_value(input.privacy_level)
            
            # Move to different folder if requested
            if input.folder_uid is not None:
                new_folder = DiaryFolder.nodes.get(uid=input.folder_uid)
                
                # Verify new folder is type 'documents'
                if new_folder.folder_type != 'documents':
                    raise GraphQLError(DiaryMessages.DOCUMENT_FOLDER_INVALID)
                
                # Verify user owns new folder
                if not new_folder.created_by.is_connected(user_node):
                    raise GraphQLError(DiaryMessages.FOLDER_NOT_OWNED)
                
                # Disconnect from old folder and connect to new
                document.folder.disconnect_all()
                document.folder.connect(new_folder)
            
            document.save()
            
            return UpdateDiaryDocument(
                document=DiaryDocumentType.from_neomodel(document),
                success=True,
                message=DiaryMessages.DOCUMENT_UPDATED
            )
        except DiaryDocument.DoesNotExist:
            return UpdateDiaryDocument(
                document=None,
                success=False,
                message=DiaryMessages.DOCUMENT_NOT_FOUND
            )
        except DiaryFolder.DoesNotExist:
            return UpdateDiaryDocument(
                document=None,
                success=False,
                message=DiaryMessages.FOLDER_NOT_FOUND
            )
        except Exception as e:
            return UpdateDiaryDocument(
                document=None,
                success=False,
                message=str(e)
            )


class DeleteDiaryDocument(Mutation):
    """
    Delete a diary document.
    
    Permanently deletes the document entry. This action cannot be undone.
    """
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = DeleteDiaryDocumentInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get document
            document = DiaryDocument.nodes.get(uid=input.uid)
            
            # Verify ownership
            if not document.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.DOCUMENT_NOT_OWNED)
            
            # Delete document
            document.delete()
            
            return DeleteDiaryDocument(
                success=True,
                message=DiaryMessages.DOCUMENT_DELETED
            )
        except DiaryDocument.DoesNotExist:
            return DeleteDiaryDocument(
                success=False,
                message=DiaryMessages.DOCUMENT_NOT_FOUND
            )
        except Exception as e:
            return DeleteDiaryDocument(
                success=False,
                message=str(e)
            )


# ========================================
# Todo Mutations
# ========================================

class CreateDiaryTodo(Mutation):
    """
    Create a new diary todo.
    
    Creates a todo item. Todos are independent and not stored in folders.
    """
    todo = graphene.Field(DiaryTodoType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = CreateDiaryTodoInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Create todo
            todo = DiaryTodo(
                title=input.title,
                description=input.description if input.description else '',
                status='pending',
                date=input.date if input.date else None,
                time=input.time if input.time else None
            )
            todo.save()
            
            # Connect to user
            todo.created_by.connect(user_node)
            user_node.diary_todos.connect(todo)
            
            return CreateDiaryTodo(
                todo=DiaryTodoType.from_neomodel(todo),
                success=True,
                message=DiaryMessages.TODO_CREATED
            )
        except Exception as e:
            return CreateDiaryTodo(
                todo=None,
                success=False,
                message=str(e)
            )


class UpdateDiaryTodo(Mutation):
    """
    Update an existing diary todo.
    
    Allows updating todo details including marking as completed.
    """
    todo = graphene.Field(DiaryTodoType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = UpdateDiaryTodoInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get todo
            todo = DiaryTodo.nodes.get(uid=input.uid)
            
            # Verify ownership
            if not todo.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.TODO_NOT_OWNED)
            
            # Update fields
            if input.title is not None:
                todo.title = input.title
            
            if input.description is not None:
                todo.description = input.description
            
            if input.status is not None:
                status_value = extract_enum_value(input.status)
                if status_value not in ['pending', 'completed']:
                    raise GraphQLError(DiaryMessages.TODO_STATUS_INVALID)
                todo.status = status_value
            
            if input.date is not None:
                todo.date = input.date
            
            if input.time is not None:
                todo.time = input.time
            
            todo.save()
            
            return UpdateDiaryTodo(
                todo=DiaryTodoType.from_neomodel(todo),
                success=True,
                message=DiaryMessages.TODO_UPDATED
            )
        except DiaryTodo.DoesNotExist:
            return UpdateDiaryTodo(
                todo=None,
                success=False,
                message=DiaryMessages.TODO_NOT_FOUND
            )
        except Exception as e:
            return UpdateDiaryTodo(
                todo=None,
                success=False,
                message=str(e)
            )


class DeleteDiaryTodo(Mutation):
    """
    Delete a diary todo.
    
    Permanently deletes the todo. This action cannot be undone.
    """
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = DeleteDiaryTodoInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError(DiaryMessages.AUTHENTICATION_REQUIRED)
            
            # Get user node
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get todo
            todo = DiaryTodo.nodes.get(uid=input.uid)
            
            # Verify ownership
            if not todo.created_by.is_connected(user_node):
                raise GraphQLError(DiaryMessages.TODO_NOT_OWNED)
            
            # Delete todo
            todo.delete()
            
            return DeleteDiaryTodo(
                success=True,
                message=DiaryMessages.TODO_DELETED
            )
        except DiaryTodo.DoesNotExist:
            return DeleteDiaryTodo(
                success=False,
                message=DiaryMessages.TODO_NOT_FOUND
            )
        except Exception as e:
            return DeleteDiaryTodo(
                success=False,
                message=str(e)
            )


# ========================================
# Mutation Class (combines all mutations)
# ========================================

class Mutation(graphene.ObjectType):
    """Root mutation class for Diary module."""
    
    # Folder mutations
    create_diary_folder = CreateDiaryFolder.Field()
    update_diary_folder = UpdateDiaryFolder.Field()
    delete_diary_folder = DeleteDiaryFolder.Field()
    
    # Note mutations
    create_diary_note = CreateDiaryNote.Field()
    update_diary_note = UpdateDiaryNote.Field()
    delete_diary_note = DeleteDiaryNote.Field()
    
    # Document mutations
    create_diary_document = CreateDiaryDocument.Field()
    update_diary_document = UpdateDiaryDocument.Field()
    delete_diary_document = DeleteDiaryDocument.Field()
    
    # Todo mutations
    create_diary_todo = CreateDiaryTodo.Field()
    update_diary_todo = UpdateDiaryTodo.Field()
    delete_diary_todo = DeleteDiaryTodo.Field()
