
import graphene
from .queries import Query as UserQuery
from .queries import QueryV2 as UserQueryV2
from .mutations import Mutation as UserMutation
from .mutations import MutationV2 as UserMutationV2

schema = graphene.Schema(query=UserQuery, mutation=UserMutation)
schemav2 = graphene.Schema(query=UserQueryV2, mutation=UserMutationV2)
