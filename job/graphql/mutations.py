import graphene
from graphene import Mutation
from graphql import GraphQLError
from .types import *
from auth_manager.models import Users
from job.models import *
from .inputs import *
from .messages import JobMessages

class CreateIndustry(graphene.Mutation):
    industry = graphene.Field(IndustryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateIndustryInput(required=True)

    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            industry = Industry(
                name=input.name,
                created_at=datetime.now(),
            )
            industry.save()
            industry.created_by.connect(user)
            return CreateIndustry(industry=IndustryType.from_neomodel(industry), success=True, message=JobMessages.INDUSTRY_CREATED)
        except Exception as e:
            return CreateIndustry(industry=None, success=False, message=str(e))
        
class UpdateIndustry(graphene.Mutation):
    industry = graphene.Field(IndustryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateIndustryInput(required=True)

    def mutate(self, info, input):
        try:
            industry = Industry.nodes.get(uid=input.uid)

            if input.name:
                industry.name = input.name

            if input.is_deleted is not None:
                industry.is_deleted = input.is_deleted

            industry.save()
            return UpdateIndustry(industry=IndustryType.from_neomodel(industry), success=True, message=JobMessages.INDUSTRY_UPDATED)
        except Exception as e:
            return UpdateIndustry(industry=None, success=False, message=str(e))
        
class DeleteIndustry(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteIndustryInput(required=True)

    def mutate(self, info, input):
        try:
            industry = Industry.nodes.get(uid=input.uid)
            industry.is_deleted = True
            industry.save()
            return DeleteIndustry(success=True, message=JobMessages.INDUSTRY_DELETED)
        except Exception as e:
            return DeleteIndustry(success=False, message=str(e))
        
class CreateCompany(graphene.Mutation):
    company = graphene.Field(CompanyType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCompanyInput(required=True)

    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)

            company = Company(
                name=input.name,
                location=input.location,
                description=input.description,
                website=input.website,
                email=input.email,
                contact_number=input.contact_number,
                logo=input.logo,
                created_at=datetime.now(),
            )
            company.save()
            company.created_by.connect(user)
            user.company.connect(company)
            return CreateCompany(company=CompanyType.from_neomodel(company), success=True, message=JobMessages.COMPANY_CREATED)
        except Exception as e:
            return CreateCompany(company=None, success=False, message=str(e))

class UpdateCompany(graphene.Mutation):
    company = graphene.Field(CompanyType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateCompanyInput(required=True)

    def mutate(self, info, input):
        try:
            company = Company.nodes.get(uid=input.uid)

            if input.name:
                company.name = input.name

            if input.location:
                company.location = input.location

            if input.description:
                company.description = input.description

            if input.website:
                company.website = input.website

            if input.email:
                company.email = input.email

            if input.contact_number:
                company.contact_number = input.contact_number

            if input.logo:
                company.logo = input.logo

            if input.is_deleted is not None:
                company.is_deleted = input.is_deleted

            company.save()
            return UpdateCompany(company=CompanyType.from_neomodel(company), success=True, message=JobMessages.COMPANY_UPDATED)
        except Exception as e:
            return UpdateCompany(company=None, success=False, message=str(e))

class DeleteCompany(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteCompanyInput(required=True)

    def mutate(self, info, input):
        try:
            company = Company.nodes.get(uid=input.uid)
            company.is_deleted = True
            company.save()
            return DeleteCompany(success=True, message=JobMessages.COMPANY_DELETED)
        except Exception as e:
            return DeleteCompany(success=False, message=str(e))

class CreateJob(graphene.Mutation):
    job = graphene.Field(JobType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateJobInput(required=True)

    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            posted_by = Users.nodes.get(user_id=user_id)
            industry = Industry.nodes.get(uid=input.industry_uid)
            company = Company.nodes.get(uid=input.company_uid)
            

            job = Job(
                title=input.title,
                description=input.description,
                requirements=input.requirements,
                location=input.location,
                employment_type=input.employment_type,
                seniority_level=input.seniority_level,
                salary_range=input.salary_range,
                job_cover_image=input.job_cover_image,
            )
            job.save()
            
            job.industry.connect(industry)
            
            job.company.connect(company)
           
            job.posted_by.connect(posted_by)
           
            posted_by.job.connect(job)
           

            return CreateJob(job=JobType.from_neomodel(job), success=True, message=JobMessages.JOB_CREATED)
        except Exception as error:
            return CreateJob(job=None, success=False, message=str(error))

class UpdateJob(graphene.Mutation):
    job = graphene.Field(JobType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateJobInput(required=True)

    def mutate(self, info, input):
        try:
            job = Job.nodes.get(uid=input.uid)

            if input.title:
                job.title = input.title
            if input.industry_uid:
                industry = Industry.nodes.get(uid=input.industry_uid)
                job.industry.connect(industry)
            if input.company_uid:
                company = Company.nodes.get(uid=input.company_uid)
                job.company.connect(company)
            if input.description:
                job.description = input.description
            if input.requirements:
                job.requirements = input.requirements
            if input.location:
                job.location = input.location
            if input.employment_type:
                job.employment_type = input.employment_type
            if input.seniority_level:
                job.seniority_level = input.seniority_level
            if input.salary_range:
                job.salary_range = input.salary_range
            if input.job_cover_image:
                job.job_cover_image = input.job_cover_image
            if input.is_deleted is not None:
                job.is_deleted = input.is_deleted

            job.save()

            return UpdateJob(job=JobType.from_neomodel(job), success=True, message=JobMessages.JOB_UPDATED)
        except Exception as error:
            return UpdateJob(job=None, success=False, message=str(error))

class DeleteJob(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteJobInput(required=True)

    def mutate(self, info, input):
        try:
            job = Job.nodes.get(uid=input.uid)
            job.is_deleted = True
            job.save()

            return DeleteJob(success=True, message=JobMessages.JOB_DELETED)
        except Exception as error:
            return DeleteJob(success=False, message=str(error))

class CreateApplication(graphene.Mutation):
    application = graphene.Field(ApplicationType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateApplicationInput(required=True)

    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            job = Job.nodes.get(uid=input.job_uid)
            applicant = Users.nodes.get(uid=input.applicant_uid)

            application = Application(
                resume=input.resume,
                cover_letter=input.cover_letter
            )
            application.save()
            application.job.connect(job)
            application.applicant.connect(applicant)
            job.application.connect(application)

            return CreateApplication(application=ApplicationType.from_neomodel(application), success=True, message=JobMessages.APPLICATION_CREATED)
        except Exception as error:
            return CreateApplication(application=None, success=False, message=str(error))

class UpdateApplication(graphene.Mutation):
    application = graphene.Field(ApplicationType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateApplicationInput(required=True)

    def mutate(self, info, input):
        try:
            application = Application.nodes.get(uid=input.uid)

            if input.resume:
                application.resume = input.resume
            if input.cover_letter:
                application.cover_letter = input.cover_letter
            if input.is_deleted is not None:
                application.is_deleted = input.is_deleted

            application.save()

            return UpdateApplication(application=ApplicationType.from_neomodel(application), success=True, message=JobMessages.APPLICATION_UPDATED)
        except Exception as error:
            return UpdateApplication(application=None, success=False, message=str(error))

class DeleteApplication(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteApplicationInput(required=True)

    def mutate(self, info, input):
        try:
            application = Application.nodes.get(uid=input.uid)
            application.delete()

            return DeleteApplication(success=True, message=JobMessages.APPLICATION_DELETED)
        except Exception as error:
            return DeleteApplication(success=False, message=str(error))

class CreateCompanyReview(graphene.Mutation):
    company_review = graphene.Field(CompanyReviewType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCompanyReviewInput(required=True)

    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            company = Company.nodes.get(uid=input.company_uid)
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            created_by = Users.nodes.get(uid=user.uid)

            company_review = CompanyReview(
                rating=input.rating,
                review=input.review,
            )
            company_review.save()
            company_review.company.connect(company)
            company_review.created_by.connect(created_by)
            company.review.connect(company_review)

            return CreateCompanyReview(company_review=CompanyReviewType.from_neomodel(company_review), success=True, message=JobMessages.COMPANY_REVIEW_CREATED)
        except Exception as error:
            return CreateCompanyReview(company_review=None, success=False, message=str(error))

class UpdateCompanyReview(graphene.Mutation):
    company_review = graphene.Field(CompanyReviewType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateCompanyReviewInput(required=True)

    def mutate(self, info, input):
        try:
            company_review = CompanyReview.nodes.get(uid=input.uid)

            if input.rating is not None:
                company_review.rating = input.rating
            if input.review:
                company_review.review = input.review
            if input.is_deleted is not None:
                company_review.is_deleted = input.is_deleted

            company_review.save()

            return UpdateCompanyReview(company_review=CompanyReviewType.from_neomodel(company_review), success=True, message=JobMessages.COMPANY_REVIEW_UPDATED)
        except Exception as error:
            return UpdateCompanyReview(company_review=None, success=False, message=str(error))

class DeleteCompanyReview(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteCompanyReviewInput(required=True)

    def mutate(self, info, input):
        try:
            company_review = CompanyReview.nodes.get(uid=input.uid)
            company_review.delete()

            return DeleteCompanyReview(success=True, message=JobMessages.COMPANY_REVIEW_DELETED)
        except Exception as error:
            return DeleteCompanyReview(success=False, message=str(error))

class Mutation(graphene.ObjectType):
    create_industry=CreateIndustry.Field()
    update_industry=UpdateIndustry.Field()
    delete_industry=DeleteIndustry.Field()

    create_company=CreateCompany.Field()
    update_company=UpdateCompany.Field()
    delete_company=DeleteCompany.Field()

    create_job=CreateJob.Field()
    update_job=UpdateJob.Field()
    delete_job=DeleteJob.Field()

    create_application=CreateApplication.Field()
    update_application=UpdateApplication.Field()
    delete_application=DeleteApplication.Field()

    create_company_review=CreateCompanyReview.Field()
    update_company_review=UpdateCompanyReview.Field()
    delete_company_review=DeleteCompanyReview.Field()