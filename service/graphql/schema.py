import graphene
from .query import Query as ServiceQuery
from .mutations import Mutation as ServiceMutation

schema = graphene.Schema(query=ServiceQuery, mutation=ServiceMutation)