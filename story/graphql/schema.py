import graphene
from .query import Query as StoryQuery
from .mutation import Mutation as StoryMutation
from .query import QueryV2 as StoryQueryV2

schema = graphene.Schema(query=StoryQuery, mutation=StoryMutation)
schemaV2 = graphene.Schema(query=StoryQueryV2, mutation=StoryMutation)
