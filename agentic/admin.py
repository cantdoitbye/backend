# Agentic Admin Configuration
# This module configures Django admin interface for agentic models.

from django.contrib import admin
from .models import AgentActionLog, AgentMemory


@admin.register(AgentActionLog)
class AgentActionLogAdmin(admin.ModelAdmin):
    """Admin configuration for AgentActionLog model."""
    
    list_display = ['agent_uid', 'community_uid', 'action_type', 'success', 'timestamp']
    list_filter = ['success', 'action_type', 'timestamp']
    search_fields = ['agent_uid', 'community_uid', 'action_type']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('agent_uid', 'community_uid', 'action_type', 'success')
        }),
        ('Action Details', {
            'fields': ('action_details', 'error_message', 'execution_time_ms')
        }),
        ('Metadata', {
            'fields': ('timestamp', 'user_context'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AgentMemory)
class AgentMemoryAdmin(admin.ModelAdmin):
    """Admin configuration for AgentMemory model."""
    
    list_display = ['agent_uid', 'community_uid', 'memory_type', 'updated_date', 'expires_at']
    list_filter = ['memory_type', 'updated_date', 'expires_at']
    search_fields = ['agent_uid', 'community_uid']
    readonly_fields = ['created_date', 'updated_date']
    ordering = ['-updated_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('agent_uid', 'community_uid', 'memory_type')
        }),
        ('Memory Content', {
            'fields': ('content',)
        }),
        ('Management', {
            'fields': ('expires_at', 'priority'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )