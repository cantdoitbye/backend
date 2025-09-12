from rest_framework import serializers
from .models import UserActivity, UserEngagementScore
from django.contrib.contenttypes.models import ContentType

class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activities."""
    activity_type_display = serializers.CharField(
        source='get_activity_type_display', 
        read_only=True
    )
    content_object = serializers.SerializerMethodField()
    
    class Meta:
        model = UserActivity
        fields = [
            'id',
            'user',
            'activity_type',
            'activity_type_display',
            'content_type',
            'object_id',
            'content_object',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['user', 'created_at']
    
    def get_content_object(self, obj):
        # Implement content object serialization based on content type
        if not obj.content_object:
            return None
            
        # Add specific serialization for different content types
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if isinstance(obj.content_object, User):
            return {
                'id': obj.content_object.id,
                'username': obj.content_object.username,
                'type': 'user'
            }
        
        # Default serialization for other content types
        return str(obj.content_object)


class UserEngagementScoreSerializer(serializers.ModelSerializer):
    """Serializer for user engagement scores."""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserEngagementScore
        fields = [
            'id',
            'user',
            'username',
            'total_activities',
            'last_activity_at',
            'engagement_score',
            'content_score',
            'social_score',
            'updated_at',
        ]
        read_only_fields = fields


class ActivityCreateSerializer(serializers.Serializer):
    """Serializer for creating new activities."""
    activity_type = serializers.ChoiceField(
        choices=[(t.value, t.label) for t in UserActivity.ActivityType]
    )
    content_type = serializers.CharField(required=False)
    object_id = serializers.IntegerField(required=False)
    metadata = serializers.JSONField(required=False, default=dict)
    
    def validate(self, data):
        """Validate activity data."""
        content_type = data.get('content_type')
        object_id = data.get('object_id')
        
        if content_type and object_id:
            try:
                model_class = ContentType.objects.get(model=content_type).model_class()
                if not model_class.objects.filter(pk=object_id).exists():
                    raise serializers.ValidationError("Invalid object_id for the given content_type")
            except ContentType.DoesNotExist:
                raise serializers.ValidationError("Invalid content_type")
        
        return data
    
    def create(self, validated_data):
        """Create a new activity."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
        
        content_type = None
        object_id = validated_data.get('object_id')
        
        if 'content_type' in validated_data and object_id is not None:
            content_type = ContentType.objects.get(
                model=validated_data['content_type']
            )
        
        activity = UserActivity.objects.create(
            user=request.user,
            activity_type=validated_data['activity_type'],
            content_type=content_type,
            object_id=object_id,
            metadata=validated_data.get('metadata', {})
        )
        
        # Update engagement scores
        self._update_engagement_scores(request.user)
        
        return activity
    
    def _update_engagement_scores(self, user):
        """Update user engagement scores after new activity."""
        score, created = UserEngagementScore.objects.get_or_create(user=user)
        score.update_scores()
