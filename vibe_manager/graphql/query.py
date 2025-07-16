# vibe_manager/graphql/query.py

import graphene
from graphene import Mutation
from graphene_django import DjangoObjectType
from neomodel import db
from graphql_jwt.decorators import login_required, superuser_required
from .types import *
from auth_manager.models import Users
from vibe_manager.models import *
from vibe_manager.graphql.enums.vibe_type import VibeTypeEnum

# GraphQL object type for Individual Vibe model
# Automatically generates GraphQL type from Django model
# Used for querying individual vibe templates from relational database
class IndividualVibeType(DjangoObjectType):
    """
    GraphQL type for IndividualVibe Django model.
    
    This automatically generates a GraphQL type from the Django model definition,
    exposing all fields of IndividualVibe through the GraphQL API.
    
    Used by:
    - Individual vibe queries
    - Vibe template selection
    - Individual vibe management interfaces
    """
    class Meta:
        model = IndividualVibe


# GraphQL object type for Community Vibe model
# Automatically generates GraphQL type from Django model
# Used for querying community vibe templates from relational database
class CommunityVibeType(DjangoObjectType):
    """
    GraphQL type for CommunityVibe Django model.
    
    Automatically exposes all CommunityVibe model fields through GraphQL,
    enabling frontend applications to query community vibe templates.
    
    Used by:
    - Community vibe queries
    - Group interaction vibe selection
    - Community vibe management
    """
    class Meta:
        model = CommunityVibe


# GraphQL object type for Brand Vibe model
# Automatically generates GraphQL type from Django model
# Used for querying brand vibe templates from relational database
class BrandVibeType(DjangoObjectType):
    """
    GraphQL type for BrandVibe Django model.
    
    Provides GraphQL access to brand vibe templates,
    supporting brand-related vibe queries and selection.
    
    Used by:
    - Brand vibe queries
    - Marketing campaign vibe selection
    - Brand interaction management
    """
    class Meta:
        model = BrandVibe


# GraphQL object type for Service Vibe model
# Automatically generates GraphQL type from Django model
# Used for querying service vibe templates from relational database
class ServiceVibeType(DjangoObjectType):
    """
    GraphQL type for ServiceVibe Django model.
    
    Enables GraphQL queries for service vibe templates,
    supporting service-related vibe functionality.
    
    Used by:
    - Service vibe queries
    - Customer service vibe selection
    - Service interaction management
    """
    class Meta:
        model = ServiceVibe


# GraphQL Union type for different vibe template types
# Allows queries to return any of the four vibe template types
# Used when frontend needs to query multiple vibe types in a single request
class VibeListDetailsType(graphene.Union):
    """
    GraphQL Union type for all vibe template types.
    
    This union allows a single query to return any of the four vibe template types
    (Individual, Community, Brand, Service) depending on the vibe_type parameter.
    
    This is useful for:
    - Dynamic vibe template selection
    - Unified vibe management interfaces
    - Flexible API responses based on context
    
    The frontend can query this union and handle different vibe types
    using GraphQL fragments or type checking.
    """
    class Meta:
        types = (IndividualVibeType, CommunityVibeType, BrandVibeType, ServiceVibeType)


# Main GraphQL Query class
# Defines all available queries for the vibe management system
# Each method corresponds to a GraphQL query that can be executed by clients
class Query(graphene.ObjectType):
    """
    Main GraphQL Query class for vibe management system.
    
    This class defines all available queries that clients can execute
    to retrieve vibe data from both Neo4j and relational databases.
    
    Each query method handles authentication, authorization, and data retrieval
    for different vibe-related use cases.
    """
    
    # Query to get all vibes from Neo4j database
    # Returns complete vibe information including relationships
    # Restricted to superusers only for security
    all_vibes = graphene.List(VibeType)
    
    # Query to get vibe template details based on vibe type
    # Returns different vibe templates from relational database
    # Accepts vibe_type parameter to filter results
    vibe_list_details = graphene.List(VibeListDetailsType, vibe_type=VibeTypeEnum())
    
    # Query to get simplified vibe list from Neo4j
    # Returns minimal vibe information for UI components
    vibe_list = graphene.List(VibeListType)
    
    # Resolver for all_vibes query
    # Requires both login and superuser privileges
    # Returns all vibes with complete information including relationships
    @login_required
    @superuser_required
    def resolve_all_vibes(self, info):
        """
        Resolves all_vibes query to return complete vibe information.
        
        This query retrieves all vibes from the Neo4j database with full details
        including relationships to creators and scoring dimensions.
        
        Authentication: Requires login and superuser privileges
        
        Returns:
            List[VibeType]: List of all vibes with complete information
            
        Security considerations:
            - Restricted to superusers only to prevent data exposure
            - Could potentially return large amounts of data
            - Should be used carefully in production
            
        Used by:
            - Admin dashboards
            - Vibe management interfaces
            - Analytics and reporting tools
        """
        return [VibeType.from_neomodel(vibe) for vibe in Vibe.nodes.all()]
    
    # Resolver for vibe_list_details query
    # Requires login but available to all authenticated users
    # Returns different vibe templates based on vibe_type parameter
    @login_required
    def resolve_vibe_list_details(self, info, vibe_type=None):
        """
        Resolves vibe_list_details query to return vibe templates by type.
        
        This query retrieves different types of vibe templates from the relational
        database based on the vibe_type parameter. It supports filtering by
        individual, community, brand, or service vibe types.
        
        Authentication: Requires login
        
        Args:
            info: GraphQL resolve info object
            vibe_type: VibeTypeEnum value to filter vibe templates
            
        Returns:
            List[VibeListDetailsType]: List of vibe templates of specified type
            
        Edge cases:
            - If vibe_type is None, returns empty list
            - If invalid vibe_type, returns empty list
            
        Used by:
            - Vibe template selection interfaces
            - Vibe creation workflows
            - Template management systems
        """
        if vibe_type.value == "individual_vibe":
            return IndividualVibe.objects.all()
        elif vibe_type.value == "community_vibe":
            return CommunityVibe.objects.all()
        elif vibe_type.value == "brand_vibe":
            return BrandVibe.objects.all()
        elif vibe_type.value == "service_vibe":
            return ServiceVibe.objects.all()
    
    # Resolver for vibe_list query
    # Requires login but available to all authenticated users
    # Returns simplified vibe information for UI components
    @login_required
    def resolve_vibe_list(self, info):
        """
        Resolves vibe_list query to return simplified vibe information.
        
        This query retrieves basic vibe information (uid and name) from Neo4j
        for use in UI components that need lightweight vibe data.
        
        Authentication: Requires login
        
        Returns:
            List[VibeListType]: List of vibes with basic information only
            
        Performance considerations:
            - More efficient than all_vibes query
            - Only transfers essential data
            - Suitable for dropdowns and selection lists
            
        Used by:
            - Vibe selection dropdowns
            - Search result lists
            - Navigation components
            - Any UI needing basic vibe identification
        """
        return [VibeListType.from_neomodel(vibe) for vibe in Vibe.nodes.all()]