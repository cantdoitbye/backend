from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import (
    Post, Community, Product, Engagement,
    CommunityMembership, ContentTag, ContentTagging
)
from users.serializers import UserProfileSerializer


class BaseContentSerializer(serializers.ModelSerializer):
    """Base serializer for all content types."""
    
    creator_info = UserProfileSerializer(source='creator', read_only=True)
    content_type_name = serializers.ReadOnlyField(source='get_content_type_name')
    engagement_stats = serializers.SerializerMethodField()
    
    class Meta:
        fields = [
            'id', 'title', 'description', 'creator', 'creator_info',
            'content_data', 'visibility', 'engagement_score',
            'trending_score', 'quality_score', 'content_type_name',
            'engagement_stats', 'created_at', 'updated_at',
            'published_at', 'is_active', 'is_featured'
        ]
        read_only_fields = [
            'id', 'engagement_score', 'trending_score', 
            'created_at', 'updated_at'
        ]
    
    def get_engagement_stats(self, obj):
        """Get engagement statistics for the content."""
        from django.db.models import Count
        
        content_type = ContentType.objects.get_for_model(obj)
        engagements = Engagement.objects.filter(
            content_type=content_type,
            object_id=obj.id
        ).values('engagement_type').annotate(
            count=Count('id')
        )
        
        stats = {eng['engagement_type']: eng['count'] for eng in engagements}
        return stats


class PostSerializer(BaseContentSerializer):
    """Serializer for Post content type."""
    
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    
    class Meta(BaseContentSerializer.Meta):
        model = Post
        fields = BaseContentSerializer.Meta.fields + [
            'content', 'image', 'video', 'image_url', 'video_url',
            'hashtags', 'mentions', 'post_type'
        ]
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_video_url(self, obj):
        if obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
        return None
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class PostCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating posts."""
    
    class Meta:
        model = Post
        fields = [
            'title', 'content', 'image', 'video',
            'hashtags', 'mentions', 'post_type',
            'visibility'
        ]
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class CommunitySerializer(BaseContentSerializer):
    """Serializer for Community content type."""
    
    membership_info = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    
    class Meta(BaseContentSerializer.Meta):
        model = Community
        fields = BaseContentSerializer.Meta.fields + [
            'community_type', 'member_count', 'max_members',
            'rules', 'category', 'tags', 'allow_posts',
            'require_approval', 'membership_info', 'can_join'
        ]
    
    def get_membership_info(self, obj):
        """Get current user's membership info."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            membership = CommunityMembership.objects.get(
                community=obj,
                user=request.user
            )
            return {
                'status': membership.status,
                'role': membership.role,
                'joined_at': membership.joined_at
            }
        except CommunityMembership.DoesNotExist:
            return None
    
    def get_can_join(self, obj):
        """Check if current user can join this community."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.can_user_join(request.user)


class CommunityCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating communities."""
    
    class Meta:
        model = Community
        fields = [
            'title', 'description', 'community_type',
            'max_members', 'rules', 'category', 'tags',
            'allow_posts', 'require_approval', 'visibility'
        ]
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        community = super().create(validated_data)
        
        # Automatically create creator membership
        CommunityMembership.objects.create(
            community=community,
            user=community.creator,
            status='approved',
            role='creator'
        )
        
        return community


class ProductSerializer(BaseContentSerializer):
    """Serializer for Product content type."""
    
    formatted_price = serializers.SerializerMethodField()
    is_purchasable = serializers.ReadOnlyField()
    
    class Meta(BaseContentSerializer.Meta):
        model = Product
        fields = BaseContentSerializer.Meta.fields + [
            'price', 'currency', 'formatted_price', 'category',
            'brand', 'model', 'availability', 'specifications',
            'images', 'is_purchasable'
        ]
    
    def get_formatted_price(self, obj):
        if obj.price:
            return f"{obj.currency} {obj.price}"
        return None


class ProductCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating products."""
    
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price', 'currency',
            'category', 'brand', 'model', 'availability',
            'specifications', 'images', 'visibility'
        ]
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class EngagementSerializer(serializers.ModelSerializer):
    """Serializer for content engagement."""
    
    user_info = UserProfileSerializer(source='user', read_only=True)
    content_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Engagement
        fields = [
            'id', 'user', 'user_info', 'engagement_type',
            'score', 'metadata', 'content_info', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_content_info(self, obj):
        """Get basic info about the engaged content."""
        content = obj.content_object
        if content:
            return {
                'id': str(content.id),
                'title': content.title,
                'type': content.get_content_type_name()
            }
        return None


class EngagementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating engagements."""
    
    # Allow specifying content by type and ID
    content_type = serializers.CharField()
    content_id = serializers.UUIDField()
    
    class Meta:
        model = Engagement
        fields = [
            'content_type', 'content_id', 'engagement_type',
            'score', 'metadata'
        ]
    
    def create(self, validated_data):
        from .registry import registry
        
        content_type_name = validated_data.pop('content_type')
        content_id = validated_data.pop('content_id')
        
        # Get the content object
        model_class = registry.get_content_type(content_type_name)
        if not model_class:
            raise serializers.ValidationError(
                f"Unknown content type: {content_type_name}"
            )
        
        try:
            content_object = model_class.objects.get(id=content_id)
        except model_class.DoesNotExist:
            raise serializers.ValidationError("Content not found")
        
        # Set the generic foreign key fields
        django_content_type = ContentType.objects.get_for_model(model_class)
        validated_data['content_type'] = django_content_type
        validated_data['object_id'] = content_id
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)


class CommunityMembershipSerializer(serializers.ModelSerializer):
    """Serializer for community membership."""
    
    user_info = UserProfileSerializer(source='user', read_only=True)
    community_info = serializers.SerializerMethodField()
    
    class Meta:
        model = CommunityMembership
        fields = [
            'id', 'community', 'user', 'user_info',
            'community_info', 'status', 'role',
            'joined_at', 'updated_at'
        ]
        read_only_fields = ['id', 'joined_at', 'updated_at']
    
    def get_community_info(self, obj):
        return {
            'id': str(obj.community.id),
            'title': obj.community.title,
            'type': obj.community.community_type
        }


class ContentTagSerializer(serializers.ModelSerializer):
    """Serializer for content tags."""
    
    class Meta:
        model = ContentTag
        fields = [
            'id', 'name', 'category', 'usage_count',
            'trending_score', 'is_active', 'created_at'
        ]
        read_only_fields = [
            'id', 'usage_count', 'trending_score', 'created_at'
        ]


class ContentRegistrySerializer(serializers.Serializer):
    """Serializer for content type registry information."""
    
    content_types = serializers.DictField(read_only=True)
    stats = serializers.DictField(read_only=True)
    
    def to_representation(self, instance):
        """Custom representation for registry data."""
        from .registry import registry
        
        return {
            'content_types': {
                name: {
                    'model_name': model._meta.model_name,
                    'verbose_name': model._meta.verbose_name,
                    'app_label': model._meta.app_label,
                    'has_custom_scorer': registry.get_scoring_engine(name) is not None,
                    'has_custom_serializer': registry.get_serializer(name) is not None
                }
                for name, model in registry.get_all_content_types().items()
            },
            'stats': registry.get_content_type_stats()
        }