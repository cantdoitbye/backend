from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from monitoring.enums.report_types import ReportTypeEnum ,StatusEnum

class Report(models.Model):
    report_type = models.CharField(
        max_length=20,
        choices=[(tag.value, tag.name) for tag in ReportTypeEnum],
        default=ReportTypeEnum.OTHER.value,
        verbose_name='Report Type',
        help_text='Select the type of report. This helps categorize the report.'
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_made',
        verbose_name='Reported By',
        help_text='The user who made the report. Leave blank if the report is anonymous.'
    )
    reported_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Reported Object ID',
        help_text='ID of the object being reported. This can be used to reference the specific object. Leave blank if not applicable.'
    )
    reported_object_type = models.CharField(
        null=True,
        max_length=50,
        blank=True,
        verbose_name='Reported Object Type',
        help_text='Type of the object being reported (e.g., "Post", "Comment"). This helps in identifying the type of object. Leave blank if not applicable.'
    )
    description = models.TextField(
        verbose_name='Description',
        help_text='Detailed description of the report. Provide as much detail as possible.'
    )
    status = models.CharField(
        max_length=20,
        choices=[(tag.value, tag.name) for tag in StatusEnum],
        default=StatusEnum.PENDING.value,
        verbose_name='Status',
        help_text='Current status of the report. Indicates the progress of handling the report.'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="Notes",
        help_text="Additional information about the report, e.g., Post ID, Post object in string format."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='The date and time when the report was created.'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At',
        help_text='The date and time when the report was last updated.'
    )

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']

    def __str__(self):
        return f'Report {self.id} - {self.report_type} - {self.status}'


class PrivacyPolicy(models.Model):
    """Model representing the privacy policy versions and content."""
    version = models.CharField(max_length=20, unique=True, help_text="Version number of the privacy policy")
    content = models.TextField(help_text="Full text of the privacy policy")
    is_active = models.BooleanField(default=True, help_text="Indicates whether this version of the policy is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Privacy Policy'
        verbose_name_plural = 'Privacy Policies'
        ordering = ['-created_at']
        db_table = 'privacy_policy'

    def __str__(self):
        return f"Privacy Policy Version {self.version}"


class AcceptPrivacyPolicy(models.Model):
    """Model representing the acceptance of privacy policies by users."""
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='accepted_privacy_policies')
    privacy_policy = models.ForeignKey(PrivacyPolicy, on_delete=models.CASCADE, related_name='accepted_users')
    accepted_at = models.DateTimeField(default=timezone.now, help_text="Timestamp when the policy was accepted")

    class Meta:
        verbose_name = 'Accepted Privacy Policy'
        verbose_name_plural = 'Accepted Privacy Policies'
        unique_together = ('user', 'privacy_policy')
        ordering = ['-accepted_at']
        db_table = 'accept_privacy_policy'

    def __str__(self):
        return f"User {self.user} accepted Policy {self.privacy_policy.version} on {self.accepted_at}"