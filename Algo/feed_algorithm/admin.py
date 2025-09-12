"""
Django admin configuration for the feed algorithm models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    UserProfile, Connection, FeedComposition, Interest, InterestCollection,
    TrendingMetric, CreatorMetric, FeedDebugEvent
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'feed_enabled', 'content_language', 'privacy_level',
        'total_engagement_score', 'last_active', 'created_at'
    ]
    list_filter = [
        'feed_enabled', 'content_language', 'privacy_level', 'created_at'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['total_engagement_score', 'last_active', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Feed Settings', {
            'fields': ('feed_enabled', 'content_language', 'privacy_level')
        }),
        ('Metrics', {
            'fields': ('total_engagement_score', 'last_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = [
        'from_user', 'to_user', 'circle_type', 'circle_weight',
        'interaction_count', 'last_interaction', 'created_at'
    ]
    list_filter = ['circle_type', 'created_at', 'last_interaction']
    search_fields = [
        'from_user__username', 'to_user__username'
    ]
    readonly_fields = ['circle_weight', 'created_at', 'updated_at']
    
    def circle_weight(self, obj):
        return obj.circle_weight
    circle_weight.short_description = 'Circle Weight'


@admin.register(FeedComposition)
class FeedCompositionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'personal_connections', 'interest_based', 'trending_content',
        'discovery_content', 'experiment_group', 'created_at'
    ]
    list_filter = ['experiment_group', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Content Composition', {
            'fields': (
                'personal_connections', 'interest_based', 'trending_content',
                'discovery_content', 'community_content', 'product_content'
            )
        }),
        ('Experimentation', {
            'fields': ('experiment_group',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        # Validate composition totals
        total = (
            obj.personal_connections + obj.interest_based + obj.trending_content +
            obj.discovery_content + obj.community_content + obj.product_content
        )
        if abs(total - 1.0) > 0.01:
            from django.contrib import messages
            messages.error(
                request, 
                f'Feed composition must sum to 1.0, currently sums to {total}'
            )
            return
        super().save_model(request, obj, form, change)


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'is_trending', 'popularity_score', 'created_at'
    ]
    list_filter = ['category', 'is_trending', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['popularity_score', 'created_at', 'updated_at']
    
    actions = ['mark_as_trending', 'unmark_as_trending']
    
    def mark_as_trending(self, request, queryset):
        queryset.update(is_trending=True)
        self.message_user(request, f'{queryset.count()} interests marked as trending.')
    mark_as_trending.short_description = 'Mark selected interests as trending'
    
    def unmark_as_trending(self, request, queryset):
        queryset.update(is_trending=False)
        self.message_user(request, f'{queryset.count()} interests unmarked as trending.')
    unmark_as_trending.short_description = 'Unmark selected interests as trending'


@admin.register(InterestCollection)
class InterestCollectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'interest', 'strength', 'source', 'created_at']
    list_filter = ['source', 'created_at']
    search_fields = ['user__username', 'interest__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TrendingMetric)
class TrendingMetricAdmin(admin.ModelAdmin):
    list_display = [
        'content_display', 'velocity_score', 'viral_coefficient',
        'engagement_rate', 'trending_window', 'calculated_at'
    ]
    list_filter = ['content_type', 'trending_window', 'calculated_at']
    readonly_fields = ['cache_key', 'calculated_at', 'expires_at']
    
    def content_display(self, obj):
        return f'{obj.content_type}#{obj.content_id}'
    content_display.short_description = 'Content'
    content_display.admin_order_field = 'content_type'


@admin.register(CreatorMetric)
class CreatorMetricAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'overall_reputation', 'content_quality_score',
        'engagement_rate', 'total_posts', 'total_engagements', 'last_calculated'
    ]
    list_filter = ['last_calculated']
    search_fields = ['user__username']
    readonly_fields = [
        'overall_reputation', 'content_quality_score', 'engagement_rate',
        'follower_growth_rate', 'total_posts', 'total_engagements',
        'total_shares', 'last_calculated', 'created_at'
    ]
    
    actions = ['recalculate_metrics']
    
    def recalculate_metrics(self, request, queryset):
        for metric in queryset:
            metric.update_metrics()
        self.message_user(
            request, 
            f'Metrics recalculated for {queryset.count()} creators.'
        )
    recalculate_metrics.short_description = 'Recalculate selected creator metrics'


@admin.register(FeedDebugEvent)
class FeedDebugEventAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'event_type', 'generation_time_display', 'request_id', 'created_at'
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__username', 'request_id']
    readonly_fields = ['created_at']
    
    def generation_time_display(self, obj):
        if obj.generation_time_ms:
            return f'{obj.generation_time_ms}ms'
        return '-'
    generation_time_display.short_description = 'Generation Time'
    generation_time_display.admin_order_field = 'generation_time_ms'
    
    def has_change_permission(self, request, obj=None):
        return False  # Debug events should be read-only


# Customize admin site
admin.site.site_header = 'Ooumph Feed Algorithm Administration'
admin.site.site_title = 'Ooumph Feed Admin'
admin.site.index_title = 'Welcome to Ooumph Feed Algorithm Administration'
