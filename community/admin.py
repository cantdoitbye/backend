from django.contrib import admin

from django_neomodel import admin as neo_admin
from django.contrib import admin as dj_admin
from community.models import Community
from community.models import Membership
from community.models import CommunityReview
from community.models import CommunityMessages


# class CommunityAdmin(dj_admin.ModelAdmin):
#     list_display = ("name", "description", "community_type", "community_circle", "created_date", "updated_date","created_by")
#     search_fields = ("name", "description")

# class MembershipAdmin(dj_admin.ModelAdmin):
#     search_fields = ('user', 'community')
#     list_display = ('uid','is_accepted','user', 'community', 'is_admin', 'is_leader',  'join_date', 'can_message', 'is_blocked')

# class CommunityReviewAdmin(dj_admin.ModelAdmin):
#     search_fields=('title','reaction')
#     list_display=('title','reaction','content')

# class CommunityMessageAdmin(dj_admin.ModelAdmin):
#     search_fields=('title','content')
#     list_display=('title','content',)

# neo_admin.register(Community, CommunityAdmin)
# neo_admin.register(Membership, MembershipAdmin)
# neo_admin.register(CommunityReview,CommunityReviewAdmin)
# neo_admin.register(CommunityMessages,CommunityMessageAdmin)
