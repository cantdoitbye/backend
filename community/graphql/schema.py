# graphql/schema.py

import graphene
from .queries import Query as CommunityQuery
from .mutations import Mutation as CommunityMutation

schema = graphene.Schema(query=CommunityQuery, mutation=CommunityMutation)
