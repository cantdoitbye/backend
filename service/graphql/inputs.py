import graphene

class CreateServiceInput(graphene.InputObjectType):
    serviceCategory_uid=graphene.String()
    name = graphene.String()
    description = graphene.String()
    ranking = graphene.Int()
    service_form=graphene.JSONString()
    category_image_id=graphene.String()

class UpdateServiceInput(graphene.InputObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    ranking = graphene.Int()

class DeleteInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateServiceCategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String()
    ranking = graphene.Int()

class UpdateServiceCategoryInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    name = graphene.String()
    description = graphene.String()
    ranking = graphene.Int()

class CreateServiceOrderInput(graphene.InputObjectType):
    service_uid = graphene.String(required=True)
    order_data = graphene.String(required=True)

class UpdateServiceOrderInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    order_data = graphene.String()

class CreateServiceProviderInput(graphene.InputObjectType):
    service_uid = graphene.String(required=True)
    other_data = graphene.String(required=True)

class UpdateServiceProviderInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    other_data = graphene.String()