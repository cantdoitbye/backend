import graphene
from .query import Query as MsgQuery
from .mutations import Mutation as MsgMutation

schema = graphene.Schema(query=MsgQuery, mutation=MsgMutation)