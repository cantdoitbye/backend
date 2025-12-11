from django.db import models
from neomodel import StructuredNode, StringProperty, FloatProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, OneOrMore, RelationshipTo,RelationshipFrom,ArrayProperty,DateProperty,IntegerProperty
from django_neomodel import DjangoNode
from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from auth_manager.models import Users 


class Industry(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    name = StringProperty()
    created_at = DateTimeProperty()
    updated_at = DateTimeProperty(default_now=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    is_deleted = BooleanProperty(default=False)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'job'

    def _str_(self):
        return

class Company(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    name = StringProperty()
    location = StringProperty()
    description = StringProperty()
    website = StringProperty()
    email = StringProperty()
    contact_number = StringProperty()
    logo = StringProperty()
    created_at = DateTimeProperty()
    updated_at = DateTimeProperty(default_now=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    is_deleted = BooleanProperty(default=False)
    review= RelationshipTo('CompanyReview','HAS_REVIEW')

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'job'


class Job(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    title = StringProperty()
    industry = RelationshipTo('Industry', 'HAS_INDUSTRY')
    company = RelationshipTo('Company', 'HAS_COMPANY')
    description = StringProperty()
    requirements = StringProperty()
    location = StringProperty()
    employment_type = StringProperty()
    seniority_level = StringProperty()
    salary_range = StringProperty()
    created_at = DateTimeProperty()
    updated_at = DateTimeProperty(default_now=True)
    posted_by = RelationshipTo('Users', 'POSTED_BY')
    job_cover_image = StringProperty()
    is_deleted = BooleanProperty(default=False)
    application=RelationshipTo('Application','HAS_APPLICATION')
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'job'


    def _str_(self):
        return self.title
    

class Application(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    job = RelationshipTo('Job', 'APPLIED_FOR')
    applicant = RelationshipTo('Users', 'HAS_USER')
    resume = StringProperty()
    cover_letter = StringProperty()
    applied_at = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)
    
    def save(self, *args, **kwargs):
        self.applied_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'job'


    def _str_(self):
        return self.resume
    
class CompanyReview(DjangoNode, StructuredNode):
    uid= UniqueIdProperty()
    company = RelationshipTo('Company', 'HAS_COMPANY')
    rating = IntegerProperty()
    review = StringProperty()
    created_at = DateTimeProperty()
    updated_at = DateTimeProperty(default_now=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    is_deleted = BooleanProperty(default=False)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'job'


    def _str_(self):
        return self.review