import graphene
from graphene import ObjectType
from datetime import datetime

from auth_manager.graphql.types import UserType
from connection.utils.score_generator import generate_connection_score
from post.redis import get_post_comment_count, get_post_like_count
from ..models import *
from auth_manager.Utils import generate_presigned_url
from ..utils import userlist, helperfunction
from community.graphql.raw_queries.community_query import *
from post.utils.reaction_manager import PostReactionUtils, IndividualVibeManager
from post.redis import get_post_comment_count, get_post_like_count
from post.models import PostReactionManager
from vibe_manager.models import IndividualVibe, CommunityVibe
from neomodel import db
from community.redis import *
from ..utils.post_data_helper import CommunityPostDataHelper
from ..utils.enhanced_query_helper import EnhancedQueryHelper



class FileDetailType(graphene.ObjectType):
    url = graphene.String()
    file_extension = graphene.String()
    file_type = graphene.String()
    file_size = graphene.Int()


class VibeFeedListType(ObjectType):
    vibe_id = graphene.String()
    vibe_name = graphene.String()
    vibe_cumulative_score = graphene.String()
    
    @classmethod
    def from_neomodel(cls, vibe):
        if isinstance(vibe, dict):
            return cls(
                vibe_id=vibe.get("vibes_id"),
                vibe_name=vibe.get("vibes_name"),
                vibe_cumulative_score=round(vibe.get("cumulative_vibe_score", 0), 1)
            )
        else:
            return cls(
                vibe_id=str(vibe.id),
                vibe_name=vibe.name_of_vibe,
                vibe_cumulative_score="0"
            )

class UserFeedType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    is_active = graphene.Boolean()
    user_type = graphene.String()
    profile = graphene.Field(lambda: ProfileFeedType)

    @classmethod
    def from_neomodel(cls, user_node, profile=None):
        try:
            return cls(
                uid=user_node.get('uid') if isinstance(user_node, dict) else user_node.uid,
                user_id=user_node.get('user_id') if isinstance(user_node, dict) else user_node.user_id,
                username=user_node.get('username') if isinstance(user_node, dict) else user_node.username,
                email=user_node.get('email') if isinstance(user_node, dict) else user_node.email,
                first_name=user_node.get('first_name') if isinstance(user_node, dict) else user_node.first_name,
                last_name=user_node.get('last_name') if isinstance(user_node, dict) else user_node.last_name,
                is_active=user_node.get('is_active') if isinstance(user_node, dict) else user_node.is_active,
                user_type=user_node.get('user_type') if isinstance(user_node, dict) else user_node.user_type,
                profile=ProfileFeedType.from_neomodel(profile) if profile else None
            )
        except Exception as e:
            print(f"Error in UserFeedType.from_neomodel: {e}")
            return None

class ProfileFeedType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic = graphene.List(lambda: FileDetailType)
    
    @classmethod
    def from_neomodel(cls, profile):
        if not profile:
            return None
        try:
            profile_img_id = profile.get("profile_pic_id") if isinstance(profile, dict) else profile.profile_pic_id
            return cls(
                uid=profile.get("uid") if isinstance(profile, dict) else profile.uid,
                user_id=profile.get("user_id") if isinstance(profile, dict) else profile.user_id,
                gender=profile.get("gender") if isinstance(profile, dict) else profile.gender,
                profile_pic_id=profile_img_id,
                profile_pic=([FileDetailType(**generate_presigned_url.generate_file_info(profile_img_id))]) if profile_img_id else None,
            )
        except Exception as e:
            print(f"Error in ProfileFeedType.from_neomodel: {e}")
            return None

class ReactionFeedType(ObjectType):
    uid = graphene.String()
    vibe = graphene.Float()
    reaction = graphene.String()
    is_deleted = graphene.Boolean()
    timestamp = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, reaction_node):
        try:
            if isinstance(reaction_node, dict):
                unix_timestamp = reaction_node['timestamp']
                return cls(
                    uid=reaction_node['uid'],
                    vibe=reaction_node['vibe'],
                    reaction=reaction_node['reaction'],
                    is_deleted=reaction_node['is_deleted'],
                    timestamp=datetime.fromtimestamp(unix_timestamp)
                )
            else:
                return cls(
                    uid=reaction_node.uid,
                    vibe=reaction_node.vibe,
                    reaction=reaction_node.reaction,
                    is_deleted=reaction_node.is_deleted,
                    timestamp=reaction_node.timestamp
                )
        except Exception as e:
            print(f"Error in ReactionFeedType.from_neomodel: {e}")
            return None      


class CommunityType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    community_type = graphene.String()
    community_circle = graphene.String()
    room_id=graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()
    number_of_members = graphene.Int()
    group_invite_link = graphene.String()
    group_icon_id = graphene.String()
    group_icon_url=graphene.Field(FileDetailType)
    cover_image_id=graphene.String()
    cover_image_url=graphene.Field(FileDetailType)
    category = graphene.String()
    generated_community=graphene.Boolean()
    created_by = graphene.Field(UserType)
    communitymessage = graphene.List(lambda:CommunityMessagesNonCommunityType)
    community_review=graphene.List(lambda:CommunityReviewNonCommunityType)
    members=graphene.List(lambda:MembershipNonCommunityType)
    mentioned_users = graphene.List(UserType)

    
    # Agent management fields
    leader_agent = graphene.Field('agentic.graphql.types.AgentType')
    has_leader_agent = graphene.Boolean()
    agent_assignments = graphene.List('agentic.graphql.types.AgentAssignmentType')
    @classmethod
    def from_neomodel(cls, community, include_agent_assignments=True):
        community.number_of_members = len(community.members.all())
        community.save()
        
        # Safely generate group icon URL - handle errors gracefully
        group_icon_url = None
        try:
            if community.group_icon_id:
                file_info = generate_presigned_url.generate_file_info(community.group_icon_id)
                if file_info and file_info.get('url'):
                    group_icon_url = FileDetailType(**file_info)
        except Exception as e:
            group_icon_url=None
            print(f"Error generating group icon URL: {e}")
            # Continue without the group icon URL
        
        # Get agent assignments only if requested to avoid circular references
        leader_agent = None
        has_leader_agent = False
        agent_assignments = []
        
        if include_agent_assignments:
            try:
                leader_agent = cls._get_leader_agent(community)
                has_leader_agent = community.has_leader_agent()
                agent_assignments = cls._get_agent_assignments(community)
            except Exception as e:
                print(f"Error loading community agent assignments: {e}")
                leader_agent = None
                has_leader_agent = False
                agent_assignments = []
        
        # Safely generate cover image URL - handle errors gracefully
        cover_image_url = None
        try:
            if community.cover_image_id:
                file_info = generate_presigned_url.generate_file_info(community.cover_image_id)
                if file_info and file_info.get('url'):
                    cover_image_url = FileDetailType(**file_info)
        except Exception as e:
            cover_image_url = None
            print(f"Error generating cover image URL: {e}")
            # Continue without the cover image URL
        
        return cls(
            uid=community.uid,
            name=community.name,
            description=community.description,
            community_type=community.community_type,
            community_circle=community.community_circle,
            room_id=community.room_id,
            created_date=community.created_date,
            updated_date=community.updated_date,
            number_of_members=community.number_of_members,
            group_invite_link=community.group_invite_link,
            group_icon_id=community.group_icon_id,
            group_icon_url=group_icon_url,
            cover_image_id=community.cover_image_id,
            cover_image_url=cover_image_url,
            category=community.category,
            # Fixed: Verify created_by is a Users object before passing to UserType
            created_by=UserType.from_neomodel(community.created_by.single()) if community.created_by.single() and isinstance(community.created_by.single(), Users) else None,
            communitymessage=[CommunityMessagesNonCommunityType.from_neomodel(x) for x in community.communitymessage],
            community_review=[CommunityReviewNonCommunityType.from_neomodel(x) for x in community.community_review],
            members=[MembershipNonCommunityType.from_neomodel(x) for x in community.members],
            mentioned_users=cls._get_description_mentioned_users(community),

            # Agent management fields
            leader_agent=leader_agent,
            has_leader_agent=has_leader_agent,
            agent_assignments=agent_assignments
        )
    
    @classmethod
    def _get_leader_agent(cls, community):
        """Get the leader agent for the community."""
        try:
            leader_agent = community.get_leader_agent()
            if leader_agent:
                # Import here to avoid circular imports
                from agentic.graphql.types import AgentType
                return AgentType.from_neomodel(leader_agent)
            return None
        except Exception as e:
            print(f"Error getting leader agent: {e}")
            return None
    
    @classmethod
    def _get_agent_assignments(cls, community):
        """Get all agent assignments for the community."""
        try:
            assignments = community.get_agent_assignments()
            if assignments:
                # Import here to avoid circular imports
                from agentic.graphql.types import AgentAssignmentType
                return [AgentAssignmentType.from_neomodel(assignment, include_community=False) for assignment in assignments if assignment]
            return []
        except Exception as e:
            print(f"Error getting agent assignments: {e}")
            return []
    @classmethod
    def _get_description_mentioned_users(cls, community):
        """Get users mentioned in the community description."""
        try:
            from post.services.mention_service import MentionService
            
            mentions = MentionService.get_mentions_for_content('community_description', community.uid)
            
            mentioned_users = []
            for mention in mentions:
                mentioned_user = mention.mentioned_user.single()
                if mentioned_user:
                    mentioned_users.append(UserType.from_neomodel(mentioned_user))
            
            return mentioned_users
            
        except Exception as e:
            print(f"Error getting mentioned users for community {community.uid}: {e}")
            return []    



class CommunityInformationType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    community_type = graphene.String()
    community_circle = graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()
    number_of_members = graphene.Int()
    group_invite_link = graphene.String()
    group_icon_id = graphene.String()
    group_icon_url=graphene.Field(FileDetailType)
    category = graphene.String()
    created_by = graphene.Field(lambda:UserCommunityDetailsType)
    
    @classmethod
    def from_neomodel(cls, community):
        # Safely generate group icon URL - handle errors gracefully
        group_icon_url = None
        try:
            if community.group_icon_id:
                file_info = generate_presigned_url.generate_file_info(community.group_icon_id)
                if file_info and file_info.get('url'):
                    group_icon_url = FileDetailType(**file_info)
        except Exception as e:
            print(f"Error generating group icon URL: {e}")
            # Continue without the group icon URL
        
        return cls(
            uid=community.uid,
            name=community.name,
            description=community.description,
            # community_type=community.community_type, these two key deliberately I am returning null
            # community_circle=community.community_circle,
            created_date=community.created_date,
            updated_date=community.updated_date,
            number_of_members=community.number_of_members,
            group_invite_link=community.group_invite_link,
            group_icon_id=community.group_icon_id,
            group_icon_url=group_icon_url,
            category=community.category,
            created_by=UserCommunityDetailsType.from_neomodel(community.created_by.single()) if community.created_by.single() else None,
        )


class CommunityMessagesType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    sender = graphene.Field(UserType)
    content = graphene.String()
    file_id = graphene.String()
    file_url=graphene.String()
    title = graphene.String()
    is_read = graphene.Boolean()
    is_deleted = graphene.Boolean()
    timestamp = graphene.DateTime()
    is_public = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, message):
        return cls(
            uid=message.uid,
            community=CommunityType.from_neomodel(message.community.single()) if message.community.single() else None,
            sender=UserType.from_neomodel(message.sender.single()) if message.sender.single() else None,
            content=message.content,
            file_id=message.file_id,
            file_url=generate_presigned_url.generate_presigned_url(message.file_id),
            title=message.title,
            is_read=message.is_read,
            is_deleted=message.is_deleted,
            timestamp=message.timestamp,
            is_public=message.is_public
        )

class MembershipType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    community = graphene.Field(CommunityType)
    is_admin = graphene.Boolean()
    is_leader = graphene.Boolean()
    is_accepted = graphene.Boolean()
    join_date = graphene.DateTime()
    can_message = graphene.Boolean()
    is_blocked = graphene.Boolean()
    

    @classmethod
    def from_neomodel(cls, membership):
        return cls(
            uid=membership.uid,
            community=CommunityType.from_neomodel(membership.community.single()) if membership.community.single() else None,
            user=UserType.from_neomodel(membership.user.single()) if membership.user.single() else None,
            is_admin=membership.is_admin,
            is_leader=membership.is_leader,
            is_accepted=membership.is_accepted,
            join_date=membership.join_date,
            can_message=membership.can_message,
            is_blocked=membership.is_blocked,
            
        )
    
class CommunityPostType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    post_id = graphene.String()
    is_accepted = graphene.Boolean()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()
    score = graphene.Float()

    @classmethod
    def from_neomodel(cls, post):
        return cls(
            uid=post.uid,
            community=CommunityType.from_neomodel(post.community.single()) if post.community.single() else None,
            post_id=post.post_id,
            is_accepted=post.is_accepted,
            created_date=post.created_date,
            updated_date=post.updated_date,
            score=generate_connection_score()
        )

class CommunityProductType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    product_id = graphene.String()
    is_accepted = graphene.Boolean()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, product):
        return cls(
            uid=product.uid,
            community=CommunityType.from_neomodel(product.community.single()) if product.community.single() else None,
            product_id=product.product_id,
            is_accepted=product.is_accepted,
            created_date=product.created_date,
            updated_date=product.updated_date
        )

class CommunityStoryType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    story_id = graphene.String()
    is_accepted = graphene.Boolean()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, story):
        return cls(
            uid=story.uid,
            community=CommunityType.from_neomodel(story.community.single()) if story.community.single() else None,
            story_id=story.story_id,
            is_accepted=story.is_accepted,
            created_date=story.created_date,
            updated_date=story.updated_date
        )

class ElectionType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    is_active = graphene.Boolean()
    start_date = graphene.DateTime()
    nomination_duration = graphene.Int()
    voting_duration = graphene.Int()
    result_announcement = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, election):
        return cls(
            uid=election.uid,
            community=CommunityType.from_neomodel(election.community.single()) if election.community.single() else None,
            is_active=election.is_active,
            start_date=election.start_date,
            nomination_duration=election.nomination_duration,
            voting_duration=election.voting_duration,
            result_announcement=election.result_announcement
        )

class NominationType(ObjectType):
    uid = graphene.String()
    election = graphene.Field(ElectionType)
    member = graphene.Field(MembershipType)
    vibes_received = graphene.Int()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, nomination):
        return cls(
            uid=nomination.uid,
            election=ElectionType.from_neomodel(nomination.election.single()) if nomination.election.single() else None,
            member=MembershipType.from_neomodel(nomination.member.single()) if nomination.member.single() else None,
            vibes_received=nomination.vibes_received,
            created_date=nomination.created_date,
            updated_date=nomination.updated_date
        )

class VoteType(ObjectType):
    uid = graphene.String()
    election = graphene.Field(ElectionType)
    voter = graphene.Field(MembershipType)
    nominee = graphene.Field(NominationType)
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, vote):
        return cls(
            uid=vote.uid,
            election=ElectionType.from_neomodel(vote.election.single()) if vote.election.single() else None,
            voter=MembershipType.from_neomodel(vote.voter.single()) if vote.voter.single() else None,
            nominee=NominationType.from_neomodel(vote.nominee.single()) if vote.nominee.single() else None,
            created_date=vote.created_date,
            updated_date=vote.updated_date
        )

class RoleType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    name = graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, role):
        return cls(
            uid=role.uid,
            community=CommunityType.from_neomodel(role.community.single()) if role.community.single() else None,
            name=role.name,
            created_date=role.created_date,
            updated_date=role.updated_date
        )

class CommunityRoleType(ObjectType):
    uid = graphene.String()
    membership = graphene.Field(MembershipType)
    role = graphene.Field(RoleType)
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, community_role):
        return cls(
            uid=community_role.uid,
            membership=MembershipType.from_neomodel(community_role.membership.single()) if community_role.membership.single() else None,
            role=RoleType.from_neomodel(community_role.role.single()) if community_role.role.single() else None,
            created_date=community_role.created_date,
            updated_date=community_role.updated_date
        )

class MessageType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    sender = graphene.Field(UserType)
    content = graphene.String()
    timestamp = graphene.DateTime()
    is_hidden = graphene.Boolean()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, message):
        return cls(
            uid=message.uid,
            community=CommunityType.from_neomodel(message.community.single()) if message.community.single() else None,
            sender=UserType.from_neomodel(message.sender.single()) if message.sender.single() else None,
            content=message.content,
            timestamp=message.timestamp,
            is_hidden=message.is_hidden,
            created_date=message.created_date,
            updated_date=message.updated_date
        )

class CommunityKeywordType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    keyword = graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, keyword):
        return cls(
            uid=keyword.uid,
            community=CommunityType.from_neomodel(keyword.community.single()) if keyword.community.single() else None,
            keyword=keyword.keyword,
            created_date=keyword.created_date,
            updated_date=keyword.updated_date
        )

class CommunityExitType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    user = graphene.Field(UserType)
    exit_date = graphene.DateTime()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, exit):
        return cls(
            uid=exit.uid,
            community=CommunityType.from_neomodel(exit.community.single()) if exit.community.single() else None,
            user=UserType.from_neomodel(exit.user.single()) if exit.user.single() else None,
            exit_date=exit.exit_date,
            created_date=exit.created_date,
            updated_date=exit.updated_date
        )

class CommunityRuleType(ObjectType):
    uid = graphene.String()
    community = graphene.Field(CommunityType)
    rule_text = graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, rule):
        return cls(
            uid=rule.uid,
            community=CommunityType.from_neomodel(rule.community.single()) if rule.community.single() else None,
            rule_text=rule.rule_text,
            created_date=rule.created_date,
            updated_date=rule.updated_date
        )

class CommunityReviewType(ObjectType):
    uid = graphene.String()
    byuser = graphene.Field(UserType)
    # tocommunity = graphene.Field(CommunityType)
    reaction = graphene.String()
    vibe = graphene.Float()
    title = graphene.String()
    content = graphene.String()
    file_id = graphene.String()
    file_url=graphene.Field(FileDetailType)
    is_deleted = graphene.Boolean()
    timestamp = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, review):
        return cls(
            uid=review.uid,
            byuser=UserType.from_neomodel(review.byuser.single()) if review.byuser.single() else None,
            # tocommunity=CommunityType.from_neomodel(review.tocommunity.single()) if review.tocommunity.single() else None,
            reaction=review.reaction,
            vibe=review.vibe,
            title=review.title,
            content=review.content,
            file_id=review.file_id,
            file_url=FileDetailType(**generate_presigned_url.generate_file_info(review.file_id)),
            is_deleted=review.is_deleted,
            timestamp=review.timestamp
        )

class CommunityUserBlockType(ObjectType):
    uid = graphene.String()
    blocker = graphene.Field(UserType)
    blocked = graphene.Field(UserType)
    created_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, block):
        return cls(
            uid=block.uid,
            blocker=UserType.from_neomodel(block.blocker.single()) if block.blocker.single() else None,
            blocked=UserType.from_neomodel(block.blocked.single()) if block.blocked.single() else None,
            created_at=block.created_at
        )

class CommunityMessagesNonCommunityType(ObjectType):
    uid = graphene.String()
    content = graphene.String()
    file_id = graphene.String()
    file_url=graphene.Field(FileDetailType)
    title = graphene.String()
    is_read = graphene.Boolean()
    is_deleted = graphene.Boolean()
    timestamp = graphene.DateTime()
    is_public = graphene.Boolean()
    sender = graphene.Field(UserType)
    @classmethod
    def from_neomodel(cls, message):
        
        return cls(
            uid=message.uid,
            content=message.content,
            file_id=message.file_id,
            file_url=FileDetailType(**generate_presigned_url.generate_file_info(message.file_id)),
            title=message.title,
            is_read=message.is_read,
            is_deleted=message.is_deleted,
            timestamp=message.timestamp,
            is_public=message.is_public,
            sender=UserType.from_neomodel(message.sender.single()) if message.sender.single() else None,
        )
    
class CommunityReviewNonCommunityType(ObjectType):
    uid = graphene.String()
    byuser = graphene.Field(UserType)
    reaction = graphene.String()
    vibe = graphene.Float()
    title = graphene.String()
    content = graphene.String()
    file_id = graphene.String()
    file_url= graphene.Field(FileDetailType)
    is_deleted = graphene.Boolean()
    timestamp = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, review):
        return cls(
            uid=review.uid,
            byuser=UserType.from_neomodel(review.byuser.single()) if review.byuser.single() else None,
            reaction=review.reaction,
            vibe=review.vibe,
            title=review.title,
            content=review.content,
            file_id=review.file_id,
            file_url=FileDetailType(**generate_presigned_url.generate_file_info(review.file_id)),
            is_deleted=review.is_deleted,
            timestamp=review.timestamp
        )
    
class MembershipNonCommunityType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    is_admin = graphene.Boolean()
    is_leader = graphene.Boolean()
    is_accepted = graphene.Boolean()
    join_date = graphene.DateTime()
    can_message = graphene.Boolean()
    is_blocked = graphene.Boolean()
    

    @classmethod
    def from_neomodel(cls, membership):
        return cls(
            uid=membership.uid,
            user=UserType.from_neomodel(membership.user.single()) if membership.user.single() else None,
            is_admin=membership.is_admin,
            is_leader=membership.is_leader,
            is_accepted=membership.is_accepted,
            join_date=membership.join_date,
            can_message=membership.can_message,
            is_blocked=membership.is_blocked,
            
        )
    
class CommunityGoalType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    file_id =graphene.List(graphene.String)
    file_url=graphene.List(FileDetailType)
    created_by = graphene.Field(UserType)
    # community = graphene.Field(CommunityType)
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()
    vibes_count = graphene.Int()
    my_vibe_details = graphene.List(ReactionFeedType)
    vibe_feed_list = graphene.List(VibeFeedListType)
    score = graphene.Float()

    @classmethod
    def from_neomodel(cls, goal,user_node=None):
            data = EnhancedQueryHelper.enhance_community_item_with_post_data(goal, user_node)
            
            # Get creator information
            creator_info = data['creator_info']
            created_by = None
            if creator_info and creator_info['creator']:
                created_by = UserFeedType.from_neomodel(
                    creator_info['creator'], 
                    creator_info['profile']
                )

            return cls(
            uid=goal.uid,
            name=goal.name,
            description=goal.description,
            file_id=goal.file_id,
            file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in goal.file_id] if goal.file_id else None),
            # Fixed: Verify created_by is a Users object before passing to UserType
            created_by=UserType.from_neomodel(goal.created_by.single()) if goal.created_by.single() and isinstance(goal.created_by.single(), Users) else None,
            # community=CommunityType.from_neomodel(goal.community.single()) if goal.community.single() else None,
            timestamp=goal.timestamp,
            is_deleted=goal.is_deleted,
            vibes_count=data['vibes_count'],
            my_vibe_details=[ReactionFeedType.from_neomodel(r) for r in data['my_vibe_details']],
            vibe_feed_list=[VibeFeedListType.from_neomodel(v) for v in data['vibe_feed_list']],
            score=generate_connection_score()
            
            )
    
class CommunityActivityType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    activity_type = graphene.String()
    file_id =graphene.List(graphene.String)
    file_url=graphene.List(FileDetailType)
    created_by = graphene.Field(UserType)
    # community = graphene.Field(CommunityType)
    date = graphene.DateTime()
    is_deleted = graphene.Boolean()
    vibes_count = graphene.Int()
    my_vibe_details = graphene.List(ReactionFeedType)
    vibe_feed_list = graphene.List(VibeFeedListType)
    score = graphene.Float()

    @classmethod
    def from_neomodel(cls, activity,user_node=None):

            data = EnhancedQueryHelper.enhance_community_item_with_post_data(activity, user_node)
            
            creator_info = data['creator_info']
            created_by = None
            if creator_info and creator_info['creator']:
                created_by = UserFeedType.from_neomodel(
                    creator_info['creator'], 
                    creator_info['profile']
                )
            return cls(
            uid=activity.uid,
            name=activity.name,
            description=activity.description,
            activity_type=activity.activity_type,
            file_id=activity.file_id,
            file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in activity.file_id] if activity.file_id else None),
            # Fixed: Verify created_by is a Users object before passing to UserType
            created_by=UserType.from_neomodel(activity.created_by.single()) if activity.created_by.single() and isinstance(activity.created_by.single(), Users) else None,
            # community=CommunityType.from_neomodel(activity.community.single()) if activity.community.single() else None,
            date=activity.date,
            is_deleted=activity.is_deleted,
            vibes_count=data['vibes_count'],
            my_vibe_details=[ReactionFeedType.from_neomodel(r) for r in data['my_vibe_details']],
            vibe_feed_list=[VibeFeedListType.from_neomodel(v) for v in data['vibe_feed_list']],
            score=generate_connection_score()
            
            )
  

class CommunityAffiliationType(ObjectType):
    uid = graphene.String()
    entity = graphene.String()
    date = graphene.DateTime()
    subject = graphene.String()
    file_id =graphene.List(graphene.String)
    file_url=graphene.List(FileDetailType)
    created_by = graphene.Field(UserType)
    # community = graphene.Field(CommunityType)
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()
    vibes_count = graphene.Int()
    my_vibe_details = graphene.List(ReactionFeedType)
    vibe_feed_list = graphene.List(VibeFeedListType)
    score = graphene.Float()

    @classmethod
    def from_neomodel(cls, affiliation,user_node=None):
             
            data = EnhancedQueryHelper.enhance_community_item_with_post_data(affiliation, user_node)
            creator_info = data['creator_info']
            created_by = None
            if creator_info and creator_info['creator']:
                created_by = UserFeedType.from_neomodel(
                    creator_info['creator'], 
                    creator_info['profile']
                )
            return cls(
            uid=affiliation.uid,
            entity=affiliation.entity,
            date=affiliation.date,
            subject=affiliation.subject,
            file_id=affiliation.file_id,
            file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in affiliation.file_id] if affiliation.file_id else None),
            # Fixed: Verify created_by is a Users object before passing to UserType
            created_by=UserType.from_neomodel(affiliation.created_by.single()) if affiliation.created_by.single() and isinstance(affiliation.created_by.single(), Users) else None,
            # community=CommunityType.from_neomodel(affiliation.community.single()) if affiliation.community.single() else None,
            timestamp=affiliation.timestamp,
            is_deleted=affiliation.is_deleted,
            vibes_count=data['vibes_count'],
            my_vibe_details=[ReactionFeedType.from_neomodel(r) for r in data['my_vibe_details']],
            vibe_feed_list=[VibeFeedListType.from_neomodel(v) for v in data['vibe_feed_list']],
            score=generate_connection_score()
           
            )

class CommunityAchievementType(ObjectType):
    uid = graphene.String()
    entity = graphene.String()
    date = graphene.DateTime()
    subject = graphene.String()
    file_id =graphene.List(graphene.String)
    file_url=graphene.List(FileDetailType)
    created_by = graphene.Field(UserType)
    # community = graphene.Field(CommunityType)
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()
    vibes_count = graphene.Int()
    my_vibe_details = graphene.List(ReactionFeedType)
    vibe_feed_list = graphene.List(VibeFeedListType)
    score = graphene.Float()

    @classmethod
    def from_neomodel(cls, achievement,user_node=None):
            enhanced_data = EnhancedQueryHelper.enhance_community_item_with_post_data(achievement, user_node)
            
            creator_info = enhanced_data['creator_info']
            created_by = None
            if creator_info and creator_info['creator']:
                created_by = UserFeedType.from_neomodel(
                    creator_info['creator'], 
                    creator_info['profile']
                )
        
            return cls(
            uid=achievement.uid,
            entity=achievement.entity,
            date=achievement.date,
            subject=achievement.subject,
            file_id=achievement.file_id,
            file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in achievement.file_id] if achievement.file_id else None),
            # Fixed: Verify created_by is a Users object before passing to UserType
            created_by=UserType.from_neomodel(achievement.created_by.single()) if achievement.created_by.single() and isinstance(achievement.created_by.single(), Users) else None,
            # community=CommunityType.from_neomodel(achievement.community.single()) if achievement.community.single() else None,
            timestamp=achievement.timestamp,
            is_deleted=achievement.is_deleted,
            vibes_count=enhanced_data['vibes_count'],
            my_vibe_details=[ReactionFeedType.from_neomodel(r) for r in enhanced_data['my_vibe_details']],
            vibe_feed_list=[VibeFeedListType.from_neomodel(v) for v in enhanced_data['vibe_feed_list']],
            score=generate_connection_score()
        
            )

class SubCommunityType(graphene.ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    sub_community_type = graphene.String()
    sub_community_group_type=graphene.String()
    sub_community_circle = graphene.String()
    room_id=graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()
    number_of_members = graphene.Int()
    group_invite_link = graphene.String()
    group_icon_id = graphene.String()
    group_icon_url = graphene.Field(FileDetailType)  # Assuming URL is generated similar to Community
    cover_image_id=graphene.String()
    cover_image_url=graphene.Field(FileDetailType)
    category = graphene.String()
    created_by = graphene.Field(UserType)  # Assuming UserType is defined similarly
    parent_community = graphene.Field(lambda: CommunityType)  # Assuming you have a CommunityType defined

    @classmethod
    def from_neomodel(cls, sub_community):
        sub_community.number_of_members=len(sub_community.sub_community_members.all())
        sub_community.save()
        
        # Safely generate group icon URL - handle errors gracefully
        group_icon_url = None
        try:
            if sub_community.group_icon_id:
                file_info = generate_presigned_url.generate_file_info(sub_community.group_icon_id)
                if file_info and file_info.get('url'):
                    group_icon_url = FileDetailType(**file_info)
        except Exception as e:
            group_icon_url = None
            print(f"Error generating sub-community group icon URL: {e}")
        
        # Safely generate cover image URL - handle errors gracefully
        cover_image_url = None
        try:
            if sub_community.cover_image_id:
                file_info = generate_presigned_url.generate_file_info(sub_community.cover_image_id)
                if file_info and file_info.get('url'):
                    cover_image_url = FileDetailType(**file_info)
        except Exception as e:
            cover_image_url = None
            print(f"Error generating sub-community cover image URL: {e}")
        
        return cls(
            uid=sub_community.uid,
            name=sub_community.name,
            description=sub_community.description,
            sub_community_type=sub_community.sub_community_type,
            sub_community_group_type=sub_community.sub_community_group_type,
            sub_community_circle=sub_community.sub_community_circle,
            room_id=sub_community.room_id,
            created_date=sub_community.created_date,
            updated_date=sub_community.updated_date,
            number_of_members=sub_community.number_of_members,  # Direct field
            group_invite_link=sub_community.group_invite_link,
            group_icon_id=sub_community.group_icon_id,
            group_icon_url=group_icon_url,
            cover_image_id=sub_community.cover_image_id,
            cover_image_url=cover_image_url,
            category=sub_community.category,
            # Fixed: Verify created_by is a Users object before passing to UserType
            created_by=UserType.from_neomodel(sub_community.created_by.single()) if sub_community.created_by.single() and isinstance(sub_community.created_by.single(), Users) else None,
            parent_community=CommunityType.from_neomodel(sub_community.parent_community.single()) if sub_community.parent_community.single() else None
        )



class SubCommunityNoParentType(graphene.ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    sub_community_type = graphene.String()
    sub_community_group_type=graphene.String()
    sub_community_circle = graphene.String()
    room_id=graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()
    number_of_members = graphene.Int()
    group_invite_link = graphene.String()
    group_icon_id = graphene.String()
    group_icon_url = graphene.Field(FileDetailType)  # Assuming URL is generated similar to Community
    category = graphene.String()
    created_by = graphene.Field(lambda:UserCommunityDetailsType)  # Assuming UserType is defined similarly
    
    @classmethod
    def from_neomodel(cls, sub_community):
        return cls(
            uid=sub_community.uid,
            name=sub_community.name,
            description=sub_community.description,
            sub_community_type=sub_community.sub_community_type,
            sub_community_group_type=sub_community.sub_community_group_type,
            sub_community_circle=sub_community.sub_community_circle,
            room_id=sub_community.room_id,
            created_date=sub_community.created_date,
            updated_date=sub_community.updated_date,
            number_of_members=sub_community.number_of_members,  # Direct field
            group_invite_link=sub_community.group_invite_link,
            group_icon_id=sub_community.group_icon_id,
            group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(sub_community.group_icon_id)),  # Define or import your function
            category=sub_community.category,
            created_by=UserCommunityDetailsType.from_neomodel(sub_community.created_by.single()) if sub_community.created_by.single() else None,
            
        )  

class UserCommunityDetailsType(ObjectType):
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
    profile = graphene.Field(lambda:ProfileCommunityDetailsType)
    

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
            profile=ProfileCommunityDetailsType.from_neomodel(user.profile.single()) if user.profile.single() else None,
            # connection=ConnectionNoUserType.from_neomodel(user.connection.single()) if user.connection.single() else None,
        )


class ProfileCommunityDetailsType(ObjectType):
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
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile.profile_pic_id)) if profile.profile_pic_id else None,
            
        )


class CommunityDetailsType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    community_type = graphene.String()
    community_circle = graphene.String()
    room_id=graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()
    number_of_members = graphene.Int()
    innermembercount=graphene.Int()
    outermembercount=graphene.Int()
    universemembercount=graphene.Int()
    group_invite_link = graphene.String()
    group_icon_id = graphene.String()
    group_icon_url=graphene.Field(FileDetailType)
    cover_image_id  =graphene.String()
    cover_image_url=graphene.Field(FileDetailType)
    category = graphene.String()
    is_login_user_member = graphene.Boolean()
    is_admin=graphene.Boolean()
    community_level=graphene.String()
    created_by = graphene.Field(lambda:UserCommunityDetailsType)
    community_vibe_list=graphene.List(lambda:VibeCommunityListType)
    my_community_vibe=graphene.List(lambda:CommunityReviewNonCommunityType)
    child_community=graphene.List(lambda:SubCommunityNoParentType)
    sibling_community=graphene.List(lambda:SubCommunityNoParentType)
    parent_community=graphene.List(lambda:CommunityInformationType)
    permission=graphene.List(lambda:CommunityPermissionType)
    vibes_count = graphene.Int()
    post_count = graphene.Int()
    
    # Agent management fields
    leader_agent = graphene.Field('agentic.graphql.types.AgentType')
    has_leader_agent = graphene.Boolean()
    agent_assignments = graphene.List('agentic.graphql.types.AgentAssignmentType')
    
    
    @classmethod
    def from_neomodel(cls, community=None,subcommunity=None,user_node=None):

        if community:

            manager = CommunityMemberCountManager(community_uid=community.uid)

            membercount=len(community.members.all())
            # Set counts
            manager.update_counts_if_needed(membercount,"community")

            # Get counts
            counts = manager.get_counts()
            inner_member_count= counts['innermembercount']
            outer_member_count= counts['outermembercount']
            universe_member_count= counts['universemembercount']
            member_count=counts['membercount']


            membership_exists = helperfunction.get_membership_for_user_in_community(user_node, community)
            i_admin = False
            is_login_user_mem = False
            if membership_exists:
                is_login_user_mem = True
                if membership_exists.is_admin == True:
                    i_admin = True
        
            community_reaction_manager = CommunityReactionManager.objects.filter(
                    community_uid=community.uid).first()

            if community_reaction_manager:
                    all_reactions = community_reaction_manager.community_vibe
                    sorted_reactions = sorted(all_reactions, key=lambda x: x.get(
                        'cumulative_vibe_score', 0), reverse=True)
                    vibes_count = sum(reaction.get('vibes_count', 0) for reaction in all_reactions)

            else:
                    sorted_reactions = CommunityVibe.objects.all()[:10]
                    vibes_count = 0

            try:
                post_count = len([post for post in community.community_post.all() if not post.is_deleted])
            except Exception:
                post_count = 0        


            
            # Get agent-related data
            leader_agent = cls._get_leader_agent(community)
            has_leader_agent = leader_agent is not None
            agent_assignments = cls._get_agent_assignments(community)
            
            return cls(
                    uid=community.uid,
                    name=community.name,
                    description=community.description,
                    community_type=community.community_type,
                    community_circle=community.community_circle,
                    room_id=community.room_id,
                    created_date=datetime.fromtimestamp(community.created_date) if isinstance(community.created_date, (int, float)) else community.created_date,
                    updated_date=community.updated_date,
                    number_of_members=member_count,
                    innermembercount=inner_member_count,
                    outermembercount=outer_member_count,
                    universemembercount=universe_member_count,
                    group_invite_link=community.group_invite_link,
                    group_icon_id=community.group_icon_id,
                    group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(
                        community.group_icon_id)) if community.group_icon_id else None,
                    cover_image_id=community.cover_image_id,
                    cover_image_url=FileDetailType(**generate_presigned_url.generate_file_info(
                        community.cover_image_id)) if community.cover_image_id else None,
                    category=community.category,
                    is_login_user_member=is_login_user_mem,
                    is_admin=i_admin,
                    community_level="Community",
                    created_by=UserCommunityDetailsType.from_neomodel(
                        community.created_by.single()) if community.created_by.single() else None,
                    
                    community_vibe_list=[VibeCommunityListType.from_neomodel(
                        vibe) for vibe in sorted_reactions],
                    my_community_vibe=[
                        CommunityReviewNonCommunityType.from_neomodel(review)
                        for review in sorted(
                            community.community_review,
                            key=lambda r: r.timestamp,  # Assuming there's a timestamp attribute to sort by
                            reverse=True
                        )
                        if review.byuser.single().uid == user_node.uid
                    ],
                    # child_community=[SubCommunityNoParentType.from_neomodel(sub_community) for sub_community in community.child_communities.all()],
                    # sibling_community=[SubCommunityNoParentType.from_neomodel(sub_community) for sub_community in community.sibling_communities.all()],
                    # parent_community=[],
                    permission=[CommunityPermissionType.from_neomodel(community)],
                    vibes_count=vibes_count,
                    post_count=post_count,
                    
                    # Agent management fields
                    leader_agent=leader_agent,
                    has_leader_agent=has_leader_agent,
                    agent_assignments=agent_assignments
                )
        
        elif subcommunity:

            manager = CommunityMemberCountManager(community_uid=subcommunity.uid)

            membercount=len(subcommunity.sub_community_members.all())
            # Set counts
            manager.update_counts_if_needed(membercount,"subcommunity")

            # Get counts
            counts = manager.get_counts()
            inner_member_count= counts['innermembercount']
            outer_member_count= counts['outermembercount']
            universe_member_count= counts['universemembercount']
            member_count=counts['membercount']

            membership_exists = helperfunction.get_membership_for_user_in_sub_community(user_node, subcommunity)
            
            community_reaction_manager = CommunityReactionManager.objects.filter(
                    community_uid=subcommunity.uid).first()

            if community_reaction_manager:
                    all_reactions = community_reaction_manager.community_vibe
                    sorted_reactions = sorted(all_reactions, key=lambda x: x.get(
                        'cumulative_vibe_score', 0), reverse=True)
                    vibes_count = sum(reaction.get('vibes_count', 0) for reaction in all_reactions)

            else:
                    sorted_reactions = CommunityVibe.objects.all()[:10]
                    vibes_count = 0
            try:
                post_count = len([post for post in subcommunity.community_post.all() if not post.is_deleted])
            except Exception:
                post_count = 0


            i_admin = False
            is_login_user_mem = False
            if membership_exists:
                is_login_user_mem = True
                if membership_exists.is_admin == True:
                    i_admin = True
            
            # Get agent-related data for subcommunity
            leader_agent = cls._get_leader_agent(subcommunity)
            has_leader_agent = leader_agent is not None
            agent_assignments = cls._get_agent_assignments(subcommunity)
            
            return cls(
                    uid=subcommunity.uid,
                    name=subcommunity.name,
                    description=subcommunity.description,
                    community_type=subcommunity.sub_community_group_type,
                    community_circle=subcommunity.sub_community_circle,
                    room_id=subcommunity.room_id,
                    created_date=subcommunity.created_date,
                    updated_date=subcommunity.updated_date,
                    number_of_members=member_count,
                    innermembercount=inner_member_count,
                    outermembercount=outer_member_count,
                    universemembercount=universe_member_count,
                    group_invite_link=subcommunity.group_invite_link,
                    group_icon_id=subcommunity.group_icon_id,
                    group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(
                        subcommunity.group_icon_id)),
                    cover_image_id=subcommunity.cover_image_id,
                    cover_image_url=FileDetailType(**generate_presigned_url.generate_file_info(
                        subcommunity.cover_image_id)) if subcommunity.cover_image_id else None,
                    category=subcommunity.category,
                    is_login_user_member=is_login_user_mem,
                    is_admin=i_admin,
                    community_level="SubCommunity",
                    created_by=UserCommunityDetailsType.from_neomodel(
                        subcommunity.created_by.single()) if subcommunity.created_by.single() else None,
                    community_vibe_list=[VibeCommunityListType.from_neomodel(
                        vibe) for vibe in sorted_reactions],
                    my_community_vibe=[],
                    # child_community=[],
                    # sibling_community=[],
                    # parent_community=[CommunityInformationType.from_neomodel(subcommunity.parent_community.single())]if subcommunity.parent_community.single()else None,
                    permission=[CommunityPermissionType.from_neomodel(subcommunity)],
                    vibes_count=vibes_count,
                    post_count=post_count,
                    
                    # Agent management fields
                    leader_agent=leader_agent,
                    has_leader_agent=has_leader_agent,
                    agent_assignments=agent_assignments
            )
    
    @classmethod
    def _get_leader_agent(cls, community):
        """Get the current leader agent for the community, including inherited from parent communities."""
        try:
            # Import here to avoid circular imports
            from agentic.models import AgentCommunityAssignment, Agent
            from agentic.graphql.types import AgentType
            from community.models import SubCommunity, Community

            # Use the inherited methods we added to the models
            if isinstance(community, Community):
                leader_agent = community.get_leader_agent_inherited()
            elif isinstance(community, SubCommunity):
                leader_agent = community.get_leader_agent_inherited()
            else:
                # Fallback to original logic for unknown types
                leader_agent = None

            if leader_agent and leader_agent.agent_type == 'COMMUNITY_LEADER':
                return AgentType.from_neomodel(leader_agent)

            return None
        except Exception as e:
            print(f"Error getting leader agent: {e}")
            return None
    
    @classmethod
    def _get_agent_assignments(cls, community):
        """Get all agent assignments for the community."""
        try:
            assignments = community.get_agent_assignments()
            if assignments:
                # Import here to avoid circular imports
                from agentic.graphql.types import AgentAssignmentType
                return [AgentAssignmentType.from_neomodel(assignment, include_community=False) for assignment in assignments if assignment]
            return []
        except Exception as e:
            print(f"Error getting agent assignments: {e}")
            return []


class CommunityPermissionType(ObjectType):
    only_admin_can_message = graphene.Boolean()
    only_admin_can_add_member = graphene.Boolean()
    only_admin_can_remove_member=graphene.Boolean()
    @classmethod
    def from_neomodel(cls, community):
        # print("community Permission")
        return cls(
            only_admin_can_message=community.only_admin_can_message,
            only_admin_can_add_member=community.only_admin_can_add_member,
            only_admin_can_remove_member=community.only_admin_can_remove_member
        )



class SubCommunityMembershipType(graphene.ObjectType):
    uid = graphene.String()
    is_accepted = graphene.Boolean()
    join_date = graphene.DateTime()
    can_message = graphene.Boolean()
    is_blocked = graphene.Boolean()
    is_notification_muted = graphene.Boolean()

    # Assuming UserType and SubCommunityType are defined similarly in your schema
    user = graphene.Field(UserType)  # Replace UserType with your actual GraphQL type for Users
    sub_community = graphene.Field(lambda: SubCommunityType)  # Replace with the appropriate type

    @classmethod
    def from_neomodel(cls, membership):
        return cls(
            uid=membership.uid,
            is_accepted=membership.is_accepted,
            join_date=membership.join_date,
            can_message=membership.can_message,
            is_blocked=membership.is_blocked,
            is_notification_muted=membership.is_notification_muted,
            user=UserType.from_neomodel(membership.user.single()) if membership.user.single() else None,
            sub_community=SubCommunityType.from_neomodel(membership.sub_community.single()) if membership.sub_community.single() else None,
        )
    

class CommunityRoleManagerDetailsType(graphene.ObjectType):
    role_id=graphene.Int()
    role_name = graphene.String()
    is_deleted = graphene.Boolean()
    is_admin = graphene.Boolean()
    can_edit_group_info = graphene.Boolean()
    can_add_new_member = graphene.Boolean()
    can_remove_member = graphene.Boolean()
    can_block_member = graphene.Boolean()
    can_create_poll = graphene.Boolean()
    can_unblock_member = graphene.Boolean()
    can_invite_member = graphene.Boolean()
    can_approve_join_request = graphene.Boolean()
    can_schedule_message = graphene.Boolean()
    can_manage_media = graphene.Boolean()
    is_active = graphene.Boolean()



class SubCommunityRoleManagerDetailsType(graphene.ObjectType):
    role_id=graphene.Int()
    role_name = graphene.String()
    is_deleted = graphene.Boolean()
    is_admin = graphene.Boolean()
    can_edit_group_info = graphene.Boolean()
    can_add_new_member = graphene.Boolean()
    can_remove_member = graphene.Boolean()
    can_block_member = graphene.Boolean()
    can_create_poll = graphene.Boolean()
    can_unblock_member = graphene.Boolean()
    can_invite_member = graphene.Boolean()
    can_approve_join_request = graphene.Boolean()
    can_schedule_message = graphene.Boolean()
    can_manage_media = graphene.Boolean()
    is_active = graphene.Boolean()


class CommunityAssignedDetailsType(graphene.ObjectType):
    user = graphene.Field(UserType)

class SubCommunityAssignedDetailsType(graphene.ObjectType):
    user = graphene.Field(UserType)
    

class VibeCommunityListType(ObjectType):
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
        

class CommunityInfoType(graphene.ObjectType):
    community=graphene.List(lambda:ParentCommunityInfoType)
    child_community=graphene.List(lambda:SubCommunityInfoType)
    Sibling_community=graphene.List(lambda:SubCommunityInfoType)

    @classmethod
    def from_neomodel(cls, results1,results2=None):
        community_details=[]
        child_details=[]
        sibling_details=[]
        for result in results1:
                community_node=result[0]
                community_details.append(ParentCommunityInfoType.from_neomodel(community_node))
                
        for result in results2:
            sub_community_node=result[0]
            if sub_community_node:
                    if sub_community_node.get("sub_community_type") == "child community":
                        child_details.append(SubCommunityInfoType.from_neomodel(sub_community_node))
                    elif sub_community_node.get("sub_community_type") == "sibling community":
                        sibling_details.append(SubCommunityInfoType.from_neomodel(sub_community_node))

        return cls(

                community=community_details,
                child_community=child_details,
                Sibling_community=sibling_details

        )




class ParentCommunityInfoType(graphene.ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    community_type = graphene.String()
    community_circle = graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()
    number_of_members = graphene.Int()
    group_invite_link = graphene.String()
    group_icon_id = graphene.String()
    group_icon_url=graphene.Field(FileDetailType)
    category = graphene.String()

    @classmethod
    def from_neomodel(cls, community_node,sub_community_node=None):
        created_date_unix=community_node.get('created_date'),
        created_date=datetime.fromtimestamp(created_date_unix[0])
        updated_date_unix=community_node.get('updated_date'),
        updated_date=datetime.fromtimestamp(updated_date_unix[0])
        

        return cls(
            uid=community_node.get("uid"),
            name=community_node.get("name"),
            description=community_node.get("description"),
            community_type=community_node.get("community_type"),
            community_circle=community_node.get("community_circle"),
            created_date=created_date,
            updated_date=updated_date,
            number_of_members=community_node.get("number_of_members"),
            group_invite_link=community_node.get("group_invite_link", ""),
            group_icon_id=community_node.get("group_icon_id"),
            group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(community_node.get("group_icon_id"))),  # Customize as needed
            category=community_node.get("category"),
        )
    

class SubCommunityInfoType(graphene.ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    sub_community_type = graphene.String()
    sub_community_group_type=graphene.String()
    sub_community_circle = graphene.String()
    created_date = graphene.DateTime()
    updated_date = graphene.DateTime()
    number_of_members = graphene.Int()
    group_invite_link = graphene.String()
    group_icon_id = graphene.String()
    group_icon_url = graphene.Field(FileDetailType)  # Assuming URL is generated similar to Community
    category = graphene.String()
    
    @classmethod
    def from_neomodel(cls, sub_community_node):
        created_date = sub_community_node.get("created_date")
        updated_date = sub_community_node.get("updated_date")
        
        # Construct the SubCommunityInfoType instance with properties from sub_community_node
        return cls(
            uid=sub_community_node.get("uid"),
            name=sub_community_node.get("name"),
            description=sub_community_node.get("description"),
            sub_community_type=sub_community_node.get("sub_community_type"),
            sub_community_group_type=sub_community_node.get("sub_community_group_type"),
            sub_community_circle=sub_community_node.get("sub_community_circle"),
            created_date=datetime.fromtimestamp(created_date) if created_date else None,
            updated_date=datetime.fromtimestamp(updated_date) if updated_date else None,
            number_of_members=sub_community_node.get("number_of_members"),
            group_invite_link=sub_community_node.get("group_invite_link", ""),
            group_icon_id=sub_community_node.get("group_icon_id"),
            group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(sub_community_node.get("group_icon_id"))),  # Customize URL as needed
            category=sub_community_node.get("category")
        )
    

class UserCommunityListType(graphene.ObjectType):
    uid = graphene.String()
    user_id=graphene.String()
    username=graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    is_active = graphene.Boolean()
    user_type = graphene.String()
    profile=graphene.Field(lambda:ProfileCommunityListType)
    member=graphene.Field(lambda:MemberCommunityListType)

    @classmethod
    def from_neomodel(cls, user_node,profile=None,member_node=None):
        return cls(
            uid=user_node['uid'],
            user_id=user_node['user_id'],
            username=user_node['username'],
            email=user_node['email'],
            first_name=user_node['first_name'],
            last_name=user_node['last_name'],
            is_active=user_node['is_active'],
            user_type=user_node['user_type'],
            profile=ProfileCommunityListType.from_neomodel(profile),
            member=MemberCommunityListType.from_neomodel(member_node) if member_node else None
        )

# This belong to FeedTestType
class ProfileCommunityListType(graphene.ObjectType):
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
        # print(type(profile["profile_pic_id"]))
        return cls(
            uid = profile["uid"],
            user_id = profile["user_id"],
            gender = profile["gender"],
            device_id = profile["device_id"],
            fcm_token = profile["fcm_token"],
            bio = profile["bio"],
            designation = profile["designation"],
            worksat = profile["worksat"],
            phone_number = profile["phone_number"],
            born = profile["born"],
            dob = profile["dob"],
            school = profile["school"],
            college = profile["college"],
            lives_in = profile["lives_in"],
            profile_pic_id = profile["profile_pic_id"],
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile["profile_pic_id"])),
        )
    


class MemberCommunityListType(graphene.ObjectType):
    uid = graphene.String()
    is_admin = graphene.Boolean()
    can_add_member = graphene.Boolean()
    can_remove_member = graphene.Boolean()
    is_accepted = graphene.Boolean()
    is_blocked = graphene.Boolean()
    is_notification_muted = graphene.Boolean()
    is_leader = graphene.Boolean()
    can_message = graphene.Boolean()

    @classmethod


    def from_neomodel(cls, member_node):
        return cls(
        uid = member_node['uid'],
        is_admin = member_node['is_admin'],
        can_add_member = member_node['can_add_member'],
        can_remove_member = member_node['can_remove_member'],
        is_accepted = member_node['is_accepted'],
        is_blocked = member_node['is_blocked'],
        is_notification_muted = member_node['is_notification_muted'],
        is_leader = member_node['is_leader'],
        can_message = member_node['can_message']
        )
    





class CommunitySubDetailsType(ObjectType):
    child_community=graphene.List(lambda:SubCommunityNoParentType)
    sibling_community=graphene.List(lambda:SubCommunityNoParentType)
    parent_community=graphene.List(lambda:CommunityInformationType)
    
    
    @classmethod
    def from_neomodel(cls, community=None,subcommunity=None, community_type=None, community_circle=None):

        if community:
            child_communities = community.child_communities.all()
            sibling_communities = community.sibling_communities.all()
            
            # Apply filtering for child communities based on `community_circle` and `community_type`
            if community_circle:
                child_communities = [
                    c for c in child_communities if c.sub_community_circle == community_circle.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_circle == community_circle.value
                ]
            if community_type:
                child_communities = [
                    c for c in child_communities if c.sub_community_group_type == community_type.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_group_type == community_type.value
                ]
        
        elif subcommunity:
            parent_community = subcommunity.parent_community.single()
            
            parent_sub_community = subcommunity.sub_community_parent.single()
            child_communities = subcommunity.sub_community_children.all()
            sibling_communities = subcommunity.sub_community_sibling.all() 
            
            flag=True
            if parent_sub_community:
                

                parent_community=parent_sub_community
                flag=False
                if community_circle and parent_community.sub_community_circle != community_circle.value:
                    parent_sub_community = []
                elif community_type and parent_community.sub_community_group_type != community_type.value:
                    parent_sub_community = []
            
            if parent_community:
                if flag:
                    if community_circle and parent_community.community_circle != community_circle.value:
                        parent_community = []
                    elif community_type and parent_community.community_type != community_type.value:
                        parent_community = []
                else:
                    if community_circle and parent_community.sub_community_circle != community_circle.value:
                        parent_community = []
                    elif community_type and parent_community.sub_community_group_type != community_type.value:
                        parent_community = []
                
                if parent_community:
                    parent_communities = [parent_community]
            
            # Apply filtering for child communities based on `community_circle` and `community_type`
            if community_circle:
                child_communities = [
                    c for c in child_communities if c.sub_community_circle == community_circle.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_circle == community_circle.value
                ]
            if community_type:
                child_communities = [
                    c for c in child_communities if c.sub_community_group_type == community_type.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_group_type == community_type.value
                ]

        return cls(
            child_community=[SubCommunityNoParentType.from_neomodel(sub_community)for sub_community in child_communities]if child_communities else [],
            sibling_community=[SubCommunityNoParentType.from_neomodel(sub_community)for sub_community in sibling_communities]if sibling_communities else [],
            parent_community=[CommunityInformationType.from_neomodel(parent_community)]if parent_community else [],
            
        )




class CommunityCategoryType(ObjectType):
    title=graphene.String()
    data=graphene.List(lambda:CommunityFeedType)
   

    @classmethod
    def from_neomodel(cls,details,community_type=None, search=None):
            
            
            data=[]
            
            # Build search filter if search term is provided
            search_filter = ""
            params = {}
            if search:
                search_filter = "AND (toLower(entity.name) CONTAINS toLower($search_term) OR toLower(entity.description) CONTAINS toLower($search_term))"
                params["search_term"] = search
            
            if details=="Popular Community":
                if community_type:
                    params["community_type"] = community_type.value
                    if search:
                        # Create search-enabled query for popular communities with filter
                        query = f"""
                        call(){{
                            // First part for Community
                            MATCH (c:Community {{community_type:$community_type}})
                            WITH c AS entity
                            WHERE true {search_filter}
                            RETURN entity
                            LIMIT 15
                            
                            UNION ALL
                            
                            MATCH (sc:SubCommunity {{sub_community_group_type:$community_type}})
                            WITH sc AS entity
                            WHERE true {search_filter}
                            RETURN entity
                            LIMIT 15
                        }}
                        
                        RETURN entity
                        ORDER by entity.number_of_members DESC, entity.created_date DESC
                        LIMIT 20
                        """
                        results1,_ = db.cypher_query(query, params)
                    else:
                        results1,_ = db.cypher_query(fetch_popular_community_feed_with_filter,params)
                else:
                    if search:
                        # Create search-enabled query for popular communities
                        query = f"""
                        call(){{
                            // First part for Community
                            MATCH (c:Community)
                            WITH c AS entity
                            WHERE true {search_filter}
                            RETURN entity
                            LIMIT 15
                            
                            UNION ALL
                            
                            MATCH (sc:SubCommunity)
                            WITH sc AS entity
                            WHERE true {search_filter}
                            RETURN entity
                            LIMIT 15
                        }}
                        
                        RETURN entity
                        ORDER by entity.number_of_members DESC, entity.created_date DESC
                        LIMIT 20
                        """
                        results1,_ = db.cypher_query(query, params)
                    else:
                        results1,_ = db.cypher_query(fetch_popular_community_feed)
                for community in results1:
                    community_node = community[0]
                    data.append(
                        CommunityFeedType.from_neomodel(community_node)

                        )
                
            elif details=="Recent Community":
                if community_type:
                    params["community_type"] = community_type.value
                    if search:
                        # Create search-enabled query for recent communities with filter
                        query = f"""
                        call(){{
                            // First part for Community
                            MATCH (c:Community{{community_type:$community_type}})
                            WITH c AS entity
                            WHERE true {search_filter}
                            RETURN entity
                            ORDER by entity.created_date DESC
                            LIMIT 15
                            
                            UNION ALL
                            
                            MATCH (sc:SubCommunity{{sub_community_group_type:$community_type}})
                            WITH sc AS entity
                            WHERE true {search_filter}
                            RETURN entity
                            ORDER by entity.created_date DESC
                            LIMIT 15
                        }}
                        
                        RETURN entity
                        ORDER by entity.created_date DESC
                        LIMIT 20
                        """
                        results2,_ = db.cypher_query(query, params)
                    else:
                        results2,_ = db.cypher_query(fetch_newest_community_feed_with_filter,params)
                else:
                    if search:
                        # Create search-enabled query for recent communities
                        query = f"""
                        call(){{
                            // First part for Community
                            MATCH (c:Community)
                            WITH c AS entity
                            WHERE true {search_filter}
                            RETURN entity
                            LIMIT 15
                            
                            UNION ALL
                            
                            MATCH (sc:SubCommunity)
                            WITH sc AS entity
                            WHERE true {search_filter}
                            RETURN entity
                            LIMIT 15
                        }}
                        
                        RETURN entity
                        ORDER by entity.created_date DESC
                        LIMIT 20
                        """
                        results2,_ = db.cypher_query(query, params)
                    else:
                        results2,_ = db.cypher_query(fetch_newest_community_feed)
                for community in results2:
                    community_node = community[0]
                    data.append(
                        CommunityFeedType.from_neomodel(community_node)

                        )

            # Sort data by created_date in descending order (latest first)
            data.sort(key=lambda x: x.created_date if x.created_date else datetime.min, reverse=True)
            
            return cls(
                title=details,
                data=data
            )

class GroupedCommunityCategoryType(ObjectType):
    title=graphene.String()
    data=graphene.List(lambda:CommunityFeedType)
   

    @classmethod
    def from_neomodel(cls,details,result1):


            data=[]
            for community in result1:
                    community_node = community[0]
                    data.append(
                        CommunityFeedType.from_neomodel(community_node)

                        )
            
           
            return cls(
                title=details,
                data=data
            )



class SecondaryCommunityCategoryType(ObjectType):
    title=graphene.String()
    data=graphene.List(lambda:CommunityFeedType)
   

    @classmethod
    def from_neomodel(cls,details,log_in_uid,user_uid,community_type=None):
            
            
            data=[]
            if details=="All Communities":
               # New query to get all communities for the user without any conditions
               if community_type:
                  params = {"user_uid": user_uid, "community_type": community_type.value}    
                  results,_ = db.cypher_query(get_all_user_communities_with_filter, params)
               else:
                  params = {"user_uid": user_uid}    
                  results,_ = db.cypher_query(get_all_user_communities, params)

               for community in results:
                   community_node = community[0]
                   data.append(
                       CommunityFeedType.from_neomodel(community_node)
                    )
            if details=="Mutual Community":

                if community_type:
                    params = {"log_in_user_uid": log_in_uid,"user_uid":user_uid,"community_type": community_type.value}    
                    results1,_ = db.cypher_query(get_mutual_community_query_with_filter,params)
                else:
                    params = {"log_in_user_uid": log_in_uid,"user_uid":user_uid}    
                    results1,_ = db.cypher_query(get_mutual_community_query,params)

                for community in results1:
                    community_node = community[0]
                    data.append(
                        CommunityFeedType.from_neomodel(community_node)

                        )
                
            elif details=="Interest Community":

                if community_type:
                    params = {"log_in_user_uid": log_in_uid,"user_uid":user_uid,"community_type": community_type.value}    
                    results2,_ = db.cypher_query(get_common_interest_community_query_with_filter,params)
                else:
                    params = {"log_in_user_uid": log_in_uid,"user_uid":user_uid}    
                    results2,_ = db.cypher_query(get_common_interest_community_query,params)

                for community in results2:
                    community_node = community[0]
                    data.append(
                        CommunityFeedType.from_neomodel(community_node)

                        )

            return cls(
                title=details,
                data=data
            )



class CommunityFeedType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    number_of_members = graphene.Int()
    group_invite_link = graphene.String()
    group_icon_id = graphene.String()
    group_icon_url=graphene.Field(FileDetailType)
    category = graphene.String()
    type = graphene.String()
    is_parent_community = graphene.Boolean()
    created_date = graphene.DateTime()
    score = graphene.Float()
    
    
    @classmethod
    def from_neomodel(cls, community):
        if hasattr(community, 'sub_community_type'):
            try: 
                return cls(
                    uid=community.uid,
                    name=community.name,
                    description=community.description,
                    number_of_members=community.number_of_members,
                    group_invite_link=community.group_invite_link,
                    group_icon_id=community.group_icon_id,
                    group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(community.group_icon_id)) if community.group_icon_id else None,
                    category=community.category,
                    type=community.sub_community_type,
                    is_parent_community=False,
                    created_date=datetime.fromtimestamp(community.created_date) if isinstance(community.created_date, (int, float)) else community.created_date,
                    score=generate_connection_score()
                )
            except:
                return cls(
                    uid=community['uid'],
                    name=community['name'],
                    description=community['description'],
                    number_of_members=community['number_of_members'],
                    group_invite_link=community['group_invite_link'],
                    group_icon_id=community['group_icon_id'],
                    group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(community['group_icon_id'])) if community['group_icon_id'] else None,
                    category=community['category'],
                    type=community['community_type'],
                    is_parent_community=community['community_type'] != None,
                    created_date=datetime.fromtimestamp(community.get('created_date')) if isinstance(community.get('created_date'), (int, float)) else community.get('created_date'),
                    score=generate_connection_score()
                )
        else:
            try: 
                return cls(
                    uid=community.uid,
                    name=community.name,
                    description=community.description,
                    number_of_members=community.number_of_members,
                    group_invite_link=community.group_invite_link,
                    group_icon_id=community.group_icon_id,
                    group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(community.group_icon_id)) if community.group_icon_id else None,
                    category=community.category,
                    type=community.community_type,
                    is_parent_community=community.community_type != None,
                    created_date=datetime.fromtimestamp(community.created_date) if isinstance(community.created_date, (int, float)) else community.created_date,
                    score=generate_connection_score()
                )
                
            except:
                return cls(
                    uid=community['uid'],
                    name=community['name'],
                    description=community['description'],
                    number_of_members=community['number_of_members'],
                    group_invite_link=community['group_invite_link'],
                    group_icon_id=community['group_icon_id'],
                    group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(community['group_icon_id'])) if community['group_icon_id'] else None,
                    category=community['category'],
                    type=community['community_type'] if community['community_type'] else community['sub_community_type'],
                    is_parent_community=community['community_type'] != None,
                    created_date=datetime.fromtimestamp(community.get('created_date')) if isinstance(community.get('created_date'), (int, float)) else community.get('created_date'),
                    score=generate_connection_score()
                )
                

class CommunityPostType(ObjectType):
    uid = graphene.String()
    post_title = graphene.String()
    post_text = graphene.String()
    post_type = graphene.String()
    post_file_id =graphene.List(graphene.String)
    post_file_url=graphene.List(FileDetailType)
    privacy = graphene.String()
    comment_count = graphene.Int()
    vibes_count=graphene.Int()
    vibe_score = graphene.Float()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    is_deleted = graphene.Boolean()
    creator = graphene.Field(UserType)
    score = graphene.Float()
    mentioned_users = graphene.List(UserType)

    
    

    @classmethod
    def from_neomodel(cls, post):
        if post.is_deleted==False:
            return cls(
                uid=post.uid,
                post_title=post.post_title,
                post_text=post.post_text,
                post_type=post.post_type,
                post_file_id=post.post_file_id,
                post_file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in post.post_file_id] if post.post_file_id else None),
                privacy=post.privacy,
                comment_count=get_post_comment_count(post.uid),
                vibes_count=get_post_like_count(post.uid),
                vibe_score=post.vibe_score,
                created_at=post.created_at,
                updated_at=post.updated_at,
                is_deleted=post.is_deleted,
                creator=UserType.from_neomodel(post.creator.single()) if post.creator.single() else None,
                score=generate_connection_score(),
            )
    def resolve_mentioned_users(self, info):
        """Get users mentioned in this community post."""
        try:
            from post.services.mention_service import MentionService
            
            mentions = MentionService.get_mentions_for_content('community_post', self.uid)
            
            mentioned_users = []
            for mention in mentions:
                mentioned_user = mention.mentioned_user.single()
                if mentioned_user:
                    mentioned_users.append(UserType.from_neomodel(mentioned_user))
            
            return mentioned_users
            
        except Exception as e:
            return []    

        

    

class CommunityDetailsByCategoryType(ObjectType):
    title = graphene.String()
    data = graphene.List(lambda: CommunityFeedType)

    @classmethod
    def from_neomodel(cls, title, communities):
        return cls(
            title=title,
            data=[CommunityFeedType.from_neomodel(community) for community in communities] if communities else []
        )

class CommunityInfoItemType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    description = graphene.String()
    community_type = graphene.String(name="communityType")
    community_circle = graphene.String(name="communityCircle")
    created_date = graphene.DateTime(name="createdDate")
    updated_date = graphene.DateTime(name="updatedDate")
    number_of_members = graphene.Int(name="numberOfMembers")
    group_invite_link = graphene.String(name="groupInviteLink")
    group_icon_id = graphene.String(name="groupIconId")
    group_icon_url = graphene.Field(FileDetailType,)  # Hide from API
    category = graphene.String()
    created_by = graphene.Field(UserCommunityDetailsType)  # Hide from API

    @classmethod
    def from_neomodel(cls, community):
        if hasattr(community, 'sub_community_type'):
            # This is a SubCommunity
            return cls(
                uid=community.uid,
                name=community.name,
                description=community.description,
                community_type=community.sub_community_group_type,
                community_circle=community.sub_community_circle,
                created_date=community.created_date,
                updated_date=community.updated_date,
                number_of_members=community.number_of_members,
                group_invite_link=community.group_invite_link,
                group_icon_id=community.group_icon_id,
                group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(community.group_icon_id)) if community.group_icon_id else None,
                category=community.category,
                created_by=UserCommunityDetailsType.from_neomodel(community.created_by.single()) if community.created_by.single() else None
            )
        else:
            # This is a Community
            return cls(
                uid=community.uid,
                name=community.name,
                description=community.description,
                community_type=community.community_type,
                community_circle=community.community_circle,
                created_date=community.created_date,
                updated_date=community.updated_date,
                number_of_members=community.number_of_members,
                group_invite_link=community.group_invite_link,
                group_icon_id=community.group_icon_id,
                group_icon_url=FileDetailType(**generate_presigned_url.generate_file_info(community.group_icon_id)) if community.group_icon_id else None,
                category=community.category,
                created_by=UserCommunityDetailsType.from_neomodel(community.created_by.single()) if community.created_by.single() else None
            )

class CommunityDetailsByUidType(ObjectType):
    child_community = graphene.Field(CommunityDetailsByCategoryType)
    sibling_community = graphene.Field(CommunityDetailsByCategoryType)
    parent_community = graphene.Field(CommunityDetailsByCategoryType)

    @classmethod
    def from_neomodel(cls, community=None, subcommunity=None, community_type=None, community_circle=None):
        child_communities = []
        sibling_communities = []
        parent_communities = []

        if community:
            child_communities = community.child_communities.all()
            sibling_communities = community.sibling_communities.all()
            
            # Apply filtering for child communities based on `community_circle` and `community_type`
            if community_circle:
                child_communities = [
                    c for c in child_communities if c.sub_community_circle == community_circle.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_circle == community_circle.value
                ]
            if community_type:
                child_communities = [
                    c for c in child_communities if c.sub_community_group_type == community_type.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_group_type == community_type.value
                ]
        
        elif subcommunity:
            parent_community = subcommunity.parent_community.single()
            
            parent_sub_community = subcommunity.sub_community_parent.single()
            child_communities = subcommunity.sub_community_children.all()
            sibling_communities = subcommunity.sub_community_sibling.all() 
            
            flag = True
            if parent_sub_community:
                parent_community = parent_sub_community
                flag = False
                if community_circle and parent_community.sub_community_circle != community_circle.value:
                    parent_community = None
                elif community_type and parent_community.sub_community_group_type != community_type.value:
                    parent_community = None
            
            if parent_community:
                if flag:
                    if community_circle and parent_community.community_circle != community_circle.value:
                        parent_community = None
                    elif community_type and parent_community.community_type != community_type.value:
                        parent_community = None
                else:
                    if community_circle and parent_community.sub_community_circle != community_circle.value:
                        parent_community = None
                    elif community_type and parent_community.sub_community_group_type != community_type.value:
                        parent_community = None
                
                if parent_community:
                    parent_communities = [parent_community]
            
            # Apply filtering for child communities based on `community_circle` and `community_type`
            if community_circle:
                child_communities = [
                    c for c in child_communities if c.sub_community_circle == community_circle.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_circle == community_circle.value
                ]
            if community_type:
                child_communities = [
                    c for c in child_communities if c.sub_community_group_type == community_type.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_group_type == community_type.value
                ]

        return cls(
            child_community=CommunityDetailsByCategoryType.from_neomodel("childCommunity", child_communities),
            sibling_community=CommunityDetailsByCategoryType.from_neomodel("siblingCommunity", sibling_communities),
            parent_community=CommunityDetailsByCategoryType.from_neomodel("parentCommunity", parent_communities)
        )


class UserAdminCommunitiesResponseType(ObjectType):
    """Paginated response type for user admin communities with total count"""
    communities = graphene.List(CommunityType)
    total = graphene.Int()

    @classmethod
    def create(cls, communities, total):
        """Create a paginated response with communities list and total count"""
        return cls(
            communities=communities,
            total=total
        )

class AllCommunitiesResponseType(ObjectType):
    """Paginated response type for all communities with total count"""
    communities = graphene.List(CommunityType)
    total = graphene.Int()

    @classmethod
    def create(cls, communities, total):
        """Create a paginated response with communities list and total count"""
        return cls(
            communities=communities,
            total=total
        )

class AllSubCommunitiesResponseType(ObjectType):
    """Paginated response type for all subcommunities with total count"""
    subcommunities = graphene.List(SubCommunityType)
    total = graphene.Int()

    @classmethod
    def create(cls, subcommunities, total):
        """Create a paginated response with subcommunities list and total count"""
        return cls(
            subcommunities=subcommunities,
            total=total
        )

class LeaveCommunityChatResponseType(ObjectType):
    """Response type for leaving community Matrix chat room"""
    success = graphene.Boolean()
    message = graphene.String()
    room_id = graphene.String()
    left_at = graphene.DateTime()

    @classmethod
    def create(cls, success, message, room_id=None, left_at=None):
        """Create a response for leaving community chat"""
        return cls(
            success=success,
            message=message,
            room_id=room_id,
            left_at=left_at
        )
    




