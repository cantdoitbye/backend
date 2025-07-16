import graphene
from graphene import ObjectType

from auth_manager.graphql.types import UserType

class IndustryType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    created_by = graphene.Field(UserType)
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, industry):
        return cls(
            uid=industry.uid,
            name=industry.name,
            created_at=industry.created_at,
            updated_at=industry.updated_at,
            created_by=UserType.from_neomodel(industry.created_by.single()) if industry.created_by.single() else None,
            is_deleted=industry.is_deleted,
        )

class CompanyType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    location = graphene.String()
    description = graphene.String()
    website = graphene.String()
    email = graphene.String()
    contact_number = graphene.String()
    logo = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    created_by = graphene.Field(UserType)
    is_deleted = graphene.Boolean()
    review =  graphene.List(lambda: CompanyReviewNonCompanyType)
    @classmethod
    def from_neomodel(cls, company):
        return cls(
            uid=company.uid,
            name=company.name,
            location=company.location,
            description=company.description,
            website=company.website,
            email=company.email,
            contact_number=company.contact_number,
            logo=company.logo,
            created_at=company.created_at,
            updated_at=company.updated_at,
            created_by=UserType.from_neomodel(company.created_by.single()) if company.created_by.single() else None,
            review=[CompanyReviewNonCompanyType.from_neomodel(x) for x in company.review],
            is_deleted=company.is_deleted,
        )

class JobType(graphene.ObjectType):
    uid = graphene.String()
    title = graphene.String()
    industry = graphene.Field(lambda: IndustryType)
    company = graphene.Field(lambda: CompanyType)
    description = graphene.String()
    requirements = graphene.String()
    location = graphene.String()
    employment_type = graphene.String()
    seniority_level = graphene.String()
    salary_range = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    posted_by = graphene.Field(lambda: UserType)
    job_cover_image = graphene.String()
    is_deleted = graphene.Boolean()
    application =  graphene.List(lambda: ApplicationNonJobType)
    @classmethod
    def from_neomodel(cls, job):
        return cls(
            uid=job.uid,
            title=job.title,
            industry=IndustryType.from_neomodel(job.industry.single()) if job.industry.single() else None,
            company=CompanyType.from_neomodel(job.company.single()) if job.company.single() else None,
            description=job.description,
            requirements=job.requirements,
            location=job.location,
            employment_type=job.employment_type,
            seniority_level=job.seniority_level,
            salary_range=job.salary_range,
            created_at=job.created_at,
            updated_at=job.updated_at,
            posted_by=UserType.from_neomodel(job.posted_by.single()) if job.posted_by.single() else None,
            application=[ApplicationNonJobType.from_neomodel(x) for x in job.application],
            job_cover_image=job.job_cover_image,
            is_deleted=job.is_deleted
        )

class ApplicationType(ObjectType):
    uid = graphene.String()
    job = graphene.Field(JobType)  # Assuming JobType is already defined
    applicant = graphene.Field(UserType)  # Assuming UserType is already defined
    resume = graphene.String()
    cover_letter = graphene.String()
    applied_at = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, application):
        return cls(
            uid=application.uid,
            job=JobType.from_neomodel(application.job.single()) if application.job.single() else None,
            applicant=UserType.from_neomodel(application.applicant.single()) if application.applicant.single() else None,
            resume=application.resume,
            cover_letter=application.cover_letter,
            applied_at=application.applied_at,
            is_deleted=application.is_deleted
        )

class CompanyReviewType(ObjectType):
    uid = graphene.String()
    company = graphene.Field(CompanyType)  # Assuming CompanyType is already defined
    rating = graphene.Int()
    review = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    created_by = graphene.Field(UserType)  # Assuming UserType is already defined
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, company_review):
        return cls(
            uid=company_review.uid,
            company=CompanyType.from_neomodel(company_review.company.single()) if company_review.company.single() else None,
            rating=company_review.rating,
            review=company_review.review,
            created_at=company_review.created_at,
            updated_at=company_review.updated_at,
            created_by=UserType.from_neomodel(company_review.created_by.single()) if company_review.created_by.single() else None,
            is_deleted=company_review.is_deleted
        )


class CompanyReviewNonCompanyType(ObjectType):
    uid = graphene.String()
    rating = graphene.Int()
    review = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    created_by = graphene.Field(UserType)  # Assuming UserType is already defined
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, company_review):
        return cls(
            uid=company_review.uid,
            rating=company_review.rating,
            review=company_review.review,
            created_at=company_review.created_at,
            updated_at=company_review.updated_at,
            created_by=UserType.from_neomodel(company_review.created_by.single()) if company_review.created_by.single() else None,
            is_deleted=company_review.is_deleted
        )



class ApplicationNonJobType(ObjectType):
    uid = graphene.String()
    applicant = graphene.Field(UserType)  # Assuming UserType is already defined
    resume = graphene.String()
    cover_letter = graphene.String()
    applied_at = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, application):
        return cls(
            uid=application.uid,
            applicant=UserType.from_neomodel(application.applicant.single()) if application.applicant.single() else None,
            resume=application.resume,
            cover_letter=application.cover_letter,
            applied_at=application.applied_at,
            is_deleted=application.is_deleted
        )







