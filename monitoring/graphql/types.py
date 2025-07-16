import graphene
from graphene_django.types import DjangoObjectType
from monitoring.models import *
from monitoring.enums.report_types import *
from django.contrib.auth import get_user_model

class ReportType(DjangoObjectType):
    class Meta:
        model = Report
        fields = ['id','report_type','reported_by','description', 'notes' , 'created_at','updated_at']

    report_type = graphene.String()
    status = graphene.String()

    def resolve_report_type(self, info):
        return ReportTypeEnum(self.report_type).name.replace('_', ' ').title()

    def resolve_status(self, info):
        return StatusEnum(self.status).name.replace('_', ' ').title()


class PrivacyPolicyType(DjangoObjectType):
    class Meta:
        model = PrivacyPolicy
        fields = ('id', 'version', 'content', 'is_active', 'created_at')


class AcceptPrivacyPolicyType(DjangoObjectType):
    class Meta:
        model = AcceptPrivacyPolicy
        fields = ('id', 'user', 'privacy_policy', 'accepted_at')

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email')