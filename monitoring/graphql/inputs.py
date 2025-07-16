import graphene
from monitoring.enums.report_types import ReportTypeEnumGQL , StatusEnumGQL



class ReportInput(graphene.InputObjectType):
    report_type = ReportTypeEnumGQL(required=True, description="Type of report to be submitted.")
    reported_by = graphene.Int(description="ID of the user submitting the report.")
    notes = graphene.String(description="Additional notes regarding the report.")
    description = graphene.String(description="Detailed description of the issue.")


class AcceptPrivacyPolicyInput(graphene.InputObjectType):
    version = graphene.String(required=True)

