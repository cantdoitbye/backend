import asyncio
import graphene
from graphene import Mutation
from graphql import GraphQLError
from datetime import datetime

from .types import *
from community.models import *
from auth_manager.models import Users

from .inputs import *
from .messages import CommMessages
from graphql_jwt.decorators import login_required,superuser_required 
from ..utils import userlist,helperfunction
from graphene_django import DjangoObjectType
from community.utils.generate_community import generate_communities_based_on_interest 
from community.utils.get_community_or_subcommunity import validate_community_admin
from msg.models import MatrixProfile
from community.utils.create_matrix_room_with_token import create_room
from community.utils.matrix_invites import process_matrix_invites
from community.utils.community_decorator import handle_graphql_community_errors 
from auth_manager.Utils.generate_presigned_url import get_valid_image
from community import matrix_logger
from community.services.notification_service import NotificationService
from community.utils.matrix_avatar_manager import set_room_avatar_score_and_filter
from community.utils.matrix_filter_manager import set_community_filter_data
from post.models import Like, PostReactionManager
from post.redis import increment_post_like_count
from user_activity.services.activity_service import ActivityService
from vibe_manager.services.vibe_activity_service import VibeActivityService
from post.services.mention_service import MentionService
from vibe_manager.utils import VibeUtils
from vibe_manager.models import IndividualVibe
from django.utils import timezone
from neomodel import db


# Common constants
ADMIN_USER_ID = "a9e34f9968504580896e722465f034b3"


class SubCommunityRoleManagerType(DjangoObjectType):
    class Meta:
        model = SubCommunityRoleManager


class CommunityRoleManagerType(DjangoObjectType):
    class Meta:
        model = CommunityRoleManager


class CommunityRoleAssignmentType(DjangoObjectType):
    class Meta:
        model = CommunityRoleAssignment


class SubCommunityRoleAssignmentType(DjangoObjectType):
    class Meta:
        model = SubCommunityRoleAssignment

# Breaks into proper module
class CreateCommunity(Mutation):
    """
    Creates a new community with specified members and settings.
    
    This mutation handles the complete community creation process including:
    - Creating the community record
    - Setting up Matrix chat room (if possible)
    - Adding initial members with appropriate permissions
    - Sending notifications to new members
    - Processing Matrix room invitations
    
    Args:
        input (CreateCommunityInput): Community creation data including:
            - name: Community name
            - description: Community description
            - community_circle: Community visibility circle
            - community_type: Type of community
            - category: Community category
            - group_icon_id: Icon identifier
            - member_uid: List of initial member UIDs
    
    Returns:
        CreateCommunity: Response containing:
            - community: Created community object (None in current implementation)
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If authentication fails or invalid member UIDs provided
    
    Note:
        - Creator automatically becomes admin member
        - Matrix room creation is optional and won't block community creation
        - All initial members receive push notifications
    """
    community = graphene.Field(CommunityType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=CreateCommunityInput()

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info,input):
        
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            try:
                created_by = Users.nodes.get(user_id=user_id)
            except Exception as e:
                raise
                
            room_id = None
            
            # Try to create a Matrix room if possible, but don't block community creation if it fails
            try:
                print("Trying to get MatrixProfile")
                matrix_profile = MatrixProfile.objects.get(user=user_id)
                if matrix_profile and matrix_profile.matrix_user_id and matrix_profile.access_token:
                    print("Matrix profile found with valid credentials")
                    matrix_user_id = matrix_profile.matrix_user_id
                    access_token = matrix_profile.access_token
                    room_name = input.get('name', '')
                    topic = str(input.get('description', ''))
                    community_metadata = {
                      'community_type': input.get('community_type').value if input.get('community_type') else '',
                    }
                    print("Creating Matrix room...")
                    room_id = asyncio.run(create_room(
                        access_token=access_token,
                        user_id=matrix_user_id,
                        room_name=room_name,
                        topic=topic,
                        visibility="private",    # Use "private" for invite-only rooms.
                        preset="private_chat",    # Change to "private_chat" if needed.
                        # initial_state=[
                        #    {
                        #       "type": "org.example.community_metadata",  # custom event type
                        #       "state_key": "",
                        #       "content": {
                        #               "community_type": input.get('community_type').value if input.get('community_type') else ''
                        #       }
                        #     }
                        # ]
                    ))
            except MatrixProfile.DoesNotExist:
                print("No Matrix profile found for user")
                matrix_logger.warning(f"No Matrix profile found for user {user_id}, creating community without chat room")
            except Exception as e:
                print(f"Matrix room creation error: {e}")
                matrix_logger.error(f"Failed to create Matrix room: {e}")
            
            # if room_id and input.get('group_icon_id'):
            #      try:
            #         print("Setting community room avatar and score...")
            #         avatar_result = asyncio.run(set_room_avatar_and_score_from_image_id(
            #             access_token=access_token,
            #             user_id=matrix_user_id,
            #             room_id=room_id,
            #             image_id=input.get('group_icon_id')
            #         ))
                    
            #         if avatar_result["success"]:
            #             matrix_logger.info(f"Set avatar and score for community room {room_id}")
            #             print(f"Community avatar and score set successfully: {avatar_result}")
            #         else:
            #             matrix_logger.warning(f"Failed to set community avatar: {avatar_result.get('error')}")
            #             print(f"Failed to set community avatar: {avatar_result.get('error')}")
                    
            #      except Exception as e:
            #         matrix_logger.warning(f"Error setting community avatar: {e}")
            #         print(f"Error setting community avatar: {e}")
            # else:
            #     print(f"DEBUG: Avatar not set. room_id={room_id}, group_icon_id={input.get('group_icon_id')}, access_token={bool(access_token)}, matrix_user_id={bool(matrix_user_id)}")

            community = Community(
                name=input.get('name', ''),
                description=input.get('description', ''),
                community_circle=input.get('community_circle').value,
                community_type=input.get('community_type').value,
                room_id=room_id,
                category=input.get('category', ''),
                group_icon_id=input.get('group_icon_id', ''),
                cover_image_id=input.get('cover_image_id', ''),
                ai_generated = input.get('ai_generated', False),
                tags = input.get('tags', []),
            )
            
            print("Checking member_uid...")
            member_uid=input.get('member_uid') or []
            
            member_uid.append(ADMIN_USER_ID)
            if not member_uid:
                print("No members selected")
                return CreateCommunity(community=None, success=False,message=f"You have not selected any user")
            
            print(f"Member UIDs: {member_uid}")
            
            print("Checking for unavailable users...")
            unavailable_user=userlist.get_unavailable_list_user(member_uid)
            
            if unavailable_user:
                print(f"Unavailable users found: {unavailable_user}")
                return CreateCommunity(community=None, success=False,message=f"These uid's do not correspond to any user {unavailable_user}")

            print("Saving community...")
            community.save()
            
            print("Connecting community with creator...")
            community.created_by.connect(created_by)
            created_by.community.connect(community)

            print("Creating creator membership...")
            #Member who created the community is itself a memeber
            membership = Membership(
                is_admin=True,
                can_message=True,
                is_notification_muted=False
            )
            membership.save()
            membership.user.connect(created_by)
            membership.community.connect(community)
            community.members.connect(membership)

            # Extract mentions from community description
            if description := input.get('description'):
                from post.utils.mention_extractor import MentionExtractor
                
                print("Extracting mentions from community description...")
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(description)
                
                if mentioned_user_uids:
                    print("Creating description mentions...")
                    MentionService.create_mentions(
                        mentioned_user_uids=mentioned_user_uids,
                        content_type='community_description',
                        content_uid=community.uid,
                        mentioned_by_uid=created_by.uid,
                        mention_context='description'
                    )

                        
            if community and access_token:
                 try:

                    community_data = {
                         'community_type': community.community_type,
                         'community_circle': community.community_circle,
                         'category': community.category,
                         'created_date': community.created_date,
                         'community_uid': community.uid,
                         'community_name': community.name,
                    }
                    print("Setting community room filter data...")
                    filter_result = asyncio.run(set_room_avatar_score_and_filter(
                        access_token=access_token,
                        user_id=user_id,
                        room_id=room_id,
                        image_id=community.group_icon_id,
                        community_data=community_data
                    ))
                    
                    if filter_result["success"]:
                        matrix_logger.info(f"Set avatar and score for community room {room_id}")
                        print(f"Community filter data set successfully: {filter_result}")
                    else:
                        matrix_logger.warning(f"Failed to set community filter: {filter_result.get('error')}")
                        print(f"Failed to set community filter data: {filter_result.get('error')}")
                    
                 except Exception as e:
                    matrix_logger.warning(f"Error setting community filter data: {e}")
                    print(f"Error setting community filter data: {e}")
            else:
                print(f"DEBUG: filter data not set. room_id={room_id}, access_token={bool(access_token)}, matrix_user_id={bool(matrix_user_id)}")


            print("Adding other members...")
            members_to_notify = []
            for member in member_uid:
                print(f"Adding member: {member}")
                user_node = Users.nodes.get(uid=member)    
                # Note:- Review and Optimisations required here(we can store can_message,can_edit_group_info,can_add_new_member,is_notification_muted in postgresql)
                membership = Membership(
                    can_message=True,
                    is_notification_muted=False
                )
                if member == ADMIN_USER_ID:
                    membership.is_admin=True
                    membership.can_message=True
                    membership.is_notification_muted=False
                    
                membership.save()
                membership.user.connect(user_node)
                membership.community.connect(community)
                community.members.connect(membership)
                
                # Collect members for notification
                profile = user_node.profile.single()
                if profile and profile.device_id:
                    members_to_notify.append({
                        'device_id': profile.device_id,
                        'uid': user_node.uid
                    })
            
            # Send notifications to initial members
            if members_to_notify:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifyCommunityCreated(
                        creator_name=created_by.username,
                        members=members_to_notify,
                        community_id=community.uid,
                        community_name=community.name,
                        community_icon=community.group_icon_id
                    ))
                finally:
                    loop.close()
            
            # Invite all members to the Matrix room if a room was created
            if room_id:
                print("Initiating Matrix room invitations in background...")
                matrix_logger.info(f"Starting background process to invite {len(member_uid)} members to Matrix room {room_id}")
                
                # Print Matrix members being invited to the room
                print(f"\n=== MATRIX ROOM MEMBERS FOR COMMUNITY '{community.name}' ===")
                print(f"Room ID: {room_id}")
                print(f"Total members to invite: {len(member_uid)}")
                print("Members being invited:")
                for i, uid in enumerate(member_uid, 1):
                    try:
                        user_node = Users.nodes.get(uid=uid)
                        print(f"  {i}. {user_node.username} (UID: {uid})")
                    except Exception as e:
                        print(f"  {i}. Unknown user (UID: {uid}) - Error: {e}")
                print("=" * 60)
                
                # Process member invites in a separate thread
                process_matrix_invites(
                    admin_user_id=user_id,
                    room_id=room_id,
                    member_ids=member_uid
                )

            # Auto-assign agent to community after creation
            agent_assignment_success = False
            agent_name = None
            assigned_agent = None
            try:
                print("Auto-assigning agent to community...")
                from agentic.services.agent_service import AgentService
                
                agent_service = AgentService()
                default_agent = agent_service.get_default_community_agent()
                
                if default_agent:
                    print(f"Found default agent: {default_agent.uid}")
                    assignment = agent_service.assign_agent_to_community(
                        agent_uid=default_agent.uid,
                        community_uid=community.uid,
                        assigned_by_uid=user_id,
                        allow_multiple_leaders=False
                    )
                    print(f"Successfully assigned agent {default_agent.uid} to community {community.uid}")
                    agent_assignment_success = True
                    agent_name = default_agent.name
                    assigned_agent = default_agent
                    
                    # Log the agent assignment
                    from agentic.services.auth_service import AgentAuthService
                    auth_service = AgentAuthService()
                    auth_service.log_agent_action(
                        agent_uid=default_agent.uid,
                        community_uid=community.uid,
                        action_type="auto_assignment",
                        details={
                            "assigned_during": "community_creation",
                            "community_name": community.name,
                            "assigned_by": user_id
                        },
                        success=True
                    )
                    
                    # Add agent to Matrix room if room was created and agent has Matrix profile
                    if room_id and assigned_agent:
                        try:
                            print(f"Adding agent {assigned_agent.name} to Matrix room {room_id}...")
                            from agentic.matrix_utils import join_agent_to_community_matrix_room
                            
                            join_agent_to_community_matrix_room(
                                agent=assigned_agent,
                                community=community
                            )
                            print(f"Successfully added agent {assigned_agent.name} to Matrix room")
                        except Exception as matrix_error:
                            print(f"Failed to add agent to Matrix room (non-critical): {matrix_error}")
                            # Don't fail community creation if agent Matrix join fails
                            import traceback
                            traceback.print_exc()
                else:
                    print("No default agent available for assignment")
                    
            except Exception as agent_error:
                # Don't fail community creation if agent assignment fails
                print(f"Agent assignment failed (non-critical): {agent_error}")
                import traceback
                traceback.print_exc()
            
            # Process tags if provided
            tags = input.get('tags') or []
            if tags:
                print(f"Processing {len(tags)} tags for community...")
                from community.models import CommunityKeyword
                
                for tag in tags:
                    if tag and tag.strip():  # Only process non-empty tags
                        tag_cleaned = tag.strip().lower()
                        try:
                            # Check if keyword already exists
                            existing_keyword = CommunityKeyword.nodes.get(keyword=tag_cleaned)
                            print(f"Tag '{tag_cleaned}' already exists, skipping...")
                        except CommunityKeyword.DoesNotExist:
                            # Create new keyword and associate with community
                            keyword = CommunityKeyword(
                                keyword=tag_cleaned
                            )
                            keyword.save()
                            keyword.community.connect(community)
                            print(f"Created and associated tag: {tag_cleaned}")
                        except Exception as tag_error:
                            print(f"Error processing tag '{tag_cleaned}': {tag_error}")
                            # Don't fail community creation for tag errors
                            continue
            
            print("Community creation completed successfully!")
            
            # Track activity for analytics
            try:
                ActivityService.track_content_interaction_by_id(
                    user_id=user_id,
                    content_type="community",
                    content_id=community.uid,
                    interaction_type="create",
                    metadata={
                        "community_id": community.uid,
                        "community_name": community.name,
                        "community_type": community.community_type,
                        "member_count": len(member_uid) if member_uid else 1,
                        "has_matrix_room": bool(room_id),
                        "agent_assigned": agent_assignment_success
                    }
                )
            except Exception as activity_error:
                print(f"Failed to track community creation activity: {activity_error}")
                # Don't fail community creation if activity tracking fails
            
            # Create enhanced success message
            success_message = str(CommMessages.COMMUNITY_CREATED)
            if agent_assignment_success and agent_name:
                # success_message += f" AI agent '{agent_name}' has been assigned as community leader."
                success_message += ""
            elif not agent_assignment_success:
                # success_message += " Note: No AI agent was assigned to manage this community."
                success_message += ""
            
            # Return success with the community object
            # S3 connection error has been fixed in CommunityType.from_neomodel
            try:
                community_obj = CommunityType.from_neomodel(community)
            except Exception as e:
                print(f"Error converting community to GraphQL type: {e}")
                # If conversion fails, still return success but without community details
                community_obj = None
            
            return CreateCommunity(
                community=community_obj,
                success=True,
                message=success_message
            )
        except Exception as error:
            print(f"ERROR in CreateCommunity: {error}")
            import traceback
            traceback.print_exc()
            message=getattr(error , 'message' , str(error) )
            return CreateCommunity(community=None, success=False,message=message)



class UpdateCommunity(Mutation):
    """
    Updates an existing community's information.
    
    This mutation allows community creators (admins) to modify community details
    such as name, description, category, and group icon.
    
    Args:
        input (UpdateCommunityInput): Update data containing:
            - uid: Community UID to update
            - name: New community name (optional)
            - description: New description (optional)
            - category: New category (optional)
            - group_icon_id: New icon identifier (optional)
    
    Returns:
        UpdateCommunity: Response containing:
            - community: Updated community object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the community creator or community not found
    
    Note:
        - Only the community creator can update community information
        - Image validation is performed for group_icon_id if provided
    """
    community = graphene.Field(CommunityType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=UpdateCommunityInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)

            # checking if user is admin of the community
            community = Community.nodes.get(uid=input.uid)
            membership = None
            
            for member in community.members.all():
                member_user = member.user.single()
                # Convert both to int for comparison to handle type mismatches
                if int(member_user.user_id) == int(user_id):
                    membership = member
                    break
            
            if not membership:
                return UpdateCommunity(community=None, success=False, message="You are not a member of this community")
            
            if not membership.is_admin:
                return UpdateCommunity(community=None, success=False, message="You must be an admin to update this community")
            # for id in input.file_id:
            if input.group_icon_id:
                valid_id=get_valid_image(input.group_icon_id)

            for key, value in input.items():
                setattr(community, key, value)
            community.save()

            # Extract mentions from updated community description  
            if description := input.get('description'):
                from post.utils.mention_extractor import MentionExtractor
                
                print("Extracting mentions from updated community description...")
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(description)
                
                if mentioned_user_uids:
                    # Clear existing mentions for this community description
                    try:
                        existing_mentions = MentionService.get_mentions_for_content('community_description', community.uid)
                        for mention in existing_mentions:
                            mention.is_active = False
                            mention.save()
                    except Exception as e:
                        print(f"Error clearing existing mentions: {e}")
                    
                    # Create new mentions
                    MentionService.create_mentions(
                        mentioned_user_uids=mentioned_user_uids,
                        content_type='community_description',
                        content_uid=community.uid,
                        mentioned_by_uid=created_by.uid,
                        mention_context='description'
                    )

            if community and community.room_id:
                try:
                    print(f"Updating Matrix room avatar for community {community.uid}")
                    matrix_profile = MatrixProfile.objects.get(user=user_id)
                    if matrix_profile.access_token and matrix_profile.matrix_user_id:
                        # avatar_result = asyncio.run(set_room_avatar_and_score_from_image_id(
                        #     access_token=matrix_profile.access_token,
                        #     user_id=matrix_profile.matrix_user_id,
                        #     room_id=community.room_id,
                        #     image_id=input.group_icon_id
                        # ))

                        community_data = {
                         'community_type': community.community_type,
                         'community_circle': community.community_circle,
                         'category': community.category,
                         'created_date': community.created_date,
                        }
                        print("Setting community room filter data...")
                        avatar_result = asyncio.run(set_room_avatar_score_and_filter(
                        access_token=matrix_profile.access_token,
                        user_id=matrix_profile.matrix_user_id,
                        room_id=community.room_id,
                        image_id=community.group_icon_id,
                        community_data=community_data
                        ))
                        
                        if avatar_result["success"]:
                            matrix_logger.info(f"Updated Matrix room avatar for community {community.uid}")
                            print(f"Community Matrix avatar updated successfully: {avatar_result}")
                        else:
                            matrix_logger.warning(f"Failed to update community Matrix avatar: {avatar_result.get('error')}")
                            print(f"Failed to update community Matrix avatar: {avatar_result.get('error')}")
                    else:
                        print("Matrix profile missing credentials for avatar update")
                        
                except MatrixProfile.DoesNotExist:
                    print(f"No Matrix profile found for user {user_id}")
                except Exception as e:
                    matrix_logger.warning(f"Error updating community Matrix avatar: {e}")
                    print(f"Error updating community Matrix avatar: {e}")


            members = community.members.all()
            members_to_notify = []
            for member in members:
                user = member.user.single()  # Get user from membership
                if user and user.uid != created_by.uid:  # Don't notify the creator
                    profile = user.profile.single()
                    if profile and profile.device_id:
                        members_to_notify.append({
                            'device_id': profile.device_id,
                            'uid': user.uid
                        })
            # Send notifications
            if members_to_notify:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifyCommunityUpdated(
                        updater_name=created_by.username,
                        members=members_to_notify,
                        community_name=community.name,
                        community_id=community.uid
                    ))
                finally:
                    loop.close()
            return UpdateCommunity(community=CommunityType.from_neomodel(community), success=True, message=CommMessages.COMMUNITY_UPDATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateCommunity(community=None, success=False, message=message)


class DeleteCommunity(Mutation):
    """
    Deletes an existing community.
    
    This mutation allows community creators (admins) to permanently delete
    their communities. Only the original creator can perform this action.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: Community UID to delete
    
    Returns:
        DeleteCommunity: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the community creator or community not found
    
    Note:
        - Only the community creator can delete the community
        - This action is irreversible and removes all community data
    """
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)
            
            # checking user login is admin or not (person who created community)
            flag_community=0
            for community in created_by.community.all():
                if community.uid==input.uid:
                    flag_community=1
                    break
            if flag_community==0:
                return DeleteCommunity(success=True,message="You are not an admin")
            
            community = Community.nodes.get(uid=input.uid)
            community.delete()
            return DeleteCommunity(success=True,message=CommMessages.COMMUNITY_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteCommunity(success=False,message=message)

class CreateCommunityMessage(Mutation):
    """
    Creates a new message in a community.
    
    This mutation allows community members to post messages within a community.
    Only members of the community can create messages. Requires superuser privileges.
    
    Args:
        input (CreateCommMessageInput): Message data containing:
            - community_uid: UID of the target community
            - content: Message content
            - file_id: Optional file attachment ID
            - title: Message title
    
    Returns:
        CreateCommunityMessage: Response containing:
            - community_messages: Created message object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not authenticated, not a community member, or lacks superuser privileges
    
    Note:
        - Only community members can create messages
        - Requires superuser privileges
        - Message content and attachments are validated
    """
    community_messages = graphene.Field(CommunityMessagesType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=CreateCommMessageInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')

            sender_user = Users.nodes.get(user_id=user_id)
            
            community = Community.nodes.get(uid=input.community_uid)
            member_node=community.members.all()
            flag=0
            for member in member_node:
                current_sender = member.user.single()
                if current_sender:
                    
                    if current_sender.email == sender_user.email:
                    # Found a match, break out of the loop
                        flag+=1
                        break
                
         
            # If no match was found after iterating through all members
            if flag == 0:
                return CreateCommunityMessage(community_messages=None, success=False, message="You are not a member of this community")

                    
            communitymessage = CommunityMessages(
                content=input.get('content', ''),
                file_id=input.get('file_id'),
                title=input.get('title', ''),
            )
            communitymessage.save()
            communitymessage.community.connect(community)
            communitymessage.sender.connect(sender_user)
            community.communitymessage.connect(communitymessage)

            members = community.members.all()
            members_to_notify = []
            for member in members:
                user = member.user.single()  # Get user from membership
                if user and user.uid != sender_user.uid:  # Don't notify the sender
                    profile = user.profile.single()
                    if profile and profile.device_id:
                        members_to_notify.append({
                            'device_id': profile.device_id,
                            'uid': user.uid
                        })

            # Send notifications to community members
            if members_to_notify:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifyCommunityMessage(
                        sender_name=sender_user.username,
                        members=members_to_notify,
                        community_name=community.name,
                        message_preview=communitymessage.content or communitymessage.title or "New message",
                        message_id=communitymessage.uid,
                        community_id=community.uid
                    ))
                finally:
                    loop.close()
            return CreateCommunityMessage(community_messages=CommunityMessagesType.from_neomodel(communitymessage), success=True, message=CommMessages.COMMUNITY_MESSAGE_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityMessage(community_messages=None, success=False, message=message)


class UpdateCommunityMessage(Mutation):
    """
    Updates an existing community message.
    
    This mutation allows authorized users to edit previously posted
    community messages. Requires superuser privileges.
    
    Args:
        input (UpdateCommMessageInput): Update data containing:
            - uid: Message UID to update
            - content: New message content (optional)
            - file_id: New file attachment ID (optional)
            - title: New message title (optional)
    
    Returns:
        UpdateCommunityMessage: Response containing:
            - community_messages: Updated message object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not authenticated, lacks superuser privileges, or message not found
    
    Note:
        - Requires superuser privileges
        - Only specified fields in input are updated
        - Message validation is performed before saving
    """
    community_messages = graphene.Field(CommunityMessagesType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=UpdateCommMessageInput()

    @login_required 
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            communitymessage = CommunityMessages.nodes.get(uid=input.uid)
            for key, value in input.items():
                setattr(communitymessage, key, value)
            communitymessage.save()
            return UpdateCommunityMessage(community_messages=CommunityMessagesType.from_neomodel(communitymessage), success=True,message=CommMessages.COMMUNITY_MESSAGE_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateCommunityMessage(community_messages=None, success=False,message=message)


class DeleteCommunityMessage(Mutation):
    """
    Deletes a community message.
    
    This mutation allows authorized users to delete community messages.
    Requires superuser privileges for execution.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: Message UID to delete
    
    Returns:
        DeleteCommunityMessage: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not authenticated, lacks superuser privileges, or message not found
    
    Note:
        - Requires superuser privileges
        - This action is irreversible
        - Message is permanently removed from the community
    """
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()
    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            communitymessage = CommunityMessages.nodes.get(uid=input.uid)
            communitymessage.delete()
            return DeleteCommunityMessage(success=True,message=CommMessages.COMMUNITY_MESSAGE_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteCommunityMessage(success=False,message=message)


class AddMember(Mutation):
    """
    Adds new members to a community.
    
    This mutation allows authorized users to add new members to a community.
    For private communities or communities with restricted member addition,
    only admins can add new members.
    
    Args:
        input (AddMemberInput): Member addition data containing:
            - community_uid: UID of the target community
            - user_uid: List of user UIDs to add as members
    
    Returns:
        AddMember: Response containing:
            - all_membership: Membership object (implementation specific)
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks authorization, invalid UIDs provided, or users already members
    
    Note:
        - Private communities require admin privileges to add members
        - Validates all user UIDs before processing
        - Sends push notifications to newly added members
        - Processes Matrix room invitations if available
        - Updates community member count automatically
    """
    all_membership = graphene.Field(MembershipType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=AddMemberInput()

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            community = Community.nodes.get(uid=input.community_uid)
            user = Users.nodes.get(user_id=user_id)

            # community = Community.nodes.get(uid=input.community_uid)
            user_uids = input.user_uid
            

            # Checking user_uid entered correct or not
            unavailable_user=userlist.get_unavailable_list_user(user_uids)
            if unavailable_user:
                return AddMember( success=False,message=f"These uid's do not correspond to any user {unavailable_user}")
            # In future it will be improve
            if(community.category=="private" or community.only_admin_can_add_member==True):
            # Check if the log-in user is already a member of the community
                membership_exists = helperfunction.get_membership_for_user_in_community(user, community)

                if not membership_exists:
                    return AddMember(success=False, message="You are not a member of this community and this communnity is private")

                if membership_exists:
                    if membership_exists.is_admin==False:
                        return AddMember(success=False, message="You are not authorised to add new member")
            
            if not user_uids:
                return AddMember(success=False, message="You have not selected any member")
            
            # Check if any of the users are already a member of the community
            for uid in user_uids:
                user_node = Users.nodes.get(uid=uid)
                membership_exists = helperfunction.get_membership_for_user_in_community(user_node, community)
                if membership_exists:
                        return AddMember(success=False, message=f"User {user_node.uid} is already a member")
            
            members_to_notify = []
            for uid in user_uids:
                user_node = Users.nodes.get(uid=uid)
                membership = Membership(
                    can_message=True,
                    is_notification_muted=False
                )
                membership.save()
                membership.user.connect(user_node)
                membership.community.connect(community)
                community.members.connect(membership)

                community.number_of_members=len(community.members.all())
                community.save()
                
                # Collect members for notification
                profile = user_node.profile.single()
                if profile and profile.device_id:
                    members_to_notify.append({
                        'device_id': profile.device_id,
                        'uid': user_node.uid
                    })
            
            # ============= NOTIFICATION CODE START (AddMember) =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyCommunityMemberAdded(
            #             added_by_name=user.username,
            #             members=members_to_notify,
            #             community_id=community.uid,
            #             community_name=community.name,
            #             community_icon=community.group_icon_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            # Send notifications to new members
            if members_to_notify:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="new_members_joined",
                        recipients=members_to_notify,
                        username=user.username,
                        community_name=community.name,
                        community_id=community.uid,
                        community_icon=community.group_icon_id if community.group_icon_id else None
                    )
                except Exception as e:
                    print(f"Failed to send new member notification: {e}")
            # ============= NOTIFICATION CODE END =============
            
            process_matrix_invites(
                admin_user_id=community.created_by.single().user_id,
                room_id=community.room_id,
                member_ids=user_uids
            )
            
            # Track activity for analytics
            try:
                ActivityService.track_content_interaction_by_id(
                    user_id=user.uid,
                    content_type="community",
                    content_id=community.uid,
                    interaction_type="member_added",
                    metadata={
                        "community_name": community.name,
                        "added_members": user_uids,
                        "member_count": len(user_uids),
                        "total_members": community.number_of_members
                    }
                )
            except Exception as e:
                print(f"Failed to track member addition activity: {e}")
            
            return AddMember(all_membership=MembershipType.from_neomodel(membership), success=True,message=CommMessages.COMMUNITY_MEMBER_ADDED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return AddMember(all_membership=None, success=False,message=message)


class RemoveMember(Mutation):
    """
    Removes members from a community.
    
    This mutation allows authorized users to remove existing members from a community.
    Community creators cannot be removed, and authorization is required based on
    community settings.
    
    Args:
        membership_uid (List[str]): List of membership UIDs to remove
    
    Returns:
        RemoveMember: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks authorization, memberships from different communities,
                  or attempting to remove community creator
    
    Note:
        - Community creators cannot be removed
        - All memberships must belong to the same community
        - Requires admin privileges if community restricts member removal
        - Permanently deletes membership records
    """
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        membership_uid = graphene.List(graphene.String, required=True)

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, membership_uid):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)

            # Check if all memberships correspond to the same community
            # Note:- Review and Optimisation needed
            memberships = []
            for uid in membership_uid:
                membership = Membership.nodes.get(uid=uid)
                memberships.append(membership)

            # Assuming that each membership has a 'community' property
            community_ids = [membership.community.single().uid for membership in memberships]
            if len(set(community_ids)) > 1:
                raise Exception("Memberships do not correspond to the same community")

            
            community_uid=community_ids[0]
            community = Community.nodes.get(uid=community_uid)

            creator=membership.user.single()
            created_by=community.created_by.single()
            if creator.email==created_by.email:
                return RemoveMember(success=False, message="Creator can not be removed")
            # Note:- Review and Optimisation needed
            membership_exists = helperfunction.get_membership_for_user_in_community(user, community)
            
            if not membership_exists:
                return RemoveMember(success=False, message="You are not authorised to remove member")

            if membership_exists and community.only_admin_can_remove_member==True:
                if membership_exists.is_admin==False:
                    return RemoveMember(success=False, message="You are not authorised to remove member")


            # Collect member info before deletion for tracking
            removed_members = []
            for uid in membership_uid:
                membership = Membership.nodes.get(uid=uid)
                removed_members.append({
                    "membership_uid": uid,
                    "user_uid": membership.user.single().uid if membership.user.single() else None
                })
                membership.delete()
            
            # Track activity for analytics
            try:
                ActivityService.track_content_interaction_by_id(
                    user_id=user.uid,
                    content_type="community",
                    content_id=community.uid,
                    interaction_type="member_removed",
                    metadata={
                        "community_name": community.name,
                        "removed_members": removed_members,
                        "member_count": len(membership_uid),
                        "remaining_members": community.number_of_members - len(membership_uid)
                    }
                )
            except Exception as e:
                print(f"Failed to track member removal activity: {e}")
                
            return RemoveMember(success=True,message=CommMessages.COMMUNITY_MEMBER_DELETED)
        except Exception as error:
            return RemoveMember(success=False, message=getattr(error,'message',str(error)))




class AddSubCommunityMember(Mutation):
    """
    Adds new members to a sub-community.
    
    This mutation allows authorized users to add new members to a sub-community.
    For private sub-communities or those with restricted member addition,
    only admins can add new members.
    
    Args:
        input (AddSubCommunityMemberInput): Member addition data containing:
            - sub_community_uid: UID of the target sub-community
            - user_uid: List of user UIDs to add as members
    
    Returns:
        AddSubCommunityMember: Response containing:
            - all_membership: Sub-community membership object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks authorization, invalid UIDs provided, or users already members
    
    Note:
        - Private sub-communities require admin privileges to add members
        - Validates all user UIDs before processing
        - Sends push notifications to newly added members
        - Processes Matrix room invitations if available
        - Members must be part of parent community
    """
    all_membership = graphene.Field(SubCommunityMembershipType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=AddSubCommunityMemberInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            sub_community = SubCommunity.nodes.get(uid=input.sub_community_uid)
            user = Users.nodes.get(user_id=user_id)

            community = sub_community.parent_community.single()
            user_uids = input.user_uid

            
            # Checking user_uid entered correct or not
            unavailable_user=userlist.get_unavailable_list_user(user_uids)
            if unavailable_user:
                return AddSubCommunityMember( success=False,message=f"These uid's do not correspond to any user {unavailable_user}")
            # In future it will be improve
            if(sub_community.category=="private" or  sub_community.only_admin_can_add_member==True):
            # Check if the log-in user is already a member of the community
                membership_exists = helperfunction.get_membership_for_user_in_community(user, community)

                if not membership_exists:
                    return AddSubCommunityMember(success=False, message="You are not a member of this community and this communnity is private")

                if membership_exists:
                    if membership_exists.is_admin==False:
                        return AddSubCommunityMember(success=False, message="You are not authorised to add new member")
            
            if not user_uids:
                return AddSubCommunityMember(success=False, message="You have not selected any member")
            
            # Check if any of the users are already a member of the community
            for uid in user_uids:
                user_node = Users.nodes.get(uid=uid)
                membership_exists = helperfunction.get_membership_for_user_in_sub_community(user_node, sub_community)
                if membership_exists:
                        return AddSubCommunityMember(success=False, message=f"User is already a member")
            
            members_to_notify = []
            for uid in user_uids:
                user_node = Users.nodes.get(uid=uid)
                membership = SubCommunityMembership(
                    can_message=True,
                    is_notification_muted=False
                )
                membership.save()
                membership.user.connect(user_node)
                membership.sub_community.connect(sub_community)
                sub_community.sub_community_members.connect(membership)
                
                # Collect members for notification
                profile = user_node.profile.single()
                if profile and profile.device_id:
                    members_to_notify.append({
                        'device_id': profile.device_id,
                        'uid': user_node.uid
                    })

            # ============= NOTIFICATION CODE START (AddSubCommunityMember) =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifySubCommunityMemberAdded(
            #             added_by_name=user.username,
            #             members=members_to_notify,
            #             sub_community_id=sub_community.uid,
            #             sub_community_name=sub_community.name,
            #             sub_community_icon=sub_community.group_icon_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            # Send notifications to new members
            if members_to_notify:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="new_members_joined",
                        recipients=members_to_notify,
                        username=user.username,
                        community_name=sub_community.name,
                        community_id=sub_community.uid,
                        community_icon=sub_community.group_icon_id if sub_community.group_icon_id else None
                    )
                except Exception as e:
                    print(f"Failed to send new sub-community member notification: {e}")
            # ============= NOTIFICATION CODE END =============

            process_matrix_invites(
                admin_user_id=sub_community.created_by.single().user_id,
                room_id=sub_community.room_id,
                member_ids=user_uids
            )
            return AddSubCommunityMember(all_membership=SubCommunityMembershipType.from_neomodel(membership), success=True,message=CommMessages.SUB_COMMUNITY_MEMBER_ADDED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return AddSubCommunityMember(all_membership=None, success=False,message=message)


class RemoveSubCommunityMember(Mutation):
    """
    Removes members from a sub-community.
    
    This mutation allows authorized users to remove existing members from a sub-community.
    Only users with admin privileges in the parent community can remove sub-community members.
    
    Args:
        sub_community_membership_uid (List[str]): List of sub-community membership UIDs to remove
    
    Returns:
        RemoveSubCommunityMember: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks authorization or memberships from different sub-communities
    
    Note:
        - Requires admin privileges in the parent community
        - All memberships must belong to the same sub-community
        - Permanently deletes sub-community membership records
    """
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        sub_community_membership_uid = graphene.List(graphene.String, required=True)

    @handle_graphql_community_errors  
    @login_required
    def mutate(self, info, sub_community_membership_uid):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)

            # Check if all memberships correspond to the same community
            # Note:- Review and Optimisation needed
            memberships = []
            for uid in sub_community_membership_uid:
                membership = SubCommunityMembership.nodes.get(uid=uid)
                memberships.append(membership)
            
            # Assuming that each membership has a 'community' property
            community_ids = [membership.sub_community.single().uid for membership in memberships]
            if len(set(community_ids)) > 1:
                raise Exception("Memberships do not correspond to the same sub_community")

            
            sub_community_uid=community_ids[0]
            sub_community = SubCommunity.nodes.get(uid=sub_community_uid)
            community=sub_community.parent_community.single()
            # Note:- Review and Optimisation needed
            membership_exists = helperfunction.get_membership_for_user_in_community(user, community)
            
            if not membership_exists:
                return RemoveSubCommunityMember(success=False, message="You are not authorised to remove member")

            if membership_exists:
                if membership_exists.is_admin==False:
                    return RemoveSubCommunityMember(success=False, message="You are not authorised to remove member")


            for uid in sub_community_membership_uid:
                membership = SubCommunityMembership.nodes.get(uid=uid)
                membership.delete()
                
            return RemoveSubCommunityMember(success=True,message=CommMessages.SUB_COMMUNITY_MEMBER_REMOVED)
        except Exception as error:
            return RemoveSubCommunityMember(success=False, message=getattr(error,'message',str(error)))


class CreateCommunityReview(Mutation):
    """
    Creates a new review for a community or sub-community.
    
    This mutation allows users to create reviews with ratings and reactions
    for communities or sub-communities. It also manages community reaction
    statistics and vibe tracking.
    
    Args:
        input (CreateCommunityReviewInput): Review data containing:
            - to_community_uid: UID of target community/sub-community
            - title: Review title
            - content: Review content
            - file_id: Optional file attachment ID
            - reaction: Reaction/vibe name
            - vibe: Numeric vibe score
    
    Returns:
        CreateCommunityReview: Response containing:
            - review: Created review object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If authentication fails or invalid file ID provided
    
    Note:
        - Automatically initializes community reaction manager if not exists
        - Updates community vibe statistics
        - Validates file attachments if provided
        - Works with both communities and sub-communities
    """
    review = graphene.Field(CommunityReviewType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=CreateCommunityReviewInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)

            # Review and Optimisation needed
            try:
                community_reaction_manager = CommunityReactionManager.objects.get(community_uid=input.to_community_uid)
            except CommunityReactionManager.DoesNotExist:
                # If no PostReactionManager exists, create and initialize with first 10 vibes
                community_reaction_manager = CommunityReactionManager(community_uid=input.to_community_uid)
                community_reaction_manager.initialize_reactions()  # Add the 10 vibes
                community_reaction_manager.save()

            community_reaction_manager.add_reaction(
                vibes_name=input.reaction,
                score=input.vibe  # Assuming `reaction` is a numeric score to be averaged
            )
            community_reaction_manager.save()

            if input.file_id:
                valid_id=get_valid_image(input.file_id)

            review = CommunityReview(
                title=input.get('title', ''),
                content=input.get('content', ''),
                file_id=input.get('file_id'),
                reaction=input.get('reaction', ''),
                vibe=input.get('vibe', ''),
               

            )
            review.save()
            review.byuser.connect(user)
            try:
                community = Community.nodes.get(uid=input.to_community_uid)
                review.tocommunity.connect(community)
                community.community_review.connect(review)
            except Community.DoesNotExist:
                community = SubCommunity.nodes.get(uid=input.to_community_uid)
                review.tosubcommunity.connect(community)
                community.community_review.connect(review)
            
                
            return CreateCommunityReview(review=CommunityReviewType.from_neomodel(review), success=True,message=CommMessages.COMMUNITY_REVIEW_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateCommunityReview(review=None, success=False,message=message)


class UpdateCommunityReview(Mutation):
    """
    Updates an existing community review.
    
    This mutation allows users to modify their previously created community
    or sub-community reviews, including content, attachments, and ratings.
    
    Args:
        input (UpdateCommunityReviewInput): Update data containing:
            - uid: Review UID to update
            - title: New review title (optional)
            - content: New review content (optional)
            - file_id: New file attachment ID (optional)
            - reaction: New reaction/vibe name (optional)
            - vibe: New numeric vibe score (optional)
    
    Returns:
        UpdateCommunityReview: Response containing:
            - review: Updated review object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If review not found or invalid file ID provided
    
    Note:
        - Validates file attachments if provided
        - Only specified fields in input are updated
        - Review validation is performed before saving
    """
    review = graphene.Field(CommunityReviewType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=UpdateCommunityReviewInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            review = CommunityReview.nodes.get(uid=input.uid)
            # for id in input.file_id:
            valid_id=get_valid_image(input.file_id)

            for key, value in input.items():
                setattr(review, key, value)
            review.save()
            return UpdateCommunityReview(review=CommunityReviewType.from_neomodel(review), success=True,message=CommMessages.COMMUNITY_REVIEW_UPDATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return UpdateCommunityReview(review=None, success=False,message=message)


class DeleteCommunityReview(Mutation):
    """
    Deletes a community review.
    
    This mutation allows users to delete their previously created community
    or sub-community reviews permanently.
    
    Args:
        uid (DeleteInput): Deletion data containing:
            - uid: Review UID to delete
    
    Returns:
        DeleteCommunityReview: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If review not found or user lacks authorization
    
    Note:
        - This action is irreversible
        - Review is permanently removed from the community/sub-community
    """
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        uid = DeleteInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            communityReview = CommunityReview.nodes.get(uid=input.uid)
            communityReview.delete()
            return DeleteCommunityReview(success=True,message=CommMessages.COMMUNITY_REVIEW_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteCommunityReview(review=None, success=False,message=message)
        

class CreateCommunityGoal(graphene.Mutation):
    """
    Creates a new goal for a community or sub-community.
    
    This mutation allows community/sub-community admins to create goals
    that help define objectives and targets for their communities.
    
    Args:
        input (CreateCommunityGoalInput): Goal creation data containing:
            - community_uid: UID of target community/sub-community
            - name: Goal name
            - description: Goal description
            - file_id: Optional list of file attachment IDs
    
    Returns:
        CreateCommunityGoal: Response containing:
            - goal: Created goal object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks admin privileges or invalid file IDs provided
    
    Note:
        - Only community/sub-community admins can create goals
        - Validates file attachments if provided
        - Works with both communities and sub-communities
        - Goal is automatically linked to the creator
    """
    goal = graphene.Field(CommunityGoalType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCommunityGoalInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            creator = Users.nodes.get(user_id=user_id)

            # Validate community or sub-community admin rights
            is_valid, community, error_message = validate_community_admin(
                user=creator,
                community_uid=input.community_uid,
                helper_function=helperfunction
            )

            if not is_valid:
                return CreateCommunityGoal(goal=None, success=False, message=error_message)
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            goal = CommunityGoal(
                name=input.name,
                description=input.description,
                file_id=input.file_id,
            )
            goal.save()
            goal.created_by.connect(creator)
            if isinstance(community, Community):
                goal.community.connect(community)
                community.communitygoal.connect(goal)
            else:
                goal.subcommunity.connect(community)
                community.communitygoal.connect(goal)

            community_name = community.name
            community_id = community.uid
            members = helperfunction.get_community_members(community)
            members_to_notify = []
            for member in members:
                user = member.user.single()  # Get user from membership
                if user and user.uid != creator.uid:  # Don't notify the creator
                    profile = user.profile.single()
                    if profile and profile.device_id:
                        members_to_notify.append({
                            'device_id': profile.device_id,
                            'uid': user.uid
                        })
            # ============= NOTIFICATION CODE START (CreateCommunityGoal) =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyCommunityGoal(
            #             creator_name=creator.username,
            #             members=members_to_notify,
            #             community_name=community_name,
            #             goal_name=goal.name,
            #             goal_id=goal.uid,
            #             community_id=community_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            # Send notifications to community members
            if members_to_notify:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="community_goal_created",
                        recipients=members_to_notify,
                        goal_name=goal.name,
                        community_name=community_name,
                        community_id=community_id,
                        goal_id=goal.uid
                    )
                except Exception as e:
                    print(f"Failed to send community goal notification: {e}")
            # ============= NOTIFICATION CODE END =============
            
            return CreateCommunityGoal(goal=CommunityGoalType.from_neomodel(goal), success=True, message=CommMessages.COMMUNITY_GOAL_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityGoal(goal=None, success=False, message=message)


class UpdateCommunityGoal(graphene.Mutation):
    """
    Updates an existing community goal.
    
    This mutation allows community admins to modify previously created
    community goals, including name, description, and file attachments.
    
    Args:
        input (UpdateCommunityGoalInput): Update data containing:
            - uid: Goal UID to update
            - name: New goal name (optional)
            - description: New goal description (optional)
            - file_id: New list of file attachment IDs (optional)
    
    Returns:
        UpdateCommunityGoal: Response containing:
            - goal: Updated goal object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the community admin or invalid file IDs provided
    
    Note:
        - Only community admins can update goals
        - Validates file attachments if provided
        - Only specified fields in input are updated
    """
    goal = graphene.Field(CommunityGoalType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateCommunityGoalInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')

            goal = CommunityGoal.nodes.get(uid=input.uid)
            community_uid = goal.community.single().uid

            flag=helperfunction.is_community_created_by_admin(user_id,community_uid)
            if(flag==False):
                return UpdateCommunityGoal(goal=None, success=False, message=CommMessages.COMMUNITY_GOAL_NOT_CREATED_BY_ADMIN)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            for key, value in input.items():
                setattr(goal, key, value)

            goal.save()
            return UpdateCommunityGoal(goal=CommunityGoalType.from_neomodel(goal), success=True, message=CommMessages.COMMUNITY_GOAL_UPDATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateCommunityGoal(goal=None, success=False, message=message)

class DeleteCommunityGoal(graphene.Mutation):
    """
    Deletes a community goal.
    
    This mutation allows community admins to permanently delete
    community goals that are no longer relevant or needed.
    
    Args:
        uid (str): Goal UID to delete
    
    Returns:
        DeleteCommunityGoal: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the community admin or goal not found
    
    Note:
        - Only community admins can delete goals
        - This action is irreversible
        - Goal is permanently removed from the community
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        uid = graphene.String(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, uid):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')

            goal = CommunityGoal.nodes.get(uid=uid)
            community_uid = goal.community.single().uid

            flag=helperfunction.is_community_created_by_admin(user_id,community_uid)
            if(flag==False):
                return DeleteCommunityGoal(success=False, message=CommMessages.COMMUNITY_GOAL_NOT_CREATED_BY_ADMIN)

            goal.delete()
            return DeleteCommunityGoal(success=True, message=CommMessages.COMMUNITY_GOAL_DELETED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteCommunityGoal(success=False, message=message)


class CreateCommunityActivity(graphene.Mutation):
    """
    Creates a new activity for a community or sub-community.
    
    This mutation allows community/sub-community admins to create activities
    that help organize events, tasks, or initiatives within their communities.
    
    Args:
        input (CreateCommunityActivityInput): Activity creation data containing:
            - community_uid: UID of target community/sub-community
            - name: Activity name
            - description: Activity description
            - activity_type: Type/category of the activity
            - file_id: Optional list of file attachment IDs
    
    Returns:
        CreateCommunityActivity: Response containing:
            - activity: Created activity object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks admin privileges or invalid file IDs provided
    
    Note:
        - Only community/sub-community admins can create activities
        - Validates file attachments if provided
        - Works with both communities and sub-communities
        - Activity is automatically linked to the creator
    """
    activity = graphene.Field(CommunityActivityType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCommunityActivityInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            creator = Users.nodes.get(user_id=user_id)

            # Validate community or sub-community admin rights
            is_valid, community, error_message = validate_community_admin(
                user=creator,
                community_uid=input.community_uid,
                helper_function=helperfunction
            )

            if not is_valid:
                return CreateCommunityActivity(activity=None, success=False, message=error_message)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            activity = CommunityActivity(
                name=input.name,
                description=input.description,
                activity_type=input.activity_type,
                file_id=input.file_id,
                date=input.date,
            )
            activity.save()
            activity.created_by.connect(creator)

            if isinstance(community, Community):
                activity.community.connect(community)
                community.communityactivity.connect(activity)
            else:
                activity.subcommunity.connect(community)
                community.communityactivity.connect(activity)

            community_name = community.name
            community_id = community.uid
            members = helperfunction.get_community_members(community)
            members_to_notify = []
            for member in members:
                user = member.user.single()  # Get user from membership
                if user and user.uid != creator.uid:  # Don't notify the creator
                    profile = user.profile.single()
                    if profile and profile.device_id:
                        members_to_notify.append({
                            'device_id': profile.device_id,
                            'uid': user.uid
                        })
            # Send notifications
            if members_to_notify:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifyCommunityActivity(
                        creator_name=creator.username,
                        members=members_to_notify,
                        community_name=community_name,
                        activity_name=activity.name,
                        activity_id=activity.uid,
                        community_id=community_id
                    ))
                finally:
                    loop.close()
            return CreateCommunityActivity(activity=CommunityActivityType.from_neomodel(activity), success=True, message=CommMessages.COMMUNITY_ACTIVITY_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityActivity(activity=None, success=False, message=message)
    
class UpdateCommunityActivity(graphene.Mutation):
    """
    Updates an existing community activity.
    
    This mutation allows community admins to modify previously created
    community activities, including name, description, type, and file attachments.
    
    Args:
        input (UpdateCommunityActivityInput): Update data containing:
            - uid: Activity UID to update
            - name: New activity name (optional)
            - description: New activity description (optional)
            - activity_type: New activity type (optional)
            - file_id: New list of file attachment IDs (optional)
    
    Returns:
        UpdateCommunityActivity: Response containing:
            - activity: Updated activity object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the community admin or invalid file IDs provided
    
    Note:
        - Only community admins can update activities
        - Validates file attachments if provided
        - Only specified fields in input are updated
    """
    activity = graphene.Field(CommunityActivityType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateCommunityActivityInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')

            activity = CommunityActivity.nodes.get(uid=input.uid)
            community_uid = activity.community.single().uid

            flag = helperfunction.is_community_created_by_admin(user_id, community_uid)
            if flag == False:
                return UpdateCommunityActivity(activity=None, success=False, message=CommMessages.COMMUNITY_ACTIVITY_NOT_CREATED_BY_ADMIN)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            for key, value in input.items():
                setattr(activity, key, value)

            activity.save()
            return UpdateCommunityActivity(activity=CommunityActivityType.from_neomodel(activity), success=True, message=CommMessages.COMMUNITY_ACTIVITY_UPDATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateCommunityActivity(activity=None, success=False, message=message)
       
class DeleteCommunityActivity(graphene.Mutation):
    """
    Deletes a community activity.
    
    This mutation allows community admins to permanently delete
    community activities that are no longer relevant or needed.
    
    Args:
        uid (str): Activity UID to delete
    
    Returns:
        DeleteCommunityActivity: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the community admin or activity not found
    
    Note:
        - Only community admins can delete activities
        - This action is irreversible
        - Activity is permanently removed from the community
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        uid = graphene.String(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, uid):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')

            activity = CommunityActivity.nodes.get(uid=uid)
            community_uid = activity.community.single().uid

            flag = helperfunction.is_community_created_by_admin(user_id, community_uid)
            if flag == False:
                return DeleteCommunityActivity(success=False, message=CommMessages.COMMUNITY_ACTIVITY_NOT_CREATED_BY_ADMIN)

            activity.delete()
            return DeleteCommunityActivity(success=True, message=CommMessages.COMMUNITY_ACTIVITY_DELETED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteCommunityActivity(success=False, message=message)


class CreateCommunityAffiliation(graphene.Mutation):
    """
    Creates a new affiliation for a community or sub-community.
    
    This mutation allows community/sub-community admins to create affiliations
    that represent partnerships, collaborations, or associations with external entities.
    
    Args:
        input (CreateCommunityAffiliationInput): Affiliation creation data containing:
            - community_uid: UID of target community/sub-community
            - entity: Name of the affiliated entity
            - date: Date of affiliation
            - subject: Subject or purpose of affiliation
            - file_id: Optional list of file attachment IDs
    
    Returns:
        CreateCommunityAffiliation: Response containing:
            - affiliation: Created affiliation object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks admin privileges or invalid file IDs provided
    
    Note:
        - Only community/sub-community admins can create affiliations
        - Validates file attachments if provided
        - Works with both communities and sub-communities
        - Affiliation is automatically linked to the creator
    """
    affiliation = graphene.Field(CommunityAffiliationType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCommunityAffiliationInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            creator = Users.nodes.get(user_id=user_id)

            # Validate community or sub-community admin rights
            is_valid, community, error_message = validate_community_admin(
                user=creator,
                community_uid=input.community_uid,
                helper_function=helperfunction
            )

            if not is_valid:
                return CreateCommunityAffiliation(affiliation=None, success=False, message=error_message)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            affiliation = CommunityAffiliation(
                entity=input.entity,
                date=input.date,
                subject=input.subject,
                file_id=input.file_id,
            )
            
            affiliation.save()
            affiliation.created_by.connect(creator)

            if isinstance(community, Community):
                affiliation.community.connect(community)
                community.communityaffiliation.connect(affiliation)
            else:
                affiliation.subcommunity.connect(community)
                community.communityaffiliation.connect(affiliation)

            community_name = community.name
            community_id = community.uid
            members = helperfunction.get_community_members(community)
            members_to_notify = []
            for member in members:
                user = member.user.single()  # Get user from membership
                if user and user.uid != creator.uid:  # Don't notify the creator
                    profile = user.profile.single()
                    if profile and profile.device_id:
                        members_to_notify.append({
                            'device_id': profile.device_id,
                            'uid': user.uid
                        })
            # ============= NOTIFICATION CODE START (CreateCommunityAffiliation) =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyCommunityAffiliation(
            #             creator_name=creator.username,
            #             members=members_to_notify,
            #             community_name=community_name,
            #             affiliation_entity=affiliation.entity,
            #             affiliation_id=affiliation.uid,
            #             community_id=community_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            # Send notifications to community members
            if members_to_notify:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="community_affiliation_created",
                        recipients=members_to_notify,
                        community_name=community_name,
                        affiliation_entity=affiliation.entity,
                        community_id=community_id,
                        affiliation_id=affiliation.uid
                    )
                except Exception as e:
                    print(f"Failed to send community affiliation notification: {e}")
            # ============= NOTIFICATION CODE END =============
            
            return CreateCommunityAffiliation(affiliation=CommunityAffiliationType.from_neomodel(affiliation), success=True, message=CommMessages.COMMUNITY_AFFILIATION_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityAffiliation(affiliation=None, success=False, message=message)

class UpdateCommunityAffiliation(graphene.Mutation):
    """
    Updates an existing community affiliation.
    
    This mutation allows community/sub-community admins to modify previously
    created affiliations, including entity name, date, subject, and file attachments.
    
    Args:
        input (UpdateCommunityAffiliationInput): Update data containing:
            - uid: Affiliation UID to update
            - entity: New entity name (optional)
            - date: New affiliation date (optional)
            - subject: New subject or purpose (optional)
            - file_id: New list of file attachment IDs (optional)
    
    Returns:
        UpdateCommunityAffiliation: Response containing:
            - affiliation: Updated affiliation object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks admin privileges or invalid file IDs provided
    
    Note:
        - Only community/sub-community admins can update affiliations
        - Validates file attachments if provided
        - Only specified fields in input are updated
    """
    affiliation = graphene.Field(CommunityAffiliationType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateCommunityAffiliationInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')

            affiliation = CommunityAffiliation.nodes.get(uid=input.uid)
            community_uid = affiliation.community.single().uid

            flag = helperfunction.is_community_created_by_admin(user_id, community_uid)
            if flag == False:
                return UpdateCommunityAffiliation(affiliation=None, success=False, message=CommMessages.COMMUNITY_AFFILIATION_NOT_CREATED_BY_ADMIN)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            for key, value in input.items():
                setattr(affiliation, key, value)

            affiliation.save()
            return UpdateCommunityAffiliation(affiliation=CommunityAffiliationType.from_neomodel(affiliation), success=True, message=CommMessages.COMMUNITY_AFFILIATION_UPDATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateCommunityAffiliation(affiliation=None, success=False, message=message)

class DeleteCommunityAffiliation(graphene.Mutation):
    """
    Deletes a community affiliation.
    
    This mutation allows community/sub-community admins to permanently delete
    affiliations that are no longer relevant or active.
    
    Args:
        uid (str): Affiliation UID to delete
    
    Returns:
        DeleteCommunityAffiliation: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks admin privileges or affiliation not found
    
    Note:
        - Only community/sub-community admins can delete affiliations
        - This action is irreversible
        - Affiliation is permanently removed from the community
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        uid = graphene.String(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, uid):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')

            affiliation = CommunityAffiliation.nodes.get(uid=uid)
            community_uid = affiliation.community.single().uid

            flag = helperfunction.is_community_created_by_admin(user_id, community_uid)
            if flag == False:
                return DeleteCommunityAffiliation(success=False, message=CommMessages.COMMUNITY_AFFILIATION_NOT_CREATED_BY_ADMIN)

            affiliation.delete()
            return DeleteCommunityAffiliation(success=True, message=CommMessages.COMMUNITY_AFFILIATION_DELETED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteCommunityAffiliation(success=False, message=message)

class CreateCommunityAchievement(graphene.Mutation):
    """
    Creates a new achievement for a community or sub-community.
    
    This mutation allows community/sub-community admins to create achievements
    that represent accomplishments, milestones, or recognitions for the community.
    
    Args:
        input (CreateCommunityAchievementInput): Achievement creation data containing:
            - community_uid: UID of target community/sub-community
            - entity: Name or title of the achievement
            - date: Date when achievement was earned
            - subject: Description or details of the achievement
            - file_id: Optional list of file attachment IDs (certificates, images, etc.)
    
    Returns:
        CreateCommunityAchievement: Response containing:
            - achievement: Created achievement object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user lacks admin privileges or invalid file IDs provided
    
    Note:
        - Only community/sub-community admins can create achievements
        - Validates file attachments if provided
        - Works with both communities and sub-communities
        - Achievement is automatically linked to the creator
    """
    achievement = graphene.Field(CommunityAchievementType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCommunityAchievementInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            creator = Users.nodes.get(user_id=user_id)

            # Validate community or sub-community admin rights
            is_valid, community, error_message = validate_community_admin(
                user=creator,
                community_uid=input.community_uid,
                helper_function=helperfunction
            )

            if not is_valid:
                return CreateCommunityAchievement(achievement=None, success=False, message=error_message)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)
            # Normalize/validate date input to accept flexible ISO-8601 strings
            from datetime import datetime
            from graphql import GraphQLError
            def _parse_datetime(value):
                if not value:
                    return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    v = value.strip()
                    if v.endswith('Z'):
                        v = v[:-1] + '+00:00'
                    if len(v) == 10 and v.count('-') == 2:
                        return datetime.fromisoformat(v + 'T00:00:00')
                    try:
                        return datetime.fromisoformat(v)
                    except Exception:
                        try:
                            return datetime.fromisoformat(v + ':00')
                        except Exception:
                            raise GraphQLError("Invalid datetime format. Must be in ISO 8601 format (YYYY-MM-DDThh:mm:ss)")
                raise GraphQLError("Invalid datetime value for 'date'")

            # Build payload for CommunityAchievement with safely parsed datetimes
            achievement_kwargs = {
                'entity': input.entity,
                'subject': input.subject,
                'file_id': input.file_id,
            }

            # Primary date
            if hasattr(CommunityAchievement, 'date'):
                parsed_date = _parse_datetime(input.get('date'))
                if parsed_date is not None:
                    achievement_kwargs['date'] = parsed_date

            # Optional range dates (map camelCase to snake_case if properties exist)
            from_date_value = _parse_datetime(input.get('fromDate'))
            to_date_value = _parse_datetime(input.get('toDate'))
            if from_date_value is not None and hasattr(CommunityAchievement, 'from_date'):
                achievement_kwargs['from_date'] = from_date_value
            if to_date_value is not None and hasattr(CommunityAchievement, 'to_date'):
                achievement_kwargs['to_date'] = to_date_value

            achievement = CommunityAchievement(**achievement_kwargs)
            achievement.save()
            achievement.created_by.connect(creator)

            if isinstance(community, Community):
                achievement.community.connect(community)
                community.communityachievement.connect(achievement)
            else:
                achievement.subcommunity.connect(community)
                community.communityachievement.connect(achievement)

            community_name = community.name
            community_id = community.uid
            members = helperfunction.get_community_members(community)
            members_to_notify = []
            for member in members:
                user = member.user.single()  # Get user from membership
                if user and user.uid != creator.uid:  # Don't notify the creator
                    profile = user.profile.single()
                    if profile and profile.device_id:
                        members_to_notify.append({
                            'device_id': profile.device_id,
                            'uid': user.uid
                        })
            # ============= NOTIFICATION CODE START (CreateCommunityAchievement) =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyCommunityAchievement(
            #             creator_name=creator.username,
            #             members=members_to_notify,
            #             community_name=community_name,
            #             achievement_title=achievement.entity,
            #             achievement_id=achievement.uid,
            #             community_id=community_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            # Send notifications to community members
            if members_to_notify:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="community_achievement_unlocked",
                        recipients=members_to_notify,
                        achievement_name=achievement.entity,
                        community_name=community_name,
                        community_id=community_id,
                        achievement_icon=achievement.file_id[0] if achievement.file_id else None
                    )
                except Exception as e:
                    print(f"Failed to send community achievement notification: {e}")
            # ============= NOTIFICATION CODE END =============
            
            return CreateCommunityAchievement(achievement=CommunityAchievementType.from_neomodel(achievement), success=True, message=CommMessages.COMMUNITY_ACHIEVEMENT_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityAchievement(achievement=None, success=False, message=message)

class UpdateCommunityAchievement(graphene.Mutation):
    """
    Updates an existing community achievement.
    
    This mutation allows community admins to modify previously created
    achievements, including entity name, date, subject, and file attachments.
    
    Args:
        input (UpdateCommunityAchievementInput): Update data containing:
            - uid: Achievement UID to update
            - entity: New entity name (optional)
            - date: New achievement date (optional)
            - subject: New subject or description (optional)
            - file_id: New list of file attachment IDs (optional)
    
    Returns:
        UpdateCommunityAchievement: Response containing:
            - achievement: Updated achievement object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the community admin or invalid file IDs provided
    
    Note:
        - Only community admins can update achievements
        - Validates file attachments if provided
        - Only specified fields in input are updated
    """
    achievement = graphene.Field(CommunityAchievementType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateCommunityAchievementInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')

            achievement = CommunityAchievement.nodes.get(uid=input.uid)
            community_uid = achievement.community.single().uid

            flag = helperfunction.is_community_created_by_admin(user_id, community_uid)
            if flag == False:
                return UpdateCommunityAchievement(achievement=None, success=False, message=CommMessages.COMMUNITY_ACHIEVEMENT_NOT_CREATED_BY_ADMIN)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            # Apply updates with proper date parsing
            from datetime import datetime
            def _parse_datetime(value):
                if not value:
                    return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    v = value.strip()
                    if v.endswith('Z'):
                        v = v[:-1] + '+00:00'
                    if len(v) == 10 and v.count('-') == 2:
                        return datetime.fromisoformat(v + 'T00:00:00')
                    try:
                        return datetime.fromisoformat(v)
                    except Exception:
                        try:
                            return datetime.fromisoformat(v + ':00')
                        except Exception:
                            raise GraphQLError("Invalid datetime format. Must be in ISO 8601 format (YYYY-MM-DDThh:mm:ss)")
                raise GraphQLError("Invalid datetime value for 'date'")

            for key, value in input.items():
                if key in ('date', 'fromDate', 'toDate') and value is not None:
                    parsed = _parse_datetime(value)
                    # Map camelCase to snake_case if necessary
                    if key == 'fromDate' and hasattr(achievement, 'from_date'):
                        setattr(achievement, 'from_date', parsed)
                    elif key == 'toDate' and hasattr(achievement, 'to_date'):
                        setattr(achievement, 'to_date', parsed)
                    elif key == 'date':
                        setattr(achievement, 'date', parsed)
                    else:
                        # If property doesn't exist, ignore silently
                        pass
                else:
                    setattr(achievement, key, value)

            achievement.save()
            return UpdateCommunityAchievement(achievement=CommunityAchievementType.from_neomodel(achievement), success=True, message=CommMessages.COMMUNITY_ACHIEVEMENT_UPDATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateCommunityAchievement(achievement=None, success=False, message=message)

class DeleteCommunityAchievement(graphene.Mutation):
    """
    Deletes a community achievement.
    
    This mutation allows community admins to permanently delete
    achievements that are no longer relevant or were created in error.
    
    Args:
        uid (str): Achievement UID to delete
    
    Returns:
        DeleteCommunityAchievement: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the community admin or achievement not found
    
    Note:
        - Only community admins can delete achievements
        - This action is irreversible
        - Achievement is permanently removed from the community
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        uid = graphene.String(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, uid):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')

            achievement = CommunityAchievement.nodes.get(uid=uid)
            community_uid = achievement.community.single().uid

            flag = helperfunction.is_community_created_by_admin(user_id, community_uid)
            if flag == False:
                return DeleteCommunityAchievement(success=False, message=CommMessages.COMMUNITY_ACHIEVEMENT_NOT_CREATED_BY_ADMIN)

            achievement.delete()
            return DeleteCommunityAchievement(success=True, message=CommMessages.COMMUNITY_ACHIEVEMENT_DELETED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteCommunityAchievement(success=False, message=message)




class MuteCommunityNotification(graphene.Mutation):
    """
    Mutes notifications for a community member.
    
    This mutation allows community members to disable notifications
    from a specific community they are part of.
    
    Args:
        input (MuteCommunityNoficationInput): Mute data containing:
            - community_uid: UID of the community to mute notifications for
    
    Returns:
        MuteCommunityNotification: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not a member of the community
    
    Note:
        - Only community members can mute notifications
        - Prevents duplicate muting (returns error if already muted)
        - User must be authenticated
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = MuteCommunityNoficationInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            community = Community.nodes.get(uid=input.community_uid)
            user = Users.nodes.get(user_id=user_id)

            member_node = helperfunction.get_membership_for_user_in_community(user, community)
            if member_node is None:
                return MuteCommunityNotification(success=False, message=CommMessages.NOT_A_MEMBER_OF_COMMUNITY)

            if member_node.is_notification_muted == True:
                return MuteCommunityNotification(success=False, message=CommMessages.COMMUNITY_NOTIFICATION_ALREADY_MUTED)
            member_node.is_notification_muted = True
            member_node.save()
            
            return MuteCommunityNotification(success=True, message=CommMessages.COMMUNITY_NOTIFICATION_MUTED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return MuteCommunityNotification(success=False, message=message)




class UnMuteCommunityNotification(graphene.Mutation):
    """
    Unmutes notifications for a community member.
    
    This mutation allows community members to re-enable notifications
    from a specific community they previously muted.
    
    Args:
        input (UnMuteCommunityNoficationInput): Unmute data containing:
            - community_uid: UID of the community to unmute notifications for
    
    Returns:
        UnMuteCommunityNotification: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not a member of the community
    
    Note:
        - Only community members can unmute notifications
        - Prevents duplicate unmuting (returns error if already unmuted)
        - User must be authenticated
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UnMuteCommunityNoficationInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            community = Community.nodes.get(uid=input.community_uid)
            user = Users.nodes.get(user_id=user_id)

            member_node = helperfunction.get_membership_for_user_in_community(user, community)
            if member_node is None:
                return UnMuteCommunityNotification(success=False, message=CommMessages.NOT_A_MEMBER_OF_COMMUNITY)

            if member_node.is_notification_muted == False:
                return UnMuteCommunityNotification(success=False, message=CommMessages.COMMUNITY_NOTIFICATION_ALREADY_UnMUTED)
            member_node.is_notification_muted = False
            member_node.save()
            
            return UnMuteCommunityNotification(success=True, message=CommMessages.COMMUNITY_NOTIFICATION_UnMUTED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UnMuteCommunityNotification(success=False, message=message)




class UpdateCommunityGroupInfo(graphene.Mutation):
    """
    Updates community group information.
    
    This mutation allows authorized community members to update
    basic community information such as name, description, and other group details.
    
    Args:
        input (UpdateCommunityGroupInfoInput): Update data containing:
            - community_uid: UID of the community to update
            - Various community fields to update (name, description, etc.)
    
    Returns:
        UpdateCommunityGroupInfo: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not a member or lacks edit permissions
    
    Note:
        - Only members with can_edit_group_info permission can update
        - User must be authenticated and a community member
        - Updates only the fields provided in input
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateCommunityGroupInfoInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            community = Community.nodes.get(uid=input.community_uid)
            user = Users.nodes.get(user_id=user_id)

            member_node = helperfunction.get_membership_for_user_in_community(user, community)
            if member_node is None:
                return UpdateCommunityGroupInfo(success=False, message=CommMessages.NOT_A_MEMBER_OF_COMMUNITY)

            if member_node.can_edit_group_info == False:
                return UpdateCommunityGroupInfo(success=False, message="You are not allowed to edit group info. Please contact admin of the group for more info.")
            
            for key, value in input.items():
                setattr(community, key, value)
            community.save()
            
            return UpdateCommunityGroupInfo(success=True, message="Community updated Successfully")
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateCommunityGroupInfo(success=False, message=message)


class CreateCommunityRoleManager(graphene.Mutation):
    """
    Creates or updates community role management settings.
    
    This mutation allows community admins to define custom roles with specific
    permissions for community members, enabling fine-grained access control.
    
    Args:
        input (CreateManageRoleInput): Role creation data containing:
            - community_uid: UID of the community
            - role_name: Name of the role to create
            - Various permission flags (is_admin, can_edit_group_info, etc.)
    
    Returns:
        CreateCommunityRoleManager: Response containing:
            - community_role_manager: Created or updated role manager object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not a community admin
    
    Note:
        - Only community admins can create/manage roles
        - If role manager exists, adds new role to existing manager
        - If not exists, creates new role manager with the role
        - Supports various permissions like member management, content creation, etc.
    """
    community_role_manager = graphene.Field(CommunityRoleManagerType)
    message = graphene.String()
    success = graphene.Boolean()

    class Arguments:
        input = CreateManageRoleInput(required=True)
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication Failure")

        payload = info.context.payload
        user_id = payload.get('user_id')

        
        
        is_admin = helperfunction.is_community_created_by_admin(user_id, input.community_uid)

        if not is_admin:
            return CreateCommunityRoleManager(
                message="You are not an admin",
                success=False
            )

        try:
            exist_community_role_manager = CommunityRoleManager.objects.filter(
                community_uid=input.community_uid
            ).first()
            if exist_community_role_manager:
                    exist_community_role_manager.add_roles(
                    role_name=input.role_name,
                    is_deleted=input.is_deleted if input.is_deleted is not None else False,
                    is_admin=input.is_admin if input.is_admin is not None else False,
                    can_edit_group_info=input.can_edit_group_info if input.can_edit_group_info is not None else False,
                    can_add_new_member=input.can_add_new_member if input.can_add_new_member is not None else False,
                    can_remove_member=input.can_remove_member if input.can_remove_member is not None else False,
                    can_block_member=input.can_block_member if input.can_block_member is not None else False,
                    can_create_poll=input.can_create_poll if input.can_create_poll is not None else False,
                    can_unblock_member=input.can_unblock_member if input.can_unblock_member is not None else False,
                    can_invite_member=input.can_invite_member if input.can_invite_member is not None else False,
                    can_approve_join_request=input.can_approve_join_request if input.can_approve_join_request is not None else False,
                    can_schedule_message=input.can_schedule_message if input.can_schedule_message is not None else False,
                    can_manage_media=input.can_manage_media if input.can_manage_media is not None else False,
                    is_active=input.is_active if input.is_active is not None else False
                    )
                
                    exist_community_role_manager.save()
                    return CreateCommunityRoleManager(
                    community_role_manager=exist_community_role_manager,
                    success=True,
                    message="Role Created Successfully"
                )

            # Create an instance of SubCommunityRoleManager
            community_role_manager = CommunityRoleManager(
                community_uid=input.community_uid,
                created_by=user,
            )
            
            # Set role related details in role_data JSON field
            community_role_manager.add_roles(
                role_name=input.role_name,
                is_deleted=input.is_deleted if input.is_deleted is not None else False,
                is_admin=input.is_admin if input.is_admin is not None else False,
                can_edit_group_info=input.can_edit_group_info if input.can_edit_group_info is not None else False,
                can_add_new_member=input.can_add_new_member if input.can_add_new_member is not None else False,
                can_remove_member=input.can_remove_member if input.can_remove_member is not None else False,
                can_block_member=input.can_block_member if input.can_block_member is not None else False,
                can_create_poll=input.can_create_poll if input.can_create_poll is not None else False,
                can_unblock_member=input.can_unblock_member if input.can_unblock_member is not None else False,
                can_invite_member=input.can_invite_member if input.can_invite_member is not None else False,
                can_approve_join_request=input.can_approve_join_request if input.can_approve_join_request is not None else False,
                can_schedule_message=input.can_schedule_message if input.can_schedule_message is not None else False,
                can_manage_media=input.can_manage_media if input.can_manage_media is not None else False,
                is_active=input.is_active if input.is_active is not None else False
            )
            
            community_role_manager.save()

            return CreateCommunityRoleManager(
                community_role_manager=community_role_manager,
                success=True,
                message="Role Created Successfully"
            )

        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityRoleManager(
                community_role_manager=None,
                success=False,
                message=message
            )



class CreateSubCommunity(Mutation):
    """
    Creates a new sub-community within an existing parent community.
    
    This mutation allows community admins to create child or sibling sub-communities
    with their own members, settings, and optional Matrix chat room integration.
    
    Args:
        input (CreateSubCommunityInput): Sub-community creation data containing:
            - parent_community_uid: UID of the parent community
            - name: Name of the sub-community
            - description: Description of the sub-community
            - sub_community_circle: Circle type (public/private)
            - sub_community_type: Type (child/sibling community)
            - sub_community_group_type: Group type classification
            - category: Category classification
            - member_uid: List of initial member UIDs
            - group_icon_id: Optional group icon ID
    
    Returns:
        CreateSubCommunity: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not a community admin or invalid member UIDs provided
    
    Note:
        - Only community admins can create sub-communities
        - Validates all member UIDs before creation
        - Creates Matrix chat room if user has Matrix profile
        - Sends notifications to initial members
        - Creator automatically becomes admin of the sub-community
        - Supports both child and sibling community types
    """
    community = graphene.Field(SubCommunityType)  # Added community field
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=CreateSubCommunityInput()

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info,input):
        user=info.context.user
        if user.is_anonymous:
            raise Exception ("Authentication Failure")
            
        payload = info.context.payload
        user_id = payload.get('user_id')
            
        created_by = Users.nodes.get(user_id=user_id)
        room_id = None
            
            # Try to create a Matrix room if possible, but don't block community creation if it fails
        try:
            print("Trying to get MatrixProfile")
            matrix_profile = MatrixProfile.objects.get(user=user_id)
            if matrix_profile and matrix_profile.matrix_user_id and matrix_profile.access_token:
                matrix_user_id = matrix_profile.matrix_user_id
                access_token = matrix_profile.access_token
                room_name = input.get('name', '')
                topic = str(input.get('description', ''))
                    
                print("Creating Matrix room...")
                room_id = asyncio.run(create_room(
                    access_token=access_token,
                    user_id=matrix_user_id,
                    room_name=room_name,
                    topic=topic,
                    visibility="private",    # Use "private" for invite-only rooms.
                    preset="private_chat"    # Change to "private_chat" if needed.
                    ))
        except MatrixProfile.DoesNotExist:
            print("No Matrix profile found for user")
            matrix_logger.warning(f"No Matrix profile found for user {user_id}, creating community without chat room")
        except Exception as e:
            print(f"Matrix room creation error: {e}")
            matrix_logger.error(f"Failed to create Matrix room: {e}")
                # Continue with community creation even if room creation fails


        
            
        # for id in input.file_id:
        if input.group_icon_id:
            valid_id=get_valid_image(input.group_icon_id)
                       
        sub_community = SubCommunity(
            name=input.get('name', ''),
            description=input.get('description', ''),
            sub_community_circle=input.get('sub_community_circle').value,
            sub_community_type=input.get('sub_community_type').value,
            sub_community_group_type=input.get('sub_community_group_type').value,
            category=input.get('category', ''),
            room_id=room_id,
            cover_image_id=input.get('cover_image_id', ''),
            group_icon_id=input.get('group_icon_id', ''), # This should be gather from env files
        )
            
        member_uid=input.get('member_uid') or []
        member_uid.append(ADMIN_USER_ID)

        if created_by.uid not in member_uid:
           member_uid.append(created_by.uid)
        if not member_uid:
            return CreateSubCommunity(community=None, success=False,message=f"You have not selected any user")
        unavailable_user=userlist.get_unavailable_list_user(member_uid)
        if unavailable_user:
            return CreateSubCommunity(community=None, success=False,message=f"These uid's do not correspond to any user {unavailable_user}")
        
        
        try:
            community=Community.nodes.get(uid=input.parent_community_uid)

            membership_exists = helperfunction.get_membership_for_user_in_community(created_by, community)

            if not membership_exists:
                return CreateSubCommunity(community=None, success=False, message="You are not a member of this community and this communnity is private")

            if membership_exists:
                if membership_exists.is_admin==False:
                    return CreateSubCommunity(community=None, success=False, message="You are not authorised to add new member")

            sub_community.save()
            sub_community.created_by.connect(created_by)
            sub_community.parent_community.connect(community)
            if input.get('sub_community_type').value=='child community':
                community.child_communities.connect(sub_community)
            if input.get('sub_community_type').value=='sibling community':
                community.sibling_communities.connect(sub_community)

            # Set Matrix room avatar and filter data for sub-community
            if sub_community and access_token:
                try:
                    sub_community_data = {
                        'community_type': sub_community.sub_community_type,
                        'community_circle': sub_community.sub_community_circle,
                        'category': sub_community.category,
                        'created_date': sub_community.created_date,
                        'community_uid': sub_community.uid,
                        'community_name': sub_community.name,
                    }
                    print("Setting sub-community room filter data...")
                    filter_result = asyncio.run(set_room_avatar_score_and_filter(
                        access_token=access_token,
                        user_id=user_id,
                        room_id=room_id,
                        image_id=sub_community.group_icon_id,
                        community_data=sub_community_data
                    ))
                    
                    if filter_result["success"]:
                        matrix_logger.info(f"Set avatar and score for sub-community room {room_id}")
                        print(f"Sub-community filter data set successfully: {filter_result}")
                    else:
                        matrix_logger.warning(f"Failed to set sub-community filter: {filter_result.get('error')}")
                        print(f"Failed to set sub-community filter data: {filter_result.get('error')}")
                    
                except Exception as e:
                    matrix_logger.warning(f"Error setting sub-community filter data: {e}")
                    print(f"Error setting sub-community filter data: {e}")
            else:
                print(f"DEBUG: sub-community filter data not set. room_id={room_id}, access_token={bool(access_token)}, matrix_user_id={bool(matrix_user_id)}")
            # Note:- Review and Optimisations required here(we can store can_message,can_edit_group_info,can_add_new_member,is_notification_muted in postgresql)
            # Member who created the community is itself a memeber
            membership = SubCommunityMembership(
                is_admin=True,
                can_message=True,
                is_notification_muted=False
            )
            membership.save()
            membership.user.connect(created_by)
            membership.sub_community.connect(sub_community)
            sub_community.sub_community_members.connect(membership)

            members_to_notify = []
            for member in member_uid:

                if member == created_by.uid:
                    continue
                user_node = Users.nodes.get(uid=member)
                
                # Note:- Review and Optimisations required here(we can store can_message,can_edit_group_info,can_add_new_member,is_notification_muted in postgresql)
                membership = SubCommunityMembership(
                    can_message=True,
                    is_notification_muted=False
                )
                if member == ADMIN_USER_ID:
                    membership.is_admin=True
                    membership.can_message=True
                    membership.is_notification_muted=False

                membership.save()
                membership.user.connect(user_node)
                membership.sub_community.connect(sub_community)
                sub_community.sub_community_members.connect(membership)

                sub_community.number_of_members=len(sub_community.sub_community_members.all())
                sub_community.save()
                
                # Collect members for notification
                profile = user_node.profile.single()
                if profile and profile.device_id:
                    members_to_notify.append({
                        'device_id': profile.device_id,
                        'uid': user_node.uid
                    })

            # Send notifications to initial members
            if members_to_notify:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifySubCommunityCreated(
                        creator_name=created_by.username,
                        members=members_to_notify,
                        sub_community_id=sub_community.uid,
                        sub_community_name=sub_community.name,
                        sub_community_icon=sub_community.group_icon_id
                    ))
                finally:
                    loop.close()

            if room_id:
                print("Initiating Matrix room invitations in background...")
                matrix_logger.info(f"Starting background process to invite {len(member_uid)} members to Matrix room {room_id}")
                
                # Process member invites in a separate thread
                process_matrix_invites(
                    admin_user_id=user_id,
                    room_id=room_id,
                    member_ids=member_uid
                )
            return CreateSubCommunity(community=SubCommunityType.from_neomodel(sub_community), success=True,message=CommMessages.COMMUNITY_CREATED)
        
        except Community.DoesNotExist:
            try:
            # If the Community does not exist, try to retrieve a SubCommunity
                community = SubCommunity.nodes.get(uid=input.parent_community_uid)

                if community.sub_community_type == 'child community':
                    return CreateSubCommunity(community=None,success=False,message=CommMessages.SUB_COMMUNITY_NOT_ALLOWED)
                
                membership_exists = helperfunction.get_membership_for_user_in_sub_community(created_by, community)

                if not membership_exists:
                    return CreateSubCommunity(community=None,success=False, message="You are not a member of this community and this communnity is private")

                if membership_exists:
                    if membership_exists.is_admin==False:
                        return CreateSubCommunity(community=None,success=False, message="You are not authorised to add new member")

                sub_community.save()
                sub_community.created_by.connect(created_by)
                sub_community.sub_community_parent.connect(community)
                if input.get('sub_community_type').value == 'child community':
                    community.sub_community_children.connect(sub_community)
                if input.get('sub_community_type').value == 'sibling community':
                    community.sub_community_sibling.connect(sub_community)

                # Set Matrix room avatar and filter data for sub-community
                if sub_community and access_token:
                    try:
                        sub_community_data = {
                            'community_type': sub_community.sub_community_type,
                            'community_circle': sub_community.sub_community_circle,
                            'category': sub_community.category,
                            'created_date': sub_community.created_date,
                            'community_uid': sub_community.uid,
                            'community_name': sub_community.name,
                        }
                        print("Setting sub-community room filter data...")
                        filter_result = asyncio.run(set_room_avatar_score_and_filter(
                            access_token=access_token,
                            user_id=user_id,
                            room_id=room_id,
                            image_id=sub_community.group_icon_id,
                            community_data=sub_community_data
                        ))
                        
                        if filter_result["success"]:
                            matrix_logger.info(f"Set avatar and score for sub-community room {room_id}")
                            print(f"Sub-community filter data set successfully: {filter_result}")
                        else:
                            matrix_logger.warning(f"Failed to set sub-community filter: {filter_result.get('error')}")
                            print(f"Failed to set sub-community filter data: {filter_result.get('error')}")
                        
                    except Exception as e:
                        matrix_logger.warning(f"Error setting sub-community filter data: {e}")
                        print(f"Error setting sub-community filter data: {e}")
                else:
                    print(f"DEBUG: sub-community filter data not set. room_id={room_id}, access_token={bool(access_token)}, matrix_user_id={bool(matrix_user_id)}")
                
                membership = SubCommunityMembership(
                    is_admin=True,
                    can_message=True,
                    is_notification_muted=False
                )
                membership.save()
                membership.user.connect(created_by)
                membership.sub_community.connect(sub_community)
                sub_community.sub_community_members.connect(membership)

                members_to_notify = []
                for member in member_uid:

                    if member == created_by.uid:
                       continue
                    user_node = Users.nodes.get(uid=member)
                    
                    # Note:- Review and Optimisations required here(we can store can_message,can_edit_group_info,can_add_new_member,is_notification_muted in postgresql)
                    membership = SubCommunityMembership(
                        can_message=True,
                        is_notification_muted=False
                    )
                    membership.save()
                    membership.user.connect(user_node)
                    membership.sub_community.connect(sub_community)
                    sub_community.sub_community_members.connect(membership)

                    sub_community.number_of_members=len(sub_community.sub_community_members.all())
                    sub_community.save()
                    
                    # Collect members for notification
                    profile = user_node.profile.single()
                    if profile and profile.device_id:
                        members_to_notify.append({
                            'device_id': profile.device_id,
                            'uid': user_node.uid
                        })

                # Send notifications to initial members
                if members_to_notify:
                    notification_service = NotificationService()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(notification_service.notifySubCommunityCreated(
                            creator_name=created_by.username,
                            members=members_to_notify,
                            sub_community_id=sub_community.uid,
                            sub_community_name=sub_community.name,
                            sub_community_icon=sub_community.group_icon_id
                        ))
                    finally:
                        loop.close()

                if room_id:
                    print("Initiating Matrix room invitations in background...")
                    matrix_logger.info(f"Starting background process to invite {len(member_uid)} members to Matrix room {room_id}")
                    
                    # Process member invites in a separate thread
                    process_matrix_invites(
                        admin_user_id=user_id,
                        room_id=room_id,
                        member_ids=member_uid
                    )
                    return CreateSubCommunity(community=SubCommunityType.from_neomodel(sub_community), success=True,message=CommMessages.COMMUNITY_CREATED)
                
            except Exception as error:
                message=getattr(error , 'message' , str(error) )
                return CreateSubCommunity(community=None, success=False,message=message)


class UpdateSubCommunity(Mutation):
    """
    Updates an existing sub-community.
    
    This mutation allows sub-community admins to modify sub-community
    information including name, description, icons, and other settings.
    
    Args:
        input (UpdateSubCommunityInput): Update data containing:
            - uid: Sub-community UID to update
            - name: New name (optional)
            - description: New description (optional)
            - group_icon_id: New group icon ID (optional)
            - cover_image_id: New cover image ID (optional)
            - Other sub-community fields to update
    
    Returns:
        UpdateSubCommunity: Response containing:
            - community: Updated sub-community object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not a sub-community admin or invalid image IDs provided
    
    Note:
        - Only sub-community admins can update sub-communities
        - Validates image attachments if provided
        - Updates only the fields provided in input
    """
    community = graphene.Field(SubCommunityType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=UpdateSubCommunityInput()
    

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)

            community = SubCommunity.nodes.get(uid=input.uid)

            # checking if user is admin of the sub-community
            membership = None
            
            for member in community.sub_community_members.all():
                member_user = member.user.single()
                # Convert both to int for comparison to handle type mismatches
                if int(member_user.user_id) == int(user_id):
                    membership = member
                    break
            
            if not membership:
                return UpdateSubCommunity(success=False, message="You are not a member of this sub-community")
            
            if not membership.is_admin:
                return UpdateSubCommunity(success=False, message="You must be an admin to update this sub-community")
            
            # for id in input.file_id:
                         # Update group icon if valid
            if input.group_icon_id:
                group_icon = get_valid_image(input.group_icon_id)
                if group_icon:
                    community.group_icon = group_icon
                else:
                    return UpdateSubCommunity(success=False, message="Invalid group_icon_id")

                # Update cover image if valid
            if input.cover_image_id:
                cover_image = get_valid_image(input.cover_image_id)
                if cover_image:
                    community.cover_image = cover_image
                else:
                    return UpdateSubCommunity(success=False, message="Invalid cover_image_id")

            
            for key, value in input.items():
                setattr(community, key, value)
            community.save()
            
            # Update Matrix room avatar and filter data for sub-community
            if community and community.room_id:
                try:
                    print(f"Updating Matrix room avatar for sub-community {community.uid}")
                    matrix_profile = MatrixProfile.objects.get(user=user_id)
                    if matrix_profile.access_token and matrix_profile.matrix_user_id:
                        sub_community_data = {
                            'community_type': community.sub_community_type,
                            'community_circle': community.sub_community_circle,
                            'category': community.category,
                            'created_date': community.created_date,
                        }
                        print("Setting sub-community room filter data...")
                        avatar_result = asyncio.run(set_room_avatar_score_and_filter(
                            access_token=matrix_profile.access_token,
                            user_id=matrix_profile.matrix_user_id,
                            room_id=community.room_id,
                            image_id=community.group_icon_id,
                            community_data=sub_community_data
                        ))
                        
                        if avatar_result["success"]:
                            matrix_logger.info(f"Updated Matrix room avatar for sub-community {community.uid}")
                            print(f"Sub-community Matrix avatar updated successfully: {avatar_result}")
                        else:
                            matrix_logger.warning(f"Failed to update sub-community Matrix avatar: {avatar_result.get('error')}")
                            print(f"Failed to update sub-community Matrix avatar: {avatar_result.get('error')}")
                    else:
                        print("Matrix profile missing credentials for avatar update")
                        
                except MatrixProfile.DoesNotExist:
                    print(f"No Matrix profile found for user {user_id}")
                except Exception as e:
                    matrix_logger.warning(f"Error updating sub-community Matrix avatar: {e}")
                    print(f"Error updating sub-community Matrix avatar: {e}")
            
            return UpdateSubCommunity(community=SubCommunityType.from_neomodel(community), success=True,message=CommMessages.COMMUNITY_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateSubCommunity(community=None, success=False,message=message)


class CreateSubCommunityRoleManager(graphene.Mutation):
    """
    Creates or updates sub-community role management settings.
    
    This mutation allows sub-community admins to define custom roles with specific
    permissions for sub-community members, enabling fine-grained access control.
    
    Args:
        input (CreateManageSubCommunityRoleInput): Role creation data containing:
            - sub_community_uid: UID of the sub-community
            - role_name: Name of the role to create
            - Various permission flags (is_admin, can_edit_group_info, etc.)
    
    Returns:
        CreateSubCommunityRoleManager: Response containing:
            - sub_community_role_manager: Created or updated role manager object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not a sub-community admin
    
    Note:
        - Only sub-community admins can create/manage roles
        - If role manager exists, adds new role to existing manager
        - If not exists, creates new role manager with the role
        - Supports various permissions like member management, content creation, etc.
    """
    sub_community_role_manager = graphene.Field(SubCommunityRoleManagerType)
    message = graphene.String()
    success = graphene.Boolean()

    class Arguments:
        input = CreateManageSubCommunityRoleInput(required=True)

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication Failure")

        payload = info.context.payload
        user_id = payload.get('user_id')

        sub_community = SubCommunity.nodes.get(uid=input.sub_community_uid)
        community_uid = sub_community.parent_community.single().uid
        is_admin = helperfunction.is_community_created_by_admin(user_id, community_uid)

        if not is_admin:
            return CreateSubCommunityRoleManager(
                message="You are not an admin",
                success=False
            )

        try:
            exist_sub_community_role_manager = SubCommunityRoleManager.objects.filter(
                sub_community_uid=input.sub_community_uid
            ).first()
            if exist_sub_community_role_manager:
                    exist_sub_community_role_manager.add_role(
                    role_name=input.role_name,
                    is_deleted=input.is_deleted if input.is_deleted is not None else False,
                    is_admin=input.is_admin if input.is_admin is not None else False,
                    can_edit_group_info=input.can_edit_group_info if input.can_edit_group_info is not None else False,
                    can_add_new_member=input.can_add_new_member if input.can_add_new_member is not None else False,
                    can_remove_member=input.can_remove_member if input.can_remove_member is not None else False,
                    can_block_member=input.can_block_member if input.can_block_member is not None else False,
                    can_create_poll=input.can_create_poll if input.can_create_poll is not None else False,
                    can_unblock_member=input.can_unblock_member if input.can_unblock_member is not None else False,
                    can_invite_member=input.can_invite_member if input.can_invite_member is not None else False,
                    can_approve_join_request=input.can_approve_join_request if input.can_approve_join_request is not None else False,
                    can_schedule_message=input.can_schedule_message if input.can_schedule_message is not None else False,
                    can_manage_media=input.can_manage_media if input.can_manage_media is not None else False,
                    is_active=input.is_active if input.is_active is not None else False
                    )
                
                    exist_sub_community_role_manager.save()
                    return CreateSubCommunityRoleManager(
                    sub_community_role_manager=exist_sub_community_role_manager,
                    success=True,
                    message="Role Created Successfully"
                )

            # Create an instance of SubCommunityRoleManager
            sub_community_role_manager = SubCommunityRoleManager(
                sub_community_uid=input.sub_community_uid,
                created_by=user,
            )
            
            # Set role related details in role_data JSON field
            sub_community_role_manager.add_role(
                role_name=input.role_name,
                is_deleted=input.is_deleted if input.is_deleted is not None else False,
                is_admin=input.is_admin if input.is_admin is not None else False,
                can_edit_group_info=input.can_edit_group_info if input.can_edit_group_info is not None else False,
                can_add_new_member=input.can_add_new_member if input.can_add_new_member is not None else False,
                can_remove_member=input.can_remove_member if input.can_remove_member is not None else False,
                can_block_member=input.can_block_member if input.can_block_member is not None else False,
                can_create_poll=input.can_create_poll if input.can_create_poll is not None else False,
                can_unblock_member=input.can_unblock_member if input.can_unblock_member is not None else False,
                can_invite_member=input.can_invite_member if input.can_invite_member is not None else False,
                can_approve_join_request=input.can_approve_join_request if input.can_approve_join_request is not None else False,
                can_schedule_message=input.can_schedule_message if input.can_schedule_message is not None else False,
                can_manage_media=input.can_manage_media if input.can_manage_media is not None else False,
                is_active=input.is_active if input.is_active is not None else False
            )
            
            sub_community_role_manager.save()

            return CreateSubCommunityRoleManager(
                sub_community_role_manager=sub_community_role_manager,
                success=True,
                message="Role Created Successfully"
            )

        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateSubCommunityRoleManager(
                sub_community_role_manager=None,
                success=False,
                message=message
            )



class AssignRoleMutation(graphene.Mutation):
    """
    Assigns a role to community members.
    
    This mutation allows community admins to assign predefined roles
    to specific community members, granting them associated permissions.
    
    Args:
        input (AssignRoleInput): Role assignment data containing:
            - community_uid: UID of the community
            - role_id: ID of the role to assign
            - user_uids: List of user UIDs to assign the role to
    
    Returns:
        AssignRoleMutation: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If role_id is invalid or role manager doesn't exist
    
    Note:
        - Validates that the role_id exists in the community's role manager
        - Creates role assignment record if it doesn't exist
        - Can assign roles to multiple users in a single operation
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = AssignRoleInput(required=True)

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        exist_community_role_manager = CommunityRoleManager.objects.filter(
                community_uid=input.community_uid
            ).first()
        
        if exist_community_role_manager:
            role_exists = False  # To track if the role_id exists
            for role in exist_community_role_manager.get_roles():
                if role.get('id') == input.role_id:  # Assuming input.role_id is the role_id to check
                    role_exists = True
                    break
    
        if role_exists==False:
             return AssignRoleMutation(success=False, message="Please enter valid role_id")
        # Get or create a RoleAssignment object for the given community_uid
        role_assignment, created = CommunityRoleAssignment.objects.get_or_create(
            community_uid=input.community_uid,
            defaults={'created_by': info.context.user}
        )

        # Assign the role to the user_uids
        role_assignment.assign_role(role_id=input.role_id, user_uid_list=input.user_uids)

        # ============= NOTIFICATION CODE START (AssignRoleMutation) =============
        # Send notification to users who received new roles
        try:
            from notification.global_service import GlobalNotificationService
            
            community = Community.nodes.get(uid=input.community_uid)
            
            # Get role name from role manager
            role_name = "New Role"
            for role in exist_community_role_manager.get_roles():
                if role.get('id') == input.role_id:
                    role_name = role.get('role_name', 'New Role')
                    break
            
            # Notify each user about their new role
            recipients = []
            for user_uid in input.user_uids:
                try:
                    user_node = Users.nodes.get(uid=user_uid)
                    profile = user_node.profile.single()
                    if profile and profile.device_id:
                        recipients.append({
                            'device_id': profile.device_id,
                            'uid': user_node.uid
                        })
                except Exception as e:
                    print(f"Error getting user {user_uid}: {e}")
            
            if recipients:
                service = GlobalNotificationService()
                service.send(
                    event_type="community_role_change",
                    recipients=recipients,
                    community_name=community.name,
                    community_id=community.uid,
                    role_name=role_name
                )
        except Exception as e:
            print(f"Failed to send role assignment notification: {e}")
        # ============= NOTIFICATION CODE END =============

        return AssignRoleMutation(success=True, message="Role assignment successful")



class AssignSubcommunityRoleMutation(graphene.Mutation):
    """
    Assigns a role to sub-community members.
    
    This mutation allows sub-community admins to assign predefined roles
    to specific sub-community members, granting them associated permissions.
    
    Args:
        input (AssignSubCommunityRoleInput): Role assignment data containing:
            - sub_community_uid: UID of the sub-community
            - role_id: ID of the role to assign
            - user_uids: List of user UIDs to assign the role to
    
    Returns:
        AssignSubcommunityRoleMutation: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If role_id is invalid or role manager doesn't exist
    
    Note:
        - Validates that the role_id exists in the sub-community's role manager
        - Creates role assignment record if it doesn't exist
        - Can assign roles to multiple users in a single operation
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = AssignSubCommunityRoleInput(required=True)

    @handle_graphql_community_errors 
    @login_required 
    def mutate(self, info, input):
        # Check if the subcommunity has a role manager
        exist_subcommunity_role_manager = SubCommunityRoleManager.objects.filter(
            sub_community_uid=input.sub_community_uid  # Updated to subcommunity_uid
        ).first()
        # print(exist_subcommunity_role_manager)  # Debugging line
        if exist_subcommunity_role_manager:
            role_exists = False  # To track if the role_id exists
            for role in exist_subcommunity_role_manager.get_roles():
                if role.get('id') == input.role_id:  # Assuming input.role_id is the role_id to check
                    role_exists = True
                    break
    
        if not role_exists:
            return AssignSubcommunityRoleMutation(success=False, message="Please enter valid role_id")
        
        # Get or create a SubcommunityRoleAssignment object for the given subcommunity_uid
        role_assignment, created = SubCommunityRoleAssignment.objects.get_or_create(
            subcommunity_uid=input.sub_community_uid,  # Updated to subcommunity_uid
            defaults={'created_by': info.context.user}
        )

        # Assign the role to the user_uids
        role_assignment.assign_role(role_id=input.role_id, user_uid_list=input.user_uids)

        # ============= NOTIFICATION CODE START (AssignSubcommunityRoleMutation) =============
        # Send notification to users who received new roles
        try:
            from notification.global_service import GlobalNotificationService
            
            sub_community = SubCommunity.nodes.get(uid=input.sub_community_uid)
            
            # Get role name from role manager
            role_name = "New Role"
            for role in exist_subcommunity_role_manager.get_roles():
                if role.get('id') == input.role_id:
                    role_name = role.get('role_name', 'New Role')
                    break
            
            # Notify each user about their new role
            recipients = []
            for user_uid in input.user_uids:
                try:
                    user_node = Users.nodes.get(uid=user_uid)
                    profile = user_node.profile.single()
                    if profile and profile.device_id:
                        recipients.append({
                            'device_id': profile.device_id,
                            'uid': user_node.uid
                        })
                except Exception as e:
                    print(f"Error getting user {user_uid}: {e}")
            
            if recipients:
                service = GlobalNotificationService()
                service.send(
                    event_type="community_role_change",
                    recipients=recipients,
                    community_name=sub_community.name,
                    community_id=sub_community.uid,
                    role_name=role_name
                )
        except Exception as e:
            print(f"Failed to send sub-community role assignment notification: {e}")
        # ============= NOTIFICATION CODE END =============

        return AssignSubcommunityRoleMutation(success=True, message="Role assignment successful")




class JoinGeneratedCommunity(Mutation):
    """
    Adds members to a generated community with automatic role assignment.
    
    This mutation allows users to join generated communities with special logic
    for role assignment based on community size and member count.
    
    Args:
        input (AddMemberInput): Member addition data containing:
            - community_uid: UID of the generated community
            - user_uid: List of user UIDs to add as members
    
    Returns:
        JoinGeneratedCommunity: Response containing:
            - all_membership: Last created membership object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If users are invalid or already members
    
    Note:
        - Validates all user UIDs before processing
        - Prevents duplicate memberships
        - Auto-assigns admin/leader roles if community has ≤5 members
        - Regular member roles for communities with >5 members
        - Designed specifically for generated communities
    """
    all_membership = graphene.Field(MembershipType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=AddMemberInput()

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            community = Community.nodes.get(uid=input.community_uid)
            user = Users.nodes.get(user_id=user_id)

            # community = Community.nodes.get(uid=input.community_uid)
            user_uids = input.user_uid
            
            # Checking user_uid entered correct or not
            unavailable_user=userlist.get_unavailable_list_user(user_uids)
            if unavailable_user:
                return JoinGeneratedCommunity( success=False,message=f"These uid's do not correspond to any user {unavailable_user}")
            # In future it will be improve
            
            
            if not user_uids:
                return JoinGeneratedCommunity(success=False, message="You have not selected any member")
            
            # Check if any of the users are already a member of the community
            for uid in user_uids:
                user_node = Users.nodes.get(uid=uid)
                membership_exists = helperfunction.get_membership_for_user_in_community(user_node, community)
                if membership_exists:
                        return JoinGeneratedCommunity(success=False, message=f"User {user_node.uid} is already a member")
            
            count_of_member=len(community.members.all()),
            # print(community.members.all())
            member_count = count_of_member[0]  # This will give you the integer 

            # Now you can use member_count for comparison
            if member_count > 5:
                for uid in user_uids:
                    user_node = Users.nodes.get(uid=uid)
                    membership = Membership(
                        can_message=True,
                        is_notification_muted=False
                    )
                    membership.save()
                    membership.user.connect(user_node)
                    membership.community.connect(community)
                    community.members.connect(membership)

            else:
                for uid in user_uids:
                    user_node = Users.nodes.get(uid=uid)
                    membership = Membership(
                        is_admin=True,
                        is_leader=True,
                        can_message=True,
                        is_notification_muted=False
                    )
                    membership.save()
                    membership.user.connect(user_node)
                    membership.community.connect(community)
                    community.members.connect(membership)
        
            # Track activity for analytics
            try:
                for uid in user_uids:
                    ActivityService.track_content_interaction_by_id(
                        user_id=uid,
                        content_type="community",
                        content_id=community.uid,
                        interaction_type="join",
                        metadata={
                            "community_name": community.name,
                            "community_type": "generated",
                            "member_count": member_count,
                            "role_assigned": "admin" if member_count <= 5 else "member"
                        }
                    )
            except Exception as e:
                print(f"Failed to track join activity: {e}")
        
            return JoinGeneratedCommunity(all_membership=MembershipType.from_neomodel(membership), success=True,message=CommMessages.COMMUNITY_MEMBER_ADDED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return JoinGeneratedCommunity(all_membership=None, success=False,message=message)



class CreateCommunityPermission(Mutation):
    """
    Sets permission settings for a community or sub-community.
    
    This mutation allows admins to configure various permission settings
    that control member actions within the community.
    
    Args:
        input (CommunityPermissionInput): Permission settings containing:
            - community_uid: UID of the community or sub-community
            - only_admin_can_message: Whether only admins can send messages
            - only_admin_can_add_member: Whether only admins can add members
            - only_admin_can_remove_member: Whether only admins can remove members
    
    Returns:
        CreateCommunityPermission: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Note:
        - Works for both communities and sub-communities
        - Falls back to sub-community if community UID not found
        - Updates permission flags directly on the community/sub-community object
    """
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=CommunityPermissionInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            community = Community.nodes.get(uid=input.community_uid)
            
           
            community.only_admin_can_message=input.get('only_admin_can_message')
            community.only_admin_can_add_member=input.get('only_admin_can_add_member')
            community.only_admin_can_remove_member=input.get('only_admin_can_remove_member')
                

            community.save()

            return CreateCommunityPermission(success=True,message="Permission Set Successfully.")
        except Community.DoesNotExist:
            try:
                sub_community=SubCommunity.nodes.get(uid=input.community_uid)
                sub_community.only_admin_can_message=input.get('only_admin_can_message')
                sub_community.only_admin_can_add_member=input.get('only_admin_can_add_member')
                sub_community.only_admin_can_remove_member=input.get('only_admin_can_remove_member')
                
                sub_community.save()
                return CreateCommunityPermission(success=True,message="Permission Set Successfully.")
            except Exception as error:
                message=getattr(error,'message',str(error))
                return CreateCommunityPermission( success=False,message=message)



class CreateGeneratedCommunity(Mutation):
    """
    Generates communities automatically based on user interests.
    
    This mutation triggers the automatic generation of communities
    using an algorithm that analyzes user interests and preferences.
    
    Returns:
        CreateGeneratedCommunity: Response containing:
            - success: Boolean indicating operation success
            - message: Success message or generation details
    
    Note:
        - Uses the generate_communities_based_on_interest() function
        - No input parameters required
        - Designed for automated community creation workflows
    """
    success = graphene.Boolean()
    message=graphene.String()

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise Exception ("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
           
            message_data=generate_communities_based_on_interest()          
            

            return CreateGeneratedCommunity(success=True,message=message_data)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateGeneratedCommunity(success=False,message=message)


class CreateCommunityPost(Mutation):
    """
    Creates a new post in a community or sub-community.
    
    This mutation allows community admins to create posts with various
    content types including text, files, and different privacy settings.
    
    Args:
        input (CreateCommunityPostInput): Post creation data containing:
            - community_uid: UID of the community or sub-community
            - post_title: Title of the post
            - post_text: Text content of the post
            - post_type: Type of post (text, image, etc.)
            - privacy: Privacy setting for the post
            - post_file_id: Optional list of file IDs to attach
    
    Returns:
        CreateCommunityPost: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not an admin or not a member
    
    Note:
        - Only community/sub-community admins can create posts
        - Validates file IDs if provided
        - Works for both communities and sub-communities
        - Connects post to creator and community/sub-community
    """
    
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCommunityPostInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            creator = Users.nodes.get(user_id=user_id)
            flag=True
            try:
             # Check if the community exists and the user is a admin of it
                community = Community.nodes.get(uid=input.community_uid)
                
                member_node = helperfunction.get_membership_for_user_in_community(creator, community)
                if member_node is None:
                    return CreateCommunityPost(success=False, message=CommMessages.NOT_A_MEMBER_OF_COMMUNITY)

                if member_node.is_admin == False:
                    return CreateCommunityPost(success=False, message=CommMessages.NOT_AN_ADMIN)
            except Community.DoesNotExist:
                community = SubCommunity.nodes.get(uid=input.community_uid)
                flag=False

                member_node = helperfunction.get_membership_for_user_in_sub_community(creator, community)
                if member_node is None:
                    return CreateCommunityPost(success=False, message=CommMessages.NOT_A_MEMBER_OF_COMMUNITY)

                if member_node.is_admin == False:
                    return CreateCommunityPost(success=False, message=CommMessages.NOT_AN_ADMIN)

            if input.post_file_id:
                for id in input.post_file_id:
                    valid_id=get_valid_image(id)

            post_title=input.post_title
            post_text=input.post_text
            post_type=input.post_type
            privacy=input.privacy
            post_file_id = input.post_file_id if input.post_file_id else None
            tags = input.tags if input.tags else None

            post = CommunityPost(
                post_title=post_title,
                post_text=post_text,
                post_type=post_type,
                privacy=privacy,
                post_file_id=post_file_id,
                tags=tags
            )
            post.save()
            post.creator.connect(creator)

            # Extract mentions from community post content (title and text)
            if post_title or post_text:
                from post.utils.mention_extractor import MentionExtractor
                
                # Combine post title and text for mention extraction
                post_content = f"{post_title or ''} {post_text or ''}".strip()
                
                print("Extracting mentions from community post content...")
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(post_content)
                
                if mentioned_user_uids:
                    MentionService.create_mentions(
                        mentioned_user_uids=mentioned_user_uids,
                        content_type='community_post',
                        content_uid=post.uid,
                        mentioned_by_uid=creator.uid,
                        mention_context='post_content'
                    )
                    
                    # ============= NOTIFICATION CODE START (Mention in Community Post) =============
                    # Send notification to mentioned users
                    try:
                        from notification.global_service import GlobalNotificationService
                        
                        # Get community info
                        community_name = community_obj.name if community_obj else "Community"
                        community_id = community_obj.uid if community_obj else post.uid
                        
                        # Collect mentioned users with device IDs
                        mention_recipients = []
                        for mentioned_uid in mentioned_user_uids:
                            try:
                                mentioned_user = Users.nodes.get(uid=mentioned_uid)
                                if mentioned_user.uid != creator.uid:  # Don't notify yourself
                                    profile = mentioned_user.profile.single()
                                    if profile and profile.device_id:
                                        mention_recipients.append({
                                            'device_id': profile.device_id,
                                            'uid': mentioned_user.uid
                                        })
                            except Exception as e:
                                print(f"Error getting mentioned user {mentioned_uid}: {e}")
                        
                        if mention_recipients:
                            service = GlobalNotificationService()
                            service.send(
                                event_type="community_post_mention",
                                recipients=mention_recipients,
                                username=creator.username,
                                community_name=community_name,
                                community_id=community_id,
                                post_id=post.uid,
                                sender_uid=creator.uid,
                                sender_id=creator.user_id
                            )
                    except Exception as e:
                        print(f"Failed to send mention notification: {e}")
                    # ============= NOTIFICATION CODE END =============
            
            if input.reaction and input.vibe:
                try:
                    # Check if user already liked their own community post to prevent duplicates
                    from neomodel import db
                    check_query = (
                        "MATCH (user:Users {uid: $user_uid})-[:HAS_USER]->(like:Like) "
                        "MATCH (like)-[:HAS_POST]->(post {uid: $post_uid}) "
                        "RETURN like"
                    )
                    check_params = {'user_uid': creator.uid, 'post_uid': post.uid}
                    existing_results, _ = db.cypher_query(check_query, check_params)
                    
                    # Only add vibe if user hasn't already reacted
                    if not existing_results:
                        # Create PostReactionManager for community post if it doesn't exist
                        try:
                            post_reaction_manager = PostReactionManager.objects.get(post_uid=post.uid)
                        except PostReactionManager.DoesNotExist:
                            post_reaction_manager = PostReactionManager(post_uid=post.uid)
                            post_reaction_manager.initialize_reactions()
                            post_reaction_manager.save()

                        # Add this reaction to the aggregated analytics
                        post_reaction_manager.add_reaction(
                            vibes_name=input.reaction,
                            score=input.vibe
                        )
                        post_reaction_manager.save()

                        # Create the individual like record
                        like = Like(
                            reaction=input.reaction,
                            vibe=input.vibe
                        )
                        like.save()
                        
                        # Establish relationships
                        like.user.connect(creator)
                        post.like.connect(like)

                    # Track vibe activity for community post reaction
                    try:
                        # Get request context for IP and user agent
                        request = info.context
                        ip_address = getattr(request, 'META', {}).get('REMOTE_ADDR', 'unknown')
                        user_agent = getattr(request, 'META', {}).get('HTTP_USER_AGENT', 'unknown')
                        
                        # Prepare vibe data
                        vibe_data = {
                            'vibe_name': input.reaction,
                            'vibe_score': input.vibe,
                            'vibe_type': 'community',
                            'category': 'community_post_reaction'
                        }
                        
                        # Track vibe sending activity
                        VibeActivityService.track_vibe_sending(
                            sender=creator,
                            receiver_id=community_obj.uid,  # Community as receiver
                            vibe_data=vibe_data,
                            vibe_score=input.vibe,
                            context={
                                'post_id': post.uid,
                                'community_id': community_obj.uid,
                                'community_name': community_obj.name,
                                'ip_address': ip_address,
                                'user_agent': user_agent
                            }
                        )
                        print(f"Vibe activity tracked for community post reaction: {input.reaction} with score {input.vibe}")
                    except Exception as vibe_tracking_error:
                        # Log the error but don't fail the main functionality
                        print(f"Error tracking vibe activity for community post reaction: {str(vibe_tracking_error)}")

                    # Update engagement metrics in Redis
                    increment_post_like_count(post.uid)
                    
                except Exception as vibe_error:
                    # Log the error but don't fail the post creation
                    print(f"Error adding vibe to community post: {str(vibe_error)}")
            if flag:
                community.community_post.connect(post)
                post.created_by.connect(community)
            else:
                community.community_post.connect(post)
                post.created_by_subcommunity.connect(community)

            community_obj = community
            community_name = community_obj.name
            community_id = community_obj.uid
            
            # Get members based on community type
            if flag:
                # For Community objects, use members relationship
                members = community_obj.members.all()
            else:
                # For SubCommunity objects, use sub_community_members relationship
                members = community_obj.sub_community_members.all()

            members_to_notify = []
            for member in members:
                user = member.user.single()  # Get user from membership
                if user and user.uid != creator.uid:  # Don't notify the creator
                    profile = user.profile.single()
                    if profile and profile.device_id:
                        members_to_notify.append({
                            'device_id': profile.device_id,
                            'uid': user.uid
                        })

            # ============= NOTIFICATION CODE START =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyCommunityPost(
            #             creator_name=creator.username,
            #             members=members_to_notify,
            #             community_name=community_name,
            #             post_title=post.post_title or "New post",
            #             post_id=post.uid,
            #             community_id=community_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            if members_to_notify:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="new_community_post",
                        recipients=members_to_notify,
                        username=creator.username,
                        community_name=community_name,
                        post_title=post.post_title[:50] if post.post_title else "New post",
                        post_id=post.uid,
                        community_id=community_id,
                        sender_uid=creator.uid,
                        sender_id=creator.user_id
                    )
                except Exception as e:
                    print(f"Failed to send community post notification: {e}")
            # ============= NOTIFICATION CODE END =============

            return CreateCommunityPost(success=True, message=CommMessages.POST_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateCommunityPost(success=False, message=message)


class DeleteCommunityPost(Mutation):
    """
    Deletes a community post by marking it as deleted.
    
    This mutation allows post creators to delete their own posts
    by setting the is_deleted flag to True.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: UID of the community post to delete
    
    Returns:
        DeleteCommunityPost: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user is not the post creator
    
    Note:
        - Only the original post creator can delete their post
        - Uses soft delete (sets is_deleted=True) rather than hard delete
        - Validates user ownership before allowing deletion
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise ("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            

            post = CommunityPost.nodes.get(uid=input.uid)
            created_by=post.creator.single()

            if created_by.user_id != str(user_id):
                return DeleteCommunityPost(success=False, message=CommMessages.POST_DELETE_PERMISSION_DENIED)

            post.is_deleted = True
            post.save()
            return DeleteCommunityPost(success=True, message=CommMessages.POST_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteCommunityPost(success=False, message=message)





class LeaveCommunityChat(Mutation):
    """
    Allows a user to leave a community's Matrix chat room and remove community membership.
    
    This mutation enables users to voluntarily leave Matrix chat rooms
    associated with communities they are members of and removes their membership.
    
    Args:
        input (LeaveCommunityChatInput): Contains room_id of the Matrix room to leave
        
    Returns:
        LeaveCommunityChatResponseType: Success status and details
        
    Note:
        - Requires user authentication
        - User must have Matrix profile with valid credentials
        - User must be a member of the Matrix room
        - Removes both Matrix chat access and community membership
        - Community creators cannot leave their own community
    """
    success = graphene.Boolean()
    message = graphene.String()
    room_id = graphene.String()
    left_at = graphene.DateTime()

    class Arguments:
        input = LeaveCommunityChatInput()
    
    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            room_id = input.room_id
            
            # Get the user node
            user_node = Users.nodes.get(user_id=user_id)
            
            # Find the community by room_id
            try:
                community = Community.nodes.get(room_id=room_id)
            except Community.DoesNotExist:
                # Try to find as sub-community
                try:
                    sub_community = SubCommunity.nodes.get(room_id=room_id)
                    # Check if user is the creator
                    creator = sub_community.created_by.single()
                    if creator and creator.user_id == str(user_id):
                        return LeaveCommunityChat(
                            success=False,
                            message="Sub-community creator cannot leave their own sub-community"
                        )
                    
                    # Find and remove membership
                    membership = None
                    for mem in sub_community.sub_community_members.all():
                        if mem.user.is_connected(user_node):
                            membership = mem
                            break
                    
                    if not membership:
                        return LeaveCommunityChat(
                            success=False,
                            message="You are not a member of this sub-community"
                        )
                    
                    # Get user's Matrix profile
                    try:
                        from msg.models import MatrixProfile
                        matrix_profile = MatrixProfile.objects.get(user=user_id)
                        if not matrix_profile.access_token or not matrix_profile.matrix_user_id:
                            return LeaveCommunityChat(
                                success=False,
                                message="Matrix profile not available or incomplete"
                            )
                    except MatrixProfile.DoesNotExist:
                        return LeaveCommunityChat(
                            success=False,
                            message="Matrix profile not found"
                        )
                    
                    # Leave the Matrix room
                    try:
                        from msg.util.matrix_message_utils import leave_matrix_room
                        import asyncio
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            success = loop.run_until_complete(
                                leave_matrix_room(
                                    access_token=matrix_profile.access_token,
                                    user_id=matrix_profile.matrix_user_id,
                                    room_id=room_id
                                )
                            )
                        finally:
                            loop.close()
                        
                        if success:
                            # Remove membership from sub-community
                            membership.delete()
                            
                            # Update sub-community member count
                            sub_community.number_of_members = len(sub_community.sub_community_members.all())
                            sub_community.save()
                            
                            return LeaveCommunityChat(
                                success=True,
                                message="Successfully left sub-community chat room and removed membership",
                                room_id=room_id,
                                left_at=datetime.now()
                            )
                        else:
                            return LeaveCommunityChat(
                                success=False,
                                message="Failed to leave Matrix room"
                            )
                            
                    except Exception as matrix_error:
                        return LeaveCommunityChat(
                            success=False,
                            message=f"Matrix error: {str(matrix_error)}"
                        )
                        
                except SubCommunity.DoesNotExist:
                    return LeaveCommunityChat(
                        success=False,
                        message="Community or sub-community not found with this room ID"
                    )
            
            # Check if user is the creator of the community
            creator = community.created_by.single()
            if creator and creator.user_id == str(user_id):
                return LeaveCommunityChat(
                    success=False,
                    message="Community creator cannot leave their own community"
                )
            
            # Find the membership for this user in the community
            membership = None
            for mem in community.members.all():
                if mem.user.is_connected(user_node):
                    membership = mem
                    break
            
            if not membership:
                return LeaveCommunityChat(
                    success=False,
                    message="You are not a member of this community"
                )
            
            # Get user's Matrix profile
            try:
                from msg.models import MatrixProfile
                matrix_profile = MatrixProfile.objects.get(user=user_id)
                if not matrix_profile.access_token or not matrix_profile.matrix_user_id:
                    return LeaveCommunityChat(
                        success=False,
                        message="Matrix profile not available or incomplete"
                    )
            except MatrixProfile.DoesNotExist:
                return LeaveCommunityChat(
                    success=False,
                    message="Matrix profile not found"
                )
            
            # Leave the Matrix room
            try:
                from msg.util.matrix_message_utils import leave_matrix_room
                import asyncio
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    success = loop.run_until_complete(
                        leave_matrix_room(
                            access_token=matrix_profile.access_token,
                            user_id=matrix_profile.matrix_user_id,
                            room_id=room_id
                        )
                    )
                finally:
                    loop.close()
                
                if success:
                    # Remove membership from community
                    membership.delete()
                    
                    # Update community member count
                    community.number_of_members = len(community.members.all())
                    community.save()
                    
                    return LeaveCommunityChat(
                        success=True,
                        message="Successfully left community chat room and removed membership",
                        room_id=room_id,
                        left_at=datetime.now()
                    )
                else:
                    return LeaveCommunityChat(
                        success=False,
                        message="Failed to leave Matrix room"
                    )
                    
            except Exception as matrix_error:
                return LeaveCommunityChat(
                    success=False,
                    message=f"Matrix error: {str(matrix_error)}"
                )
                
        except Exception as error:
            return LeaveCommunityChat(
                success=False,
                message=f"Error leaving community chat: {str(error)}"
            )


class CreateCommunityV2(Mutation):
    """
    V2: Creates a new community with enhanced fields including username, location, and contact info.
    
    New fields in V2:
    - username: Unique handle for the community
    - city, state, country: Location information
    - website_url, contact_email: Contact information
    - enable_comments: Setting to allow/disallow comments on posts
    
    This version maintains all the functionality of V1 while adding the new fields.
    """
    community = graphene.Field(CommunityType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCommunityInputV2()

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise Exception("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            try:
                created_by = Users.nodes.get(user_id=user_id)
            except Exception as e:
                raise
            
            # Check if username already exists across all entities (Users, Communities, SubCommunities)
            username = input.get('username', '').strip().lower()
            if username:
                conflicts = []
                
                # Check in Users
                try:
                    existing_user = Users.nodes.get(username=username)
                    if existing_user:
                        conflicts.append("user")
                except Users.DoesNotExist:
                    pass
                
                # Check in Communities
                try:
                    existing_community = Community.nodes.get(username=username)
                    if existing_community:
                        conflicts.append("community")
                except Community.DoesNotExist:
                    pass
                
                # Check in SubCommunities
                try:
                    existing_subcommunity = SubCommunity.nodes.get(username=username)
                    if existing_subcommunity:
                        conflicts.append("subcommunity")
                except SubCommunity.DoesNotExist:
                    pass
                
                # If any conflicts exist, return error
                if conflicts:
                    if len(conflicts) == 1:
                        entity_type = conflicts[0]
                        return CreateCommunityV2(
                            community=None, 
                            success=False,
                            message=f"Username '{username}' is already taken by a {entity_type}. Please choose a different username."
                        )
                    else:
                        conflict_text = ", ".join(conflicts)
                        return CreateCommunityV2(
                            community=None, 
                            success=False,
                            message=f"Username '{username}' is already taken (conflicts: {conflict_text}). Please choose a different username."
                        )
            
            room_id = None
            access_token = None
            
            # Try to create a Matrix room if possible
            try:
                print("Trying to get MatrixProfile")
                matrix_profile = MatrixProfile.objects.get(user=user_id)
                if matrix_profile and matrix_profile.matrix_user_id and matrix_profile.access_token:
                    print("Matrix profile found with valid credentials")
                    matrix_user_id = matrix_profile.matrix_user_id
                    access_token = matrix_profile.access_token
                    room_name = input.get('name', '')
                    topic = str(input.get('description', ''))
                    
                    print("Creating Matrix room...")
                    room_id = asyncio.run(create_room(
                        access_token=access_token,
                        user_id=matrix_user_id,
                        room_name=room_name,
                        topic=topic,
                        visibility="private",
                        preset="private_chat",
                    ))
            except MatrixProfile.DoesNotExist:
                print("No Matrix profile found for user")
                matrix_logger.warning(f"No Matrix profile found for user {user_id}, creating community without chat room")
            except Exception as e:
                print(f"Matrix room creation error: {e}")
                matrix_logger.error(f"Failed to create Matrix room: {e}")
            
            # Create community with V2 fields
            community = Community(
                name=input.get('name', ''),
                username=username,
                description=input.get('description', ''),
                community_circle=input.get('community_circle').value,
                community_type=input.get('community_type').value,
                room_id=room_id,
                category=input.get('category', ''),
                city=input.get('city', ''),
                state=input.get('state', ''),
                country=input.get('country', ''),
                address=input.get('address', ''),
                website_url=input.get('website_url', ''),
                contact_email=input.get('contact_email', ''),
                enable_comments=input.get('enable_comments', True),
                group_icon_id=input.get('group_icon_id', ''),
                cover_image_id=input.get('cover_image_id', ''),
                ai_generated=input.get('ai_generated', False),
                tags=input.get('tags', []),
            )
            
            print("Checking member_uid...")
            member_uid = input.get('member_uid') or []
            
            member_uid.append(ADMIN_USER_ID)
            if not member_uid:
                print("No members selected")
                return CreateCommunityV2(community=None, success=False, message=f"You have not selected any user")
            
            print(f"Member UIDs: {member_uid}")
            
            print("Checking for unavailable users...")
            unavailable_user = userlist.get_unavailable_list_user(member_uid)
            
            if unavailable_user:
                print(f"Unavailable users found: {unavailable_user}")
                return CreateCommunityV2(community=None, success=False, message=f"These uid's do not correspond to any user {unavailable_user}")

            print("Saving community...")
            community.save()
            
            print("Connecting community with creator...")
            community.created_by.connect(created_by)
            created_by.community.connect(community)

            print("Creating creator membership...")
            membership = Membership(
                is_admin=True,
                can_message=True,
                is_notification_muted=False
            )
            membership.save()
            membership.user.connect(created_by)
            membership.community.connect(community)
            community.members.connect(membership)

            # Extract mentions from community description
            if description := input.get('description'):
                from post.utils.mention_extractor import MentionExtractor
                
                print("Extracting mentions from community description...")
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(description)
                
                if mentioned_user_uids:
                    print("Creating description mentions...")
                    MentionService.create_mentions(
                        mentioned_user_uids=mentioned_user_uids,
                        content_type='community_description',
                        content_uid=community.uid,
                        mentioned_by_uid=created_by.uid,
                        mention_context='description'
                    )

            if community and access_token:
                try:
                    community_data = {
                        'community_type': community.community_type,
                        'community_circle': community.community_circle,
                        'category': community.category,
                        'created_date': community.created_date,
                        'community_uid': community.uid,
                        'community_name': community.name,
                    }
                    print("Setting community room filter data...")
                    filter_result = asyncio.run(set_room_avatar_score_and_filter(
                        access_token=access_token,
                        user_id=user_id,
                        room_id=room_id,
                        image_id=community.group_icon_id,
                        community_data=community_data
                    ))
                    
                    if filter_result["success"]:
                        matrix_logger.info(f"Set avatar and score for community room {room_id}")
                        print(f"Community filter data set successfully: {filter_result}")
                    else:
                        matrix_logger.warning(f"Failed to set community filter: {filter_result.get('error')}")
                        print(f"Failed to set community filter data: {filter_result.get('error')}")
                    
                except Exception as e:
                    matrix_logger.warning(f"Error setting community filter data: {e}")
                    print(f"Error setting community filter data: {e}")

            print("Adding other members...")
            members_to_notify = []
            for member in member_uid:
                print(f"Adding member: {member}")
                user_node = Users.nodes.get(uid=member)
                membership = Membership(
                    can_message=True,
                    is_notification_muted=False
                )
                if member == ADMIN_USER_ID:
                    membership.is_admin = True
                    membership.can_message = True
                    membership.is_notification_muted = False
                    
                membership.save()
                membership.user.connect(user_node)
                membership.community.connect(community)
                community.members.connect(membership)
                
                # Collect members for notification
                profile = user_node.profile.single()
                if profile and profile.device_id:
                    members_to_notify.append({
                        'device_id': profile.device_id,
                        'uid': user_node.uid
                    })
            
            # ============= NOTIFICATION CODE START (CreateCommunityV2) =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyCommunityCreated(
            #             creator_name=created_by.username,
            #             members=members_to_notify,
            #             community_id=community.uid,
            #             community_name=community.name,
            #             community_icon=community.group_icon_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            # Send notifications to initial members
            if members_to_notify:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="user_joined_community",
                        recipients=members_to_notify,
                        username=created_by.username,
                        community_name=community.name,
                        community_id=community.uid,
                        community_icon=community.group_icon_id if community.group_icon_id else None
                    )
                except Exception as e:
                    print(f"Failed to send community creation notification: {e}")
            # ============= NOTIFICATION CODE END =============
            
            # Invite all members to the Matrix room if a room was created
            if room_id:
                print("Initiating Matrix room invitations in background...")
                matrix_logger.info(f"Starting background process to invite {len(member_uid)} members to Matrix room {room_id}")
                
                process_matrix_invites(
                    admin_user_id=user_id,
                    room_id=room_id,
                    member_ids=member_uid
                )

            # Auto-assign agent to community after creation
            agent_assignment_success = False
            agent_name = None
            assigned_agent = None
            try:
                print("Auto-assigning agent to community...")
                from agentic.services.agent_service import AgentService
                
                agent_service = AgentService()
                default_agent = agent_service.get_default_community_agent()
                
                if default_agent:
                    print(f"Found default agent: {default_agent.uid}")
                    assignment = agent_service.assign_agent_to_community(
                        agent_uid=default_agent.uid,
                        community_uid=community.uid,
                        assigned_by_uid=user_id,
                        allow_multiple_leaders=False
                    )
                    print(f"Successfully assigned agent {default_agent.uid} to community {community.uid}")
                    agent_assignment_success = True
                    agent_name = default_agent.name
                    assigned_agent = default_agent
                    
                    from agentic.services.auth_service import AgentAuthService
                    auth_service = AgentAuthService()
                    auth_service.log_agent_action(
                        agent_uid=default_agent.uid,
                        community_uid=community.uid,
                        action_type="auto_assignment",
                        details={
                            "assigned_during": "community_creation",
                            "community_name": community.name,
                            "assigned_by": user_id
                        },
                        success=True
                    )
                    
                    if room_id and assigned_agent:
                        try:
                            print(f"Adding agent {assigned_agent.name} to Matrix room {room_id}...")
                            from agentic.matrix_utils import join_agent_to_community_matrix_room
                            
                            join_agent_to_community_matrix_room(
                                agent=assigned_agent,
                                community=community
                            )
                            print(f"Successfully added agent {assigned_agent.name} to Matrix room")
                        except Exception as matrix_error:
                            print(f"Failed to add agent to Matrix room (non-critical): {matrix_error}")
                            import traceback
                            traceback.print_exc()
                else:
                    print("No default agent available for assignment")
                    
            except Exception as agent_error:
                print(f"Agent assignment failed (non-critical): {agent_error}")
                import traceback
                traceback.print_exc()
            
            # Process tags if provided
            tags = input.get('tags') or []
            if tags:
                print(f"Processing {len(tags)} tags for community...")
                from community.models import CommunityKeyword
                
                for tag in tags:
                    if tag and tag.strip():
                        tag_cleaned = tag.strip().lower()
                        try:
                            existing_keyword = CommunityKeyword.nodes.get(keyword=tag_cleaned)
                            print(f"Tag '{tag_cleaned}' already exists, skipping...")
                        except CommunityKeyword.DoesNotExist:
                            keyword = CommunityKeyword(
                                keyword=tag_cleaned
                            )
                            keyword.save()
                            keyword.community.connect(community)
                            print(f"Created and associated tag: {tag_cleaned}")
                        except Exception as tag_error:
                            print(f"Error processing tag '{tag_cleaned}': {tag_error}")
                            continue
            
            print("Community creation V2 completed successfully!")
            
            # Track activity for analytics
            try:
                ActivityService.track_content_interaction_by_id(
                    user_id=user_id,
                    content_type="community",
                    content_id=community.uid,
                    interaction_type="create",
                    metadata={
                        "community_id": community.uid,
                        "community_name": community.name,
                        "community_username": community.username,
                        "community_type": community.community_type,
                        "member_count": len(member_uid) if member_uid else 1,
                        "has_matrix_room": bool(room_id),
                        "agent_assigned": agent_assignment_success,
                        "version": "v2"
                    }
                )
            except Exception as activity_error:
                print(f"Failed to track community creation activity: {activity_error}")
            
            success_message = str(CommMessages.COMMUNITY_CREATED)
            
            try:
                community_obj = CommunityType.from_neomodel(community)
            except Exception as e:
                print(f"Error converting community to GraphQL type: {e}")
                community_obj = None
            
            return CreateCommunityV2(
                community=community_obj,
                success=True,
                message=success_message
            )
        except Exception as error:
            print(f"ERROR in CreateCommunityV2: {error}")
            import traceback
            traceback.print_exc()
            message = getattr(error, 'message', str(error))
            return CreateCommunityV2(community=None, success=False, message=message)


class CreateSubCommunityV2(Mutation):
    """
    V2: Creates a new sub-community with enhanced fields including username, location, and contact info.
    
    New fields in V2:
    - username: Unique handle for the sub-community
    - city, state, country: Location information
    - website_url, contact_email: Contact information
    - enable_comments: Setting to allow/disallow comments on posts
    
    This version maintains all the functionality of V1 while adding the new fields.
    """
    community = graphene.Field(SubCommunityType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateSubCommunityInputV2()

    @handle_graphql_community_errors 
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication Failure")
            
        payload = info.context.payload
        user_id = payload.get('user_id')
            
        created_by = Users.nodes.get(user_id=user_id)
        
        # Check if username already exists across all entities (Users, Communities, SubCommunities)
        username = input.get('username', '').strip().lower()
        if username:
            conflicts = []
            
            # Check in Users
            try:
                existing_user = Users.nodes.get(username=username)
                if existing_user:
                    conflicts.append("user")
            except Users.DoesNotExist:
                pass
            
            # Check in Communities
            try:
                existing_community = Community.nodes.get(username=username)
                if existing_community:
                    conflicts.append("community")
            except Community.DoesNotExist:
                pass
            
            # Check in SubCommunities
            try:
                existing_subcommunity = SubCommunity.nodes.get(username=username)
                if existing_subcommunity:
                    conflicts.append("subcommunity")
            except SubCommunity.DoesNotExist:
                pass
            
            # If any conflicts exist, return error
            if conflicts:
                if len(conflicts) == 1:
                    entity_type = conflicts[0]
                    return CreateSubCommunityV2(
                        community=None, 
                        success=False,
                        message=f"Username '{username}' is already taken by a {entity_type}. Please choose a different username."
                    )
                else:
                    conflict_text = ", ".join(conflicts)
                    return CreateSubCommunityV2(
                        community=None, 
                        success=False,
                        message=f"Username '{username}' is already taken (conflicts: {conflict_text}). Please choose a different username."
                    )
        
        room_id = None
        access_token = None
            
        # Try to create a Matrix room if possible
        try:
            print("Trying to get MatrixProfile")
            matrix_profile = MatrixProfile.objects.get(user=user_id)
            if matrix_profile and matrix_profile.matrix_user_id and matrix_profile.access_token:
                matrix_user_id = matrix_profile.matrix_user_id
                access_token = matrix_profile.access_token
                room_name = input.get('name', '')
                topic = str(input.get('description', ''))
                    
                print("Creating Matrix room...")
                room_id = asyncio.run(create_room(
                    access_token=access_token,
                    user_id=matrix_user_id,
                    room_name=room_name,
                    topic=topic,
                    visibility="private",
                    preset="private_chat"
                ))
        except MatrixProfile.DoesNotExist:
            print("No Matrix profile found for user")
            matrix_logger.warning(f"No Matrix profile found for user {user_id}, creating community without chat room")
        except Exception as e:
            print(f"Matrix room creation error: {e}")
            matrix_logger.error(f"Failed to create Matrix room: {e}")

        if input.group_icon_id:
            valid_id = get_valid_image(input.group_icon_id)
                       
        # Create sub-community with V2 fields
        sub_community = SubCommunity(
            name=input.get('name', ''),
            username=username,
            description=input.get('description', ''),
            sub_community_circle=input.get('sub_community_circle').value,
            sub_community_type=input.get('sub_community_type').value,
            sub_community_group_type=input.get('sub_community_group_type').value,
            category=input.get('category', ''),
            city=input.get('city', ''),
            state=input.get('state', ''),
            country=input.get('country', ''),
            address=input.get('address', ''),
            website_url=input.get('website_url', ''),
            contact_email=input.get('contact_email', ''),
            enable_comments=input.get('enable_comments', True),
            room_id=room_id,
            cover_image_id=input.get('cover_image_id', ''),
            group_icon_id=input.get('group_icon_id', ''),
        )
            
        member_uid = input.get('member_uid') or []
        member_uid.append(ADMIN_USER_ID)

        if created_by.uid not in member_uid:
           member_uid.append(created_by.uid)
        if not member_uid:
            return CreateSubCommunityV2(community=None, success=False, message=f"You have not selected any user")
        unavailable_user = userlist.get_unavailable_list_user(member_uid)
        if unavailable_user:
            return CreateSubCommunityV2(community=None, success=False, message=f"These uid's do not correspond to any user {unavailable_user}")
        
        try:
            community = Community.nodes.get(uid=input.parent_community_uid)

            membership_exists = helperfunction.get_membership_for_user_in_community(created_by, community)

            if not membership_exists:
                return CreateSubCommunityV2(community=None, success=False, message="You are not a member of this community and this communnity is private")

            if membership_exists:
                if membership_exists.is_admin == False:
                    return CreateSubCommunityV2(community=None, success=False, message="You are not authorised to add new member")

            sub_community.save()
            sub_community.created_by.connect(created_by)
            sub_community.parent_community.connect(community)
            if input.get('sub_community_type').value == 'child community':
                community.child_communities.connect(sub_community)
            if input.get('sub_community_type').value == 'sibling community':
                community.sibling_communities.connect(sub_community)

            # Set Matrix room avatar and filter data for sub-community
            if sub_community and access_token:
                try:
                    sub_community_data = {
                        'community_type': sub_community.sub_community_type,
                        'community_circle': sub_community.sub_community_circle,
                        'category': sub_community.category,
                        'created_date': sub_community.created_date,
                        'community_uid': sub_community.uid,
                        'community_name': sub_community.name,
                    }
                    print("Setting sub-community room filter data...")
                    filter_result = asyncio.run(set_room_avatar_score_and_filter(
                        access_token=access_token,
                        user_id=user_id,
                        room_id=room_id,
                        image_id=sub_community.group_icon_id,
                        community_data=sub_community_data
                    ))
                    
                    if filter_result["success"]:
                        matrix_logger.info(f"Set avatar and score for sub-community room {room_id}")
                        print(f"Sub-community filter data set successfully: {filter_result}")
                    else:
                        matrix_logger.warning(f"Failed to set sub-community filter: {filter_result.get('error')}")
                        print(f"Failed to set sub-community filter data: {filter_result.get('error')}")
                    
                except Exception as e:
                    matrix_logger.warning(f"Error setting sub-community filter data: {e}")
                    print(f"Error setting sub-community filter data: {e}")

            # Member who created the sub-community is itself a member
            membership = SubCommunityMembership(
                is_admin=True,
                can_message=True,
                is_notification_muted=False
            )
            membership.save()
            membership.user.connect(created_by)
            membership.sub_community.connect(sub_community)
            sub_community.sub_community_members.connect(membership)


            members_to_notify = []
            for member in member_uid:

                if member == created_by.uid:
                   continue
                user_node = Users.nodes.get(uid=member)
                membership = SubCommunityMembership(
                    can_message=True,
                    is_notification_muted=False
                )
                if member == ADMIN_USER_ID:
                    membership.is_admin = True
                    membership.can_message = True
                    membership.is_notification_muted = False
                    
                membership.save()
                membership.user.connect(user_node)
                membership.sub_community.connect(sub_community)
                sub_community.sub_community_members.connect(membership)
                
                # Collect members for notification
                profile = user_node.profile.single()
                if profile and profile.device_id:
                    members_to_notify.append({
                        'device_id': profile.device_id,
                        'uid': user_node.uid
                    })

            # ============= NOTIFICATION CODE START (CreateSubCommunityV2) =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifySubCommunityCreated(
            #             creator_name=created_by.username,
            #             members=members_to_notify,
            #             sub_community_id=sub_community.uid,
            #             sub_community_name=sub_community.name,
            #             sub_community_icon=sub_community.group_icon_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            # Send notifications to initial members
            if members_to_notify:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    # Determine if it's a child or sibling community
                    sub_type = input.get('sub_community_type').value
                    event_type = "new_child_community" if sub_type == 'child community' else "new_sibling_community"
                    
                    service.send(
                        event_type=event_type,
                        recipients=members_to_notify,
                        community_name=sub_community.name,
                        community_id=sub_community.uid,
                        community_icon=sub_community.group_icon_id if sub_community.group_icon_id else None
                    )
                except Exception as e:
                    print(f"Failed to send sub-community creation notification: {e}")
            # ============= NOTIFICATION CODE END =============

            if room_id:
                print("Initiating Matrix room invitations in background...")
                matrix_logger.info(f"Starting background process to invite {len(member_uid)} members to Matrix room {room_id}")
                
                process_matrix_invites(
                    admin_user_id=user_id,
                    room_id=room_id,
                    member_ids=member_uid
                )
            
            # Track activity for analytics
            try:
                ActivityService.track_content_interaction_by_id(
                    user_id=user_id,
                    content_type="subcommunity",
                    content_id=sub_community.uid,
                    interaction_type="create",
                    metadata={
                        "subcommunity_id": sub_community.uid,
                        "subcommunity_name": sub_community.name,
                        "subcommunity_username": sub_community.username,
                        "parent_community_id": community.uid,
                        "member_count": len(member_uid) if member_uid else 1,
                        "has_matrix_room": bool(room_id),
                        "version": "v2"
                    }
                )
            except Exception as activity_error:
                print(f"Failed to track subcommunity creation activity: {activity_error}")
            
            return CreateSubCommunityV2(community=SubCommunityType.from_neomodel(sub_community), success=True, message=CommMessages.COMMUNITY_CREATED)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateSubCommunityV2(community=None, success=False, message=message)
class SendVibeToCommunityContent(Mutation):
    """
    Sends a vibe reaction to community content (achievement, activity, goal, affiliation).
    
    This mutation allows authenticated community members to send vibe reactions to
    community content using the IndividualVibe system for standardized vibe metadata and scoring.
    
    Features:
    - Validates vibe intensity (1.0 to 5.0)
    - Gets IndividualVibe from PostgreSQL for metadata
    - Validates community membership before allowing vibe
    - Checks for existing vibe and updates if found (one vibe per user per content)
    - Creates CommunityContentVibe node in Neo4j
    - Updates user scores via VibeUtils
    
    Returns:
        success: Boolean indicating if vibe was sent successfully
        message: Status message or error description
        community_content_vibe: The created or updated vibe reaction
    """
    success = graphene.Boolean()
    message = graphene.String()
    community_content_vibe = graphene.Field(CommunityContentVibeType)
    
    class Arguments:
        input = SendVibeToCommunityContentInput()
    
    @handle_graphql_community_errors
    @login_required
    def mutate(self, info, input):
        try:
            # Get authenticated user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Validate vibe intensity (1.0 to 5.0)
            if not (1.0 <= input.vibe_intensity <= 5.0):
                return SendVibeToCommunityContent(
                    success=False,
                    message="Vibe intensity must be between 1.0 and 5.0",
                    community_content_vibe=None
                )
            
            try:
                clean_intensity = round(float(input.vibe_intensity), 2)
            except (ValueError, TypeError):
                return SendVibeToCommunityContent(
                    success=False,
                    message="Invalid vibe intensity format",
                    community_content_vibe=None
                )
            
            if not (1.0 <= clean_intensity <= 5.0):
                return SendVibeToCommunityContent(
                    success=False,
                    message="Vibe intensity must be between 1.0 and 5.0",
                    community_content_vibe=None
                )
            
            # Get the individual vibe from PostgreSQL
            try:
                individual_vibe = IndividualVibe.objects.get(id=input.individual_vibe_id)
            except IndividualVibe.DoesNotExist:
                return SendVibeToCommunityContent(
                    success=False,
                    message="Invalid vibe selected",
                    community_content_vibe=None
                )
            
            # Get the content node based on category
            content_node = None
            # Enum value is already a string (e.g., 'community_achievement', 'community_activity')
            category = input.content_category
            
            try:
                if category == 'community_achievement':
                    content_node = CommunityAchievement.nodes.get(uid=input.content_uid)
                elif category == 'community_activity':
                    content_node = CommunityActivity.nodes.get(uid=input.content_uid)
                elif category == 'community_goal':
                    content_node = CommunityGoal.nodes.get(uid=input.content_uid)
                elif category == 'community_affiliation':
                    content_node = CommunityAffiliation.nodes.get(uid=input.content_uid)
                else:
                    return SendVibeToCommunityContent(
                        success=False,
                        message="Invalid content category. Must be community_achievement, community_activity, community_goal, or community_affiliation.",
                        community_content_vibe=None
                    )
            except Exception as e:
                return SendVibeToCommunityContent(
                    success=False,
                    message=f"Content not found: {str(e)}",
                    community_content_vibe=None
                )
            
            # Validate community membership
            try:
                community = content_node.community.single()
                subcommunity = content_node.subcommunity.single() if hasattr(content_node, 'subcommunity') else None
                
                target_community = subcommunity if subcommunity else community
                
                if target_community:
                    # Check if user is a member using the helper function
                    membership = helperfunction.get_membership_for_user_in_community(user_node, target_community)
                    
                    if not membership:
                        return SendVibeToCommunityContent(
                            success=False,
                            message="You must be a member of this community to send vibes",
                            community_content_vibe=None
                        )
            except Exception as e:
                # If we can't validate, allow the vibe (fail open for better UX)
                pass
            
            # Check if user has already reacted to this content with a vibe
            existing_vibe = None
            try:
                query = f"""
                MATCH (u:Users {{uid: $user_uid}})-[:REACTED_BY]-(ccv:CommunityContentVibe)<-[:HAS_VIBE_REACTION]-(content {{uid: $content_uid}})
                WHERE ccv.is_active = true
                RETURN ccv
                """
                results, _ = db.cypher_query(query, {
                    'user_uid': user_node.uid,
                    'content_uid': input.content_uid
                })
                
                if results:
                    # Update existing vibe instead of creating new one
                    from community.models import CommunityContentVibe
                    existing_vibe_node = CommunityContentVibe.inflate(results[0][0])
                    existing_vibe_node.individual_vibe_id = input.individual_vibe_id
                    existing_vibe_node.vibe_name = individual_vibe.name_of_vibe
                    existing_vibe_node.vibe_intensity = clean_intensity
                    existing_vibe_node.reaction_type = "vibe"
                    existing_vibe_node.timestamp = timezone.now()
                    existing_vibe_node.is_active = True
                    existing_vibe_node.save()
                    
                    return SendVibeToCommunityContent(
                        success=True,
                        message="Vibe updated successfully",
                        community_content_vibe=CommunityContentVibeType.from_neomodel(existing_vibe_node)
                    )
            except Exception as e:
                # Continue if query fails - better to allow than block valid reactions
                pass
            
            # Create new vibe reaction in Neo4j
            from community.models import CommunityContentVibe
            community_content_vibe = CommunityContentVibe(
                individual_vibe_id=input.individual_vibe_id,
                vibe_name=individual_vibe.name_of_vibe,
                vibe_intensity=clean_intensity,
                reaction_type="vibe"
            )
            community_content_vibe.save()
            
            # Connect to user
            community_content_vibe.reacted_by.connect(user_node)
            
            # Connect to content
            content_node.vibe_reactions.connect(community_content_vibe)
            
            # Update user's vibe score using existing system
            vibe_score_multiplier = clean_intensity / 5.0  # Convert to 0.0-1.0 multiplier
            
            # Apply weightages from IndividualVibe
            adjusted_score = (
                individual_vibe.weightage_iaq + 
                individual_vibe.weightage_iiq + 
                individual_vibe.weightage_ihq + 
                individual_vibe.weightage_isq
            ) / 4.0 * vibe_score_multiplier
            
            VibeUtils.onVibeCreated(user_node, individual_vibe.name_of_vibe, adjusted_score)
            
            return SendVibeToCommunityContent(
                success=True,
                message="Vibe sent to community content successfully!",
                community_content_vibe=CommunityContentVibeType.from_neomodel(community_content_vibe)
            )
            
        except Exception as e:
            return SendVibeToCommunityContent(
                success=False,
                message=f"Error sending vibe: {str(e)}",
                community_content_vibe=None
            )


class Mutation(graphene.ObjectType):
    create_community = CreateCommunity.Field()
    update_community = UpdateCommunity.Field()
    delete_community = DeleteCommunity.Field()

    update_community_group_info=UpdateCommunityGroupInfo.Field()

    create_community_message = CreateCommunityMessage.Field()
    edit_community_message= UpdateCommunityMessage.Field()

    add_member=AddMember.Field()
    remove_member=RemoveMember.Field()
    leave_community_chat=LeaveCommunityChat.Field()

    add_sub_community_member=AddSubCommunityMember.Field()
    remove_sub_community_member=RemoveSubCommunityMember.Field()

    create_community_review=CreateCommunityReview.Field()
    delete_community_review=DeleteCommunityReview.Field()
    update_community_review=UpdateCommunityReview.Field()
    delete_community_message=DeleteCommunityMessage.Field()

    create_community_goal=CreateCommunityGoal.Field()
    update_community_goal=UpdateCommunityGoal.Field()
    delete_community_goal=DeleteCommunityGoal.Field()

    create_community_activity=CreateCommunityActivity.Field()
    update_community_activity=UpdateCommunityActivity.Field()
    delete_community_activity=DeleteCommunityActivity.Field()

    create_community_affiliation=CreateCommunityAffiliation.Field()
    update_community_affiliation=UpdateCommunityAffiliation.Field()
    delete_community_affiliation=DeleteCommunityAffiliation.Field()

    create_community_achievement=CreateCommunityAchievement.Field()
    update_community_achievement=UpdateCommunityAchievement.Field()
    delete_community_achievement=DeleteCommunityAchievement.Field()

    mute_community_notification=MuteCommunityNotification.Field()
    unmute_community_notification=UnMuteCommunityNotification.Field()


    create_sub_community=CreateSubCommunity.Field()
    update_sub_community=UpdateSubCommunity.Field()

    

    
    create_community_role_manager=CreateCommunityRoleManager.Field()
    assign_community_role=AssignRoleMutation.Field()

    assign_sub_community_role=AssignSubcommunityRoleMutation.Field()

    create_sub_community_role_manager=CreateSubCommunityRoleManager.Field()

    join_generated_community=JoinGeneratedCommunity.Field()

    create_community_permission=CreateCommunityPermission.Field()

    create_generated_community=CreateGeneratedCommunity.Field()

    create_community_post=CreateCommunityPost.Field()
    delete_community_post=DeleteCommunityPost.Field()
    leave_community_chat=LeaveCommunityChat.Field()
    
    # V2 Mutations with enhanced fields
    create_community_v2=CreateCommunityV2.Field()
    create_sub_community_v2=CreateSubCommunityV2.Field()
    send_vibe_to_community_content=SendVibeToCommunityContent.Field()



