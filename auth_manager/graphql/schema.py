
import graphene
from .queries import Query as UserQuery
from .mutations import Mutation as UserMutation

schema = graphene.Schema(query=UserQuery, mutation=UserMutation)
