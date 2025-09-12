import graphene
from graphql_jwt.decorators import login_required
from django.core.exceptions import ValidationError
from ..models import UserProfile, FeedComposition
from .types import UserProfileType, FeedCompositionType

class UpdateFeedProfile(graphene.Mutation):
    """Update the current user's feed profile settings."""
    
    class Arguments:
        feed_enabled = graphene.Boolean()
        content_language = graphene.String()
        privacy_level = graphene.String()
    
    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @login_required
    def mutate(self, info, **kwargs):
        try:
            profile = UserProfile.objects.get(user=info.context.user)
            
            # Update fields if provided
            for field in ['feed_enabled', 'content_language', 'privacy_level']:
                if field in kwargs:
                    setattr(profile, field, kwargs[field])
            
            profile.save()
            return UpdateFeedProfile(
                profile=profile,
                success=True,
                message="Feed profile updated successfully"
            )
            
        except Exception as e:
            return UpdateFeedProfile(
                profile=None,
                success=False,
                message=str(e)
            )

class UpdateFeedComposition(graphene.Mutation):
    """Update the current user's feed composition settings."""
    
    class Arguments:
        personal_connections = graphene.Float()
        interest_based = graphene.Float()
        trending_content = graphene.Float()
        discovery_content = graphene.Float()
        community_content = graphene.Float()
        product_content = graphene.Float()
    
    composition = graphene.Field(FeedCompositionType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @login_required
    def mutate(self, info, **kwargs):
        try:
            composition = FeedComposition.objects.get(user=info.context.user)
            
            # Update fields if provided
            for field in [
                'personal_connections', 'interest_based', 'trending_content',
                'discovery_content', 'community_content', 'product_content'
            ]:
                if field in kwargs:
                    setattr(composition, field, kwargs[field])
            
            # This will trigger clean() validation
            composition.save()
            
            return UpdateFeedComposition(
                composition=composition,
                success=True,
                message="Feed composition updated successfully"
            )
            
        except ValidationError as e:
            return UpdateFeedComposition(
                composition=None,
                success=False,
                message=str(e)
            )
        except Exception as e:
            return UpdateFeedComposition(
                composition=None,
                success=False,
                message=f"An error occurred: {str(e)}"
            )

class FeedMutations(graphene.ObjectType):
    """GraphQL mutations for feed algorithm functionality."""
    update_feed_profile = UpdateFeedProfile.Field()
    update_feed_composition = UpdateFeedComposition.Field()
