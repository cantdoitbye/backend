from neomodel import StructuredNode, StringProperty, IntegerProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom, JSONProperty
from django_neomodel import DjangoNode
from datetime import datetime
from auth_manager.models import Users
from django.db import models 


class Connection(DjangoNode, StructuredNode):
    """
    Neo4j model representing user connections in the social network.
    
    This model manages the connection relationships between users, tracking
    connection requests, acceptances, rejections, and cancellations. Each
    connection is associated with a circle that defines the relationship type
    and privacy level.
    
    Business Logic:
    - Connections can be in one of four states: Received, Accepted, Rejected, Cancelled
    - Each connection has a sender (created_by) and receiver
    - Connections are associated with circles that define relationship context
    - Timestamps track when connections are created or modified
    
    Use Cases:
    - Friend requests and acceptance workflow
    - Professional networking connections
    - Family relationship establishment
    - Connection status tracking and management
    """
    uid = UniqueIdProperty()  # Unique identifier for the connection
    
    # Available connection status options
    STATUS_CHOICES = {
        'Received': 'Received',    # Connection request received but not yet acted upon
        'Accepted': 'Accepted',    # Connection request accepted
        'Rejected': 'Rejected',    # Connection request rejected
        'Cancelled': 'Cancelled'   # Connection request cancelled by sender
    }

    # User who will receive the connection request
    receiver = RelationshipTo('Users','HAS_RECIEVED_CONNECTION')
    # User who initiated the connection request
    created_by = RelationshipTo('Users','HAS_SEND_CONNECTION')
    # Current status of the connection request
    connection_status = StringProperty(choices=STATUS_CHOICES.items())
    # When the connection was created or last modified
    timestamp = DateTimeProperty(default_now=True)
    # Associated circle defining the relationship context
    circle = RelationshipTo('Circle','HAS_CIRCLE')

    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'connection'

    def __str__(self):
        return self.connection_status

class Circle(DjangoNode, StructuredNode):
    """
    Neo4j model representing relationship circles that categorize connections.
    
    Circles define the privacy and intimacy level of relationships between users.
    They help organize connections into meaningful groups based on relationship
    types and determine what information is shared between connected users.
    
    Business Logic:
    - Three circle types: Outer (acquaintances), Inner (close relationships), Universal (public)
    - Each circle can have a main relation type and specific sub-relation
    - Circle type determines privacy levels and information sharing permissions
    - Relations help categorize the nature of the relationship
    
    Use Cases:
    - Privacy control for shared content
    - Relationship categorization (family, friends, colleagues)
    - Content filtering based on relationship intimacy
    - Social graph organization and management
    """
    uid = UniqueIdProperty()  # Unique identifier for the circle
    
    # Available circle types defining privacy and intimacy levels
    CIRCLE_CHOICES = {
        'Outer': 'Outer Circle',      # Acquaintances, limited access
        'Inner': 'Inner Circle',      # Close relationships, broader access
        'Universal': 'Universal',     # Public or universal access
    }
    
    # Main relationship category (e.g., 'Family', 'Friends', 'Professional')
    relation = StringProperty()
    # Specific relationship type (e.g., 'Father', 'Best Friend', 'Colleague')
    sub_relation = StringProperty()
    # Circle type determining privacy and access levels
    circle_type = StringProperty(choices=CIRCLE_CHOICES.items())
    
    class Meta:
        app_label = 'connection'

    def __str__(self):
        return self.sub_relation
    



class Relation(models.Model):
    """
    Django model representing main relationship categories in the connection system.
    
    This model defines the primary relationship types that users can have with
    each other, serving as the parent category for more specific sub-relations.
    It provides the foundational structure for organizing and categorizing
    different types of social connections.
    
    Business Logic:
    - Serves as the parent category for sub-relations
    - Each relation type can have multiple associated sub-relations
    - Names must be unique across the system
    - Used for relationship categorization and organization
    
    Use Cases:
    - Defining broad relationship categories (Family, Friends, Professional)
    - Organizing connection types in the user interface
    - Filtering and searching connections by relationship type
    - Analytics and reporting on relationship patterns
    
    Examples:
    - 'Family' relation with sub-relations like 'Father', 'Mother', 'Sibling'
    - 'Professional' relation with sub-relations like 'Colleague', 'Manager', 'Client'
    - 'Friends' relation with sub-relations like 'Best Friend', 'Close Friend'
    """
    # Main relationship category name (must be unique)
    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="The main relation type, e.g., Relatives, Friend, Professional."
    )
    
    def __str__(self):
        return self.name

class SubRelation(models.Model):
    """
    Django model representing specific relationship types within main relation categories.
    
    This model defines the detailed relationship types that provide granular
    categorization of connections between users. Each sub-relation belongs to
    a main relation and includes metadata about directionality, approval
    requirements, and default privacy settings.
    
    Business Logic:
    - Each sub-relation belongs to exactly one main relation
    - Directionality determines if the relationship is mutual or one-way
    - Approval requirements control whether connections need confirmation
    - Reverse connections enable bidirectional relationship mapping
    - Default circles provide automatic privacy level assignment
    
    Use Cases:
    - Detailed relationship specification (Father, Mother, Boss, Employee)
    - Automatic relationship reciprocity (Father <-> Child)
    - Privacy level automation based on relationship type
    - Connection approval workflow customization
    
    Examples:
    - 'Father' (unidirectional, reverse: 'Child', default: Inner Circle)
    - 'Friend' (bidirectional, approval required, default: Outer Circle)
    - 'Spouse' (bidirectional, approval required, default: Inner Circle)
    """
    # Parent relation category this sub-relation belongs to
    relation = models.ForeignKey(
        Relation, 
        on_delete=models.CASCADE, 
        related_name='sub_relations', 
        help_text="The main relation type this sub-relation belongs to."
    )
    # Specific name of the sub-relationship
    sub_relation_name = models.CharField(
        max_length=100, 
        help_text="Specific sub-relation, e.g., father, son, husband."
    )
    # Whether the relationship is one-way or mutual
    directionality = models.CharField(
        max_length=50, 
        choices=[('Unidirectional', 'Unidirectional'), ('Bidirectional', 'Bidirectional')], 
        help_text="The direction of the relationship."
    )
    # Whether this relationship type requires approval from the receiver
    approval_required = models.BooleanField(
        default=True, 
        help_text="Is approval required for this relationship?"
    )
    # The corresponding relationship from the other person's perspective
    reverse_connection = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="The reverse relation of this sub-relation, e.g., for Father -> Child."
    )
    # Default privacy circle for this relationship type
    default_circle = models.CharField(
        max_length=100,
        blank=True,
        help_text="The default circle for this sub-relation"
    )
    class Meta:
        unique_together = ('relation', 'sub_relation_name')

    def __str__(self):
        return f"{self.sub_relation_name} ({self.relation.name})"

class ConnectionV2(DjangoNode, StructuredNode):
    """
    Enhanced Neo4j model for user connections with improved functionality.
    
    This is the second version of the Connection model, providing enhanced
    features and improved relationship management. It works with CircleV2
    to provide more flexible and dynamic relationship handling compared
    to the original Connection model.
    
    Business Logic:
    - Same connection states as v1: Received, Accepted, Rejected, Cancelled
    - Enhanced circle integration with CircleV2 for dynamic relationship data
    - Improved timestamp management and connection lifecycle tracking
    - Better support for complex relationship scenarios
    
    Use Cases:
    - Advanced connection management with dynamic relationship properties
    - Enhanced privacy controls through CircleV2 integration
    - Improved connection analytics and relationship tracking
    - Support for evolving relationship types and circle modifications
    
    Differences from Connection v1:
    - Uses CircleV2 instead of Circle for enhanced relationship management
    - Better support for dynamic relationship properties
    - Improved integration with user relationship tracking
    """
    uid = UniqueIdProperty()  # Unique identifier for the connection
    
    # Available connection status options (same as v1)
    STATUS_CHOICES = {
        'Received': 'Received',    # Connection request received but not yet acted upon
        'Accepted': 'Accepted',    # Connection request accepted
        'Rejected': 'Rejected',    # Connection request rejected
        'Cancelled': 'Cancelled'   # Connection request cancelled by sender
    }

    # User who will receive the connection request
    receiver = RelationshipTo('Users','HAS_RECIEVED_CONNECTION')
    # User who initiated the connection request
    created_by = RelationshipTo('Users','HAS_SEND_CONNECTION')
    # Current status of the connection request
    connection_status = StringProperty(choices=STATUS_CHOICES.items())
    # When the connection was created or last modified
    timestamp = DateTimeProperty(default_now=True)
    # Associated enhanced circle with dynamic relationship properties
    circle = RelationshipTo('CircleV2','HAS_CIRCLE')

    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'connection'

    def __str__(self):
        return self.connection_status
    

class CircleV2(DjangoNode, StructuredNode):
    """
    Enhanced Neo4j model for relationship circles with dynamic user-specific properties.
    
    This is the second version of the Circle model, providing advanced functionality
    for managing dynamic relationship properties on a per-user basis. Unlike the
    original Circle model, CircleV2 stores user-specific relationship data in a
    JSON structure, allowing for flexible and evolving relationship management.
    
    Business Logic:
    - Stores initial relationship configuration (sub_relation, directionality)
    - Maintains user-specific relationship data in JSON format
    - Supports dynamic relationship modification tracking
    - Enables per-user circle type and sub-relation customization
    - Tracks modification counts for relationship changes
    
    Use Cases:
    - Dynamic relationship evolution (e.g., colleague becomes friend)
    - Per-user relationship customization within the same circle
    - Relationship modification history and analytics
    - Flexible privacy and access control based on individual relationships
    
    Key Features:
    - JSON-based user_relations for flexible data storage
    - Modification count tracking for relationship changes
    - Individual circle type assignment per user
    - Support for relationship evolution over time
    """
    uid = UniqueIdProperty()  # Unique identifier for the circle
    
    # Initial sub-relation type when the circle was created
    initialsub_relation = StringProperty()
    # Initial directionality setting for the relationship
    initial_directionality = StringProperty()
    # JSON object storing per-user relationship data and preferences
    user_relations = JSONProperty(default={})
    
    class Meta:
        app_label = 'connection'

    def __str__(self):
        return self.sub_relation
    
    def update_user_relation(self, user_uid, sub_relation=None, circle_type=None):
        """
        Update or add relationship data for a specific user within this circle.
        
        This method allows dynamic modification of relationship properties on a
        per-user basis, enabling relationship evolution and customization.
        
        Args:
            user_uid (str): Unique identifier of the user whose relation data to update
            sub_relation (str, optional): New sub-relation type for this user
            circle_type (str, optional): New circle type for this user
        
        Business Logic:
        - Creates user entry if it doesn't exist
        - Increments modification count when sub_relation is updated
        - Preserves existing data when updating specific fields
        - Automatically saves changes to the database
        
        Use Cases:
        - Relationship evolution (colleague -> friend)
        - Privacy level adjustments (outer -> inner circle)
        - Relationship refinement based on interaction history
        """
        current_relations = dict(self.user_relations or {})  # Convert to dict if None
            
        if user_uid not in current_relations:
            current_relations[user_uid] = {}
        
        if sub_relation is not None:
            current_relations[user_uid]['sub_relation'] = sub_relation
            current_relations[user_uid]["sub_relation_modification_count"] += 1
        if circle_type is not None:
            current_relations[user_uid]['circle_type'] = circle_type
        
        self.user_relations = current_relations
        self.save()

    def get_user_relation(self, user_uid):
        """
        Retrieve relationship data for a specific user within this circle.
        
        Args:
            user_uid (str): Unique identifier of the user whose relation data to retrieve
        
        Returns:
            dict or None: User's relationship data including sub_relation, circle_type,
                         and modification_count, or None if user not found
        
        Use Cases:
        - Checking current relationship status with a user
        - Retrieving privacy settings for content sharing
        - Analytics on relationship evolution patterns
        """
        if not self.user_relations:
            return None
        return self.user_relations.get(user_uid)
    
    def get_sub_relation_modification_count(self, user_uid):
        """
        Get the number of times a user's sub-relation has been modified.
        
        This method tracks relationship evolution by counting how many times
        the sub-relation has been changed for a specific user.
        
        Args:
            user_uid (str): Unique identifier of the user
        
        Returns:
            int: Number of sub-relation modifications, 0 if user not found
        
        Use Cases:
        - Relationship stability analytics
        - Identifying frequently changing relationships
        - Limiting relationship modification frequency
        - User behavior analysis
        """
        current_relations = dict(self.user_relations or {})
        if user_uid in current_relations:
            return current_relations[user_uid].get('sub_relation_modification_count', 0)
        return 0
    
    def reset_sub_relation_modification_count(self, user_uid):
        """
        Reset the sub-relation modification count to zero for a specific user.
        
        This method is useful for administrative purposes or when implementing
        modification limits that reset periodically.
        
        Args:
            user_uid (str): Unique identifier of the user
        
        Returns:
            bool: True if reset was successful, False if user not found
        
        Use Cases:
        - Periodic reset of modification limits
        - Administrative relationship management
        - Clearing modification history for fresh start
        - Implementing time-based modification quotas
        """
        current_relations = dict(self.user_relations or {})
        if user_uid in current_relations:
            current_relations[user_uid]['sub_relation_modification_count'] = 0
            self.user_relations = current_relations
            self.save()
            return True
        return False
    
    def get_circle_type(self, user_uid):
        """
        Get the circle type (privacy level) for a specific user.
        
        This method retrieves the privacy/intimacy level assigned to a specific
        user within this circle, which determines access permissions and content sharing.
        
        Args:
            user_uid (str): Unique identifier of the user
        
        Returns:
            str or None: Circle type ('Outer', 'Inner', 'Universal') if found,
                        None if user or circle type not found
        
        Use Cases:
        - Content filtering based on relationship intimacy
        - Privacy control for shared information
        - Access level determination for features
        - Personalized user experience based on relationship closeness
        """
        current_relations = dict(self.user_relations or {})
        if user_uid in current_relations:
            return current_relations[user_uid].get('circle_type')
        return None
    
    def update_user_relation_only(self, user_uid, sub_relation=None):
        """
        Update only the sub-relation for a specific user without affecting other properties.
        
        This method provides a lightweight way to update just the sub-relation
        without modifying circle_type or incrementing modification counts.
        
        Args:
            user_uid (str): Unique identifier of the user whose sub-relation to update
            sub_relation (str, optional): New sub-relation type for this user
        
        Business Logic:
        - Creates user entry if it doesn't exist
        - Updates only sub_relation field
        - Does not increment modification count (unlike update_user_relation)
        - Preserves all other user relationship data
        
        Use Cases:
        - Initial relationship setup
        - Administrative relationship corrections
        - Bulk relationship updates without count tracking
        - System-initiated relationship adjustments
        """
        current_relations = dict(self.user_relations or {})  # Convert to dict if None
            
        if user_uid not in current_relations:
            current_relations[user_uid] = {}
        
        if sub_relation is not None:
            current_relations[user_uid]['sub_relation'] = sub_relation
            
        
        self.user_relations = current_relations
        self.save()
    