# vibe_manager/graphql/types.py
import graphene
from graphene import ObjectType
from auth_manager.graphql.types import UserType

# GraphQL type definition for Vibe objects
# This defines the structure of Vibe data when returned through GraphQL API
# Used by frontend applications to query vibe data with type safety
class VibeType(ObjectType):
    """
    GraphQL type for Vibe objects returned from Neo4j database.
    
    This type defines the structure of vibe data when queried through GraphQL API.
    It provides type safety for frontend applications and defines exactly what
    fields can be requested and their data types.
    
    Used by:
    - Frontend applications querying vibe data
    - GraphQL schema generation
    - API documentation generation
    - Type checking in GraphQL queries
    
    Maps directly to the Vibe model fields from Neo4j database.
    """
    
    # Unique identifier for the vibe
    uid = graphene.String()
    
    # Basic vibe information fields
    name = graphene.String()  # Display name of the vibe
    category = graphene.String()  # Main category classification
    description = graphene.String()  # Detailed description
    subCategory = graphene.String()  # More specific categorization
    desc = graphene.String()  # Additional description field
    
    # Vibe scoring dimensions - these affect user scores when vibe is sent
    # Each dimension represents a different aspect of the vibe's impact
    iq = graphene.Float()  # Intelligence quotient impact (0.0-4.0)
    aq = graphene.Float()  # Appeal quotient impact (0.0-4.0)
    sq = graphene.Float()  # Social quotient impact (0.0-4.0)
    hq = graphene.Float()  # Human quotient impact (0.0-4.0)
    
    # Relationship to the user who created this vibe
    # Returns a UserType object with creator information
    created_by = graphene.Field(UserType)  # Assuming UserType is already defined
    
    # Popularity metric - how often this vibe has been used/sent
    popularity = graphene.Int()
    
    # Class method to convert Neo4j Vibe model instance to GraphQL type
    # This is the bridge between database model and GraphQL API response
    @classmethod
    def from_neomodel(cls, vibe):
        """
        Converts a Neo4j Vibe model instance to GraphQL VibeType.
        
        This method bridges the gap between the database model and GraphQL API.
        It safely extracts data from the Neo4j model and creates a GraphQL type
        that can be serialized and sent to frontend applications.
        
        Args:
            vibe: Vibe model instance from Neo4j database
            
        Returns:
            VibeType: GraphQL type instance with vibe data
            
        Edge cases:
            - Handles case where created_by relationship might not exist
            - Returns None for created_by if no relationship found
            
        Used by:
            - GraphQL query resolvers
            - Vibe list endpoints
            - Individual vibe detail queries
        """
        return cls(
            uid=vibe.uid,
            name=vibe.name,
            category=vibe.category,
            description=vibe.description,
            subCategory=vibe.subCategory,
            desc=vibe.desc,
            iq=vibe.iq,
            aq=vibe.aq,
            sq=vibe.sq,
            hq=vibe.hq,
            # Safely handle created_by relationship - return None if no creator found
            created_by=UserType.from_neomodel(vibe.created_by.single()) if vibe.created_by.single() else None,
            popularity=vibe.popularity,
        )


# Simplified GraphQL type for vibe lists
# Used when you only need basic vibe information (like in dropdown lists or search results)
# More efficient than full VibeType when detailed information isn't needed
class VibeListType(ObjectType):
    """
    Simplified GraphQL type for vibe list views.
    
    This lighter version of VibeType is used when you only need basic vibe information,
    such as in dropdown lists, search results, or navigation components.
    
    It's more efficient than full VibeType because it only transfers essential data,
    reducing bandwidth and improving performance for list-based queries.
    
    Used by:
    - Vibe selection dropdowns
    - Search result lists
    - Navigation menus
    - Any UI that needs basic vibe identification
    
    Assumptions:
    - UI only needs uid and name for basic vibe identification
    - Performance is prioritized over detailed information
    """
    
    # Minimal fields needed for vibe identification
    uid = graphene.String()  # Unique identifier for selection/linking
    name = graphene.String()  # Display name for user interface
    
    # Conversion method from Neo4j model to GraphQL type
    @classmethod
    def from_neomodel(cls, vibe):
        """
        Converts Neo4j Vibe model to simplified GraphQL VibeListType.
        
        This method creates a lightweight version of the vibe data,
        containing only the essential information needed for list views.
        
        Args:
            vibe: Vibe model instance from Neo4j database
            
        Returns:
            VibeListType: Simplified GraphQL type with minimal vibe data
            
        Used by:
            - Vibe list query resolvers
            - Search functionality
            - Dropdown population
            - Quick vibe reference lookups
        """
        return cls(
            uid=vibe.uid,
            name=vibe.name,
        )