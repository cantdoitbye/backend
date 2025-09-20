from django.contrib import admin
from .models import (
    UserActivity,
    ContentInteraction,
    ProfileActivity,
    MediaInteraction,
    SocialInteraction,
    SessionActivity
)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'timestamp', 'ip_address')
    list_filter = ('activity_type', 'timestamp', 'user')
    search_fields = ('user__username', 'activity_type', 'ip_address')
    readonly_fields = ('timestamp', 'created_at', 'updated_at')
    ordering = ('-timestamp',)


@admin.register(ContentInteraction)
class ContentInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'content_id', 'interaction_type', 'timestamp')
    list_filter = ('content_type', 'interaction_type', 'timestamp')
    search_fields = ('user__username', 'content_id')
    readonly_fields = ('timestamp', 'created_at', 'updated_at')
    ordering = ('-timestamp',)


@admin.register(ProfileActivity)
class ProfileActivityAdmin(admin.ModelAdmin):
    list_display = ('visitor', 'profile_owner', 'activity_type', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('visitor__username', 'profile_owner__username')
    readonly_fields = ('timestamp', 'created_at', 'updated_at')
    ordering = ('-timestamp',)


@admin.register(MediaInteraction)
class MediaInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_type', 'media_id', 'interaction_type', 'timestamp')
    list_filter = ('media_type', 'interaction_type', 'timestamp')
    search_fields = ('user__username', 'media_id')
    readonly_fields = ('timestamp', 'created_at', 'updated_at')
    ordering = ('-timestamp',)


@admin.register(SocialInteraction)
class SocialInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_user', 'interaction_type', 'timestamp')
    list_filter = ('interaction_type', 'timestamp')
    search_fields = ('user__username', 'target_user__username')
    readonly_fields = ('timestamp', 'created_at', 'updated_at')
    ordering = ('-timestamp',)


@admin.register(SessionActivity)
class SessionActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'start_time', 'end_time', 'duration_seconds')
    list_filter = ('start_time', 'end_time')
    search_fields = ('user__username', 'session_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-start_time',)