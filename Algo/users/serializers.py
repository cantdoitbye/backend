from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, Connection, Interest, UserInterest, InterestCollection

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with feed preferences."""
    
    connection_count = serializers.ReadOnlyField(source='total_connections')
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'location', 'website', 'avatar_url',
            'feed_composition', 'feed_preferences',
            'is_private', 'allow_recommendations',
            'connection_count', 'engagement_score',
            'ab_test_group', 'created_at', 'last_active'
        ]
        read_only_fields = [
            'id', 'engagement_score', 'ab_test_group', 
            'created_at', 'last_active'
        ]
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None
    
    def validate_feed_composition(self, value):
        """Ensure feed composition ratios sum to 1.0."""
        if value:
            total = sum(value.values())
            if not (0.95 <= total <= 1.05):  # Allow small floating point errors
                raise serializers.ValidationError(
                    "Feed composition ratios must sum to approximately 1.0"
                )
        return value


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'website', 'avatar',
            'feed_composition', 'feed_preferences',
            'is_private', 'allow_recommendations'
        ]
    
    def validate_feed_composition(self, value):
        """Ensure feed composition ratios sum to 1.0."""
        if value:
            total = sum(value.values())
            if not (0.95 <= total <= 1.05):
                raise serializers.ValidationError(
                    "Feed composition ratios must sum to approximately 1.0"
                )
        return value


class ConnectionSerializer(serializers.ModelSerializer):
    """Serializer for user connections."""
    
    from_user_info = UserProfileSerializer(source='from_user', read_only=True)
    to_user_info = UserProfileSerializer(source='to_user', read_only=True)
    circle_weight = serializers.ReadOnlyField(source='get_circle_weight')
    
    class Meta:
        model = Connection
        fields = [
            'id', 'from_user', 'to_user',
            'from_user_info', 'to_user_info',
            'circle_type', 'status',
            'circle_weight', 'interaction_count',
            'last_interaction', 'created_at'
        ]
        read_only_fields = [
            'id', 'interaction_count', 'last_interaction', 'created_at'
        ]


class ConnectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating connections."""
    
    class Meta:
        model = Connection
        fields = ['to_user', 'circle_type']
    
    def create(self, validated_data):
        validated_data['from_user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        request = self.context['request']
        if data['to_user'] == request.user:
            raise serializers.ValidationError(
                "Cannot create connection to yourself."
            )
        
        # Check if connection already exists
        if Connection.objects.filter(
            from_user=request.user,
            to_user=data['to_user']
        ).exists():
            raise serializers.ValidationError(
                "Connection already exists."
            )
        
        return data


class InterestSerializer(serializers.ModelSerializer):
    """Serializer for interests."""
    
    class Meta:
        model = Interest
        fields = [
            'id', 'name', 'category', 'description',
            'follower_count', 'trending_score',
            'is_active', 'created_at'
        ]
        read_only_fields = [
            'id', 'follower_count', 'trending_score', 'created_at'
        ]


class UserInterestSerializer(serializers.ModelSerializer):
    """Serializer for user interests."""
    
    interest_info = InterestSerializer(source='interest', read_only=True)
    
    class Meta:
        model = UserInterest
        fields = [
            'id', 'interest', 'interest_info',
            'interest_type', 'strength',
            'engagement_count', 'last_engaged',
            'created_at'
        ]
        read_only_fields = [
            'id', 'engagement_count', 'last_engaged', 'created_at'
        ]


class UserInterestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user interests."""
    
    class Meta:
        model = UserInterest
        fields = ['interest', 'interest_type', 'strength']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        request = self.context['request']
        
        # Check if user interest already exists
        if UserInterest.objects.filter(
            user=request.user,
            interest=data['interest']
        ).exists():
            raise serializers.ValidationError(
                "User interest already exists."
            )
        
        return data


class InterestCollectionSerializer(serializers.ModelSerializer):
    """Serializer for interest collections."""
    
    interests = InterestSerializer(many=True, read_only=True)
    interest_count = serializers.ReadOnlyField(source='interests.count')
    creator_info = UserProfileSerializer(source='creator', read_only=True)
    
    class Meta:
        model = InterestCollection
        fields = [
            'id', 'name', 'description', 'interests',
            'interest_count', 'is_system',
            'creator', 'creator_info', 'created_at'
        ]
        read_only_fields = [
            'id', 'interest_count', 'creator_info', 'created_at'
        ]