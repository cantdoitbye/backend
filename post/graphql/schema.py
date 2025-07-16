import graphene
from .query import Query as PostQuery
from .mutation import Mutation as PostMutation
from .query import QueryV2 as PostQueryV2

schema = graphene.Schema(query=PostQuery, mutation=PostMutation)
schemaV2 = graphene.Schema(query=PostQueryV2, mutation=PostMutation)
