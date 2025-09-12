import graphene
from graphql_jwt.decorators import login_required
from ..models import UserProfile, FeedComposition
from .types import UserProfileType, FeedCompositionType, FeedResponseType

class FeedQuery(graphene.ObjectType):
    """GraphQL queries for feed algorithm functionality."""
    
    # Get current user's feed profile
    my_feed_profile = graphene.Field(UserProfileType)
    
    # Get current user's feed composition
    my_feed_composition = graphene.Field(FeedCompositionType)
    
    # Generate a personalized feed
    generate_feed = graphene.Field(
        FeedResponseType,
        size=graphene.Int(default_value=20),
        refresh_cache=graphene.Boolean(default_value=False),
        description="Generate a personalized feed based on user's preferences"
    )
    
    @login_required
    def resolve_my_feed_profile(self, info, **kwargs):
        """Resolve current user's feed profile."""
        return UserProfile.objects.get_or_create(user=info.context.user)[0]
    
    @login_required
    def resolve_my_feed_composition(self, info, **kwargs):
        """Resolve current user's feed composition settings."""
        return FeedComposition.objects.get_or_create(user=info.context.user)[0]
    
    @login_required
    def resolve_generate_feed(self, info, size=20, refresh_cache=False, **kwargs):
        """
        Generate a personalized feed for the current user.
        
        Args:
            size: Number of items to return (default: 20)
            refresh_cache: Whether to bypass cache (default: False)
            
        Returns:
            FeedResponseType with generated feed items and metadata
        """
        from ..services import FeedGenerationService
        
        try:
            # Initialize feed generation service with current user
            feed_service = FeedGenerationService(info.context.user)
            
            # Generate feed using the service
            feed_data = feed_service.generate_feed(size=size, force_refresh=refresh_cache)
            
            return {
                'success': True,
                'message': 'Feed generated successfully',
                'items': feed_data.get('items', []),
                'total_count': feed_data.get('total_count', 0),
                'has_more': feed_data.get('has_more', False),
                'composition': feed_data.get('composition', {}),
                'generated_at': feed_data.get('generated_at')
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'items': [],
                'total_count': 0,
                'has_more': False,
                'generated_at': timezone.now()
            }
