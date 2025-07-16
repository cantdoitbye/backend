import graphene
from graphene import Mutation
from neomodel import db
from graphql_jwt.decorators import login_required,superuser_required

from .types import *
from auth_manager.models import Users
from shop.models import *

class Query(graphene.ObjectType):
    product_by_uid = graphene.Field(ProductType, uid=graphene.String(required=True))
    all_products = graphene.List(ProductType)

    @login_required
    def resolve_product_by_uid(self, info, uid):
        try:
            product = Product.nodes.get(uid=uid)
            return ProductType.from_neomodel(product)
        except Product.DoesNotExist:
            return None
    @superuser_required
    @login_required
    def resolve_all_products(self, info):
        return [ProductType.from_neomodel(product) for product in Product.nodes.all() if not product.is_deleted]
    

    my_product=graphene.List(ProductType)

    @login_required
    def resolve_my_product(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:
            
            my_products=list(user_node.product.all())

            return [ProductType.from_neomodel(x) for x in my_products]
        except Exception as e:
            raise Exception(e)

    rating_by_uid = graphene.Field(RatingType, uid=graphene.String(required=True))
    all_ratings = graphene.List(RatingType)

    @login_required
    def resolve_rating_by_uid(self, info, uid):
        try:
            return RatingType.from_neomodel(Rating.nodes.get(uid=uid))
        except Rating.DoesNotExist:
            return None
    @superuser_required
    @login_required
    def resolve_all_ratings(self, info):
        return [RatingType.from_neomodel(rating) for rating in Rating.nodes.all()]
    
    my_product_rating = graphene.List(RatingType)

    @login_required
    def resolve_my_product_rating(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            my_products = user_node.product.all()
            ratings = []
            for product in my_products:
                ratings.extend(list(product.rating))
            return [RatingType.from_neomodel(x) for x in ratings]
        except Exception as e:
            raise Exception(e)

    review_shop_by_uid = graphene.Field(ReviewShopType, uid=graphene.String(required=True))
    all_review_shops = graphene.List(ReviewShopType)

    @login_required
    def resolve_review_shop_by_uid(self, info, uid):
        try:
            return ReviewShopType.from_neomodel(ReviewShop.nodes.get(uid=uid))
        except ReviewShop.DoesNotExist:
            return None
    @superuser_required
    @login_required
    def resolve_all_review_shops(self, info):
        return [ReviewShopType.from_neomodel(review_shop) for review_shop in ReviewShop.nodes.all()]
    
    my_product_review = graphene.List(ReviewShopType)

    @login_required
    def resolve_my_product_review(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            my_products = user_node.product.all()
            reviews = []
            for product in my_products:
                reviews.extend(list(product.reviewshop))
            return [ReviewShopType.from_neomodel(x) for x in reviews]
        except Exception as e:
            raise Exception(e)


    product_category_by_uid = graphene.Field(ProductCategoryType, uid=graphene.String(required=True))
    all_product_categories = graphene.List(ProductCategoryType)

    @login_required
    def resolve_product_category_by_uid(self, info, uid):
        try:
            return ProductCategoryType.from_neomodel(ProductCategory.nodes.get(uid=uid))
        except ProductCategory.DoesNotExist:
            return None
    @superuser_required
    @login_required
    def resolve_all_product_categories(self, info):
        return [ProductCategoryType.from_neomodel(product_category) for product_category in ProductCategory.nodes.all()]
    

    order_by_uid = graphene.Field(OrderType, uid=graphene.String(required=True))

    @login_required
    def resolve_order_by_uid(self, info, uid):
        try:
            order = Order.nodes.get(uid=uid)
            return OrderType.from_neomodel(order)
        except Order.DoesNotExist:
            return None
        
    all_orders = graphene.List(OrderType)
    @superuser_required
    @login_required
    def resolve_all_orders(self, info):
        orders = Order.nodes.all()
        return [OrderType.from_neomodel(order) for order in orders]
    
    my_product_order = graphene.List(OrderType)

    @login_required
    def resolve_my_product_order(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            my_products = user_node.product.all()
            orders = []
            for product in my_products:
                orders.extend(list(product.order))
            return [ReviewShopType.from_neomodel(x) for x in orders]
        except Exception as e:
            raise Exception(e)