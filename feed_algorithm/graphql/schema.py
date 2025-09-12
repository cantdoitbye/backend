import graphene
from .query import FeedQuery
from .mutations import FeedMutations

class Query(FeedQuery, graphene.ObjectType):
    """Root query that includes all feed algorithm queries."""
    pass

class Mutation(FeedMutations, graphene.ObjectType):
    """Root mutation that includes all feed algorithm mutations."""
    pass

# Create the schema
schema = graphene.Schema(query=Query, mutation=Mutation)
