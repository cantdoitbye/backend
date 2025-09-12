from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import UserProfile, FeedComposition

User = get_user_model()

class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile model."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Feed Profile'
    fk_name = 'user'
    
    def has_add_permission(self, request, obj=None):
        return False

class FeedCompositionInline(admin.StackedInline):
    """Inline admin for FeedComposition model."""
    model = FeedComposition
    can_delete = False
    verbose_name_plural = 'Feed Composition'
    fk_name = 'user'
    
    def has_add_permission(self, request, obj=None):
        return False

class CustomUserAdmin(admin.ModelAdmin):
    """Extend User admin to include feed-related inlines."""
    inlines = (UserProfileInline, FeedCompositionInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_select_related = ('profile', 'feed_composition')
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# Unregister the default User admin if already registered
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Register User with our custom admin
admin.site.register(User, CustomUserAdmin)

@admin.register(FeedComposition)
class FeedCompositionAdmin(admin.ModelAdmin):
    """Admin for FeedComposition model."""
    list_display = ('user', 'personal_connections', 'interest_based', 'trending_content', 
                   'discovery_content', 'community_content', 'product_content')
    list_filter = ('experiment_group',)
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Content Distribution', {
            'fields': (
                'personal_connections', 'interest_based', 'trending_content',
                'discovery_content', 'community_content', 'product_content'
            ),
            'description': 'These values must sum to 1.0 (100%)'
        }),
        ('Experiment Settings', {
            'fields': ('experiment_group',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Prevent adding new compositions directly

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""
    list_display = ('user', 'feed_enabled', 'content_language', 'privacy_level', 'total_engagement_score')
    list_filter = ('feed_enabled', 'privacy_level', 'content_language')
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Feed Preferences', {
            'fields': ('feed_enabled', 'content_language', 'privacy_level')
        }),
        ('Engagement', {
            'fields': ('total_engagement_score', 'last_active'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Prevent adding new profiles directly
