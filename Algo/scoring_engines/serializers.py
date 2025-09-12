from rest_framework import serializers
from .models import (
    ScoringFactor, UserScoringPreference, ContentScore,
    TrendingMetric, CreatorMetric, FeedDebugEvent
)
from users.serializers import UserProfileSerializer


class ScoringFactorSerializer(serializers.ModelSerializer):
    """Serializer for scoring factors."""
    
    class Meta:
        model = ScoringFactor
        fields = [
            'id', 'name', 'factor_type', 'description',
            'weight', 'config', 'is_active', 'is_global',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_weight(self, value):
        """Validate weight is within acceptable range."""
        if not (0.0 <= value <= 10.0):
            raise serializers.ValidationError(
                "Weight must be between 0.0 and 10.0"
            )
        return value
    
    def validate_config(self, value):
        """Validate configuration JSON."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Config must be a valid JSON object"
            )
        return value


class UserScoringPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user scoring preferences."""
    
    user_info = UserProfileSerializer(source='user', read_only=True)
    
    class Meta:
        model = UserScoringPreference
        fields = [
            'id', 'user', 'user_info', 'custom_weights',
            'engagement_decay_rate', 'freshness_preference',
            'diversity_preference', 'algorithm_variant',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_custom_weights(self, value):
        """Validate custom weights configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Custom weights must be a valid JSON object"
            )
        
        # Validate weight values
        for engine_name, weight in value.items():
            if not isinstance(weight, (int, float)):
                raise serializers.ValidationError(
                    f"Weight for {engine_name} must be a number"
                )
            if not (0.0 <= weight <= 10.0):
                raise serializers.ValidationError(
                    f"Weight for {engine_name} must be between 0.0 and 10.0"
                )
        
        return value


class UserScoringPreferenceUpdateSerializer(serializers.ModelSerializer):
    """Simplified serializer for updating user scoring preferences."""
    
    class Meta:
        model = UserScoringPreference
        fields = [
            'custom_weights', 'engagement_decay_rate',
            'freshness_preference', 'diversity_preference'
        ]
    
    def update(self, instance, validated_data):
        """Update user scoring preferences."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ContentScoreSerializer(serializers.ModelSerializer):
    """Serializer for content scores."""
    
    user_info = UserProfileSerializer(source='user', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = ContentScore
        fields = [
            'id', 'content_type', 'content_id', 'user',
            'user_info', 'final_score', 'factor_scores',
            'algorithm_version', 'is_expired',
            'computed_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'computed_at', 'expires_at', 'is_expired'
        ]


class TrendingMetricSerializer(serializers.ModelSerializer):
    """Serializer for trending metrics."""
    
    class Meta:
        model = TrendingMetric
        fields = [
            'id', 'metric_type', 'metric_id', 'velocity_score',
            'viral_coefficient', 'engagement_volume',
            'window_1h', 'window_24h', 'window_7d',
            'trending_score', 'last_updated', 'created_at'
        ]
        read_only_fields = [
            'id', 'last_updated', 'created_at'
        ]


class CreatorMetricSerializer(serializers.ModelSerializer):
    """Serializer for creator metrics."""
    
    creator_info = UserProfileSerializer(source='creator', read_only=True)
    
    class Meta:
        model = CreatorMetric
        fields = [
            'id', 'creator', 'creator_info', 'reputation_score',
            'authority_score', 'consistency_score',
            'total_engagements', 'avg_engagement_rate',
            'total_content_created', 'content_quality_avg',
            'follower_growth_rate', 'connection_influence',
            'recent_activity_score', 'last_calculated', 'created_at'
        ]
        read_only_fields = [
            'id', 'last_calculated', 'created_at'
        ]


class FeedDebugEventSerializer(serializers.ModelSerializer):
    """Serializer for feed debug events."""
    
    user_info = UserProfileSerializer(source='user', read_only=True)
    
    class Meta:
        model = FeedDebugEvent
        fields = [
            'id', 'user', 'user_info', 'event_type',
            'event_data', 'execution_time_ms',
            'algorithm_version', 'composition_config',
            'created_at'
        ]
        read_only_fields = [
            'id', 'created_at'
        ]


class ScoringEngineInfoSerializer(serializers.Serializer):
    """Serializer for scoring engine registry information."""
    
    engines = serializers.DictField(read_only=True)
    active_factors = serializers.ListField(read_only=True)
    default_config = serializers.DictField(read_only=True)
    
    def to_representation(self, instance):
        """Custom representation for scoring engine data."""
        from .registry import registry
        from .models import ScoringFactor
        
        # Get registered engines
        engines = {}
        for name, engine_class in registry.get_all_engines().items():
            engine_instance = registry.get_engine(name)
            engines[name] = {
                'name': engine_instance.get_name() if engine_instance else name,
                'class_name': engine_class.__name__,
                'required_data': engine_instance.get_required_data() if engine_instance else [],
                'weight': engine_instance.get_weight() if engine_instance else 1.0
            }
        
        # Get active scoring factors from database
        active_factors = list(
            ScoringFactor.objects.filter(is_active=True)
            .values('name', 'factor_type', 'weight', 'config')
        )
        
        # Get default configuration
        from django.conf import settings
        default_config = getattr(settings, 'FEED_CONFIG', {})
        
        return {
            'engines': engines,
            'active_factors': active_factors,
            'default_config': default_config
        }


class ContentScoreRequestSerializer(serializers.Serializer):
    """Serializer for content score calculation requests."""
    
    content_type = serializers.CharField()
    content_id = serializers.UUIDField()
    force_recalculate = serializers.BooleanField(default=False)
    engine_configs = serializers.DictField(required=False)
    
    def validate_content_type(self, value):
        """Validate content type is registered."""
        from content_types.registry import registry as content_registry
        
        if not content_registry.is_registered(value):
            raise serializers.ValidationError(
                f"Content type '{value}' is not registered"
            )
        return value


class BulkScoringRequestSerializer(serializers.Serializer):
    """Serializer for bulk scoring requests."""
    
    content_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of content items to score"
    )
    force_recalculate = serializers.BooleanField(default=False)
    engine_configs = serializers.DictField(required=False)
    
    def validate_content_items(self, value):
        """Validate content items format."""
        for item in value:
            if 'content_type' not in item or 'content_id' not in item:
                raise serializers.ValidationError(
                    "Each content item must have 'content_type' and 'content_id'"
                )
        return value