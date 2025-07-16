from django.contrib import admin
from .models import Report,PrivacyPolicy,AcceptPrivacyPolicy
from monitoring.enums.report_types import ReportTypeEnum, StatusEnum

class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'report_type_display', 'reported_by', 'reported_object_id', 'reported_object_type', 'status_display', 'created_at', 'updated_at')
    list_filter = ('report_type', 'status', 'created_at', 'updated_at')
    search_fields = ('description', 'reported_object_type')
    ordering = ('-created_at',)

    def report_type_display(self, obj):
        return ReportTypeEnum(obj.report_type).name.replace('_', ' ').title()
    report_type_display.short_description = 'Report Type'

    def status_display(self, obj):
        return StatusEnum(obj.status).name.replace('_', ' ').title()
    status_display.short_description = 'Status'

admin.site.register(Report, ReportAdmin)
admin.site.register([PrivacyPolicy,AcceptPrivacyPolicy])
