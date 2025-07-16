
import graphene
from .queries import Query as monitoringQuery
from .mutations import Mutation as monitoringMutation

schema = graphene.Schema(query=monitoringQuery, mutation=monitoringMutation)
