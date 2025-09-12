from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import UserProfile, Connection, Interest, UserInterest, InterestCollection


@admin.register(UserProfile)
class UserProfileAdmin(BaseUserAdmin):
    """Enhanced user admin with feed preferences and analytics."""
    
    list_display = [
        'username', 
        'email', 
        'engagement_score', 
        'total_connections', 
        'last_active',
        'ab_test_group',
        'is_private'
    ]
    
    list_filter = [
        'is_private',
        'allow_recommendations',
        'ab_test_group',
        'last_active',
        'date_joined'
    ]
    
    search_fields = ['username', 'email', 'bio']
    
    readonly_fields = [
        'engagement_score',
        'total_connections',
        'last_active',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': (
                'bio',
                'location',
                'website',
                'avatar'
            )
        }),
        ('Feed Preferences', {
            'fields': (
                'feed_composition',
                'feed_preferences',
                'allow_recommendations'
            )
        }),
        ('Privacy & Settings', {
            'fields': (
                'is_private',
                'ab_test_group'
            )
        }),
        ('Analytics', {
            'fields': (
                'engagement_score',
                'total_connections',
                'last_active',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    """Connection management with circle insights."""
    
    list_display = [
        'from_user',
        'to_user',
        'circle_type',
        'status',
        'interaction_count',
        'last_interaction',
        'created_at'
    ]
    
    list_filter = [
        'circle_type',
        'status',
        'created_at',
        'last_interaction'
    ]
    
    search_fields = [
        'from_user__username',
        'to_user__username'
    ]
    
    readonly_fields = [
        'interaction_count',
        'last_interaction',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Connection Details', {
            'fields': (
                'from_user',
                'to_user',
                'circle_type',
                'status'
            )
        }),
        ('Interaction Analytics', {
            'fields': (
                'interaction_count',
                'last_interaction',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'from_user', 'to_user'
        )


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    """Interest management with trending metrics."""
    
    list_display = [
        'name',
        'category',
        'follower_count',
        'trending_score_display',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'category',
        'is_active',
        'created_at'
    ]
    
    search_fields = ['name', 'category', 'description']
    
    readonly_fields = [
        'follower_count',
        'trending_score',
        'created_at'
    ]
    
    def trending_score_display(self, obj):
        if obj.trending_score > 0.8:
            color = 'red'  # Hot
        elif obj.trending_score > 0.5:
            color = 'orange'  # Trending
        else:
            color = 'gray'  # Normal
        
        return format_html(
            '<span style="color: {};">{:.2f}</span>',
            color,
            obj.trending_score
        )
    trending_score_display.short_description = 'Trending Score'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('collections')


class UserInterestInline(admin.TabularInline):
    """Inline for user interests in UserProfile admin."""
    model = UserInterest
    extra = 0
    readonly_fields = [
        'engagement_count',
        'last_engaged',
        'created_at',
        'updated_at'
    ]


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    """User-Interest relationship management."""
    
    list_display = [
        'user',
        'interest',
        'interest_type',
        'strength',
        'engagement_count',
        'last_engaged'
    ]
    
    list_filter = [
        'interest_type',
        'strength',
        'created_at',
        'last_engaged'
    ]
    
    search_fields = [
        'user__username',
        'interest__name'
    ]
    
    readonly_fields = [
        'engagement_count',
        'last_engaged',
        'created_at',
        'updated_at'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'interest'
        )


@admin.register(InterestCollection)
class InterestCollectionAdmin(admin.ModelAdmin):
    """Interest collection management."""
    
    list_display = [
        'name',
        'interest_count',
        'is_system',
        'creator',
        'created_at'
    ]
    
    list_filter = [
        'is_system',
        'created_at'
    ]
    
    search_fields = ['name', 'description']
    filter_horizontal = ['interests']
    
    def interest_count(self, obj):
        return obj.interests.count()
    interest_count.short_description = 'Interest Count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'interests'
        ).select_related('creator')