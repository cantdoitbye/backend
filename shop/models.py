from django.db import models
from neomodel import StructuredNode, StringProperty, FloatProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, OneOrMore, RelationshipTo,RelationshipFrom,ArrayProperty,DateProperty,JSONProperty,IntegerProperty
from django_neomodel import DjangoNode
from datetime import datetime

from django.utils import timezone
from datetime import timedelta
from auth_manager.models import Users 

class Product(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()	
    name = StringProperty()
    description = StringProperty()
    cta_link = StringProperty()
    cta = StringProperty()
    hashtags = StringProperty()
    highlights = JSONProperty()
    price = FloatProperty(default=2.0)
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    is_deleted = BooleanProperty(default=False)
    productcategory= RelationshipTo('ProductCategory','HAS_PRODUCT_CATEGORY')
    rating= RelationshipTo('Rating','HAS_RATING')
    reviewshop= RelationshipTo('ReviewShop','HAS_REVIEW')
    order= RelationshipTo('ORDER','HAS_ORDER')
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'shop'  

    def _str_(self):
        return self.name
    
class Rating(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()	
    user = RelationshipTo('Users', 'RATED_BY')
    product = RelationshipTo('Product', 'HAS_PRODUCT')
    rating = IntegerProperty()

    class Meta:
        app_label = 'shop'  

    def _str_(self):
        return self.rating
    
class ReviewShop(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    user = RelationshipTo('Users', 'REVIEWED_BY')
    product = RelationshipTo('Product', 'HAS_PRODUCT')
    text = StringProperty()
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'shop'  

    def _str_(self):
        return self.text
    
class ProductCategory(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    name = StringProperty()
    description = StringProperty()
    created_at = DateTimeProperty(default_now=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    updated_at = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)
	
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'shop'

    def _str_(self):
        return self.name
    
class Order(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    user = RelationshipTo('Users', 'ORDERED_BY')
    product = RelationshipTo('Product', 'HAS_PRODUCT')
    quantity = IntegerProperty()
    order_date = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)
    
    def save(self, *args, **kwargs):
            self.order_at = datetime.now()
            super().save(*args, **kwargs)

    class Meta:
        app_label = 'shop'

    def _str_(self):
        return






