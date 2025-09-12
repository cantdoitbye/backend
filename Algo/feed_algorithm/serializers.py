"""
Django REST Framework serializers for the feed algorithm API.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Connection, FeedComposition, Interest, InterestCollection,
    TrendingMetric, CreatorMetric, FeedDebugEvent
)
from feed_content_types.models import Post, Community, Product, Engagement


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'username', 'feed_enabled', 'content_language', 
            'total_engagement_score', 'privacy_level', 'last_active'
        ]
        read_only_fields = ['total_engagement_score', 'last_active']


class FeedCompositionSerializer(serializers.ModelSerializer):
    """Serializer for feed composition settings."""
    
    class Meta:
        model = FeedComposition
        fields = [
            'personal_connections', 'interest_based', 'trending_content',
            'discovery_content', 'community_content', 'product_content',
            'experiment_group'
        ]
    
    def validate(self, data):
        """Validate that all percentages sum to 1.0."""
        total = (
            data.get('personal_connections', 0) +
            data.get('interest_based', 0) +
            data.get('trending_content', 0) +
            data.get('discovery_content', 0) +
            data.get('community_content', 0) +
            data.get('product_content', 0)
        )
        
        if abs(total - 1.0) > 0.01:
            raise serializers.ValidationError(
                f'Feed composition percentages must sum to 1.0, got {total}'
            )
        
        return data


class InterestSerializer(serializers.ModelSerializer):
    """Serializer for interests."""
    
    class Meta:
        model = Interest
        fields = [
            'id', 'name', 'description', 'category', 
            'is_trending', 'popularity_score'
        ]
        read_only_fields = ['is_trending', 'popularity_score']


class InterestCollectionSerializer(serializers.ModelSerializer):
    """Serializer for user interest collections."""
    interest = InterestSerializer(read_only=True)
    interest_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = InterestCollection
        fields = [
            'id', 'interest', 'interest_id', 'strength', 
            'source', 'created_at'
        ]
        read_only_fields = ['created_at']


class ConnectionSerializer(serializers.ModelSerializer):
    """Serializer for user connections."""
    from_user = serializers.CharField(source='from_user.username', read_only=True)
    to_user = serializers.CharField(source='to_user.username', read_only=True)
    to_user_id = serializers.IntegerField(write_only=True)
    circle_weight = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Connection
        fields = [
            'id', 'from_user', 'to_user', 'to_user_id', 'circle_type',
            'circle_weight', 'interaction_count', 'last_interaction', 'created_at'
        ]
        read_only_fields = ['interaction_count', 'last_interaction', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts in feed."""
    creator = serializers.CharField(source='creator.username', read_only=True)
    engagement = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'creator', 'post_type', 'visibility',
            'location', 'image_urls', 'video_url', 'tags', 'engagement',
            'engagement_score', 'quality_score', 'trending_score',
            'created_at', 'published_at'
        ]
        read_only_fields = [
            'engagement_score', 'quality_score', 'trending_score',
            'created_at', 'published_at'
        ]
    
    def get_engagement(self, obj):
        return {
            'views': obj.view_count,
            'likes': obj.like_count,
            'comments': obj.comment_count,
            'shares': obj.share_count
        }


class CommunitySerializer(serializers.ModelSerializer):
    """Serializer for communities."""
    creator = serializers.CharField(source='creator.username', read_only=True)
    
    class Meta:
        model = Community
        fields = [
            'id', 'title', 'description', 'creator', 'category',
            'is_private', 'requires_approval', 'member_count',
            'avatar_url', 'banner_url', 'theme_color',
            'created_at'
        ]
        read_only_fields = ['member_count', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products."""
    creator = serializers.CharField(source='creator.username', read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'creator', 'price', 'currency',
            'formatted_price', 'brand', 'model', 'category',
            'stock_quantity', 'is_in_stock', 'primary_image_url',
            'gallery_urls', 'attributes', 'created_at'
        ]
        read_only_fields = ['formatted_price', 'created_at']


class FeedItemSerializer(serializers.Serializer):
    """Serializer for individual feed items."""
    id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    content = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    creator = serializers.CharField()
    created_at = serializers.CharField()
    engagement = serializers.DictField()
    score = serializers.FloatField()
    category = serializers.CharField()
    
    # Optional fields depending on content type
    price = serializers.CharField(required=False)
    circle_type = serializers.CharField(required=False)
    matched_interests = serializers.ListField(required=False)
    trending_metrics = serializers.DictField(required=False)
    reason = serializers.CharField(required=False)


class FeedResponseSerializer(serializers.Serializer):
    """Serializer for feed API response."""
    user_id = serializers.IntegerField()
    items = FeedItemSerializer(many=True)
    composition = serializers.DictField()
    generated_at = serializers.CharField()
    total_items = serializers.IntegerField()
    cache_status = serializers.CharField()


class TrendingMetricSerializer(serializers.ModelSerializer):
    """Serializer for trending metrics."""
    
    class Meta:
        model = TrendingMetric
        fields = [
            'content_type', 'content_id', 'velocity_score',
            'viral_coefficient', 'engagement_rate', 'trending_window',
            'calculated_at', 'expires_at'
        ]
        read_only_fields = ['calculated_at', 'expires_at']


class CreatorMetricSerializer(serializers.ModelSerializer):
    """Serializer for creator metrics."""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = CreatorMetric
        fields = [
            'username', 'overall_reputation', 'content_quality_score',
            'engagement_rate', 'follower_growth_rate', 'total_posts',
            'total_engagements', 'total_shares', 'last_calculated'
        ]
        read_only_fields = [
            'overall_reputation', 'content_quality_score', 'engagement_rate',
            'follower_growth_rate', 'total_posts', 'total_engagements',
            'total_shares', 'last_calculated'
        ]
