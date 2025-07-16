from neomodel import StructuredNode, StringProperty, DateProperty,IntegerProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom,ZeroOrMore,JSONProperty
from django_neomodel import DjangoNode
from datetime import datetime
from auth_manager.models import Users 

class Service(DjangoNode, StructuredNode):
    uid=UniqueIdProperty()
    name = StringProperty()
    description = StringProperty()
    created_at = DateTimeProperty(default_now=True)
    created_by = RelationshipTo("Users","CREATED_BY")
    ranking =  IntegerProperty()
    service_form =JSONProperty()
    servicecategory=RelationshipTo("ServiceCategory","HAS_SERVICE_CATEGORY")
    serviceorder=RelationshipTo("ServiceOrder","HAS_ORDER")
    serviceprovider=RelationshipTo("ServiceProviders","HAS_SERVICE_PROVIDER")
    def save(self, *args, **kwargs):
        self.created_at = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'service' 

    def __str__(self):
        return self.name
   
class ServiceCategory(DjangoNode, StructuredNode):
    uid=UniqueIdProperty()
    name = StringProperty()
    description = StringProperty()
    created_at =  DateTimeProperty(default_now=True)
    created_by = RelationshipTo("Users","CREATED_BY")
    ranking = IntegerProperty()
    category_image_id=StringProperty()
    
    def save(self, *args, **kwargs):
        self.created_at = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'service' 

    def __str__(self):
        return self.name
    
class ServiceOrder(DjangoNode, StructuredNode):
    uid=UniqueIdProperty()
    user = RelationshipTo("Users","ORDERED_BY")
    service = RelationshipTo("Service","HAS_SERVICE")
    order_data = StringProperty()
    created_at = DateTimeProperty(default_now=True)
    
    def save(self, *args, **kwargs):
        self.created_at = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'service' 

    def __str__(self):
        return 


class ServiceProviders(DjangoNode, StructuredNode):
    uid=UniqueIdProperty()
    user = RelationshipTo("Users","SERVICE_PROVIDER")
    service = RelationshipTo("Service","HAS_SERVICE")
    other_data = StringProperty()
    joined_on = DateTimeProperty(default_now=True)
    
    def save(self, *args, **kwargs):
        self.joined_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'service' 

    def __str__(self):
        return 