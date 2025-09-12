import graphene
from graphene_django import DjangoObjectType
from .models import UserProfile, FeedComposition

class UserProfileType(DjangoObjectType):
    """GraphQL type for UserProfile model."""
    class Meta:
        model = UserProfile
        fields = '__all__'
        interfaces = (graphene.relay.Node,)

class FeedCompositionType(DjangoObjectType):
    """GraphQL type for FeedComposition model."""
    composition = graphene.JSONString()
    
    class Meta:
        model = FeedComposition
        fields = '__all__'
        interfaces = (graphene.relay.Node,)
    
    def resolve_composition(self, info):
        return self.composition_dict()

class FeedItemType(graphene.ObjectType):
    """GraphQL type for feed items returned by the algorithm."""
    id = graphene.ID(required=True)
    content_type = graphene.String(required=True)
    content_id = graphene.ID(required=True)
    score = graphene.Float(required=True)
    ranking = graphene.Int(required=True)
    metadata = graphene.JSONString()
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)

class FeedResponseType(graphene.ObjectType):
    """GraphQL response type for feed generation."""
    success = graphene.Boolean(required=True)
    message = graphene.String()
    items = graphene.List(FeedItemType)
    total_count = graphene.Int()
    has_more = graphene.Boolean()
    composition = graphene.JSONString()
    generated_at = graphene.DateTime(required=True)
