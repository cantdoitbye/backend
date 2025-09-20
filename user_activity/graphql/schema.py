import graphene
from user_activity.graphql.queries import Query
from user_activity.graphql.mutations import Mutation


class UserActivityQuery(Query, graphene.ObjectType):
    """User Activity GraphQL Query"""
    pass


class UserActivityMutation(Mutation, graphene.ObjectType):
    """User Activity GraphQL Mutation"""
    pass


schema = graphene.Schema(
    query=UserActivityQuery,
    mutation=UserActivityMutation
)