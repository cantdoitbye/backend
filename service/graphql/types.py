import graphene
from graphene import ObjectType

from auth_manager.graphql.types import UserType
from auth_manager.Utils import generate_presigned_url

class ServiceCategoryType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    ranking = graphene.Int()
    category_image_id=graphene.String()
    category_image_url=graphene.String()
    created_at = graphene.DateTime()
    created_by = graphene.Field(UserType)
    
    
    @classmethod
    def from_neomodel(cls, service_category):
        return cls(
            uid=service_category.uid,
            name=service_category.name,
            description=service_category.description,
            ranking=service_category.ranking,
            created_at=service_category.created_at,
            category_image_id=service_category.category_image_id,
            category_image_url=generate_presigned_url.generate_presigned_url(service_category.category_image_id),
            created_by=UserType.from_neomodel(service_category.created_by.single()) if service_category.created_by.single() else None,
            
        )

class ServiceType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    created_at = graphene.DateTime()
    created_by = graphene.Field(UserType)
    ranking = graphene.Int()
    service_form=graphene.JSONString()
    servicecategory=graphene.Field(ServiceCategoryType)
    serviceorder=graphene.List(lambda:ServiceOrderNonServiceType)
    serviceprovider=graphene.List(lambda:ServiceProviderNonServiceType)
    @classmethod
    def from_neomodel(cls, service):
        return cls(
            uid=service.uid,
            name=service.name,
            description=service.description,
            created_at=service.created_at,
            created_by=UserType.from_neomodel(service.created_by.single()) if service.created_by.single() else None,
            servicecategory=ServiceCategoryType.from_neomodel(service.servicecategory.single())if service.servicecategory.single() else None,
            ranking=service.ranking,
            service_form=service.service_form,
            serviceorder=[ServiceOrderNonServiceType.from_neomodel(x) for x in service.serviceorder],
            serviceprovider=[ServiceProviderNonServiceType.from_neomodel(x) for x in service.serviceprovider],

        )
    
class ServiceOrderType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    service = graphene.Field(ServiceType)
    order_data = graphene.String()
    created_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, service_order):
        return cls(
            uid=service_order.uid,
            user=UserType.from_neomodel(service_order.user.single()) if service_order.user.single() else None,
            service=ServiceType.from_neomodel(service_order.service.single()) if service_order.service.single() else None,
            order_data=service_order.order_data,
            created_at=service_order.created_at
        )

class ServiceProviderType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    service = graphene.Field(ServiceType)
    other_data = graphene.String()
    joined_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, service_provider):
        return cls(
            uid=service_provider.uid,
            user=UserType.from_neomodel(service_provider.user.single()) if service_provider.user.single() else None,
            service=ServiceType.from_neomodel(service_provider.service.single()) if service_provider.service.single() else None,
            other_data=service_provider.other_data,
            joined_on=service_provider.joined_on,
        )

class ServiceOrderNonServiceType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    order_data = graphene.String()
    created_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, service_order):
        return cls(
            uid=service_order.uid,
            user=UserType.from_neomodel(service_order.user.single()) if service_order.user.single() else None,
            order_data=service_order.order_data,
            created_at=service_order.created_at
        )

class ServiceProviderNonServiceType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    other_data = graphene.String()
    joined_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, service_provider):
        return cls(
            uid=service_provider.uid,
            user=UserType.from_neomodel(service_provider.user.single()) if service_provider.user.single() else None,
            other_data=service_provider.other_data,
            joined_on=service_provider.joined_on,
        )