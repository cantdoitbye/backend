import graphene
from graphene import ObjectType

from auth_manager.graphql.types import UserType

class ProductType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    cta_link = graphene.String()
    cta = graphene.String()
    hashtags = graphene.String()
    highlights = graphene.JSONString()
    price = graphene.Float()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    created_by = graphene.Field(UserType)
    is_deleted = graphene.Boolean()
    productcategory= graphene.Field(lambda:ProductCategoryType)
    rating=graphene.List(lambda:RatingNonProductType)
    reviewshop=graphene.List(lambda:ReviewShopNonProductType)
    order=graphene.List(lambda:OrderNonProductType)
    @classmethod
    def from_neomodel(cls, product):
        return cls(
            uid=product.uid,
            name=product.name,
            description=product.description,
            cta_link=product.cta_link,
            cta=product.cta,
            hashtags=product.hashtags,
            highlights=product.highlights,
            price=product.price,
            created_at=product.created_at,
            updated_at=product.updated_at,
            created_by=UserType.from_neomodel(product.created_by.single()) if product.created_by.single() else None,
            productcategory=UserType.from_neomodel(product.productcategory.single()) if product.productcategory.single() else None,
            rating=[RatingNonProductType.from_neomodel(x) for x in product.rating],
            reviewshop=[ReviewShopNonProductType.from_neomodel(x) for x in product.reviewshop],
            order= [OrderNonProductType.from_neomodel(x) for x in product.order],
            is_deleted=product.is_deleted,
        )
    
class RatingType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    product = graphene.Field(ProductType)
    rating = graphene.Int()

    @classmethod
    def from_neomodel(cls, rating_instance):
        return cls(
            uid=rating_instance.uid,
            user=UserType.from_neomodel(rating_instance.user.single()) if rating_instance.user.single() else None,
            product=ProductType.from_neomodel(rating_instance.product.single()) if rating_instance.product.single() else None,
            rating=rating_instance.rating,
        )
    
class ReviewShopType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    product = graphene.Field(ProductType)
    text = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, review_shop):
        return cls(
            uid=review_shop.uid,
            user=UserType.from_neomodel(review_shop.user.single()) if review_shop.user.single() else None,
            product=ProductType.from_neomodel(review_shop.product.single()) if review_shop.product.single() else None,
            text=review_shop.text,
            created_at=review_shop.created_at,
            updated_at=review_shop.updated_at,
            is_deleted=review_shop.is_deleted,
        )
    
class ProductCategoryType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    created_at = graphene.DateTime()
    created_by = graphene.Field(UserType)
    updated_at = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, product_category):
        return cls(
            uid=product_category.uid,
            name=product_category.name,
            description=product_category.description,
            created_at=product_category.created_at,
            created_by=UserType.from_neomodel(product_category.created_by.single()) if product_category.created_by.single() else None,
            updated_at=product_category.updated_at,
            is_deleted=product_category.is_deleted,
        )
    
class OrderType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    product = graphene.Field(ProductType)
    quantity = graphene.Int()
    order_date = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, order):
        return cls(
            uid=order.uid,
            user=UserType.from_neomodel(order.user.single()) if order.user.single() else None,
            product=ProductType.from_neomodel(order.product.single()) if order.product.single() else None,
            quantity=order.quantity,
            order_date=order.order_date,
            is_deleted=order.is_deleted,
        )

class RatingNonProductType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    rating = graphene.Int()

    @classmethod
    def from_neomodel(cls, rating_instance):
        return cls(
            uid=rating_instance.uid,
            user=UserType.from_neomodel(rating_instance.user.single()) if rating_instance.user.single() else None,
            rating=rating_instance.rating,
        )
    
class ReviewShopNonProductType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    text = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, review_shop):
        return cls(
            uid=review_shop.uid,
            user=UserType.from_neomodel(review_shop.user.single()) if review_shop.user.single() else None,
            text=review_shop.text,
            created_at=review_shop.created_at,
            updated_at=review_shop.updated_at,
            is_deleted=review_shop.is_deleted,
        )
    

    
class OrderNonProductType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    quantity = graphene.Int()
    order_date = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, order):
        return cls(
            uid=order.uid,
            user=UserType.from_neomodel(order.user.single()) if order.user.single() else None,
            quantity=order.quantity,
            order_date=order.order_date,
            is_deleted=order.is_deleted,
        )









