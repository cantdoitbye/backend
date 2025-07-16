import graphene

class CreateIndustryInput(graphene.InputObjectType):
    name = graphene.String(required=True)

class UpdateIndustryInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    name = graphene.String()
    is_deleted = graphene.Boolean()

class DeleteIndustryInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateCompanyInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    location = graphene.String()
    description = graphene.String()
    website = graphene.String()
    email = graphene.String()
    contact_number = graphene.String()
    logo = graphene.String()
    

class UpdateCompanyInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    name = graphene.String()
    location = graphene.String()
    description = graphene.String()
    website = graphene.String()
    email = graphene.String()
    contact_number = graphene.String()
    logo = graphene.String()
    is_deleted = graphene.Boolean()

class DeleteCompanyInput(graphene.InputObjectType):
    uid = graphene.String(required=True)


class CreateJobInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    industry_uid = graphene.String(required=True)
    company_uid = graphene.String(required=True)
    description = graphene.String()
    requirements = graphene.String()
    location = graphene.String()
    employment_type = graphene.String()
    seniority_level = graphene.String()
    salary_range = graphene.String()
    job_cover_image = graphene.String()

class UpdateJobInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    title = graphene.String()
    industry_uid = graphene.String()
    company_uid = graphene.String()
    description = graphene.String()
    requirements = graphene.String()
    location = graphene.String()
    employment_type = graphene.String()
    seniority_level = graphene.String()
    salary_range = graphene.String()
    job_cover_image = graphene.String()
    is_deleted = graphene.Boolean()

class DeleteJobInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateApplicationInput(graphene.InputObjectType):
    job_uid = graphene.String(required=True)
    applicant_uid = graphene.String(required=True)
    resume = graphene.String(required=True)
    cover_letter = graphene.String()

class UpdateApplicationInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    resume = graphene.String()
    cover_letter = graphene.String()
    is_deleted = graphene.Boolean()

class DeleteApplicationInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateCompanyReviewInput(graphene.InputObjectType):
    company_uid = graphene.String(required=True)
    rating = graphene.Int(required=True)
    review = graphene.String(required=True)

class UpdateCompanyReviewInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    rating = graphene.Int()
    review = graphene.String()
    is_deleted = graphene.Boolean()

class DeleteCompanyReviewInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

