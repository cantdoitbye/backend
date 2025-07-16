import graphene
from .query import Query as JobQuery
from .mutations import Mutation as JobMutation

schema = graphene.Schema(query=JobQuery, mutation=JobMutation)