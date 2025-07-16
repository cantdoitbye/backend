import graphene
from graphene import ObjectType
from auth_manager.graphql.types import UserType,ProfileNoUserType,ProfileType,ConnectionStatsType
from graphene_django import DjangoObjectType
from auth_manager.models import Users
from connection.models import Relation, SubRelation
from connection.utils import relation
from auth_manager.Utils import generate_presigned_url
from connection.graphql.raw_queries import user_related_queries
from neomodel import db

class StatusEnum(graphene.Enum):
    RECEIVED = "Received"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"
    SENT="Sent"


class StatusSecondaryUserEnum(graphene.Enum):
    ACCEPTED = "Accepted"
    

class CircleTypeEnum(graphene.Enum):
    OUTER = "Outer"
    INNER = "Inner"
    UNIVERSAL = "Universal"


class CircleTypeEnumV2(graphene.Enum):
    OUTER = "Outer"
    INNER = "Inner"
    UNIVERSAL = "Universe"

class FileDetailType(graphene.ObjectType):
    url = graphene.String()
    file_extension = graphene.String()
    file_type = graphene.String()
    file_size = graphene.Int()

class ConnectionType(ObjectType):
    uid=graphene.String()
    receiver = graphene.Field(UserType)
    created_by = graphene.Field(UserType)
    connection_status = graphene.String()
    timestamp = graphene.DateTime()
    circle= graphene.Field(lambda:CircleType)

    @classmethod
    def from_neomodel(cls, connection):
        return cls(
            uid=connection.uid,
            receiver=UserType.from_neomodel(connection.receiver.single()) if connection.receiver.single() else None,
            created_by=UserType.from_neomodel(connection.created_by.single()) if connection.created_by.single() else None,
            circle=CircleType.from_neomodel(connection.circle.single()) if connection.circle.single() else None,
            connection_status=connection.connection_status,
            timestamp=connection.timestamp,
            
        )

class CircleType(graphene.ObjectType):
    uid = graphene.String()
    relation = graphene.String()
    circle_type = graphene.String()
    sub_relation = graphene.String()

    @classmethod
    def from_neomodel(cls, circle):
        #NOTE:- Review and optimisation required
        if circle.sub_relation:
            return cls(
                uid=circle.uid,
                sub_relation=circle.sub_relation,
                circle_type=circle.circle_type,
                relation=relation.get_relation_from_subrelation(circle.sub_relation),
                
            )
        elif circle.relation:
            return cls(
                uid=circle.uid,
                sub_relation=circle.sub_relation,
                circle_type=circle.circle_type,
                relation=relation.get_relation_from_subrelation(circle.relation),
                
            )

    

class CircleV2Type(graphene.ObjectType):
    uid = graphene.String()
    relation = graphene.String()
    circle_type = graphene.String()
    is_sub_relation = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, circle_v2_node):
        if not circle_v2_node:
            return None
        return cls(
            uid=circle_v2_node.get('uid') if circle_v2_node else None,
            relation=circle_v2_node.get('relation') if circle_v2_node.get('relation') else circle_v2_node.get('sub_relation') if circle_v2_node.get('sub_relation') else None,
            circle_type=circle_v2_node.get('circle_type') if circle_v2_node.get('circle_type') else None,
            is_sub_relation=circle_v2_node.get('relation') is None if circle_v2_node else None,
        )

class ConnectionV2Type(ObjectType):
    uid=graphene.String()
    user_id=graphene.String()
    username=graphene.String()
    email=graphene.String()
    first_name=graphene.String()
    last_name=graphene.String()
    user_type=graphene.String()
    profile=graphene.Field(lambda:ProfileForConnectedUserTypeV2)
    connection = graphene.Field(lambda: ConnectionConnectedUserType)

    

    @classmethod
    def from_neomodel(cls, connection_v2_node, user_uid=None):
        if connection_v2_node.connection_status != 'Accepted':
            return None
            
        user = Users.nodes.get(uid=user_uid)
        return cls(
            uid=user.uid,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
            profile=ProfileForConnectedUserTypeV2.from_neomodel(user.profile.single()) if user.profile.single() else None,
            connection=ConnectionConnectedUserType.from_neomodel(user.connection.single()) if user.connection.single() else None,
        )
class GroupedCommunityMemberType(ObjectType):
    uid=graphene.String()
    user_id=graphene.String()
    username=graphene.String()
    email=graphene.String()
    first_name=graphene.String()
    last_name=graphene.String()
    user_type=graphene.String()
    profile=graphene.Field(lambda:ProfileForConnectedUserTypeV2)

    

    @classmethod
    def from_neomodel(cls, user_uid=None):
        
            
        user = Users.nodes.get(uid=user_uid)
        return cls(
            uid=user.uid,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
            profile=ProfileForConnectedUserTypeV2.from_neomodel(user.profile.single()) if user.profile.single() else None,
        )

class ConnectionV2CategoryType(graphene.ObjectType):
    title = graphene.String()
    data = graphene.List(ConnectionV2Type)

class GroupedCommunityMemberCategoryType(graphene.ObjectType):
    title = graphene.String()
    data = graphene.List(GroupedCommunityMemberType)

class SubRelationType(DjangoObjectType):
    class Meta:
        model = SubRelation
        fields = ('id','sub_relation_name', 'directionality', 'approval_required')

class RelationType(DjangoObjectType):
    class Meta:
        model = Relation
        fields = ('id', 'name', 'sub_relations')
    sub_relations = graphene.List(SubRelationType)
    def resolve_sub_relations(self, info):
        return self.sub_relations.all()
    
class RecommendedUserType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name=graphene.String()
    last_name=graphene.String()
    user_type=graphene.String()
    
    profile = graphene.Field(lambda:ProfileRecommendedUserType)
    # connection = graphene.Field(lambda: ConnectionType)

    @classmethod
    def from_neomodel(cls, user,profile=None):
        return cls(
            uid=user["uid"],
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            user_type=user["user_type"],

            profile=ProfileRecommendedUserType.from_neomodel(profile) if profile else None,
            # connection=ConnectionType.from_neomodel(user.connection.single()) if user.connection.single() else None,
        )

class ConnectionIsConnectedType(ObjectType):
    uid=graphene.String()
    receiver = graphene.Field(UserType)
    created_by = graphene.Field(UserType)
    connection_status = graphene.String()
    timestamp = graphene.DateTime()
    circle= graphene.Field(lambda:CircleType)
    
    @classmethod
    def from_neomodel(cls, connection):
            return cls(
                uid=connection.uid,
                receiver=UserType.from_neomodel(connection.receiver.single()) if connection.receiver.single() else None,
                created_by=UserType.from_neomodel(connection.created_by.single()) if connection.created_by.single() else None,
                circle=CircleType.from_neomodel(connection.circle.single()) if connection.circle.single() else None,
                connection_status=connection.connection_status,
                timestamp=connection.timestamp,
                
            )
        

class RecommendedUserForCommunityType(graphene.ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    user_type = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    created_by = graphene.String()
    updated_by = graphene.String()
    is_member = graphene.Boolean()  # Add this field
    profile = graphene.Field(ProfileNoUserType)
    # connection = graphene.Field(lambda: ConnectionType)
    @classmethod
    def from_neomodel(cls, user):
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
            profile=ProfileType.from_neomodel(user.profile.single()) if user.profile.single() else None,
            # connection=ConnectionType.from_neomodel(user.connection.single()) if user.connection.single() else None,
        )
    

class ConnectionConnectedUserType(ObjectType):
    uid=graphene.String()
    # receiver = graphene.Field(UserType)
    # created_by = graphene.Field(UserType)
    connection_status = graphene.String()
    timestamp = graphene.DateTime()
    circle= graphene.Field(lambda:CircleType)

    @classmethod
    def from_neomodel(cls, connection):
        return cls(
            uid=connection.uid,
            # receiver=UserType.from_neomodel(connection.receiver.single()) if connection.receiver.single() else None,
            # created_by=UserType.from_neomodel(connection.created_by.single()) if connection.created_by.single() else None,
            circle=CircleType.from_neomodel(connection.circle.single()) if connection.circle.single() else None,
            connection_status=connection.connection_status,
            timestamp=connection.timestamp,
            
        )
    

class UserConnectedUserType(ObjectType):
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
    connection = graphene.Field(lambda: ConnectionConnectedUserType)

    @classmethod
    def from_neomodel(cls, user):
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
            connection=ConnectionConnectedUserType.from_neomodel(user.connection.single()) if user.connection.single() else None,
        )
    

class ProfileRecommendedUserType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic=graphene.Field(FileDetailType)

    

    @classmethod


    def from_neomodel(cls, profile):
        return cls(
            uid=profile['uid'],
            user_id=profile['user_id'],
            gender=profile['gender'],
            lives_in=profile['lives_in'],
            profile_pic_id=profile['profile_pic_id'],
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile['profile_pic_id'])),

            
        )
    
class UserCategoryType(ObjectType):
    title=graphene.String()
    data=graphene.List(lambda:RecommendedUserType)
    

    @classmethod
    def from_neomodel(cls,user_node,detail):
            
            uid=user_node.uid
            params = {"uid": uid}

            data=[]
            if detail=="Top Vibes - Hobbies":
                results1,_ = db.cypher_query(user_related_queries.get_top_vibes_hobbies_query)
                for user in results1:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )
                    
            elif detail=="Top Vibes - Trending Topics":
                results1,_ = db.cypher_query(user_related_queries.get_top_vibes_trending_topics_query)
                for user in results1:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )
                    
            elif detail=="Top Vibes - Country":
                results1,_ = db.cypher_query(user_related_queries.get_top_vibes_country_query)
                for user in results1:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )
                    
            elif detail=="Top Vibes - Organisation":
                results1,_ = db.cypher_query(user_related_queries.get_top_vibes_organisation_query)
                for user in results1:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )

            elif detail=="Top Vibes - Sport":
                results1,_ = db.cypher_query(user_related_queries.get_top_vibes_organisation_query)
                for user in results1:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )        
            
            elif detail=="Connected Circle":
                results1,_ = db.cypher_query(user_related_queries.recommended_connected_users_query,params)
                for user in results1:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )
                
            elif detail=="New Arrivals":
                results2,_ = db.cypher_query(user_related_queries.recommended_recent_users_query)
                for user in results2:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )

            return cls(
                title=detail,
                data=data,
            )
    

class SecondaryUserType(ObjectType):
    title=graphene.String()
    data=graphene.List(lambda:RecommendedUserType)
    

    @classmethod
    def from_neomodel(cls,user_node_uid,user_uid,detail):
            
            
            params = {"login_user_uid": user_node_uid,"secondary_user_uid":user_uid}

            data=[]
            if detail=="Mutual Connection":
                results1,_ = db.cypher_query(user_related_queries.get_mutual_connected_user_query,params)
                for user in results1:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )
                
            elif detail=="Common Interest":
                results2,_ = db.cypher_query(user_related_queries.get_common_interest_user_query,params)
                for user in results2:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )

            return cls(
                title=detail,
                data=data,
            )
    
class ProfileForConnectedUserTypeV2(ObjectType):
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
            cover_image_id=profile.cover_image_id,
            cover_image=FileDetailType(**generate_presigned_url.generate_file_info(profile.cover_image_id))
            
            
        )

class ConnectionConnectedUserTypeV2(ObjectType):
    uid=graphene.String()
    # receiver = graphene.Field(UserType)
    # created_by = graphene.Field(UserType)
    connection_status = graphene.String()
    timestamp = graphene.DateTime()
    circle= graphene.Field(lambda:CircleTypeV2)

    @classmethod
    def from_neomodel(cls, connection,user_uid):
        return cls(
            uid=connection.uid,
            # receiver=UserType.from_neomodel(connection.receiver.single()) if connection.receiver.single() else None,
            # created_by=UserType.from_neomodel(connection.created_by.single()) if connection.created_by.single() else None,
            circle=CircleTypeV2.from_neomodel(connection.circle.single(),user_uid) if connection.circle.single() else None,
            connection_status=connection.connection_status,
            timestamp=connection.timestamp,
            
        )
    
class CircleTypeV2(graphene.ObjectType):
    uid = graphene.String()
    # relation = graphene.String()
    circle_type = graphene.String()
    sub_relation = graphene.String()

    @classmethod
    def from_neomodel(cls, circle,login_user_uid):
        
        user_data = circle.get_user_relation(login_user_uid)
        sub_relation = user_data.get('sub_relation')
        circle_type = user_data.get('circle_type')

        return cls(
            uid=circle.uid,
            sub_relation=sub_relation,
            circle_type=circle_type,
            
            )
    

class UserConnectedUserTypeV2(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name=graphene.String()
    last_name=graphene.String()
    user_type=graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    connection_stat = graphene.Field(lambda: ConnectionStatsType)
    profile = graphene.Field(lambda:ProfileForConnectedUserTypeV2)
    connection = graphene.Field(lambda: ConnectionConnectedUserTypeV2)

    @classmethod
    def from_neomodel(cls, user,login_user_uid,connection_details):
        
        return cls(
            uid=user.uid,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
            created_at=user.created_at,
            updated_at=user.updated_at,
            connection_stat=ConnectionStatsType.from_neomodel(user.connection_stat.single()) if user.connection_stat.single() else 0,
            profile=ProfileForConnectedUserTypeV2.from_neomodel(user.profile.single()) if user.profile.single() else None,
            connection=ConnectionConnectedUserTypeV2.from_neomodel(connection_details,login_user_uid) if connection_details else None,
        )
    

class SecondaryUserTypeV2(ObjectType):
    title=graphene.String()
    data=graphene.List(lambda:RecommendedUserType)
    

    @classmethod
    def from_neomodel(cls,user_node_uid,user_uid,detail):
            
            
            params = {"login_user_uid": user_node_uid,"secondary_user_uid":user_uid}

            data=[]
            if detail=="Mutual Connection":
                results1,_ = db.cypher_query(user_related_queries.get_mutual_connected_user_queryV2,params)
                for user in results1:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )
                
            elif detail=="Common Interest":
                results2,_ = db.cypher_query(user_related_queries.get_common_interest_user_queryV2,params)
                for user in results2:
                    user_node = user[0]
                    profile_node=user[1]

                    data.append(
                        RecommendedUserType.from_neomodel(user_node,profile_node)

                        )

            return cls(
                title=detail,
                data=data,
            )