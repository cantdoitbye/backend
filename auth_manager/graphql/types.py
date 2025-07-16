# auth_manager/graphql/types.py 
import graphene
from graphene import ObjectType
from  auth_manager.models import *
from auth_manager.Utils import generate_presigned_url
from graphene_django import DjangoObjectType
from django.conf import settings
from community.models import CommunityReactionManager
from post.models import PostReactionManager


from django.core.files.storage import default_storage
from urllib.parse import urljoin
from neomodel import db
from connection.models import Connection
from auth_manager.Utils import generate_presigned_url
from connection.utils import relation as RELATIONUTILLS
from vibe_manager.models import IndividualVibe
from datetime import datetime


class FileDetailType(graphene.ObjectType):
    url = graphene.String()
    file_extension = graphene.String()
    file_type = graphene.String()
    file_size = graphene.Int()


class WelcomeScreenMessageType(DjangoObjectType):
    class Meta:
        model = WelcomeScreenMessage
        fields=("title","content","image","rank","is_visible")

    image = graphene.String()

    def resolve_image(self, info):
        if self.image:
            base_url = settings.AWS_S3_ENDPOINT_URL
            bucket_path = f"{settings.AWS_STORAGE_BUCKET_NAME}/"
            return urljoin(base_url, bucket_path + str(self.image))
        return None


class UserType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name=graphene.String()
    last_name=graphene.String()
    user_type=graphene.String()
    created_at = graphene.DateTime()
    created_by = graphene.String()
    updated_at = graphene.DateTime()
    updated_by = graphene.String()
    connection_stat = graphene.Field(lambda: ConnectionStatsType)
    profile = graphene.Field(lambda:ProfileNoUserType)
    # connection = graphene.Field(lambda: ConnectionNoUserType)

    @classmethod
    def from_neomodel(cls, user):
        try:
            return cls(
                uid=user.uid,
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                user_type=user.user_type,
                created_at=user.created_at,
                created_by=user.created_by,
                updated_at=user.updated_at,
                updated_by=user.updated_by,
                connection_stat=ConnectionStatsType.from_neomodel(user.connection_stat.single()) if user.connection_stat.single() else 0,
                profile=ProfileNoUserType.from_neomodel(user.profile.single()) if user.profile.single() else None,
                # connection=ConnectionNoUserType.from_neomodel(user.connection.single()) if user.connection.single() else None,
                
        )
        except:
            user_uid=user.get('uid')
            created_at_unix=user.get('created_at')
            created_at=datetime.fromtimestamp(created_at_unix)
            updated_at_unix=user.get('updated_at')
            updated_at=datetime.fromtimestamp(updated_at_unix)
            user_node=Users.nodes.get(uid=user_uid)
            # print(user_node)
            return cls( 
                uid = user.get('uid'),
                user_id = user.get('user_id'),
                username = user.get('username'),
                email = user.get('email'),
                first_name = user.get('first_name'),
                last_name = user.get('last_name'),
                user_type = user.get('user_type'),
                created_at = created_at,
                created_by = user.get('created_by'),
                updated_at = updated_at,
                updated_by = user.get('updated_by'),
                connection_stat=ConnectionStatsType.from_neomodel(user_node.connection_stat.single()) if user_node.connection_stat.single() else 0,
                profile=ProfileNoUserType.from_neomodel(user_node.profile.single()) if user_node.profile.single() else None,
    
            )


class ProfileType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()
    bio = graphene.String()
    designation = graphene.String()
    worksat = graphene.String()
    phone_number = graphene.String()
    born = graphene.DateTime()
    dob = graphene.DateTime()
    school = graphene.String()
    college = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic=graphene.Field(FileDetailType)
    cover_image_id = graphene.String()
    cover_image=graphene.Field(FileDetailType)
    user = graphene.Field(UserType)
    city = graphene.String()
    state = graphene.String()

    onboarding_status = graphene.List(lambda:OnboardingStatusNonProfileType)
    contact_info = graphene.List(lambda:ContactInfoTypeNoProfile)
    score = graphene.Field(lambda:ScoreNonProfileType)
    interest = graphene.List(lambda:InterestNonProfileType)
    achievement=graphene.List(lambda:AchievementNonProfileType)
    experience=graphene.List(lambda:ExperienceNonProfileType)
    skill=graphene.List(lambda:SkillNonProfileType)
    education=graphene.List(lambda:EducationNonProfileType)
    

    @classmethod


    def from_neomodel(cls, profile):
        return cls(
            uid=profile.uid,
            user_id=profile.user_id,
            gender=profile.gender,
            device_id=profile.device_id,
            fcm_token=profile.fcm_token,
            bio=profile.bio,
            designation=profile.designation,
            worksat=profile.worksat,
            phone_number=profile.phone_number,
            born=profile.born,
            dob=profile.dob,
            school=profile.school,
            college=profile.college,
            lives_in=profile.lives_in,
            profile_pic_id=profile.profile_pic_id,
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile.profile_pic_id)) if profile.profile_pic_id else None,
            cover_image_id=profile.cover_image_id,
            cover_image=FileDetailType(**generate_presigned_url.generate_file_info(profile.cover_image_id)) if profile.cover_image_id else None,    
            user=UserType.from_neomodel(profile.user.single()) if profile.user.single() else None,
            city=profile.city,
            state=profile.state,
            onboarding_status=[OnboardingStatusNonProfileType.from_neomodel(status) for status in profile.onboarding],
            contact_info=[ContactInfoTypeNoProfile.from_neomodel(contact) for contact in profile.contactinfo],
            score=ScoreNonProfileType.from_neomodel(profile.score.single()) if profile.score.single() else None,
            interest=[InterestNonProfileType.from_neomodel(interest) for interest in profile.interest],
            achievement=[AchievementNonProfileType.from_neomodel(achievement) for achievement in profile.achievement],
            experience=[ExperienceNonProfileType.from_neomodel(experience) for experience in profile.experience],
            skill=[SkillNonProfileType.from_neomodel(skill) for skill in profile.skill],
            education=[EducationNonProfileType.from_neomodel(education) for education in profile.education]
        )
    

class OnboardingStatusType(ObjectType):
    uid = graphene.String()
    email_verified = graphene.Boolean()
    phone_verified = graphene.Boolean()
    username_selected = graphene.Boolean()
    first_name_set = graphene.Boolean()
    last_name_set = graphene.Boolean()
    gender_set = graphene.Boolean()
    bio_set = graphene.Boolean()
    profile = graphene.Field(ProfileType)  # Assuming ProfileType is already defined

    @classmethod
    def from_neomodel(cls, onboarding_status):
        return cls(
            uid=onboarding_status.uid,
            email_verified=onboarding_status.email_verified,
            phone_verified=onboarding_status.phone_verified,
            username_selected=onboarding_status.username_selected,
            first_name_set=onboarding_status.first_name_set,
            last_name_set=onboarding_status.last_name_set,
            gender_set=onboarding_status.gender_set,
            bio_set=onboarding_status.bio_set,
            profile=ProfileType.from_neomodel(onboarding_status.profile.single()) if onboarding_status.profile.single() else None
        )

class ContactInfoType(ObjectType):
    uid = graphene.String()
    type = graphene.String()
    value = graphene.String()
    platform = graphene.String()
    link = graphene.String()
    profile = graphene.Field(ProfileType)

    @classmethod
    def from_neomodel(cls, contact_info):
        return cls(
            uid=contact_info.uid,
            type=contact_info.type,
            value=contact_info.value,
            platform=contact_info.platform,
            link=contact_info.link,
            profile=ProfileType.from_neomodel(contact_info.profile.single()) if contact_info.profile.single() else None
        )

class ScoreType(ObjectType):
    uid = graphene.String()
    vibers_count = graphene.Float()
    cumulative_vibescore = graphene.Float()
    intelligence_score = graphene.Float()
    appeal_score = graphene.Float()
    social_score = graphene.Float()
    human_score = graphene.Float()
    repo_score = graphene.Float()
    profile = graphene.Field(ProfileType)  # Ensure 'ProfileType' is defined

    @classmethod
    def from_neomodel(cls, score):
        return cls(
            uid=score.uid,
            vibers_count=score.vibers_count,
            cumulative_vibescore=score.cumulative_vibescore,
            intelligence_score=score.intelligence_score,
            appeal_score=score.appeal_score,
            social_score=score.social_score,
            human_score=score.human_score,
            repo_score=score.repo_score,
            profile=ProfileType.from_neomodel(score.profile.single()) if score.profile.single() else None,
        )

class InterestType(ObjectType):
    uid = graphene.String()
    is_deleted = graphene.Boolean()
    names = graphene.List(graphene.String)
    profile = graphene.Field(ProfileType)

    @classmethod
    def from_neomodel(cls, interest):
        return cls(
            uid=interest.uid,
            is_deleted=interest.is_deleted,
            names=interest.names,
            profile=ProfileType.from_neomodel(interest.profile.single()) if interest.profile.single() else None,
        )


class AchievementType(ObjectType):
     uid = graphene.String()
     profile = graphene.Field(ProfileType)
     what = graphene.String()
     description = graphene.String()
     date_achieved = graphene.DateTime()
     created_on = graphene.DateTime()
     is_deleted = graphene.Boolean()
     file_id =graphene.List(graphene.String)
     file_url=graphene.List(FileDetailType)
     from_source = graphene.String()
     from_date = graphene.DateTime()
     to_date = graphene.DateTime()

     @classmethod
     def from_neomodel(cls, achievement):
        return cls(
            uid=achievement.uid,
            what = achievement.what,
            description = achievement.description,
            created_on = achievement.created_on,
            date_achieved = achievement.date_achieved,
            is_deleted=achievement.is_deleted,
            file_id=achievement.file_id,
            file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in achievement.file_id] if achievement.file_id else None),
            from_source = achievement.from_source,
            from_date = achievement.from_date,
            to_date = achievement.to_date,
            profile=ProfileType.from_neomodel(achievement.profile.single()) if achievement.profile.single() else None,
        )
     




# Contact info type with out profile connected 

class ContactInfoTypeNoProfile(ObjectType):
    uid = graphene.String()
    type = graphene.String()
    value = graphene.String()
    platform = graphene.String()
    link = graphene.String()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, contact_info):
        return cls(
            uid=contact_info.uid,
            type=contact_info.type,
            value=contact_info.value,
            platform=contact_info.platform,
            link=contact_info.link,
            is_deleted = contact_info.is_deleted,
        )

class OnboardingStatusNonProfileType(ObjectType):
    uid = graphene.String()
    email_verified = graphene.Boolean()
    phone_verified = graphene.Boolean()
    username_selected = graphene.Boolean()
    first_name_set = graphene.Boolean()
    last_name_set = graphene.Boolean()
    gender_set = graphene.Boolean()
    bio_set = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, onboarding_status):
        if isinstance(onboarding_status, OnboardingStatus):
            return cls(
                uid=onboarding_status.uid,
                email_verified=onboarding_status.email_verified,
                phone_verified=onboarding_status.phone_verified,
                username_selected=onboarding_status.username_selected,
                first_name_set=onboarding_status.first_name_set,
                last_name_set=onboarding_status.last_name_set,
                gender_set=onboarding_status.gender_set,
                bio_set=onboarding_status.bio_set,

            )
        else :
            return cls(
                
                uid = onboarding_status.get('uid'),
                email_verified = onboarding_status.get('email_verified'),
                phone_verified = onboarding_status.get('phone_verified'),
                username_selected = onboarding_status.get('username_selected'),
                first_name_set = onboarding_status.get('first_name_set'),
                last_name_set = onboarding_status.get('last_name_set'),
                gender_set = onboarding_status.get('gender_set'),
                bio_set = onboarding_status.get('bio_set')
            )


class ScoreNonProfileType(ObjectType):
    uid = graphene.String()
    vibers_count = graphene.Float()
    cumulative_vibescore = graphene.Float()
    intelligence_score = graphene.Float()
    appeal_score = graphene.Float()
    social_score = graphene.Float()
    human_score = graphene.Float()
    repo_score = graphene.Float()

    @classmethod
    def from_neomodel(cls, score):
        if isinstance(score, Score):
            return cls(
                uid=score.uid,
                vibers_count=score.vibers_count,
                cumulative_vibescore=score.cumulative_vibescore,
                intelligence_score=score.intelligence_score,
                appeal_score=score.appeal_score,
                social_score=score.social_score,
                human_score=score.human_score,
                repo_score=score.repo_score,
            )
        else:
            return cls(
                uid = score.get('uid'),  
                vibers_count = score.get('vibers_count'),  
                cumulative_vibescore = score.get('cumulative_vibescore'),  
                intelligence_score = score.get('intelligence_score'),  
                appeal_score = score.get('appeal_score'),  
                social_score = score.get('social_score'),  
                human_score = score.get('human_score'),  
                repo_score = score.get('repo_score')  

            )


class InterestNonProfileType(ObjectType):
    uid = graphene.String()
    names = graphene.List(graphene.String)

    @classmethod
    def from_neomodel(cls, interest):
        if isinstance(interest, Interest):
            return cls(
                uid=interest.uid,
                names=interest.names,
            )
        else:
            return cls(
                uid=interest.get('uid'),
                names=interest.get('names'),
            )



class AchievementNonProfileType(ObjectType):
     uid = graphene.String()
     what = graphene.String()
     description = graphene.String()
     created_on = graphene.DateTime()
     from_source = graphene.String()
     from_date = graphene.DateTime()
     to_date = graphene.DateTime()
     file_id =graphene.List(graphene.String)
     file_url=graphene.List(FileDetailType)

     @classmethod
     def from_neomodel(cls, achievement):
        if isinstance(achievement, Achievement):
            return cls(
                uid=achievement.uid,
                what = achievement.what,
                description = achievement.description,
                created_on = achievement.created_on,
                from_source = achievement.from_source,
                from_date = achievement.from_date,
                to_date = achievement.to_date,
                file_id=achievement.file_id,
                file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in achievement.file_id] if achievement.file_id else None),
                
            )
        else:
            created_on_unix=achievement.get('created_on')
            created_on=datetime.fromtimestamp(created_on_unix)
            from_date_unix=achievement.get('from_date')
            from_date=datetime.fromtimestamp(from_date_unix)
            to_date_unix=achievement.get('to_date')
            if to_date_unix:
                to_date=datetime.fromtimestamp(to_date_unix)
            else:
                to_date=None
            return cls(
                uid = achievement.get('uid'),
                what = achievement.get('what'),
                description = achievement.get('description'),
                created_on = created_on,
                from_source = achievement.get('from_source'),
                from_date = from_date,
                to_date = to_date,
                file_id = achievement.get('file_id'),
                file_url = (
                    [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) 
                    for file_id in achievement.get('file_id', [])] if achievement.get('file_id') else None
                )

            )


class EducationNonProfileType(ObjectType):
     uid = graphene.String()
     what = graphene.String()
     field_of_study = graphene.String() 
     from_date = graphene.DateTime()
     to_date = graphene.DateTime()
     created_on =  graphene.DateTime()
     file_id =graphene.List(graphene.String)
     file_url=graphene.List(FileDetailType)
     
     
     @classmethod
     def from_neomodel(cls, education):
        if isinstance(education, Education):
            return cls(
                uid=education.uid,
                what = education.what,
                field_of_study = education.field_of_study, 
                from_date = education.from_date,
                to_date = education.to_date,
                created_on =  education.created_on,
                file_id=education.file_id,
                file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in education.file_id] if education.file_id else None),
                
            )
        else:
            created_on_unix=education.get('created_on')
            created_on=datetime.fromtimestamp(created_on_unix)
            from_date_unix=education.get('from_date')
            from_date=datetime.fromtimestamp(from_date_unix)
            to_date_unix=education.get('to_date')
            if to_date_unix:
                to_date=datetime.fromtimestamp(to_date_unix)
            else:
                to_date=None
            return cls(
                uid = education.get('uid'),
                what = education.get('what'),
                field_of_study = education.get('field_of_study'),
                from_date = from_date,
                to_date = to_date,
                created_on = created_on,
                file_id = education.get('file_id'),
                file_url = (
                    [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) 
                    for file_id in education.get('file_id', [])] if education.get('file_id') else None
                )

            )

class SkillNonProfileType(ObjectType):
     uid = graphene.String()
     what = graphene.String()
     from_date = graphene.DateTime() 
     to_date = graphene.DateTime()
     created_on =  graphene.DateTime()
     file_id =graphene.List(graphene.String)
     file_url=graphene.List(FileDetailType)
     
     
     @classmethod
     def from_neomodel(cls, skill):
        if isinstance(skill, Skill):
            return cls(
                uid=skill.uid,
                what = skill.what,
                from_date = skill.from_date,
                to_date = skill.to_date,
                created_on =  skill.created_on,
                file_id=skill.file_id,
                file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in skill.file_id] if skill.file_id else None),
                
            )
        else:
            created_on_unix=skill.get('created_on')
            created_on=datetime.fromtimestamp(created_on_unix)
            from_date_unix=skill.get('from_date')
            from_date=datetime.fromtimestamp(from_date_unix)
            to_date_unix=skill.get('to_date')
            if to_date_unix:
                to_date=datetime.fromtimestamp(to_date_unix)
            else:
                to_date=None
            return cls(
                uid = skill.get('uid'),
                what = skill.get('what'),
                from_date = from_date,
                to_date = to_date,
                created_on = created_on,
                file_id = skill.get('file_id'),
                file_url = (
                    [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) 
                    for file_id in skill.get('file_id', [])] if skill.get('file_id') else None
                ),

            )
     


class UsersReviewType(ObjectType):
    uid = graphene.String()
    byuser = graphene.Field(UserType)  # Assuming UserType is already defined
    touser = graphene.Field(UserType)  # Assuming UserType is already defined
    reaction = graphene.String()
    vibe = graphene.Float()
    title = graphene.String()
    content = graphene.String()
    file_id = graphene.String()
    is_deleted = graphene.Boolean()
    connection = graphene.Field(lambda: ConnectionNoUserType)

    @classmethod
    def from_neomodel(cls, users_review):
        # print(users_review)
        # Assuming `users_review.byuser` and `users_review.touser` are the relationships to User nodes
        byuser_node = users_review.byuser.single()
        touser_node = users_review.touser.single()

        if not byuser_node or not touser_node:
            return None

        # Cypher query to find a common connection node between byuser and touser
        query = """
        MATCH (byuser:Users {uid: $byuser_uid})-[c1:HAS_CONNECTION]->(conn:Connection)
        MATCH (conn)-[c3:HAS_CIRCLE]->(circle:Circle)
        MATCH (touser:Users {uid: $touser_uid})-[c2:HAS_CONNECTION]->(conn)
        RETURN conn, circle
        """
        params = {
            "byuser_uid": byuser_node.uid,
            "touser_uid": touser_node.uid,
        }
        result = db.cypher_query(query, params)
        
        if result and result[0]: 
            
            connection_node = result[0][0][0]
            circle_node=result[0][0][1]
            
            connection_instance = ConnectionNoUserType.from_neomodel(connection_node,circle_node)
            
            return cls(
                uid=users_review.uid,
                byuser=UserType.from_neomodel(byuser_node),
                touser=UserType.from_neomodel(touser_node),
                reaction=users_review.reaction,
                vibe=users_review.vibe,
                title=users_review.title,
                content=users_review.content,
                file_id=users_review.file_id,
                is_deleted=users_review.is_deleted,
                connection=connection_instance
            )
        else:
            return cls(
                uid=users_review.uid,
                byuser=UserType.from_neomodel(byuser_node),
                touser=UserType.from_neomodel(touser_node),
                reaction=users_review.reaction,
                vibe=users_review.vibe,
                title=users_review.title,
                content=users_review.content,
                file_id=users_review.file_id,
                is_deleted=users_review.is_deleted,
                
            )  # Return None if no common connection is found


class ExperienceNonProfileType(ObjectType):
     uid = graphene.String()
     what = graphene.String()
     description = graphene.String()
     created_on = graphene.DateTime()
     from_source = graphene.String()
     from_date = graphene.DateTime()
     to_date = graphene.DateTime()
     file_id =graphene.List(graphene.String)
     file_url=graphene.List(FileDetailType)
     
     @classmethod
     def from_neomodel(cls, experience):
        if isinstance(experience, Experience):
            return cls(
                uid = experience.uid,
                what = experience.what,
                description = experience.description,
                created_on = experience.created_on,
                from_source = experience.from_source,
                from_date = experience.from_date,
                to_date = experience.to_date,
                file_id = experience.file_id,
                file_url = (
                    [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) 
                    for file_id in experience.file_id] if experience.file_id else None
                )
                
            )
        else:
            created_on_unix=experience.get('created_on')
            created_on=datetime.fromtimestamp(created_on_unix)
            from_date_unix=experience.get('from_date')
            from_date=datetime.fromtimestamp(from_date_unix)
            to_date_unix=experience.get('to_date')
            if to_date_unix:
                to_date=datetime.fromtimestamp(to_date_unix)
            else:
                to_date=None
            return cls(
                uid = experience.get('uid'),
                what = experience.get('what'),
                description = experience.get('description'),
                created_on = created_on,
                from_source = experience.get('from_source'),
                from_date = from_date,
                to_date = to_date,
                file_id = experience.get('file_id'),
                file_url = (
                    [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) 
                    for file_id in experience.get('file_id', [])] if experience.get('file_id') else None
                )

            )


class DeleteTypeEnum(graphene.Enum):
    DEACTIVATION = "deactivation"
    DELETE = "delete"

class VibeRangeCountType(ObjectType):
    lessthen1 = graphene.Int()
    lessthen2 = graphene.Int()
    lessthen3 = graphene.Int()
    lessthen4 = graphene.Int()
    lessthen5 = graphene.Int()

class CustomUserReviewType(ObjectType):
    reaction = graphene.String()
    count = graphene.Int()
    average_vibe = graphene.Float()
    vibe_range_count = graphene.Field(VibeRangeCountType)

class UserVibeRepoType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)  # Assuming UserType is already defined
    category = graphene.String()
    custom_value = graphene.Float()
    created_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, user_vibe_repo):
        return cls(
            uid=user_vibe_repo.uid,
            user=UserType.from_neomodel(user_vibe_repo.user.single()) if user_vibe_repo.user.single() else None,
            category=user_vibe_repo.category,
            custom_value=user_vibe_repo.custom_value,
            created_at=user_vibe_repo.created_at,
        )
    


class ConnectionStatsType(graphene.ObjectType):
    uid = graphene.String()
    received_connections_count = graphene.Int()
    accepted_connections_count = graphene.Int()
    rejected_connections_count = graphene.Int()
    sent_connections_count = graphene.Int()
    inner_circle_count = graphene.Int()
    outer_circle_count = graphene.Int()
    universal_circle_count = graphene.Int()

    @classmethod
    def from_neomodel(cls, connection_stat):
        return cls(
            uid=connection_stat.uid,
            received_connections_count=connection_stat.received_connections_count or 0,
            accepted_connections_count=connection_stat.accepted_connections_count or 0,
            rejected_connections_count=connection_stat.rejected_connections_count or 0,
            sent_connections_count=connection_stat.sent_connections_count or 0,
            inner_circle_count=connection_stat.inner_circle_count or 0,
            outer_circle_count=connection_stat.outer_circle_count or 0,
            universal_circle_count=connection_stat.universal_circle_count or 0
        )


class ProfileNoUserType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()
    bio = graphene.String()
    designation = graphene.String()
    worksat = graphene.String()
    phone_number = graphene.String()
    born = graphene.DateTime()
    dob = graphene.DateTime()
    school = graphene.String()
    college = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic=graphene.Field(FileDetailType)

    onboarding_status = graphene.List(lambda:OnboardingStatusNonProfileType)
    contact_info = graphene.List(lambda:ContactInfoTypeNoProfile)
    score = graphene.Field(lambda:ScoreNonProfileType)
    interest = graphene.List(lambda:InterestNonProfileType)
    achievement=graphene.List(lambda:AchievementNonProfileType)
    experience=graphene.List(lambda:ExperienceNonProfileType)
    skill=graphene.List(lambda:SkillNonProfileType)
    education=graphene.List(lambda:EducationNonProfileType)
    

    @classmethod


    def from_neomodel(cls, profile):
        return cls(
            uid=profile.uid,
            user_id=profile.user_id,
            gender=profile.gender,
            device_id=profile.device_id,
            fcm_token=profile.fcm_token,
            bio=profile.bio,
            designation=profile.designation,
            worksat=profile.worksat,
            phone_number=profile.phone_number,
            born=profile.born,
            dob=profile.dob,
            school=profile.school,
            college=profile.college,
            lives_in=profile.lives_in,
            profile_pic_id=profile.profile_pic_id,
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile.profile_pic_id)) if profile.profile_pic_id else None,
            onboarding_status=[OnboardingStatusNonProfileType.from_neomodel(status) for status in profile.onboarding],
            contact_info=[ContactInfoTypeNoProfile.from_neomodel(contact) for contact in profile.contactinfo],
            score=ScoreNonProfileType.from_neomodel(profile.score.single()) if profile.score.single() else None,
            interest=[InterestNonProfileType.from_neomodel(interest) for interest in profile.interest],
            achievement=[AchievementNonProfileType.from_neomodel(achievement) for achievement in profile.achievement],
            experience=[ExperienceNonProfileType.from_neomodel(experience) for experience in profile.experience],
            skill=[SkillNonProfileType.from_neomodel(skill) for skill in profile.skill],
            education=[EducationNonProfileType.from_neomodel(education) for education in profile.education]
        )

class CircleUserType(graphene.ObjectType):
    uid = graphene.String()
    relation = graphene.String()
    sub_relation=graphene.String()
    circle_type = graphene.String()
    

    @classmethod
    def from_neomodel(cls, circle):
        uid = circle.get('uid')
        relation = circle.get('relation')
        circle_type = circle.get('circle_type')
        sub_relation = circle.get('sub_relation')
        
        # NOTE:- Review and optimisation required
        if sub_relation:
            return cls(
                uid=uid,
                sub_relation=sub_relation,
                circle_type=circle_type,
                relation=RELATIONUTILLS.get_relation_from_subrelation(sub_relation),
                
            )
        elif relation:
            return cls(
                uid=uid,
                sub_relation=sub_relation,
                circle_type=circle_type,
                relation=RELATIONUTILLS.get_relation_from_subrelation(relation),
                
            )


    
class ConnectionNoUserType(ObjectType):
    uid = graphene.String()
    connection_status = graphene.String()
    timestamp = graphene.DateTime()
    circle = graphene.Field(CircleUserType)

    @classmethod
    def from_neomodel(cls, connection_node,circle_node):
        uid = connection_node.get('uid')
        connection_status = connection_node.get('connection_status')
        
        return cls(
                uid=uid,  # Access properties using the dictionary-like interface
                connection_status=connection_status,
                circle=CircleUserType.from_neomodel(circle_node) 
            )
       
class InviteListType(ObjectType):
    contact = graphene.List(graphene.String)

    @classmethod
    def from_neomodel(cls, contct):
        return cls(
            contact=contct, 
        )


# optimisation and review required
class ProfileDetailsVibeType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()
    bio = graphene.String()
    designation = graphene.String()
    worksat = graphene.String()
    phone_number = graphene.String()
    born = graphene.DateTime()
    dob = graphene.DateTime()
    school = graphene.String()
    college = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic=graphene.Field(FileDetailType)
    cover_image_id = graphene.String()
    cover_image=graphene.Field(FileDetailType)
    user = graphene.Field(UserType)
    city = graphene.String()
    state = graphene.String()
    onboarding_status = graphene.List(lambda:OnboardingStatusNonProfileType)
    contact_info = graphene.List(lambda:ContactInfoTypeNoProfile)
    score = graphene.Field(lambda:ScoreNonProfileType)
    interest = graphene.List(lambda:InterestNonProfileType)
    achievement=graphene.List(lambda:AchievementNonProfileType)
    experience=graphene.List(lambda:ExperienceNonProfileType)
    skill=graphene.List(lambda:SkillNonProfileType)
    education=graphene.List(lambda:EducationNonProfileType)
    profile_vibe_list=graphene.List(lambda:VibeProfileListType)
    user_review_list=graphene.List(lambda:UsersReviewType)
    my_review_list=graphene.List(lambda:UsersReviewType)
    vibes_count = graphene.Int()
    post_count = graphene.Int()
    

    @classmethod


    def from_neomodel(cls, profile,user_node):
        profile_reaction_manager = ProfileReactionManager.objects.filter(profile_uid=profile.uid).first()

        
        if profile_reaction_manager:
            all_reactions = profile_reaction_manager.profile_vibe
            sorted_reactions = sorted(all_reactions, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)
            vibes_count = sum(reaction.get('vibes_count', 0) for reaction in all_reactions)

        else:
            sorted_reactions = IndividualVibe.objects.all()[:10]
            vibes_count = 0

        try:
            user_for_posts = profile.user.single() if profile.user.single() else user_node
            post_count = len([post for post in user_for_posts.post.all() if not post.is_deleted]) if user_for_posts else 0
        except Exception:
            post_count = 0    

        return cls(
            uid=profile.uid,
            user_id=profile.user_id,
            gender=profile.gender,
            device_id=profile.device_id,
            fcm_token=profile.fcm_token,
            bio=profile.bio,
            designation=profile.designation,
            worksat=profile.worksat,
            phone_number=profile.phone_number,
            born=profile.born,
            dob=profile.dob,
            school=profile.school,
            college=profile.college,
            lives_in=profile.lives_in,
            profile_pic_id=profile.profile_pic_id,
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile.profile_pic_id)) if profile.profile_pic_id else None,
            cover_image_id=profile.cover_image_id,
            cover_image=FileDetailType(**generate_presigned_url.generate_file_info(profile.cover_image_id)) if profile.cover_image_id else None,
            user=UserType.from_neomodel(profile.user.single()) if profile.user.single() else None,
            city=profile.city,
            state=profile.state,
            onboarding_status=[OnboardingStatusNonProfileType.from_neomodel(status) for status in profile.onboarding],
            contact_info=[ContactInfoTypeNoProfile.from_neomodel(contact) for contact in profile.contactinfo],
            score=ScoreNonProfileType.from_neomodel(profile.score.single()) if profile.score.single() else None,
            interest=[InterestNonProfileType.from_neomodel(interest) for interest in profile.interest],
            achievement=[AchievementNonProfileType.from_neomodel(achievement) for achievement in profile.achievement],
            experience=[ExperienceNonProfileType.from_neomodel(experience) for experience in profile.experience],
            skill=[SkillNonProfileType.from_neomodel(skill) for skill in profile.skill],
            education=[EducationNonProfileType.from_neomodel(education) for education in profile.education],
            profile_vibe_list=[VibeProfileListType.from_neomodel(vibe) for vibe in sorted_reactions],
            user_review_list=[UsersReviewType.from_neomodel(review) for review in profile.user.single().user_review],
            my_review_list = [
                UsersReviewType.from_neomodel(review)
                for review in sorted(
                    profile.user.single().user_review,
                    key=lambda r: r.timestamp,  # Assuming there's a timestamp attribute to sort by
                    reverse=True
                )
                if review.byuser.single().uid == user_node.uid
            ],
            vibes_count=vibes_count,
            post_count=post_count,
        )
    

class VibeProfileListType(ObjectType):
        vibe_id=graphene.String()
        vibe_name=graphene.String()
        vibe_cumulative_score=graphene.String()

        @classmethod
        def from_neomodel(cls, vibe):
            # print(vibe['vibes_id'])
            if isinstance(vibe, dict):
                return cls(
                    vibe_id=vibe.get("vibes_id"),  # Use dictionary access
                    vibe_name=vibe.get("vibes_name"),
                    vibe_cumulative_score=vibe.get("cumulative_vibe_score")  # Use dictionary access
                )
            else:
                # Assume it's an IndividualVibe object
                return cls(
                    vibe_id=vibe.id,  # Use the attribute directly
                    vibe_name=vibe.name_of_vibe,
                    vibe_cumulative_score="0"  # Use the attribute directly
                )
            



class MatrixInfoType(graphene.ObjectType):
    matrix_user_id = graphene.String(required=True)


class MatrixUserType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name=graphene.String()
    last_name=graphene.String()
    user_type=graphene.String()
    created_at = graphene.DateTime()
    created_by = graphene.String()
    updated_at = graphene.DateTime()
    updated_by = graphene.String()
    matrix_info = graphene.Field(MatrixInfoType)

    @classmethod
    def from_neomodel(cls, user,matrix_info=None):
        return cls(
            uid=user.uid,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
            created_at=user.created_at,
            created_by=user.created_by,
            updated_at=user.updated_at,
            updated_by=user.updated_by,
            matrix_info=matrix_info,
        )
class ProfileInfoType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()
    bio = graphene.String()
    designation = graphene.String()
    worksat = graphene.String()
    phone_number = graphene.String()
    born = graphene.DateTime()
    dob = graphene.DateTime()
    school = graphene.String()
    college = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic=graphene.Field(FileDetailType)
    cover_image_id = graphene.String()
    cover_image=graphene.Field(FileDetailType)
    city = graphene.String()
    state = graphene.String()
    user = graphene.Field(UserType)
    onboarding_status = graphene.List(lambda:OnboardingStatusNonProfileType)
    score = graphene.Field(lambda:ScoreNonProfileType)
    interest = graphene.List(lambda:InterestNonProfileType)
    achievement=graphene.List(lambda:AchievementNonProfileType)
    experience=graphene.List(lambda:ExperienceNonProfileType)
    skill=graphene.List(lambda:SkillNonProfileType)
    education=graphene.List(lambda:EducationNonProfileType)
    vibes_count = graphene.Int()
    post_count = graphene.Int()
    total_vibes_received = graphene.Int()
    community_count = graphene.Int()
    connection_count = graphene.Int()
    

    @classmethod


    def from_neomodel(cls,profile=None,user=None,onboardingStatus=None,score=None,interest_node=None,achievement_node=None,education_node=None,skill_node=None,experience_node=None, post_count=0, community_count=0,connection_count=0):
        born_unix=profile.get('born')
        born=None
        dob=None
        if born_unix:
            born=datetime.fromtimestamp(born_unix)
        dob_unix=profile.get('created_at')
        if dob_unix:
            dob=datetime.fromtimestamp(dob_unix)

        profile_uid = profile.get('uid')
        user_uid = user.get('uid')
        vibes_count = cls._get_profile_vibes_count(profile_uid)
 
      
    

       
        return cls(
            uid = profile.get('uid'),
            user_id = profile.get('user_id'),
            gender = profile.get('gender'),
            device_id = profile.get('device_id'),
            fcm_token = profile.get('fcm_token'),
            bio = profile.get('bio'),
            designation = profile.get('designation'),
            worksat = profile.get('worksat'),
            phone_number = profile.get('phone_number'),
            born = born,
            dob = dob,
            school = profile.get('school'),
            college = profile.get('college'),
            lives_in = profile.get('lives_in'),
            profile_pic_id = profile.get('profile_pic_id'),
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile.get('profile_pic_id')))if profile.get('profile_pic_id') else None,
            cover_image_id = profile.get('cover_image_id'),
            cover_image=FileDetailType(**generate_presigned_url.generate_file_info(profile.get('cover_image_id')))if profile.get('cover_image_id') else None,
            user=UserType.from_neomodel(user) if user else None,
            city=profile.get('city'),
            state=profile.get('state'),
            onboarding_status=[OnboardingStatusNonProfileType.from_neomodel(onboardingStatus)],
            score=ScoreNonProfileType.from_neomodel(score) if score else None,
            interest=[InterestNonProfileType.from_neomodel(interest) for interest in interest_node] if interest_node else [],
            achievement=[AchievementNonProfileType.from_neomodel(achievement) for achievement in achievement_node] if achievement_node else [],
            experience=[ExperienceNonProfileType.from_neomodel(experience) for experience in experience_node] if experience_node else [],
            skill=[SkillNonProfileType.from_neomodel(skill) for skill in skill_node] if skill_node else [],
            education=[EducationNonProfileType.from_neomodel(education) for education in education_node] if education_node else [],
            vibes_count=vibes_count,
            post_count=post_count,
            community_count=community_count,
            connection_count=connection_count, 
        )
    
    @staticmethod
    def _get_profile_vibes_count(profile_uid):
        """Only profile vibes"""
        try:
            profile_reaction_manager = ProfileReactionManager.objects.get(profile_uid=profile_uid)
            return sum(reaction['vibes_count'] for reaction in profile_reaction_manager.profile_vibe)
        except ProfileReactionManager.DoesNotExist:
            return 0


class BackProfileListType(ObjectType):
    vibe_id = graphene.String()
    vibe_name = graphene.String()
    vibes_count = graphene.String()
    vibe_cumulative_score = graphene.String()

    @classmethod
    def from_neomodel(cls, profile_uid):
        profile_reaction_manager = BackProfileReactionManager.objects.filter(profile_uid=profile_uid).first()

        if not profile_reaction_manager or not profile_reaction_manager.profile_vibe:
            vibe_list=IndividualVibe.objects.all()[:10]
            return [ cls(
                vibe_id=vibe.id,  # Use the attribute directly
                vibe_name=vibe.name_of_vibe,
                vibes_count="0",
                vibe_cumulative_score="0"  # Use the attribute directly
            )
            for vibe in vibe_list
            ]

        else:
            all_reactions = profile_reaction_manager.profile_vibe
            # filtered_vibes = [vibe for vibe in all_reactions if vibe.get('vibes_count', 0) != 0]

            # Sort the filtered vibes by cumulative_vibe_score in descending order
            vibes = sorted(all_reactions, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)


            # Collect all vibe data into a list
            return [
                cls(
                    vibe_id=vibe.get('vibes_id'),
                    vibe_name=vibe.get('vibes_name'),
                    vibes_count=str(vibe.get('vibes_count', 0)),  # Ensure it is a string
                    vibe_cumulative_score=str(round(vibe.get('cumulative_vibe_score', 0), 1)),  # Round and convert
                )
                for vibe in vibes
            ]
        


class ProfileDataType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()
    bio = graphene.String()
    designation = graphene.String()
    worksat = graphene.String()
    phone_number = graphene.String()
    born = graphene.DateTime()
    dob = graphene.DateTime()
    school = graphene.String()
    college = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic=graphene.Field(FileDetailType)

    @classmethod

    def from_neomodel(cls, profile):
        return cls(
            uid=profile.uid,
            user_id=profile.user_id,
            gender=profile.gender,
            device_id=profile.device_id,
            fcm_token=profile.fcm_token,
            bio=profile.bio,
            designation=profile.designation,
            worksat=profile.worksat,
            phone_number=profile.phone_number,
            born=profile.born,
            dob=profile.dob,
            school=profile.school,
            college=profile.college,
            lives_in=profile.lives_in,
            profile_pic_id=profile.profile_pic_id,
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile.profile_pic_id)),
            
        )

class ProfileDataTypeV2(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()
    bio = graphene.String()
    designation = graphene.String()
    worksat = graphene.String()
    phone_number = graphene.String()
    born = graphene.DateTime()
    dob = graphene.DateTime()
    school = graphene.String()
    college = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic=graphene.Field(FileDetailType)

    @classmethod

    def from_neomodel(cls, profile_data):
        return cls(
            uid=profile_data.get('uid'),
            user_id=profile_data.get('user_id'),
            gender=profile_data.get('gender'),
            device_id=profile_data.get('device_id'),
            fcm_token=profile_data.get('fcm_token'),
            bio=profile_data.get('bio'),
            designation=profile_data.get('designation'),
            worksat=profile_data.get('worksat'),
            phone_number=profile_data.get('phone_number'),
            born=profile_data.get('born'),
            dob=profile_data.get('dob'),
            school=profile_data.get('school'),
            college=profile_data.get('college'),
            lives_in=profile_data.get('lives_in'),
            profile_pic_id=profile_data.get('profile_pic_id'),
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile_data.get('profile_pic_id'))),
            
        )



class UserInfoType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name=graphene.String()
    last_name=graphene.String()
    user_type=graphene.String()
    profile = graphene.Field(ProfileDataType)
    

    @classmethod
    def from_neomodel(cls, user):
        if isinstance(user, Users):
            return cls(
                uid=user.uid,
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                user_type=user.user_type,
                profile=ProfileDataType.from_neomodel(user.profile.single()) if user.profile.single() else None,
                
                
            )

class UserInfoTypeV2(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name=graphene.String()
    last_name=graphene.String()
    user_type=graphene.String()
    profile = graphene.Field(ProfileDataTypeV2)
    

    @classmethod
    def from_neomodel(cls, user_data, profile_data):
            return cls(
                uid=user_data.get('uid'),
                user_id=user_data.get('user_id'),
                username=user_data.get('username'),
                email=user_data.get('email'),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                user_type=user_data.get('user_type'),
                profile=ProfileDataTypeV2.from_neomodel(profile_data),  
            )


class BackProfileReviewType(ObjectType):
    uid = graphene.String()
    byuser = graphene.Field(UserInfoType)  # Assuming UserType is already defined
    touser = graphene.Field(UserInfoType)  # Assuming UserType is already defined
    reaction = graphene.String()
    vibe = graphene.Float()
    title = graphene.String()
    content = graphene.String()
    file_id = graphene.String()
    is_deleted = graphene.Boolean()
    connection=graphene.Field(ConnectionNoUserType)

    @classmethod
    def from_neomodel(cls, users_review):
        
        byuser_node = users_review.byuser.single()
        touser_node = users_review.touser.single()

        if not byuser_node or not touser_node:
            return None

        # Cypher query to find a common connection node between byuser and touser
        query = """
        MATCH (byuser:Users {uid: $byuser_uid})-[c1:HAS_CONNECTION]->(conn:Connection)
        MATCH (conn)-[c3:HAS_CIRCLE]->(circle:Circle)
        MATCH (touser:Users {uid: $touser_uid})-[c2:HAS_CONNECTION]->(conn)
        RETURN conn, circle
        """
        params = {
            "byuser_uid": byuser_node.uid,
            "touser_uid": touser_node.uid,
        }
        result = db.cypher_query(query, params)
        
        if result and result[0]: 
            
            connection_node = result[0][0][0]
            circle_node=result[0][0][1]
            
            connection_instance = ConnectionNoUserType.from_neomodel(connection_node,circle_node)
            
            return cls(
                uid=users_review.uid,
                byuser=UserInfoType.from_neomodel(byuser_node),
                touser=UserInfoType.from_neomodel(touser_node),
                reaction=users_review.reaction,
                vibe=users_review.vibe,
                title=users_review.title,
                content=users_review.content,
                file_id=users_review.file_id,
                is_deleted=users_review.is_deleted,
                connection=connection_instance
            )
        else:
            return cls(
                uid=users_review.uid,
                byuser=UserInfoType.from_neomodel(byuser_node),
                touser=UserInfoType.from_neomodel(touser_node),
                reaction=users_review.reaction,
                vibe=users_review.vibe,
                title=users_review.title,
                content=users_review.content,
                file_id=users_review.file_id,
                is_deleted=users_review.is_deleted,
                
            )  # Return None if no common connection is found

class ProfileDataReactionType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserInfoType)
    reaction = graphene.String()
    vibe = graphene.Float()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, like):
        return cls(
            uid=like.uid,
            user=UserInfoType.from_neomodel(like.user.single()) if like.user.single() else None,
            reaction=like.reaction,
            vibe=like.vibe,
            timestamp=like.timestamp,
            is_deleted=like.is_deleted
        )


class ProfileDataCommentType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserInfoType)
    comment = graphene.String()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, comment_data):
        return cls(
            uid=comment_data.uid,
            user=UserInfoType.from_neomodel(comment_data.user.single()) if comment_data.user.single() else None,
            comment=comment_data.content,
            timestamp=comment_data.timestamp,
            is_deleted=comment_data.is_deleted
        )


class ProfileDataCommentTypeV2(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserInfoTypeV2)
    comment = graphene.String()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, comment_data, user_data, profile_data):

        timestamp_val = comment_data.get('timestamp')
        timestamp = datetime.fromtimestamp(timestamp_val) if isinstance(timestamp_val, (int, float)) else None

        return cls(
            uid=comment_data.get('uid'),
            user=UserInfoTypeV2.from_neomodel(user_data,profile_data),
            comment=comment_data.get('content'),
            timestamp=timestamp,
            is_deleted=comment_data.get('is_deleted')
        )

class AchievementType(ObjectType):
     uid = graphene.String()
     what = graphene.String()
     description = graphene.String()
     from_source = graphene.String()
     from_date = graphene.DateTime()
     to_date = graphene.DateTime()
     created_on = graphene.DateTime()
     is_deleted = graphene.Boolean()
     file_id =graphene.List(graphene.String)
     file_url=graphene.List(FileDetailType)
     category = graphene.String()
     comment_count=graphene.String()
     vibe_count=graphene.String()
     vibe_list=graphene.List(lambda: ProfileDataVibeListType)
     comment=graphene.List(lambda:ProfileDataCommentType)
     like=graphene.List(lambda:ProfileDataReactionType)
     @classmethod
     def from_neomodel(cls, achievement):
        return cls(
            uid=achievement.uid,
            what = achievement.what,
            description = achievement.description,
            from_source = achievement.from_source,
            created_on = achievement.created_on,
            from_date = achievement.from_date,
            to_date = achievement.to_date,
            is_deleted=achievement.is_deleted,
            file_id=achievement.file_id,
            file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in achievement.file_id] if achievement.file_id else None),
            category="achievement",
            comment_count= len(achievement.comment.all()),
            vibe_count= len(achievement.like.all()),
            vibe_list=ProfileDataVibeListType.from_neomodel(achievement.uid,"achievement"),
            comment=[ProfileDataCommentType.from_neomodel(comment) for comment in achievement.comment[:2]],
            like=[ProfileDataReactionType.from_neomodel(like) for like in achievement.like[:2]],
        )
     
class EducationType(ObjectType):
    uid = graphene.String()
    what = graphene.String()
    from_date = graphene.DateTime()
    to_date = graphene.DateTime()
    field_of_study = graphene.String()
    from_source = graphene.String()
    created_on = graphene.DateTime()
    is_deleted = graphene.Boolean()
    file_id = graphene.List(graphene.String)
    file_url = graphene.List(FileDetailType)
    category = graphene.String()
    comment_count=graphene.String()
    vibe_count=graphene.String()
    vibe_list=graphene.List(lambda: ProfileDataVibeListType)
    comment=graphene.List(lambda:ProfileDataCommentType)
    like=graphene.List(lambda:ProfileDataReactionType)

    @classmethod
    def from_neomodel(cls, education):
        return cls(
            uid=education.uid,
            what=education.what,
            from_date=education.from_date,
            to_date=education.to_date,
            field_of_study=education.field_of_study,
            from_source=education.from_source,
            created_on=education.created_on,
            is_deleted=education.is_deleted,
            file_id=education.file_id,
            file_url=(
                [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in education.file_id]
                if education.file_id else None
            ),
            category = "education",
            comment_count=len(education.comment.all()),
            vibe_count=len(education.like.all()),
            vibe_list=ProfileDataVibeListType.from_neomodel(education.uid,"education"),
            comment=[ProfileDataCommentType.from_neomodel(comment) for comment in education.comment[:2]],
            like=[ProfileDataReactionType.from_neomodel(like) for like in education.like[:2]],
        )

class ExperienceType(ObjectType):
    uid = graphene.String()
    what = graphene.String()
    from_source = graphene.String()
    from_date = graphene.DateTime()
    to_date = graphene.DateTime()
    description = graphene.String()
    created_on = graphene.DateTime()
    is_deleted = graphene.Boolean()
    file_id = graphene.List(graphene.String)
    file_url = graphene.List(FileDetailType)
    category = graphene.String()
    comment_count=graphene.String()
    vibe_count=graphene.String()
    vibe_list=graphene.List(lambda: ProfileDataVibeListType)
    comment=graphene.List(lambda:ProfileDataCommentType)
    like=graphene.List(lambda:ProfileDataReactionType)

    @classmethod
    def from_neomodel(cls, experience):
        return cls(
            uid=experience.uid,
            what=experience.what,
            from_source=experience.from_source,
            from_date=experience.from_date,
            to_date=experience.to_date,
            description=experience.description,
            created_on=experience.created_on,
            is_deleted=experience.is_deleted,
            file_id=experience.file_id,
            file_url=(
                [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in experience.file_id]
                if experience.file_id else None
            ),
            category="experience",
            comment_count=len(experience.comment.all()),
            vibe_count= len(experience.like.all()),
            vibe_list=ProfileDataVibeListType.from_neomodel(experience.uid,"experience"),
            comment=[ProfileDataCommentType.from_neomodel(comment) for comment in experience.comment[:2]],
            like=[ProfileDataReactionType.from_neomodel(like) for like in experience.like[:2]],
        )

class SkillType(ObjectType):
    uid = graphene.String()
    what = graphene.String()
    from_source = graphene.String()
    from_date = graphene.DateTime()
    to_date = graphene.DateTime()
    created_on = graphene.DateTime()
    is_deleted = graphene.Boolean()
    file_id = graphene.List(graphene.String)
    file_url = graphene.List(FileDetailType)
    category = graphene.String()
    comment_count=graphene.String()
    vibe_count=graphene.String()
    vibe_list=graphene.List(lambda: ProfileDataVibeListType)
    comment=graphene.List(lambda:ProfileDataCommentType)
    like=graphene.List(lambda:ProfileDataReactionType)

    @classmethod
    def from_neomodel(cls, skill):
        return cls(
            uid=skill.uid,
            what=skill.what,
            from_source=skill.from_source,
            from_date=skill.from_date,
            to_date=skill.to_date,
            created_on=skill.created_on,
            is_deleted=skill.is_deleted,
            file_id=skill.file_id,
            file_url=(
                [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in skill.file_id]
                if skill.file_id else None
            ),
            category = "skill",
            comment_count=len(skill.comment.all()),
            vibe_count=len(skill.like.all()),
            vibe_list=ProfileDataVibeListType.from_neomodel(skill.uid,"skill"),
            comment=[ProfileDataCommentType.from_neomodel(comment) for comment in skill.comment[:2]],
            like=[ProfileDataReactionType.from_neomodel(like) for like in skill.like[:2]],
        )


class ProfileDataVibeListType(ObjectType):
    vibe_id = graphene.String()
    vibe_name = graphene.String()
    vibes_count = graphene.String()
    vibe_cumulative_score = graphene.String()

    @classmethod
    def from_neomodel(cls, uid, category):
        """
        Fetch and return vibes based on the category (e.g., 'achievement', 'education', etc.).
        """
        category_map = {
            "achievement": AchievementReactionManager,
            "education": EducationReactionManager,
            "skill": SkillReactionManager,
            "experience": ExperienceReactionManager
        }
    
        if category not in category_map:
            raise ValueError("Invalid category. Choose from 'achievement', 'education', 'skill', or 'experience'.")

        reaction_manager_model = category_map[category]

        category_uid_field = f"{category}_uid"
        reaction_manager = reaction_manager_model.objects.filter(**{category_uid_field: uid}).first()
        
        vibes_field_mapping = {
                    "education": "education_vibe",
                    "achievement": "achievement_vibe",
                    "skill": "skill_vibe",
                    "experience": "experience_vibe",
                }
                
        vibes_field = vibes_field_mapping.get(category, "uid")

        if not reaction_manager or not getattr(reaction_manager, vibes_field, None):
            vibe_list = IndividualVibe.objects.all()[:10]
            return [
                cls(
                    vibe_id=str(vibe.id),
                    vibe_name=vibe.name_of_vibe,
                    vibes_count="0",
                    vibe_cumulative_score="0"
                )
                for vibe in vibe_list
            ]

        all_reactions = getattr(reaction_manager, vibes_field, None)
        vibes = sorted(all_reactions, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)

        return [
            cls(
                vibe_id=str(vibe.get('vibes_id')),
                vibe_name=vibe.get('vibes_name'),
                vibes_count=str(vibe.get('vibes_count', 0)),
                vibe_cumulative_score=str(round(vibe.get('cumulative_vibe_score', 0), 1))
            )
            for vibe in vibes
        ]



class AchievementOnlyType(ObjectType):
     uid = graphene.String()
     what = graphene.String()
     description = graphene.String()
     from_source = graphene.String()
     from_date = graphene.DateTime()
     to_date = graphene.DateTime()
     created_on = graphene.DateTime()
     is_deleted = graphene.Boolean()
     file_id =graphene.List(graphene.String)
     file_url=graphene.List(FileDetailType)
     category = graphene.String()
     
     @classmethod
     def from_neomodel(cls, achievement):
        return cls(
            uid=achievement.uid,
            what = achievement.what,
            description = achievement.description,
            from_source = achievement.from_source,
            created_on = achievement.created_on,
            from_date = achievement.from_date,
            to_date = achievement.to_date,
            is_deleted=achievement.is_deleted,
            file_id=achievement.file_id,
            file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in achievement.file_id] if achievement.file_id else None),
            category="achievement",
        )
     
class EducationOnlyType(ObjectType):
    uid = graphene.String()
    what = graphene.String()
    field_of_study = graphene.String()
    from_source = graphene.String()
    from_date = graphene.DateTime()
    to_date = graphene.DateTime()
    created_on = graphene.DateTime()
    is_deleted = graphene.Boolean()
    file_id = graphene.List(graphene.String)
    file_url = graphene.List(FileDetailType)
    category = graphene.String()
    

    @classmethod
    def from_neomodel(cls, education):
        return cls(
            uid=education.uid,
            what=education.what,
            field_of_study=education.field_of_study,
            from_source=education.from_source,
            created_on=education.created_on,
            from_date = education.from_date,
            to_date = education.to_date,
            is_deleted=education.is_deleted,
            file_id=education.file_id,
            file_url=(
                [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in education.file_id]
                if education.file_id else None
            ),
            category = "education",
            
        )

class ExperienceOnlyType(ObjectType):
    uid = graphene.String()
    what = graphene.String()
    from_source = graphene.String()
    from_date = graphene.DateTime()
    to_date = graphene.DateTime()
    description = graphene.String()
    created_on = graphene.DateTime()
    is_deleted = graphene.Boolean()
    file_id = graphene.List(graphene.String)
    file_url = graphene.List(FileDetailType)
    category = graphene.String()
    

    @classmethod
    def from_neomodel(cls, experience):
        return cls(
            uid=experience.uid,
            what=experience.what,
            from_source=experience.from_source,
            created_on=experience.created_on,
            from_date = experience.from_date,
            to_date = experience.to_date,
            description=experience.description,
            is_deleted=experience.is_deleted,
            file_id=experience.file_id,
            file_url=(
                [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in experience.file_id]
                if experience.file_id else None
            ),
            category="experience",
            
        )

class SkillOnlyType(ObjectType):
    uid = graphene.String()
    what = graphene.String()
    from_source = graphene.String()
    from_date = graphene.DateTime()
    to_date = graphene.DateTime()
    created_on = graphene.DateTime()
    is_deleted = graphene.Boolean()
    file_id = graphene.List(graphene.String)
    file_url = graphene.List(FileDetailType)
    category = graphene.String()
    

    @classmethod
    def from_neomodel(cls, skill):
        return cls(
            uid=skill.uid,
            what=skill.what,
            from_source=skill.from_source,
            created_on=skill.created_on,
            from_date = skill.from_date,
            to_date = skill.to_date,
            is_deleted=skill.is_deleted,
            file_id=skill.file_id,
            file_url=(
                [FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in skill.file_id]
                if skill.file_id else None
            ),
            category = "skill",
            
        )

class UserProfileDataType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()
    bio = graphene.String()
    designation = graphene.String()
    worksat = graphene.String()
    phone_number = graphene.String()
    born = graphene.DateTime()
    dob = graphene.DateTime()
    school = graphene.String()
    college = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic=graphene.Field(FileDetailType)
    user = graphene.Field(UserInfoType)
    city = graphene.String()
    state = graphene.String()

    
    achievement=graphene.List(lambda:AchievementOnlyType)
    experience=graphene.List(lambda:ExperienceOnlyType)
    skill=graphene.List(lambda:SkillOnlyType)
    education=graphene.List(lambda:EducationOnlyType)
    
    vibes_count = graphene.Int()
    post_count = graphene.Int()
    total_vibes_received = graphene.Int()
    community_count = graphene.Int()
    connection_count = graphene.Int()
    

    @classmethod


    def from_neomodel(cls, profile):
        user_node = profile.user.single() if profile.user else None
        
        # Calculate statistics efficiently
        vibes_count = cls._get_profile_vibes_count(profile.uid)
        post_count = cls._get_user_post_count(user_node)
        total_vibes_received = cls._get_total_vibes_received(user_node, profile.uid)
        community_count = cls._get_user_community_count(user_node)
        connection_count = cls._get_user_connection_count(user_node)

        return cls(
            uid=profile.uid,
            user_id=profile.user_id,
            gender=profile.gender,
            device_id=profile.device_id,
            fcm_token=profile.fcm_token,
            bio=profile.bio,
            designation=profile.designation,
            worksat=profile.worksat,
            phone_number=profile.phone_number,
            born=profile.born,
            dob=profile.dob,
            school=profile.school,
            college=profile.college,
            lives_in=profile.lives_in,
            profile_pic_id=profile.profile_pic_id,
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile.profile_pic_id)),
            user=UserInfoType.from_neomodel(profile.user.single()) if profile.user.single() else None,
            city=profile.city,
            state=profile.state,
            achievement=[AchievementOnlyType.from_neomodel(achievement) for achievement in profile.achievement],
            experience=[ExperienceOnlyType.from_neomodel(experience) for experience in profile.experience],
            skill=[SkillOnlyType.from_neomodel(skill) for skill in profile.skill],
            education=[EducationOnlyType.from_neomodel(education) for education in profile.education],
            vibes_count=vibes_count,
            post_count=post_count,
            total_vibes_received=total_vibes_received,
            community_count=community_count,
            connection_count=connection_count,
        )
        # ADD THESE STATIC METHODS to calculate statistics
    @staticmethod
    def _get_profile_vibes_count(profile_uid):
        """Get vibes count for the profile from ProfileReactionManager"""
        try:
            profile_reaction_manager = ProfileReactionManager.objects.get(profile_uid=profile_uid)
            return sum(reaction['vibes_count'] for reaction in profile_reaction_manager.profile_vibe)
        except ProfileReactionManager.DoesNotExist:
            return 0

    @staticmethod
    def _get_user_post_count(user_node):
        """Get total posts created by the user"""
        try:
            if user_node:
                return len([post for post in user_node.post.all() if not post.is_deleted])
            return 0
        except Exception:
            return 0

    @staticmethod
    def _get_total_vibes_received(user_node, profile_uid):
        """Get total vibes received from all sources (profile, posts, communities)"""
        total_vibes = 0
        
        # Profile vibes
        total_vibes += UserProfileDataType._get_profile_vibes_count(profile_uid)
        
        # Post vibes
        try:
            if user_node:
                posts = [post for post in user_node.post.all() if not post.is_deleted]
                for post in posts:
                    try:
                        post_reaction_manager = PostReactionManager.objects.get(post_uid=post.uid)
                        total_vibes += sum(reaction['vibes_count'] for reaction in post_reaction_manager.post_vibe)
                    except PostReactionManager.DoesNotExist:
                        continue
        except Exception:
            pass
        
        # Community vibes
        try:
            if user_node:
                communities = user_node.community.all()
                for community in communities:
                    try:
                        community_reaction_manager = CommunityReactionManager.objects.get(community_uid=community.uid)
                        total_vibes += sum(reaction['vibes_count'] for reaction in community_reaction_manager.community_vibe)
                    except CommunityReactionManager.DoesNotExist:
                        continue
        except Exception:
            pass
        
        return total_vibes

    @staticmethod
    def _get_user_community_count(user_node):
        """Get total communities created by the user"""
        try:
            if user_node:
                return len(user_node.community.all())
            return 0
        except Exception:
            return 0

    @staticmethod
    def _get_user_connection_count(user_node):
        """Get total connections for the user"""
        try:
            if user_node:
                # Count accepted connections
                connections = user_node.connection.all()
                return len([conn for conn in connections if hasattr(conn, 'connection_status') and conn.connection_status == 'Accepted'])
            return 0
        except Exception:
            return 0
