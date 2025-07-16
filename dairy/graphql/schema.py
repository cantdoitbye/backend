import graphene
from .query import Query as DairyQuery
from .mutations import Mutation as DairyMutation

schema = graphene.Schema(query=DairyQuery, mutation=DairyMutation)
