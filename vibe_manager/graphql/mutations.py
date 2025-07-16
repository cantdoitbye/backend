# vibe_manager/graphql/mutations.py

import graphene
from graphene import Mutation
from graphql import GraphQLError
from .types import *
from auth_manager.models import Users, Score
from vibe_manager.models import *
from ..utils import *
from graphql_jwt.decorators import login_required, superuser_required

# GraphQL Input type for creating new vibes
# Defines the structure and validation rules for vibe creation requests
# Used by CreateVibe mutation to validate and process incoming data
class CreateVibeInput(graphene.InputObjectType):
    """
    GraphQL input type for creating new vibes.
    
    This input type defines the structure and validation rules for vibe creation requests.
    It specifies which fields are required, their data types, and any constraints.
    
    Used by:
    - CreateVibe mutation
    - Vibe creation forms in frontend
    - API documentation generation
    - Input validation and type checking
    
    Validation rules:
    - name: Required, must be unique
    - category: Required, used for vibe classification
    - iq, aq, sq, hq: Required, must be valid float values (typically 0.0-4.0)
    - Other fields: Optional, can be null or empty
    """
    
    # Required fields for vibe creation
    name = graphene.String(required=True)  # Display name - must be unique
    category = graphene.String(required=True)  # Main category classification
    
    # Optional descriptive fields
    description = graphene.String()  # Detailed description
    subCategory = graphene.String()  # More specific categorization
    desc = graphene.String()  # Additional description field
    
    # Required scoring dimensions that affect user scores when vibe is sent
    iq = graphene.Float(required=True)  # Intelligence quotient impact
    aq = graphene.Float(required=True)  # Appeal quotient impact
    sq = graphene.Float(required=True)  # Social quotient impact
    hq = graphene.Float(required=True)  # Human quotient impact
    
    # Optional popularity metric
    popularity = graphene.Int()  # Initial popularity value


# GraphQL Mutation for creating new vibes
# Handles the creation of new vibe entities in the Neo4j database
# Establishes relationships between vibes and their creators
class CreateVibe(graphene.Mutation):
    """
    GraphQL mutation for creating new vibes.
    
    This mutation handles the complete process of creating a new vibe entity:
    1. Validates user authentication
    2. Extracts user information from JWT token
    3. Creates new vibe in Neo4j database
    4. Establishes bidirectional relationship with creator
    5. Returns success/failure response
    
    Authentication: Requires valid JWT token
    
    Process flow:
    1. Validate user is authenticated
    2. Extract user_id from JWT payload
    3. Find creator user in database
    4. Create new vibe with provided data
    5. Save vibe to Neo4j
    6. Connect vibe to creator (bidirectional relationship)
    7. Return success response with created vibe
    
    Used by:
    - Vibe creation forms
    - Admin vibe management interfaces
    - Bulk vibe creation tools
    """
    
    # Response fields returned after mutation execution
    vibe = graphene.Field(VibeType)  # The created vibe object
    success = graphene.Boolean()  # Whether operation succeeded
    message = graphene.String()  # Success/error message for user feedback
    
    # Input arguments for the mutation
    class Arguments:
        input = CreateVibeInput(required=True)
    
    # Mutation resolver method
    @login_required
    def mutate(self, info, input):
        """
        Executes the vibe creation process.
        
        This method handles the complete vibe creation workflow including
        authentication, validation, database operations, and relationship creation.
        
        Args:
            info: GraphQL resolve info containing request context
            input: CreateVibeInput with vibe data
            
        Returns:
            CreateVibe: Mutation response with vibe, success flag, and message
            
        Authentication:
            - Requires valid JWT token
            - Extracts user_id from JWT payload
            - Validates user exists in database
            
        Edge cases:
            - Anonymous user access (returns authentication error)
            - Invalid user_id in JWT (returns user not found error)
            - Database connection issues (returns error message)
            - Duplicate vibe names (handled by database constraints)
            
        Side effects:
            - Creates new vibe in Neo4j database
            - Establishes bidirectional relationship with creator
            - Updates user's created vibes list
        """
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            # Extract user information from JWT token
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            # Find the creator user in Neo4j database
            created_by = Users.nodes.get(user_id=user_id)
            
            # Create new vibe instance with provided data
            vibe = Vibe(
                name=input.name,
                category=input.category,
                description=input.description,
                subCategory=input.subCategory,
                desc=input.desc,
                iq=input.iq,
                aq=input.aq,
                sq=input.sq,
                hq=input.hq,
                popularity=input.popularity,
            )
            
            # Save vibe to Neo4j database
            vibe.save()
            
            # Establish bidirectional relationship between vibe and creator
            vibe.created_by.connect(created_by)  # Vibe -> User relationship
            created_by.vibe.connect(vibe)  # User -> Vibe relationship
            
            return CreateVibe(
                vibe=VibeType.from_neomodel(vibe), 
                success=True, 
                message="Vibe created successfully."
            )
            
        except Exception as error:
            # Handle any errors during vibe creation
            return CreateVibe(
                vibe=None, 
                success=False, 
                message=str(error)
            )


# GraphQL Mutation for sending vibes between users
# Handles the process of sending vibes and updating user scores
# Integrates with the scoring system to affect user metrics
class SendVibe(graphene.Mutation):
    """
    GraphQL mutation for sending vibes between users.
    
    This mutation handles the complete process of sending a vibe:
    1. Validates user authentication
    2. Identifies the vibe being sent
    3. Calculates score impacts
    4. Updates user scores and metrics
    5. Records the vibe transaction
    
    This is a core feature of the vibe system that affects user scores
    and creates social interactions between users.
    
    Authentication: Requires valid JWT token
    
    Process flow:
    1. Validate user authentication
    2. Extract user information from JWT
    3. Call VibeUtils.onVibeCreated() to handle scoring
    4. Return success/failure response
    
    Used by:
    - Vibe sending interfaces
    - Social interaction features
    - User scoring system
    - Analytics and engagement tracking
    """
    
    # Response fields
    message = graphene.String()  # Success/error message
    
    # Input arguments
    class Arguments:
        vibename = graphene.String(required=True)  # Name of vibe to send
        vibescore = graphene.Float(required=True)  # Score value for this vibe send
    
    def mutate(self, info, vibename, vibescore):
        """
        Executes the vibe sending process.
        
        This method handles the complete vibe sending workflow including
        authentication, score calculation, and user metric updates.
        
        Args:
            info: GraphQL resolve info containing request context
            vibename: String name of the vibe to send
            vibescore: Float score value for this vibe interaction
            
        Returns:
            SendVibe: Mutation response with success/error message
            
        Authentication:
            - Requires valid JWT token
            - Extracts user_id from JWT payload
            - Validates user exists in database
            
        Score calculation:
            - Delegates to VibeUtils.onVibeCreated()
            - Updates user's IQ, AQ, SQ, HQ scores
            - Records vibe transaction history
            - Updates cumulative vibe scores
            
        Edge cases:
            - Anonymous user access (returns authentication error)
            - Invalid vibe name (handled by VibeUtils)
            - Database connection issues (caught by exception handler)
            
        Side effects:
            - Updates user score metrics
            - Creates UserVibeRepo record
            - Increments user's vibers_count
        """
        user = info.context.user
        try:
            # Validate user authentication
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            # Extract user information from JWT token
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            # Find the user in Neo4j database
            user = Users.nodes.get(user_id=user_id)
            
            # Delegate to VibeUtils to handle score calculation and updates
            # This method handles all the complex scoring logic
            VibeUtils.onVibeCreated(user, vibename, vibescore)
            
            return SendVibe(message="Vibe send successfully")
            
        except Exception as e:
            # Handle any errors during vibe sending
            return SendVibe(message=str(e))


# Main Mutation class that combines all vibe-related mutations
# This class is registered with the GraphQL schema to expose mutations
# Provides a single entry point for all vibe mutation operations
class Mutation(graphene.ObjectType):
    """
    Main GraphQL Mutation class for vibe management system.
    
    This class serves as the central registry for all vibe-related mutations.
    It combines individual mutation classes into a single interface that
    gets registered with the GraphQL schema.
    
    By organizing mutations this way, the GraphQL schema stays clean and
    all vibe-related operations are grouped together logically.
    
    Available mutations:
    - create_vibe: Creates new vibe entities
    - send_vibe: Sends vibes between users and updates scores
    
    Used by:
    - GraphQL schema registration
    - API documentation generation
    - Frontend mutation calls
    - GraphQL introspection queries
    """
    
    # Register CreateVibe mutation
    create_vibe = CreateVibe.Field()
    
    # Register SendVibe mutation  
    send_vibe = SendVibe.Field()