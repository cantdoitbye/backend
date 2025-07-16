import graphene
from graphene import Mutation
from graphql_jwt.decorators import login_required,superuser_required

from .types import *
from auth_manager.models import Users
from service.models import *

class Query(graphene.ObjectType):
    all_services = graphene.List(ServiceType)
    @superuser_required
    @login_required
    # @superuser_required
    def resolve_all_services(self, info):
        return [ServiceType.from_neomodel(service) for service in Service.nodes.all()]
    
    service_by_uid = graphene.Field(ServiceType, uid=graphene.String())
    @login_required
    def resolve_service_by_uid(self, info, uid):
        try:
            category = Service.nodes.get(uid=uid)
            return ServiceType.from_neomodel(category)
        except ServiceCategory.DoesNotExist:
            return None
    
    my_service=graphene.List(ServiceType)
    @login_required
    def resolve_my_service(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:
            
            my_services=list(user_node.service.all())

            return [ServiceType.from_neomodel(story) for story in my_services]
        except Exception as e:
            raise Exception(e)
    

    all_service_categories = graphene.List(ServiceCategoryType)
    service_category_by_uid = graphene.Field(ServiceCategoryType, uid=graphene.String())
    @superuser_required
    @login_required
    def resolve_all_service_categories(self, info):
        return [ServiceCategoryType.from_neomodel(category) for category in ServiceCategory.nodes.all()]
    @login_required
    def resolve_service_category_by_uid(self, info, uid):
        try:
            category = ServiceCategory.nodes.get(uid=uid)
            return ServiceCategoryType.from_neomodel(category)
        except ServiceCategory.DoesNotExist:
            return None
        
    service_category_by_service_uid = graphene.List(ServiceCategoryType, service_uid=graphene.String())
    @login_required
    def resolve_service_category_by_service_uid(self, info, service_uid):
        service = Service.nodes.get(uid=service_uid)
        servicecategory = list(service.servicecategory.all())
        return [ServiceCategoryType.from_neomodel(x) for x in servicecategory]
    

    all_service_order = graphene.List(ServiceOrderType)
    service_order_by_uid = graphene.Field(ServiceOrderType, uid=graphene.String())
    @superuser_required
    @login_required
    def resolve_all_service_order(self, info):
        return [ServiceOrderType.from_neomodel(order) for order in ServiceOrder.nodes.all()]
    @login_required
    def resolve_service_order_by_uid(self, info, uid):
        try:
            category = ServiceOrder.nodes.get(uid=uid)
            return ServiceOrderType.from_neomodel(category)
        except ServiceOrder.DoesNotExist:
            return None
        
    all_service_provider = graphene.List(ServiceOrderType)
    service_provider_by_uid = graphene.Field(ServiceOrderType, uid=graphene.String())
    @superuser_required
    @login_required
    def resolve_all_service_provider(self, info):
        return [ServiceProviderType.from_neomodel(order) for order in ServiceProviders.nodes.all()]
    @login_required
    def resolve_service_provider_by_uid(self, info, uid):
        try:
            category = ServiceProviders.nodes.get(uid=uid)
            return ServiceProviderType.from_neomodel(category)
        except ServiceOrder.DoesNotExist:
            return None