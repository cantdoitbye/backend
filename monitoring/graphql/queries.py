import graphene
from graphene_django.types import DjangoObjectType
from monitoring.models import *
from .types import *
from graphql_jwt.decorators import login_required, superuser_required
from graphene import Field, List, Int, String

class Query(graphene.ObjectType):
    all_reports = graphene.List(
        ReportType, 
        report_type=graphene.String(required=False), 
        status=graphene.String(required=False)
    )
    report = graphene.Field(ReportType, id=graphene.Int(required=True))
    
    @login_required
    @superuser_required
    def resolve_all_reports(self, info, report_type=None, status=None, **kwargs):
        reports = Report.objects.all()
        if report_type:
            reports = reports.filter(report_type=report_type)
        if status:
            reports = reports.filter(status=status)
        return reports
    
    @login_required
    def resolve_report(self, info, id):
        try:
            return Report.objects.get(pk=id)
        except Report.DoesNotExist:
            raise Exception("Report with this ID does not exist.")

    all_privacy_policies = graphene.List(PrivacyPolicyType)

    @superuser_required
    @login_required
    def resolve_all_privacy_policies(self, info):
        return PrivacyPolicy.objects.filter(is_active=True)
    
    privacy_policy_by_version = graphene.Field(PrivacyPolicyType, version=graphene.String(required=True))
    @superuser_required
    @login_required
    def resolve_privacy_policy_by_version(self, info, version):
        try:
            return PrivacyPolicy.objects.get(version=version)
        except PrivacyPolicy.DoesNotExist:
            return None
            
    user_accepted_policy = graphene.Field(AcceptPrivacyPolicyType, version=graphene.String(required=True))
    @superuser_required
    @login_required
    def resolve_user_accepted_policy(self, info, version):
        user = info.context.user
        if user.is_anonymous:
            return None

        try:
            policy = PrivacyPolicy.objects.get(version=version)
            return AcceptPrivacyPolicy.objects.get(user=user, privacy_policy=policy)
        except (PrivacyPolicy.DoesNotExist, AcceptPrivacyPolicy.DoesNotExist):
            return None
