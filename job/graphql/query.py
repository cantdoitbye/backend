import graphene
from graphene import Mutation
from neomodel import db
from graphql_jwt.decorators import login_required,superuser_required

from .types import *
from auth_manager.models import Users
from job.models import *

class Query(ObjectType):
    industry_by_uid = graphene.Field(IndustryType, uid=graphene.String(required=True))

    def resolve_industry_by_uid(self, info, uid):
        try:
            industry = Industry.nodes.get(uid=uid)
            return IndustryType.from_neomodel(industry)
        except Industry.DoesNotExist:
            return None
        
    all_industries = graphene.List(IndustryType)

    def resolve_all_industries(self, info):
        industries = Industry.nodes.filter(is_deleted=False)
        return [IndustryType.from_neomodel(industry) for industry in industries]
    
    company_by_uid = graphene.Field(CompanyType, uid=graphene.String(required=True))

    def resolve_company_by_uid(self, info, uid):
        try:
            company = Company.nodes.get(uid=uid)
            return CompanyType.from_neomodel(company)
        except Company.DoesNotExist:
            return None
        
    all_companies = graphene.List(CompanyType)

    def resolve_all_companies(self, info):
        companies = Company.nodes.filter(is_deleted=False)
        return [CompanyType.from_neomodel(company) for company in companies]
    
    my_company=graphene.List(CompanyType)

    @login_required
    def resolve_my_company(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:

            my_companies=list(user_node.company.all())

            return [CompanyType.from_neomodel(x) for x in my_companies]
        except Exception as e:
            raise Exception(e)
    
    job_by_uid = graphene.Field(JobType, uid=graphene.String(required=True))
    all_jobs = graphene.List(JobType)

    def resolve_job_by_uid(self, info, uid):
        try:
            job = Job.nodes.get(uid=uid)
            return JobType.from_neomodel(job)
        except Job.DoesNotExist:
            return None

    def resolve_all_jobs(self, info):
        return [JobType.from_neomodel(job) for job in Job.nodes.all() if not job.is_deleted]
    

    my_job=graphene.List(JobType)

    @login_required
    def resolve_my_company(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:

            my_jobs=list(user_node.job.all())

            return [JobType.from_neomodel(x) for x in my_jobs]
        except Exception as e:
            raise Exception(e)



    application_by_uid = graphene.Field(ApplicationType, uid=graphene.String(required=True))
    all_applications = graphene.List(ApplicationType)

    def resolve_application_by_uid(self, info, uid):
        try:
            application = Application.nodes.get(uid=uid)
            return ApplicationType.from_neomodel(application)
        except Application.DoesNotExist:
            return None

    def resolve_all_applications(self, info):
        return [ApplicationType.from_neomodel(app) for app in Application.nodes.all()]
    

    company_review_by_uid = graphene.Field(CompanyReviewType, uid=graphene.String(required=True))
    all_company_reviews = graphene.List(CompanyReviewType)

    def resolve_company_review_by_uid(self, info, uid):
        try:
            company_review = CompanyReview.nodes.get(uid=uid)
            return CompanyReviewType.from_neomodel(company_review)
        except CompanyReview.DoesNotExist:
            return None

    def resolve_all_company_reviews(self, info):
        return [CompanyReviewType.from_neomodel(review) for review in CompanyReview.nodes.all()]