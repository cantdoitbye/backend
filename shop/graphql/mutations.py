import graphene
from graphene import Mutation
from graphql import GraphQLError
from .types import *
from auth_manager.models import Users
from shop.models import *
from .input import *
from .messages import ShopMessages
from graphql_jwt.decorators import login_required,superuser_required

class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateProductInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)
            category = ProductCategory.nodes.get(uid=input.product_category_uid)
            product = Product(
                name=input.name,
                description=input.description,
                cta_link=input.cta_link,
                cta=input.cta,
                hashtags=input.hashtags,
                highlights=input.highlights,
                price=input.price,
            )
            product.save()
            product.created_by.connect(created_by)
            product.productcategory.connect(category)
            created_by.product.connect(product)
            return CreateProduct(product=ProductType.from_neomodel(product), success=True, message=ShopMessages.MEETING_CREATED)
        except Exception as e:
            return CreateProduct(product=None, success=False, message=str(e))
        
class UpdateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateProductInput(required=True)
    
    @login_required
    def mutate(self, info, input):
        try:
            product = Product.nodes.get(uid=input.uid)

            if input.name:
                product.name = input.name
            if input.description:
                product.description = input.description
            if input.cta_link:
                product.cta_link = input.cta_link
            if input.cta:
                product.cta = input.cta
            if input.hashtags:
                product.hashtags = input.hashtags
            if input.highlights:
                product.highlights = input.highlights
            if input.price is not None:
                product.price = input.price
            if input.is_deleted is not None:
                product.is_deleted = input.is_deleted

            product.save()
            return UpdateProduct(product=ProductType.from_neomodel(product), success=True, message=ShopMessages.MEETING_UPDATED)
        except Exception as e:
            return UpdateProduct(product=None, success=False, message=str(e))

class DeleteProduct(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteProductInput(required=True)
    
    @login_required 
    def mutate(self, info, input):
        try:
            product = Product.nodes.get(uid=input.uid)
            product.is_deleted = True
            product.save()
            return DeleteProduct(success=True, message=ShopMessages.MEETING_DELETED)
        except Exception as e:
            return DeleteProduct(success=False, message=str(e))

class CreateRating(Mutation):
    rating = graphene.Field(RatingType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateRatingInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_instance = Users.nodes.get(user_id=user_id)
            product_instance = Product.nodes.get(uid=input.product_uid)
            rating_instance = Rating(
                rating=input.rating
            )
            rating_instance.save()
            rating_instance.user.connect(user_instance)
            rating_instance.product.connect(product_instance)
            product_instance.rating.connect()
            return CreateRating(rating=RatingType.from_neomodel(rating_instance), success=True, message=ShopMessages.RATING_CREATED)
        except Exception as e:
            return CreateRating(rating=None, success=False, message=str(e))    
        
class UpdateRating(Mutation):
    rating = graphene.Field(RatingType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateRatingInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            rating_instance = Rating.nodes.get(uid=input.uid)
            rating_instance.rating = input.rating
            rating_instance.save()
            return UpdateRating(rating=RatingType.from_neomodel(rating_instance), success=True, message=ShopMessages.RATING_UPDATED)
        except Exception as e:
            return UpdateRating(rating=None, success=False, message=str(e))
        
class DeleteRating(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteRatingInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            rating_instance = Rating.nodes.get(uid=input.uid)
            rating_instance.delete()
            return DeleteRating(success=True, message=ShopMessages.RATING_DELETED)
        except Exception as e:
            return DeleteRating(success=False, message=str(e))

class CreateReviewShop(graphene.Mutation):
    review_shop = graphene.Field(ReviewShopType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateReviewShopInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            product = Product.nodes.get(uid=input.product_uid)

            review_shop = ReviewShop(
                text=input.text
            )
            review_shop.save()
            review_shop.user.connect(user)
            review_shop.product.connect(product)
            product.reviewshop.connect(review_shop)

            return CreateReviewShop(review_shop=ReviewShopType.from_neomodel(review_shop), success=True, message=ShopMessages.REVIEW_SHOP_CREATED)
        except Exception as e:
            return CreateReviewShop(review_shop=None, success=False, message=str(e))

class UpdateReviewShop(graphene.Mutation):
    review_shop = graphene.Field(ReviewShopType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateReviewShopInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            review_shop = ReviewShop.nodes.get(uid=input.uid)
            if input.text:
                review_shop.text = input.text
            if input.is_deleted is not None:
                review_shop.is_deleted = input.is_deleted
            review_shop.save()

            return UpdateReviewShop(review_shop=ReviewShopType.from_neomodel(review_shop), success=True, message=ShopMessages.REVIEW_SHOP_UPDATED)
        except Exception as e:
            return UpdateReviewShop(review_shop=None, success=False, message=str(e))

class DeleteReviewShop(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteReviewShopInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            review_shop = ReviewShop.nodes.get(uid=input.uid)
            review_shop.delete()

            return DeleteReviewShop(success=True, message=ShopMessages.REVIEW_SHOP_CREATED)
        except Exception as e:
            return DeleteReviewShop(success=False, message=str(e))

class CreateProductCategory(graphene.Mutation):
    product_category = graphene.Field(ProductCategoryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateProductCategoryInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)

            product_category = ProductCategory(
                name=input.name,
                description=input.description
            )
            product_category.save()
            product_category.created_by.connect(user)

            return CreateProductCategory(product_category=ProductCategoryType.from_neomodel(product_category), success=True, message=ShopMessages.PRODUCT_CATEGORY_CREATED)
        except Exception as e:
            return CreateProductCategory(product_category=None, success=False, message=str(e))

class UpdateProductCategory(graphene.Mutation):
    product_category = graphene.Field(ProductCategoryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateProductCategoryInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            product_category = ProductCategory.nodes.get(uid=input.uid)
            if input.name:
                product_category.name = input.name
            if input.description:
                product_category.description = input.description
            if input.is_deleted is not None:
                product_category.is_deleted = input.is_deleted
            product_category.save()

            return UpdateProductCategory(product_category=ProductCategoryType.from_neomodel(product_category), success=True, message=ShopMessages.PRODUCT_CATEGORY_UPDATED)
        except Exception as e:
            return UpdateProductCategory(product_category=None, success=False, message=str(e))

class DeleteProductCategory(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteProductCategoryInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            product_category = ProductCategory.nodes.get(uid=input.uid)
            product_category.delete()

            return DeleteProductCategory(success=True, message=ShopMessages.PRODUCT_CATEGORY_DELETED)
        except Exception as e:
            return DeleteProductCategory(success=False, message=str(e))

class CreateOrder(graphene.Mutation):
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateOrderInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            product = Product.nodes.get(uid=input.product_uid)

            order = Order(
                quantity=input.quantity,
            )
            order.save()
            order.user.connect(user)
            order.product.connect(product)
            product.order.connect(order)
            return CreateOrder(order=OrderType.from_neomodel(order), success=True, message=ShopMessages.ORDER_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateOrder(order=None, success=False, message=message)

class UpdateOrder(graphene.Mutation):
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateOrderInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            order = Order.nodes.get(uid=input.uid)
            
            if input.quantity:
                order.quantity = input.quantity

            if input.is_deleted is not None:
                order.is_deleted = input.is_deleted

            order.save()
            return UpdateOrder(order=OrderType.from_neomodel(order), success=True, message=ShopMessages.ORDER_UPDATED)
        except Exception as e:
            return UpdateOrder(order=None, success=False, message=str(e))

class DeleteOrder(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteOrderInput(required=True)
        
    @login_required
    def mutate(self, info, input):
        try:
            order = Order.nodes.get(uid=input.uid)
            order.is_deleted = True
            order.save()
            return DeleteOrder(success=True, message=ShopMessages.ORDER_DELETED)
        except Exception as e:
            return DeleteOrder(success=False, message=str(e))


class Mutation(graphene.ObjectType):
    create_product=CreateProduct.Field()
    update_product=UpdateProduct.Field()
    delete_product=DeleteProduct.Field()

    create_rating=CreateRating.Field()
    update_rating=UpdateRating.Field()
    delete_rating=DeleteRating.Field()

    create_review_shop=CreateReviewShop.Field()
    update_review_shop=UpdateReviewShop.Field()
    delete_review_shop=DeleteReviewShop.Field()

    create_product_category=CreateProductCategory.Field()
    update_product_category=UpdateProductCategory.Field()
    delete_product_category=DeleteProductCategory.Field()

    create_order=CreateOrder.Field()
    update_order=UpdateOrder.Field()
    delete_order=DeleteOrder.Field()