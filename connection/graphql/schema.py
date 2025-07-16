import graphene
from .query import Query as ConnectionQuery
from .query import QueryV2 as ConnectionQueryV2
from .mutations import Mutation as ConnectionMutation
from .mutations import MutationV2 as ConnectionMutationV2


schema = graphene.Schema(query=ConnectionQuery, mutation=ConnectionMutation)
schemaV2 = graphene.Schema(query=ConnectionQueryV2, mutation=ConnectionMutationV2)

