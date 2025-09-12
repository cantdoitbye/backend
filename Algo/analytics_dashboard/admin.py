from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    ABTestExperiment, ExperimentParticipant, ExperimentMetric,
    RealTimeMetric, AnalyticsDashboard, UserBehaviorInsight
)
from .services import AnalyticsService


@admin.register(ABTestExperiment)
class ABTestExperimentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'status', 'traffic_allocation', 'participants_count',
        'days_running', 'is_statistically_significant', 'winner',
        'created_by', 'created_at'
    ]
    list_filter = ['status', 'primary_metric', 'is_statistically_significant', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'is_statistically_significant',
        'winner', 'results_summary', 'participants_count', 'days_running'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'status', 'created_by')
        }),
        ('Experiment Configuration', {
            'fields': (
                'traffic_allocation', 'duration_days', 'primary_metric',
                'confidence_level', 'minimum_sample_size'
            )
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Configuration', {
            'fields': ('control_config', 'treatment_config'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': (
                'is_statistically_significant', 'winner', 'results_summary',
                'participants_count', 'days_running'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['start_experiments', 'stop_experiments', 'calculate_results']
    
    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Participants'
    
    def days_running(self, obj):
        if obj.start_date:
            days = (timezone.now() - obj.start_date).days
            if obj.status == 'running':
                return format_html('<span style="color: green;">{} days</span>', days)
            return f"{days} days"
        return "Not started"
    days_running.short_description = 'Days Running'
    
    def start_experiments(self, request, queryset):
        count = 0
        for experiment in queryset.filter(status='draft'):
            experiment.status = 'running'
            experiment.start_date = timezone.now()
            experiment.end_date = experiment.start_date + timezone.timedelta(days=experiment.duration_days)
            experiment.save()
            count += 1
        
        self.message_user(request, f"Started {count} experiments.")
    start_experiments.short_description = "Start selected experiments"
    
    def stop_experiments(self, request, queryset):
        count = 0
        for experiment in queryset.filter(status='running'):
            experiment.status = 'completed'
            experiment.end_date = timezone.now()
            experiment.save()
            count += 1
        
        self.message_user(request, f"Stopped {count} experiments.")
    stop_experiments.short_description = "Stop selected experiments"
    
    def calculate_results(self, request, queryset):
        from .tasks import calculate_experiment_results
        
        count = 0
        for experiment in queryset:
            calculate_experiment_results.delay(str(experiment.id))
            count += 1
        
        self.message_user(request, f"Scheduled result calculation for {count} experiments.")
    calculate_results.short_description = "Calculate results for selected experiments"


@admin.register(ExperimentParticipant)
class ExperimentParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'experiment', 'group', 'assigned_at',
        'first_exposure', 'last_activity', 'is_active'
    ]
    list_filter = ['group', 'is_active', 'assigned_at', 'experiment__status']
    search_fields = ['user__username', 'user__email', 'experiment__name']
    readonly_fields = ['assigned_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'experiment')


@admin.register(ExperimentMetric)
class ExperimentMetricAdmin(admin.ModelAdmin):
    list_display = [
        'experiment', 'participant_user', 'participant_group',
        'metric_name', 'metric_value', 'metric_type', 'recorded_at'
    ]
    list_filter = [
        'metric_name', 'metric_type', 'recorded_at',
        'participant__group', 'experiment__status'
    ]
    search_fields = [
        'experiment__name', 'participant__user__username',
        'metric_name', 'session_id'
    ]
    readonly_fields = ['recorded_at']
    
    def participant_user(self, obj):
        return obj.participant.user.username
    participant_user.short_description = 'User'
    
    def participant_group(self, obj):
        group = obj.participant.group
        color = 'blue' if group == 'control' else 'green'
        return format_html('<span style="color: {};">{}</span>', color, group.title())
    participant_group.short_description = 'Group'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'experiment', 'participant__user'
        )


@admin.register(RealTimeMetric)
class RealTimeMetricAdmin(admin.ModelAdmin):
    list_display = [
        'metric_name', 'metric_category', 'value', 'unit',
        'aggregation_window', 'timestamp'
    ]
    list_filter = [
        'metric_category', 'metric_name', 'aggregation_window',
        'timestamp'
    ]
    search_fields = ['metric_name']
    readonly_fields = ['timestamp']
    
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        # Limit to recent metrics for performance
        return super().get_queryset(request).filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=7)
        )


@admin.register(AnalyticsDashboard)
class AnalyticsDashboardAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'created_by', 'is_public', 'created_at', 'updated_at'
    ]
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    
    filter_horizontal = ['allowed_users']


@admin.register(UserBehaviorInsight)
class UserBehaviorInsightAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'engagement_score', 'retention_score',
        'session_duration_avg', 'data_points_count', 'last_calculated'
    ]
    list_filter = ['last_calculated']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['last_calculated']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'last_calculated', 'data_points_count')
        }),
        ('Behavior Patterns', {
            'fields': (
                'session_duration_avg', 'daily_active_hours',
                'preferred_content_types', 'engagement_patterns'
            )
        }),
        ('AI Insights', {
            'fields': ('optimal_feed_composition',)
        }),
        ('Scores', {
            'fields': ('engagement_score', 'retention_score')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['recalculate_insights']
    
    def recalculate_insights(self, request, queryset):
        from .tasks import process_user_behavior_insights
        
        # Trigger background task to recalculate insights
        process_user_behavior_insights.delay()
        
        self.message_user(
            request,
            "Scheduled insight recalculation for selected users."
        )
    recalculate_insights.short_description = "Recalculate insights for selected users"


# Admin site customization
admin.site.site_header = "Ooumph Feed Algorithm Administration"
admin.site.site_title = "Ooumph Admin"
admin.site.index_title = "Feed Algorithm Management"
