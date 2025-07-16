import graphene
from .query import Query as VibeQuery
from .mutations import Mutation as VibeMutation

schema = graphene.Schema(query=VibeQuery, mutation=VibeMutation)
