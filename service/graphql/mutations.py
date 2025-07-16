import graphene
from graphene import Mutation

from .types import *
from service.models import *
from auth_manager.models import Users
from .inputs import *
from .messages import ServiceMessages
from graphql import GraphQLError
from graphql_jwt.decorators import login_required,superuser_required

class CreateService(graphene.Mutation):
    service = graphene.Field(ServiceType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateServiceInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)
            service_category=ServiceCategory.nodes.get(uid=input.serviceCategory_uid)

            service = Service(
                name=input.name,
                description=input.description,
                ranking=input.ranking,
                service_form=input.service_form,
            )
            service.save()
            service.created_by.connect(created_by)
            service.servicecategory.connect(service_category)
            created_by.service.connect(service)


            return CreateService(service=ServiceType.from_neomodel(service), success=True, message=ServiceMessages.SERVICE_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateService(service=None, success=False, message=message)
        
class UpdateService(graphene.Mutation):
    service = graphene.Field(ServiceType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateServiceInput(required=True)

    @login_required
    def mutate(self, info,  input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            service = Service.nodes.get(uid=input.uid)

            if input.name is not None:
                service.name = input.name
            if input.description is not None:
                service.description = input.description
            if input.ranking is not None:
                service.ranking = input.ranking
            service.save()

            return UpdateService(service=ServiceType.from_neomodel(service), success=True, message=ServiceMessages.SERVICE_UPDATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return UpdateService(service=None, success=False, message=message)

class DeleteService(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            service = Service.nodes.get(uid=input.uid)
            service.delete()
            return DeleteService(success=True, message=ServiceMessages.SERVICE_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteService(success=False, message=message)

class CreateServiceCategory(graphene.Mutation):
    service_category = graphene.Field(ServiceCategoryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateServiceCategoryInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)

            service_category = ServiceCategory(
                name=input.name,
                description=input.description,
                ranking=input.ranking,
                category_image_id=input.category_image_id
            )
            service_category.save()
            service_category.created_by.connect(created_by)


            return CreateServiceCategory(service_category=ServiceCategoryType.from_neomodel(service_category), success=True, message=ServiceMessages.SERVICE_CATEGORY_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateServiceCategory(service_category=None, success=False, message=message)

class UpdateServiceCategory(graphene.Mutation):
    service_category = graphene.Field(ServiceCategoryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateServiceCategoryInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            service_category = ServiceCategory.nodes.get(uid=input.uid)

            if input.name:
                service_category.name = input.name
            if input.description:
                service_category.description = input.description
            if input.ranking:
                service_category.ranking = input.ranking

            service_category.save()

            return UpdateServiceCategory(service_category=ServiceCategoryType.from_neomodel(service_category), success=True, message=ServiceMessages.SERVICE_CATEGORY_UPDATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateServiceCategory(service_category=None, success=False, message=message)

class DeleteServiceCategory(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            service_category = ServiceCategory.nodes.get(uid=input.uid)
            service_category.delete()

            return DeleteServiceCategory(success=True, message=ServiceMessages.SERVICE_CATEGORY_DELETED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteServiceCategory(success=False, message=message)

class CreateServiceOrder(graphene.Mutation):
    service_order = graphene.Field(ServiceOrderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateServiceOrderInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            service = Service.nodes.get(uid=input.service_uid)
            
            service_order = ServiceOrder(
                order_data=input.order_data
            )
            service_order.save()
            service_order.user.connect(user_node)
            service_order.service.connect(service)
            service.serviceorder.connect(service_order)
            
            return CreateServiceOrder(service_order=ServiceOrderType.from_neomodel(service_order), success=True, message=ServiceMessages.SERVICE_ORDER_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateServiceOrder(service_order=None, success=False, message=message)
        
class UpdateServiceOrder(graphene.Mutation):
    service_order = graphene.Field(ServiceOrderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateServiceOrderInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            service_order = ServiceOrder.nodes.get(uid=input.uid)
            if input.order_data:
                service_order.order_data = input.order_data
            service_order.save()
            
            return UpdateServiceOrder(service_order=ServiceOrderType.from_neomodel(service_order), success=True, message=ServiceMessages.SERVICE_ORDER_UPDATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return UpdateServiceOrder(service_order=None, success=False, message=message)

class DeleteServiceOrder(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            service_order = ServiceOrder.nodes.get(uid=input.uid)
            service_order.delete()
            
            return DeleteServiceOrder(success=True, message=ServiceMessages.SERVICE_ORDER_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteServiceOrder(success=False, message=message)

class CreateServiceProvider(graphene.Mutation):
    service_provider = graphene.Field(ServiceProviderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateServiceProviderInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            service_node = Service.nodes.get(uid=input.service_uid)

            service_provider = ServiceProviders(
                other_data=input.other_data
            )
            service_provider.save()

            service_provider.user.connect(user_node)
            service_provider.service.connect(service_node)
            service_node.serviceprovider.connect(service_provider)

            return CreateServiceProvider(service_provider=ServiceProviderType.from_neomodel(service_provider), success=True, message=ServiceMessages.SERVICE_PROVIDER_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateServiceProvider(service_provider=None, success=False, message=message)

class UpdateServiceProvider(graphene.Mutation):
    service_provider = graphene.Field(ServiceProviderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateServiceProviderInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            service_provider = ServiceProviders.nodes.get(uid=input.uid)

            if input.other_data:
                service_provider.other_data = input.other_data

            service_provider.save()
            return UpdateServiceProvider(service_provider=ServiceProviderType.from_neomodel(service_provider), success=True, message=ServiceMessages.SERVICE_PROVIDER_UPDATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return UpdateServiceProvider(service_provider=None, success=False, message=message)


class DeleteServiceProvider(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            service_provider = ServiceProviders.nodes.get(uid=input.uid)
            service_provider.delete()
            return DeleteServiceProvider(success=True, message=ServiceMessages.SERVICE_PROVIDER_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteServiceProvider(success=False, message=message)

class Mutation(graphene.ObjectType):
    create_service=CreateService.Field()
    update_service=UpdateService.Field()
    delete_service=DeleteService.Field()

    create_service_category=CreateServiceCategory.Field()
    update_service_category=UpdateServiceCategory.Field()
    delete_service_category=DeleteServiceCategory.Field()

    create_service_order=CreateServiceOrder.Field()
    update_service_order=UpdateServiceOrder.Field()
    delete_service_order=DeleteServiceOrder.Field()
    
    create_service_provider=CreateServiceProvider.Field()
    update_service_provider=UpdateServiceProvider.Field()
    delete_service_provider=DeleteServiceProvider.Field()

