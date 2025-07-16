import graphene
from .query import Query as ShopQuery
from .mutations import Mutation as ShopMutation

schema = graphene.Schema(query=ShopQuery, mutation=ShopMutation)