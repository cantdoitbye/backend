from django.contrib.auth.models import AbstractUser
from django_neomodel import admin as neo_admin
from django.contrib import admin as dj_admin
from auth_manager.models import Users,Profile,OTP,WelcomeScreenMessage

from django.contrib.auth.admin import UserAdmin
from post_office.models import EmailTemplate


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': 'uid',
        }


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active')
        labels = {
            'username': 'uid',
        }



class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    list_display = ('display_username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    def display_username(self, obj):
        return obj.username
    display_username.short_description = 'uid'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('username',)
        return self.readonly_fields


dj_admin.site.unregister(User)
dj_admin.site.register(User, CustomUserAdmin)



dj_admin.site.unregister(EmailTemplate)

class EmailTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = '__all__'
        widgets = {
            'subject': forms.TextInput(attrs={'size': 1000, 'placeholder': 'Enter the subject here', 'style': 'display:block !important; background:red'}),
            'content': forms.Textarea(attrs={'rows': 10, 'cols': 100, 'placeholder': 'Enter the content here', 'style': 'display:block;'}),
            'html_content': forms.Textarea(attrs={'rows': 10, 'cols': 100, 'placeholder': 'Enter the HTML content here', 'style': 'display:block;'}),
        }

class EmailTemplateAdmin(dj_admin.ModelAdmin):
    form = EmailTemplateAdminForm
    list_display = ('name', 'description', 'subject')
    search_fields = ('name', 'description', 'subject')
    fields = ('name', 'description', 'subject', 'content', 'html_content', 'language')

dj_admin.site.register(EmailTemplate, EmailTemplateAdmin)


class OTPAdmin(dj_admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at', 'expires_at')
    search_fields = ('user__username', 'otp')
    list_filter = ('created_at', 'expires_at')

dj_admin.site.register(OTP, OTPAdmin)



class UserAdmin(dj_admin.ModelAdmin):
    list_display = ("username","email")
neo_admin.register(Users,UserAdmin)


class ProfileAdmin(dj_admin.ModelAdmin):
    list_display = ("uid",)
neo_admin.register(Profile,ProfileAdmin)





@dj_admin.register(WelcomeScreenMessage)
class WelcomeScreenMessageAdmin(dj_admin.ModelAdmin):
    list_display = ('title', 'content_type', 'rank', 'timestamp', 'is_visible')
    list_filter = ('content_type', 'is_visible', 'timestamp')
    search_fields = ('title', 'content')
    ordering = ['rank', '-timestamp']
    list_editable = ('rank', 'is_visible')
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'image', 'rank', 'is_visible', 'content_type')
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('timestamp',)

    def save_model(self, request, obj, form, change):
        if not obj.rank:
            obj.rank = WelcomeScreenMessage.objects.count() + 1
        super().save_model(request, obj, form, change)

