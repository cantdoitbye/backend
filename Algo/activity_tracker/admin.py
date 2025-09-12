from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import UserActivity, UserEngagementScore

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activity_type', 'content_object', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'metadata')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')


@admin.register(UserEngagementScore)
class UserEngagementScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'engagement_score', 'content_score', 'social_score', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('user__username',)
    readonly_fields = ('updated_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Add to your app's admin
admin.site.site_header = 'Activity Tracker Admin'
admin.site.index_title = 'Activity Tracker Administration'
