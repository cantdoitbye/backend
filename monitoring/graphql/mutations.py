import graphene
from monitoring.models import Report
from .types import *
from .inputs import *
from graphql_jwt.decorators import login_required

class CreateReport(graphene.Mutation):
    class Arguments:
        input = ReportInput(required=True)

    report = graphene.Field(ReportType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, input):
        try:
            report = Report(
                report_type=input.report_type.value,
                reported_by_id=input.reported_by,
                description=input.description,
                notes=input.notes,
            )
            report.save()
            return CreateReport(
                report=report,
                success=True,
                message="Report created successfully."
            )
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateReport(
                report=None,
                success=False,
                message=f"Failed to create report: {message}"
            )

class UpdateReport(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        input = ReportInput()

    report = graphene.Field(ReportType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, id, input=None):
        try:
            report = Report.objects.get(pk=id)
            if input:
                if input.report_type:
                    report.report_type = input.report_type
                if input.reported_by:
                    report.reported_by_id = input.reported_by
                if input.description:
                    report.description = input.description
                if input.notes:
                    report.notes = input.notes
                if input.status:
                    report.status = input.status
                report.save()
            return UpdateReport(
                report=report,
                success=True,
                message="Report updated successfully."
            )
        except Report.DoesNotExist:
            return UpdateReport(
                report=None,
                success=False,
                message="Report not found."
            )
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateReport(
                report=None,
                success=False,
                message=f"Failed to update report: {message}"
            )


class AcceptPrivacyPolicyMutation(graphene.Mutation):
    class Arguments:
        input = AcceptPrivacyPolicyInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        user = info.context.user
        if user.is_anonymous:
            return AcceptPrivacyPolicyMutation(success=False, message="You must be logged in.")
        payload = info.context.payload
        user_id = payload.get('user_id')
        try:
            privacy_policy = PrivacyPolicy.objects.get(version=input.version)
        except PrivacyPolicy.DoesNotExist:
            return AcceptPrivacyPolicyMutation(success=False, message="Privacy policy not found.")

        if AcceptPrivacyPolicy.objects.filter(user=user, privacy_policy=privacy_policy).exists():
            return AcceptPrivacyPolicyMutation(success=False, message="Policy already accepted.")

        AcceptPrivacyPolicy.objects.create(user=user, privacy_policy=privacy_policy)

        return AcceptPrivacyPolicyMutation(success=True, message="Privacy policy accepted successfully.")



class Mutation(graphene.ObjectType):
    create_report = CreateReport.Field()
    update_report = UpdateReport.Field()
    accept_privacy_policy = AcceptPrivacyPolicyMutation.Field()
