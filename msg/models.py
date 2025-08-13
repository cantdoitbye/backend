from neomodel import StructuredNode, StringProperty, IntegerProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom,FloatProperty,ArrayProperty
from django_neomodel import DjangoNode
from datetime import datetime
from django.db import models
from auth_manager.models import Users
from django.contrib.auth.models import User
 

class Conversation(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    members = RelationshipTo('Users', 'HAS_MEMBER')
    name = StringProperty(required=True)
    timestamp = DateTimeProperty(default_now=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    conv_message=RelationshipTo('ConversationMessages','HAS_MESSAGE')
    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'msg'
        
    def __str__(self):
        return 

class VibeReaction(DjangoNode, StructuredNode):
    """
    Model for storing vibe reactions sent to Matrix messages
    Integrates with your existing vibe system in PostgreSQL
    """
    uid = UniqueIdProperty()
    
    # Relationships
    conv_message = RelationshipTo('ConversationMessages', 'REACTS_TO')
    reacted_by = RelationshipTo('Users', 'REACTED_BY')
    
    # Vibe data from your PostgreSQL IndividualVibe model
    individual_vibe_id = IntegerProperty()  # References IndividualVibe.id
    vibe_name = StringProperty(required=True)  # From name_of_vibe field
    vibe_intensity = FloatProperty(required=True)  # 1.0 to 5.0 user selection
    
    # Matrix integration
    matrix_event_id = StringProperty()  # Matrix reaction event ID
    matrix_room_id = StringProperty()   # Matrix room where reaction was sent
    
    # Metadata
    reaction_type = StringProperty(default="vibe")
    timestamp = DateTimeProperty(default_now=True)
    is_active = BooleanProperty(default=True)
    
    class Meta:
        app_label = 'msg' 
    
class ConversationMessages(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    conversation = RelationshipTo('Conversation','HAS_CONVERSATION')
    sender = RelationshipTo('Users','HAS_MSG_SENDER')
    content = StringProperty()
    title =StringProperty()
    file_id=StringProperty()
    is_read = BooleanProperty(default=False)
    is_deleted = BooleanProperty(default=False)
    timestamp =  DateTimeProperty(default_now=True)
    visible_to_blocked = BooleanProperty(default=False)
    reaction=RelationshipTo('Reaction','HAS_REACTION')
    vibe_reactions = RelationshipTo('VibeReaction', 'HAS_VIBE_REACTION')


    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'msg'
        
    def __str__(self):
        return self.content
    

class Reaction(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    conv_message = RelationshipTo('ConversationMessages','HAS_CONVERSATION_MESSAGE')
    reacted_by = RelationshipTo('Users', 'REACTED_BY')
    reaction_type = StringProperty()
    emoji = StringProperty()
    timestamp =  DateTimeProperty(default_now=True)
    
    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'msg'
        
    def __str__(self):
        return self.emoji
    

class Block(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    blocker = RelationshipTo('Users','BLOCKER')
    blocked = RelationshipTo('Users','BLOCKED')
    created_at = DateTimeProperty(default_now=True)

    def save(self, *args, **kwargs):
        self.created_at = datetime.now()
        super().save(*args, **kwargs)
    

    class Meta:
        app_label = 'msg'
        
    def __str__(self):
        return 
    


class MatrixProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matrix_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    access_token = models.CharField(max_length=255, null=True, blank=True)
    pending_matrix_registration = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Matrix Profile"