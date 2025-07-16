from django.contrib import admin

from django_neomodel import admin as neo_admin
from django.contrib import admin as dj_admin
from story.models import Story,StoryComment,StoryRating,StoryReaction,StoryView


class StoryAdmin(dj_admin.ModelAdmin):
    list_display = ("title", "content", "created_at", "updated_at", "privacy", "is_deleted","created_by")
    search_fields = ("title", "content")

class StoryCommentAdmin(dj_admin.ModelAdmin):
    list_display = ( "content", "timestamp",  "is_deleted")
    search_fields = ( "content",'is_deleted')

class StoryReactionAdmin(dj_admin.ModelAdmin):
    list_display=("reaction","vibe","uid","is_deleted")
    search_fields=("reaction","vibe")

class StoryRatingAdmin(dj_admin.ModelAdmin):
    list_display=("rating","uid")
    search_fields=("rating","uid")

class StoryViewAdmin(dj_admin.ModelAdmin):
    list_display=("uid","viewed_at")
   


neo_admin.register(Story, StoryAdmin)
neo_admin.register(StoryComment,StoryCommentAdmin)
neo_admin.register(StoryReaction,StoryReactionAdmin)
neo_admin.register(StoryRating,StoryRatingAdmin)
neo_admin.register(StoryView,StoryViewAdmin)




# Register your models here.
