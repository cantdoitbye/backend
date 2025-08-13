# Agentic GraphQL Schema
# This module defines the GraphQL schema for the agentic community management system.

import graphene
from .queries import AgentQueries
from .mutations import AgentMutations


class AgentQuery(AgentQueries, graphene.ObjectType):
    """
    Root query class for agentic operations.
    Combines all agent-related queries.
    """
    pass


class AgentMutation(AgentMutations, graphene.ObjectType):
    """
    Root mutation class for agentic operations.
    Combines all agent-related mutations.
    """
    pass


# Export for main schema integration
__all__ = ['AgentQuery', 'AgentMutation']