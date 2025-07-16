from neomodel import StructuredNode, StringProperty, FloatProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, OneOrMore, RelationshipTo,RelationshipFrom,ArrayProperty,DateProperty
from django_neomodel import DjangoNode
from datetime import datetime

from django.db import models
from django.utils import timezone
from datetime import timedelta
from auth_manager.models import Users 



class TaskCategory(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty()
    created_on = DateTimeProperty(default_now=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    todo=RelationshipTo('ToDo','HAS_TODO')
    meeting=RelationshipTo('Meeting','HAS_MEETING')
    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'story'  

    def _str_(self):
        return self.name

class ToDo(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    user = RelationshipTo('Users', 'HAS_USER')
    title = StringProperty()
    description = StringProperty()
    category = RelationshipTo('TaskCategory', 'HAS_CATEGORY')
    status = BooleanProperty(default=False)
    time_todo = DateTimeProperty(default_now=False)
    created_on = DateTimeProperty(default_now=True)

    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'dairy'  

    def _str_(self):
        return self.title
    
class NoteCollection(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    created_by = RelationshipTo('Users', 'CREATED_BY')
    name = StringProperty()
    created_on = DateTimeProperty(default_now=True)
    note=RelationshipTo('Note','HAS_NOTE')
    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'dairy'  

    def _str_(self):
        return self.name
    
class Note(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    user = RelationshipTo('Users', 'HAS_USER')
    collection = RelationshipTo('NoteCollection', 'HAS_COLLECTION')
    title = StringProperty()
    content = StringProperty()
    created_on = DateTimeProperty(default_now=True)
    
    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'dairy'  

    def _str_(self):
        return self.title
    
class Reminder(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    user = RelationshipTo('Users', 'HAS_USER')
    title = StringProperty()
    description = StringProperty()
    date = DateProperty() #dateproperty
    time = DateTimeProperty()
    created_on = DateTimeProperty(default_now=True)

    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'dairy'  

    def _str_(self):
        return self.title
    
class Meeting(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    created_by = RelationshipTo('Users', 'CREATED_BY')
    title = StringProperty()
    description = StringProperty()
    category = RelationshipTo('TaskCategory', 'HAS_CATEGORY')
    date = DateProperty()
    time = DateTimeProperty()
    participants = RelationshipTo('Users', 'HAS_PAERTICIPANT')
    created_on = DateTimeProperty(default_now=True)

    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'dairy'  

    def _str_(self):
        return self.title
    

