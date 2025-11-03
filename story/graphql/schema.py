import graphene
from .query import Query as StoryQuery
from .mutation import Mutation as StoryMutation


schema = graphene.Schema(query=StoryQuery, mutation=StoryMutation)
