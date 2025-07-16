from neomodel import StructuredNode, StringProperty, IntegerProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom, JSONProperty
from django_neomodel import DjangoNode
from datetime import datetime
from auth_manager.models import Users
from django.db import models 


class Connection(DjangoNode, StructuredNode):
    uid=UniqueIdProperty()
    STATUS_CHOICES = {
        'Received': 'Received',
        'Accepted': 'Accepted',
        'Rejected': 'Rejected',
        'Cancelled': 'Cancelled'
    }

    receiver = RelationshipTo('Users','HAS_RECIEVED_CONNECTION')
    created_by = RelationshipTo('Users','HAS_SEND_CONNECTION')
    connection_status = StringProperty( choices= STATUS_CHOICES.items())
    timestamp = DateTimeProperty(default_now=True)
    circle=RelationshipTo('Circle','HAS_CIRCLE')

    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'connection'

    def __str__(self):
        return self.connection_status

class Circle(DjangoNode, StructuredNode):
    uid=UniqueIdProperty()
    CIRCLE_CHOICES = {
        'Outer': 'Outer Circle',
        'Inner': 'Inner Circle',
        'Universal': 'Universal',
    }
    relation = StringProperty()
    sub_relation=StringProperty()
    circle_type = StringProperty( choices= CIRCLE_CHOICES.items())
    
    class Meta:
        app_label = 'connection'

    def __str__(self):
        return self.sub_relation
    



class Relation(models.Model):
    """
    Model representing the main types of relationships like 'Relatives', 'Friend', etc.
    """
    name = models.CharField(max_length=100, unique=True, help_text="The main relation type, e.g., Relatives, Friend, Professional.")
    
    def __str__(self):
        return self.name

class SubRelation(models.Model):
    """
    Model representing specific sub-relationships, e.g., 'Father', 'Son', etc.
    """
    relation = models.ForeignKey(Relation, on_delete=models.CASCADE, related_name='sub_relations', help_text="The main relation type this sub-relation belongs to.")
    sub_relation_name = models.CharField(max_length=100, help_text="Specific sub-relation, e.g., father, son, husband.")
    directionality = models.CharField(max_length=50, choices=[('Unidirectional', 'Unidirectional'), ('Bidirectional', 'Bidirectional')], help_text="The direction of the relationship.")
    approval_required = models.BooleanField(default=True, help_text="Is approval required for this relationship?")
    reverse_connection = models.CharField(max_length=100, blank=True, help_text="The reverse relation of this sub-relation, e.g., for Father -> Child.")
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
    uid=UniqueIdProperty()
    STATUS_CHOICES = {
        'Received': 'Received',
        'Accepted': 'Accepted',
        'Rejected': 'Rejected',
        'Cancelled': 'Cancelled'
    }

    receiver = RelationshipTo('Users','HAS_RECIEVED_CONNECTION')
    created_by = RelationshipTo('Users','HAS_SEND_CONNECTION')
    connection_status = StringProperty( choices= STATUS_CHOICES.items())
    timestamp = DateTimeProperty(default_now=True)
    circle=RelationshipTo('CircleV2','HAS_CIRCLE')

    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'connection'

    def __str__(self):
        return self.connection_status
    

class CircleV2(DjangoNode, StructuredNode):
    uid=UniqueIdProperty()
    initialsub_relation=StringProperty()
    initial_directionality=StringProperty()
    user_relations = JSONProperty(default={})
    
    class Meta:
        app_label = 'connection'

    def __str__(self):
        return self.sub_relation
    
    def update_user_relation(self, user_uid, sub_relation=None, circle_type=None):
        """
        Update or add relation data for a specific user
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
        Get relation data for a specific user
        """
        if not self.user_relations:
            return None
        return self.user_relations.get(user_uid)
    
    def get_sub_relation_modification_count(self, user_uid):
        """
        Get the sub_relation count for a specific user
        """
        current_relations = dict(self.user_relations or {})
        if user_uid in current_relations:
            return current_relations[user_uid].get('sub_relation_modification_count', 0)
        return 0
    
    def reset_sub_relation_modification_count(self, user_uid):
        """
        Reset the sub_relation count to 0 for a specific user
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
        Get the circle type for a specific user
        Returns:
            str: Circle type if found
            None: If user or circle type not found
        """
        current_relations = dict(self.user_relations or {})
        if user_uid in current_relations:
            return current_relations[user_uid].get('circle_type')
        return None
    
    def update_user_relation_only(self, user_uid, sub_relation=None):
        """
        Update or add relation data for a specific user
        """
        current_relations = dict(self.user_relations or {})  # Convert to dict if None
            
        if user_uid not in current_relations:
            current_relations[user_uid] = {}
        
        if sub_relation is not None:
            current_relations[user_uid]['sub_relation'] = sub_relation
            
        
        self.user_relations = current_relations
        self.save()
    