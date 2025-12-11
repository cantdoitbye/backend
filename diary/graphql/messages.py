"""
Message constants for Diary module GraphQL operations.

Contains success and error messages for mutations and queries.
"""


class DiaryMessages:
    """Success and error message constants for Diary operations."""
    
    # Folder messages
    FOLDER_CREATED = "Diary folder has been successfully created."
    FOLDER_UPDATED = "Diary folder has been successfully updated."
    FOLDER_DELETED = "Diary folder has been successfully deleted."
    FOLDER_NOT_FOUND = "Diary folder not found."
    FOLDER_NOT_OWNED = "You do not have permission to modify this folder."
    FOLDER_HAS_ITEMS = "Cannot delete folder that contains items."
    FOLDER_TYPE_INVALID = "Invalid folder type. Must be 'notes' or 'documents'."
    
    # Note messages
    NOTE_CREATED = "Note has been successfully created."
    NOTE_UPDATED = "Note has been successfully updated."
    NOTE_DELETED = "Note has been successfully deleted."
    NOTE_NOT_FOUND = "Note not found."
    NOTE_NOT_OWNED = "You do not have permission to modify this note."
    NOTE_FOLDER_INVALID = "Note can only be added to folders of type 'notes'."
    
    # Document messages
    DOCUMENT_CREATED = "Document has been successfully created."
    DOCUMENT_UPDATED = "Document has been successfully updated."
    DOCUMENT_DELETED = "Document has been successfully deleted."
    DOCUMENT_NOT_FOUND = "Document not found."
    DOCUMENT_NOT_OWNED = "You do not have permission to modify this document."
    DOCUMENT_FOLDER_INVALID = "Document can only be added to folders of type 'documents'."
    DOCUMENT_FILES_REQUIRED = "At least one document file is required."
    
    # Todo messages
    TODO_CREATED = "Todo has been successfully created."
    TODO_UPDATED = "Todo has been successfully updated."
    TODO_DELETED = "Todo has been successfully deleted."
    TODO_NOT_FOUND = "Todo not found."
    TODO_NOT_OWNED = "You do not have permission to modify this todo."
    TODO_STATUS_INVALID = "Invalid status. Must be 'pending' or 'completed'."
    
    # General messages
    AUTHENTICATION_REQUIRED = "Authentication is required."
    INVALID_INPUT = "Invalid input provided."

