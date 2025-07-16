from django.contrib import admin
from .models import UploadFiles
# Register your models here.

# admin.site.register([UploadFiles])


class UploadFilesAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'file', 'uploaded_at')  # Include all fields you want to display
    search_fields = ('username',)  # Allow searching by username
    list_filter = ('uploaded_at',)  # Add filters for uploaded date


admin.site.register(UploadFiles, UploadFilesAdmin)