from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    ABTestExperiment, ExperimentParticipant, ExperimentMetric,
    RealTimeMetric, AnalyticsDashboard, UserBehaviorInsight
)


class ABTestExperimentSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    participants_count = serializers.SerializerMethodField()
    days_running = serializers.ReadOnlyField()
    
    class Meta:
        model = ABTestExperiment
        fields = [
            'id', 'name', 'description', 'status', 'traffic_allocation',
            'control_config', 'treatment_config', 'start_date', 'end_date',
            'duration_days', 'primary_metric', 'confidence_level',
            'minimum_sample_size', 'is_statistically_significant',
            'winner', 'results_summary', 'created_by', 'created_by_username',
            'created_at', 'updated_at', 'participants_count', 'days_running'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_participants_count(self, obj):
        return obj.participants.count()


class ExperimentParticipantSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    experiment_name = serializers.CharField(source='experiment.name', read_only=True)
    
    class Meta:
        model = ExperimentParticipant
        fields = [
            'id', 'experiment', 'experiment_name', 'user', 'username',
            'group', 'assigned_at', 'first_exposure', 'last_activity',
            'is_active'
        ]
        read_only_fields = ['id', 'assigned_at']


class ExperimentMetricSerializer(serializers.ModelSerializer):
    participant_username = serializers.CharField(source='participant.user.username', read_only=True)
    participant_group = serializers.CharField(source='participant.group', read_only=True)
    
    class Meta:
        model = ExperimentMetric
        fields = [
            'id', 'experiment', 'participant', 'participant_username',
            'participant_group', 'metric_name', 'metric_value',
            'metric_type', 'session_id', 'metadata', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']


class RealTimeMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealTimeMetric
        fields = [
            'id', 'metric_name', 'metric_category', 'value', 'unit',
            'aggregation_window', 'timestamp', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']


class AnalyticsDashboardSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AnalyticsDashboard
        fields = [
            'id', 'name', 'description', 'layout_config', 'widgets',
            'created_by', 'created_by_username', 'is_public',
            'allowed_users', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserBehaviorInsightSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserBehaviorInsight
        fields = [
            'id', 'user', 'username', 'session_duration_avg',
            'daily_active_hours', 'preferred_content_types',
            'engagement_patterns', 'optimal_feed_composition',
            'engagement_score', 'retention_score', 'last_calculated',
            'data_points_count'
        ]
        read_only_fields = ['id', 'last_calculated']
