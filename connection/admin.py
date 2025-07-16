from django.contrib import admin
from .models import Relation, SubRelation

@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    """
    Admin view for the Relation model.
    """
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(SubRelation)
class SubRelationAdmin(admin.ModelAdmin):
    """
    Admin view for the SubRelation model.
    """
    list_display = ('sub_relation_name', 'relation', 'directionality', 'approval_required', 'reverse_connection')
    list_filter = ('relation', 'directionality', 'approval_required')
    search_fields = ('sub_relation_name', 'reverse_connection')
    ordering = ('relation', 'sub_relation_name')
    autocomplete_fields = ('relation',)
