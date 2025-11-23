"""
GraphQL Schema for Notification Module

This module provides the complete GraphQL schema for notifications,
including queries and mutations.

Usage:
    Add to your main schema.py:
    
    from notification.graphql.schema import NotificationQueries, NotificationMutations
    
    class Query(NotificationQueries, OtherQueries, graphene.ObjectType):
        pass
    
    class Mutation(NotificationMutations, OtherMutations, graphene.ObjectType):
        pass
"""

import graphene
from notification.graphql.queries import NotificationQueries
from notification.graphql.mutations import NotificationMutations


# Export for easy import
__all__ = ['NotificationQueries', 'NotificationMutations']


# Example schema (if using standalone)
class Query(NotificationQueries, graphene.ObjectType):
    """Root Query"""
    pass


class Mutation(NotificationMutations, graphene.ObjectType):
    """Root Mutation"""
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
