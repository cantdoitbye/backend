import graphene
from .query import Query as PostQuery
from .mutation import Mutation as PostMutation


schema = graphene.Schema(query=PostQuery, mutation=PostMutation)
