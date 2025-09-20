"""Analytics GraphQL Schema

This module defines the main GraphQL schema for analytics,
combining queries and mutations for comprehensive analytics functionality.
"""

import graphene
from .queries import AnalyticsQuery
from .mutations import AnalyticsMutation


class Query(AnalyticsQuery, graphene.ObjectType):
    """Root query for analytics."""
    pass


class Mutation(AnalyticsMutation, graphene.ObjectType):
    """Root mutation for analytics."""
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)