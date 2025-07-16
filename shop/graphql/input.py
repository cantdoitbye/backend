import graphene


class CreateProductInput(graphene.InputObjectType):
    product_category_uid=graphene.String()
    name = graphene.String(required=True)
    description = graphene.String()
    cta_link = graphene.String()
    cta = graphene.String()
    hashtags = graphene.String()
    highlights = graphene.JSONString()
    price = graphene.Float(required=True)

class UpdateProductInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    name = graphene.String()
    description = graphene.String()
    cta_link = graphene.String()
    cta = graphene.String()
    hashtags = graphene.String()
    highlights = graphene.JSONString()
    price = graphene.Float()
    is_deleted = graphene.Boolean()

class DeleteProductInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateRatingInput(graphene.InputObjectType):
    product_uid = graphene.String(required=True)
    rating = graphene.Int(required=True)

class UpdateRatingInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    rating = graphene.Int(required=True)

class DeleteRatingInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateReviewShopInput(graphene.InputObjectType):
    product_uid = graphene.String(required=True)
    text = graphene.String(required=True)

class UpdateReviewShopInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    text = graphene.String()
    is_deleted = graphene.Boolean()

class DeleteReviewShopInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateProductCategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String()

class UpdateProductCategoryInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    name = graphene.String()
    description = graphene.String()
    is_deleted = graphene.Boolean()

class DeleteProductCategoryInput(graphene.InputObjectType):
    uid = graphene.String(required=True)


class CreateOrderInput(graphene.InputObjectType):
    product_uid = graphene.String(required=True)
    quantity = graphene.Int(required=True)

class UpdateOrderInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    quantity = graphene.Int()
    is_deleted = graphene.Boolean()

class DeleteOrderInput(graphene.InputObjectType):
    uid = graphene.String(required=True)










