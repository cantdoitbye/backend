"""
Diary Models

Neo4j-based models for the diary management system.
Includes DiaryFolder, DiaryNote, DiaryDocument, and DiaryTodo models.
"""

from neomodel import (
    StructuredNode, StringProperty, DateTimeProperty, 
    BooleanProperty, UniqueIdProperty, RelationshipTo,
    ArrayProperty, DateProperty
)
from django_neomodel import DjangoNode
from datetime import datetime


class DiaryFolder(DjangoNode, StructuredNode):
    """
    DiaryFolder: User-created folders for organizing notes or documents.
    
    A folder can be of type 'notes' or 'documents' and is used to organize
    diary items. Each folder has a color for visual organization in the UI.
    
    Fields:
        uid: Unique identifier
        name: Folder name (e.g., "Work Notes", "Personal Ideas")
        folder_type: Type of folder - 'notes' or 'documents'
        color: Hex color code for UI (e.g., '#FF6B6B')
        created_on: Timestamp when folder was created
        updated_on: Timestamp when folder was last updated
        
    Relationships:
        created_by: User who created this folder
        notes: DiaryNote items in this folder (if folder_type='notes')
        documents: DiaryDocument items in this folder (if folder_type='documents')
    """
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    folder_type = StringProperty(required=True, choices={
        'notes': 'Notes',
        'documents': 'Documents'
    })
    color = StringProperty(default='#FF6B6B')
    created_on = DateTimeProperty(default_now=True)
    updated_on = DateTimeProperty(default_now=True)
    
    # Relationships
    created_by = RelationshipTo('auth_manager.models.Users', 'CREATED_BY')
    notes = RelationshipTo('DiaryNote', 'CONTAINS_NOTE')
    documents = RelationshipTo('DiaryDocument', 'CONTAINS_DOCUMENT')
    
    def save(self, *args, **kwargs):
        """Override save to update the updated_on timestamp."""
        self.updated_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'diary'
    
    def __str__(self):
        return f"{self.name} ({self.folder_type})"


class DiaryNote(DjangoNode, StructuredNode):
    """
    DiaryNote: Individual notes stored in Notes folders.
    
    Notes are rich-text entries that users create to capture ideas, thoughts,
    or information. Each note must belong to a folder of type 'notes'.
    
    Fields:
        uid: Unique identifier
        title: Note title (required)
        content: Note content (rich text/HTML)
        privacy_level: Privacy setting - 'private', 'inner', 'outer', 'universe'
        created_on: Timestamp when note was created
        updated_on: Timestamp when note was last updated
        
    Relationships:
        created_by: User who created this note
        folder: DiaryFolder this note belongs to (must be type='notes')
    """
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    content = StringProperty()
    privacy_level = StringProperty(default='private', choices={
        'private': 'Private',
        'inner': 'Inner Circle',
        'outer': 'Outer Circle',
        'universe': 'Universe'
    })
    created_on = DateTimeProperty(default_now=True)
    updated_on = DateTimeProperty(default_now=True)
    
    # Relationships
    created_by = RelationshipTo('auth_manager.models.Users', 'CREATED_BY')
    folder = RelationshipTo('DiaryFolder', 'IN_FOLDER')
    
    def save(self, *args, **kwargs):
        """Override save to update the updated_on timestamp."""
        self.updated_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'diary'
    
    def __str__(self):
        return self.title


class DiaryDocument(DjangoNode, StructuredNode):
    """
    DiaryDocument: Documents stored in Documents folders.
    
    Documents are file-based entries (PDFs, Word docs, etc.) that users upload
    and organize. Each document must belong to a folder of type 'documents'.
    
    Fields:
        uid: Unique identifier
        title: Document title (required)
        description: Optional description of the document
        document_ids: Array of file IDs for uploaded documents
        privacy_level: Privacy setting - 'private', 'inner', 'outer', 'universe'
        created_on: Timestamp when document was created
        updated_on: Timestamp when document was last updated
        
    Relationships:
        created_by: User who created this document entry
        folder: DiaryFolder this document belongs to (must be type='documents')
    """
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    description = StringProperty()
    document_ids = ArrayProperty(StringProperty())
    privacy_level = StringProperty(default='private', choices={
        'private': 'Private',
        'inner': 'Inner Circle',
        'outer': 'Outer Circle',
        'universe': 'Universe'
    })
    created_on = DateTimeProperty(default_now=True)
    updated_on = DateTimeProperty(default_now=True)
    
    # Relationships
    created_by = RelationshipTo('auth_manager.models.Users', 'CREATED_BY')
    folder = RelationshipTo('DiaryFolder', 'IN_FOLDER')
    
    def save(self, *args, **kwargs):
        """Override save to update the updated_on timestamp."""
        self.updated_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'diary'
    
    def __str__(self):
        return self.title


class DiaryTodo(DjangoNode, StructuredNode):
    """
    DiaryTodo: Todo items with calendar integration.
    
    Todos are independent task items that are not stored in folders.
    They have their own separate list/view and can be organized by date
    for calendar integration.
    
    Fields:
        uid: Unique identifier
        title: Todo title (required)
        description: Optional description of the todo
        status: Current status - 'pending' or 'completed'
        date: Optional date for calendar organization
        time: Optional specific time for the todo
        created_on: Timestamp when todo was created
        updated_on: Timestamp when todo was last updated
        
    Relationships:
        created_by: User who created this todo
    """
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    description = StringProperty()
    status = StringProperty(default='pending', choices={
        'pending': 'Pending',
        'completed': 'Completed'
    })
    date = DateProperty()
    time = DateTimeProperty()
    created_on = DateTimeProperty(default_now=True)
    updated_on = DateTimeProperty(default_now=True)
    
    # Relationships
    created_by = RelationshipTo('auth_manager.models.Users', 'CREATED_BY')
    
    def save(self, *args, **kwargs):
        """Override save to update the updated_on timestamp."""
        self.updated_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'diary'
    
    def __str__(self):
        return f"{self.title} ({self.status})"
