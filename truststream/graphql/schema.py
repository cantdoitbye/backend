# truststream/graphql/schema.py

"""
TrustStream GraphQL Schema

This module combines all TrustStream GraphQL queries and mutations into a cohesive schema.
"""

from .queries import TrustStreamQuery
from .mutations import TrustStreamMutation


# Export the query and mutation classes for integration with the main schema
TrustQuery = TrustStreamQuery
TrustMutation = TrustStreamMutation