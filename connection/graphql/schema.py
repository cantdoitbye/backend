import graphene
from .query import Query as ConnectionQuery
from .mutations import Mutation as ConnectionMutation


schema = graphene.Schema(query=ConnectionQuery, mutation=ConnectionMutation)

