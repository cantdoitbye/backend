import asyncio
import graphene
from graphene import Mutation

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

            community = Community(
                name=input.get('name', ''),
                description=input.get('description', ''),
                community_circle=input.get('community_circle').value,
                community_type=input.get('community_type').value,
                room_id=room_id,
                category=input.get('category', ''),
                group_icon_id=input.get('group_icon_id', ''),
            )
            
            print("Checking member_uid...")
            member_uid=input.get('member_uid')
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
            # Note:- Review and Optimisations required here(we can store can_message,can_edit_group_info,can_add_new_member,is_notification_muted in postgresql)
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
                
                # Process member invites in a separate thread
                process_matrix_invites(
                    admin_user_id=user_id,
                    room_id=room_id,
                    member_ids=member_uid
                )

            print("Community creation completed successfully!")
            
            # Return success without trying to convert the community object
            # Bypassing CommunityType.from_neomodel which was causing the S3 connection error
            return CreateCommunity(
                community=None,  # Don't return community details in the initial response
                success=True,
                message=CommMessages.COMMUNITY_CREATED
            )
        except Exception as error:
            print(f"ERROR in CreateCommunity: {error}")
            import traceback
            traceback.print_exc()
            message=getattr(error , 'message' , str(error) )
            return CreateCommunity(community=None, success=False,message=message)



# This mutation is performed only by person who created this(admin)
class UpdateCommunity(Mutation):
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

            # checking user login is admin or not (person who created community)
            flag_community=0
            for community in created_by.community.all():
                if community.uid==input.uid:
                    flag_community=1
                    break
            if flag_community==0:
                return UpdateCommunity(community=None, success=False,message=CommMessages.COMMUNITY_NOT_CREATED_BY_USER)
            
            community = Community.nodes.get(uid=input.uid)
            # for id in input.file_id:
            if input.group_icon_id:
                valid_id=get_valid_image(input.group_icon_id)

            for key, value in input.items():
                setattr(community, key, value)
            community.save()
            return UpdateCommunity(community=CommunityType.from_neomodel(community), success=True,message=CommMessages.COMMUNITY_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateCommunity(community=None, success=False,message=message)


# This mutation is performed only by person who created this(admin)
class DeleteCommunity(Mutation):
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
            return CreateCommunityMessage(community_messages=CommunityMessagesType.from_neomodel(communitymessage), success=True, message=CommMessages.COMMUNITY_MESSAGE_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateCommunityMessage(community_messages=None, success=False,message=message)

class UpdateCommunityMessage(Mutation):
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
            
            # Send notifications to new members
            if members_to_notify:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifyCommunityMemberAdded(
                        added_by_name=user.username,
                        members=members_to_notify,
                        community_id=community.uid,
                        community_name=community.name,
                        community_icon=community.group_icon_id
                    ))
                finally:
                    loop.close()
            
            process_matrix_invites(
                admin_user_id=community.created_by.single().user_id,
                room_id=community.room_id,
                member_ids=user_uids
            )
            return AddMember(all_membership=MembershipType.from_neomodel(membership), success=True,message=CommMessages.COMMUNITY_MEMBER_ADDED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return AddMember(all_membership=None, success=False,message=message)


class RemoveMember(Mutation):

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


            for uid in membership_uid:
                membership = Membership.nodes.get(uid=uid)
                membership.delete()
                
            return RemoveMember(success=True,message=CommMessages.COMMUNITY_MEMBER_DELETED)
        except Exception as error:
            return RemoveMember(success=False, message=getattr(error,'message',str(error)))




class AddSubCommunityMember(Mutation):
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

            # Send notifications to new members
            if members_to_notify:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifySubCommunityMemberAdded(
                        added_by_name=user.username,
                        members=members_to_notify,
                        sub_community_id=sub_community.uid,
                        sub_community_name=sub_community.name,
                        sub_community_icon=sub_community.group_icon_id
                    ))
                finally:
                    loop.close()

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
            
            return CreateCommunityGoal(goal=CommunityGoalType.from_neomodel(goal), success=True, message=CommMessages.COMMUNITY_GOAL_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityGoal(goal=None, success=False, message=message)


class UpdateCommunityGoal(graphene.Mutation):
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
            )
            activity.save()
            activity.created_by.connect(creator)

            if isinstance(community, Community):
                activity.community.connect(community)
                community.communityactivity.connect(activity)
            else:
                activity.subcommunity.connect(community)
                community.communityactivity.connect(activity)

            return CreateCommunityActivity(activity=CommunityActivityType.from_neomodel(activity), success=True, message=CommMessages.COMMUNITY_ACTIVITY_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityActivity(activity=None, success=False, message=message)
    
class UpdateCommunityActivity(graphene.Mutation):
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
            
            return CreateCommunityAffiliation(affiliation=CommunityAffiliationType.from_neomodel(affiliation), success=True, message=CommMessages.COMMUNITY_AFFILIATION_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityAffiliation(affiliation=None, success=False, message=message)

class UpdateCommunityAffiliation(graphene.Mutation):
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

            achievement = CommunityAchievement(
                entity=input.entity,
                date=input.date,
                subject=input.subject,
                file_id=input.file_id,
            )
            achievement.save()
            achievement.created_by.connect(creator)

            if isinstance(community, Community):
                achievement.community.connect(community)
                community.communityachievement.connect(achievement)
            else:
                achievement.subcommunity.connect(community)
                community.communityachievement.connect(achievement)
            
            return CreateCommunityAchievement(achievement=CommunityAchievementType.from_neomodel(achievement), success=True, message=CommMessages.COMMUNITY_ACHIEVEMENT_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateCommunityAchievement(achievement=None, success=False, message=message)

class UpdateCommunityAchievement(graphene.Mutation):
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

            for key, value in input.items():
                setattr(achievement, key, value)

            achievement.save()
            return UpdateCommunityAchievement(achievement=CommunityAchievementType.from_neomodel(achievement), success=True, message=CommMessages.COMMUNITY_ACHIEVEMENT_UPDATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateCommunityAchievement(achievement=None, success=False, message=message)

class DeleteCommunityAchievement(graphene.Mutation):
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
            group_icon_id=input.get('group_icon_id', '38'), # This should be gather from env files
        )
            
        member_uid=input.get('member_uid')
        if not member_uid:
            return CreateSubCommunity(success=False,message=f"You have not selected any user")
            
        unavailable_user=userlist.get_unavailable_list_user(member_uid)
        if unavailable_user:
            return CreateSubCommunity(success=False,message=f"These uid's do not correspond to any user {unavailable_user}")
        
        
        try:
            community=Community.nodes.get(uid=input.parent_community_uid)

            membership_exists = helperfunction.get_membership_for_user_in_community(created_by, community)

            if not membership_exists:
                return CreateSubCommunity(success=False, message="You are not a member of this community and this communnity is private")

            if membership_exists:
                if membership_exists.is_admin==False:
                    return CreateSubCommunity(success=False, message="You are not authorised to add new member")

            sub_community.save()
            sub_community.created_by.connect(created_by)
            sub_community.parent_community.connect(community)
            if input.get('sub_community_type').value=='child community':
                community.child_communities.connect(sub_community)
            if input.get('sub_community_type').value=='sibling community':
                community.sibling_communities.connect(sub_community)
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
            return CreateSubCommunity( success=True,message=CommMessages.COMMUNITY_CREATED)
        
        except Community.DoesNotExist:
            try:
            # If the Community does not exist, try to retrieve a SubCommunity
                community = SubCommunity.nodes.get(uid=input.parent_community_uid)

                if community.sub_community_type == 'child community':
                    return CreateSubCommunity(success=False,message=CommMessages.SUB_COMMUNITY_NOT_ALLOWED)
                
                membership_exists = helperfunction.get_membership_for_user_in_sub_community(created_by, community)

                if not membership_exists:
                    return CreateSubCommunity(success=False, message="You are not a member of this community and this communnity is private")

                if membership_exists:
                    if membership_exists.is_admin==False:
                        return CreateSubCommunity(success=False, message="You are not authorised to add new member")

                sub_community.save()
                sub_community.created_by.connect(created_by)
                sub_community.sub_community_parent.connect(community)
                if input.get('sub_community_type').value == 'child community':
                    community.sub_community_children.connect(sub_community)
                if input.get('sub_community_type').value == 'sibling community':
                    community.sub_community_sibling.connect(sub_community)
                
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
                    return CreateSubCommunity( success=True,message=CommMessages.COMMUNITY_CREATED)
                
            except Exception as error:
                message=getattr(error , 'message' , str(error) )
                return CreateSubCommunity( success=False,message=message)


class UpdateSubCommunity(Mutation):
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

            membership_details=helperfunction.get_membership_for_user_in_sub_community(created_by,community)

            # checking user login is admin or not 
            
            if not membership_details:
                    return UpdateSubCommunity(success=False, message="You are not a member of this community")

            if membership_details:
                if  membership_details.is_admin==False:
                    return UpdateSubCommunity(success=False, message="You are not authorised to add new member")
            
            # for id in input.file_id:
            if input.group_icon_id:
                valid_id=get_valid_image(input.group_icon_id)

            if input.cover_image_id:
                valid_id=get_valid_image(input.cover_image_id)
            
            for key, value in input.items():
                setattr(community, key, value)
            community.save()
            return UpdateSubCommunity(community=SubCommunityType.from_neomodel(community), success=True,message=CommMessages.COMMUNITY_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateSubCommunity(community=None, success=False,message=message)


class CreateSubCommunityRoleManager(graphene.Mutation):
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

        return AssignRoleMutation(success=True, message="Role assignment successful")



class AssignSubcommunityRoleMutation(graphene.Mutation):
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

        return AssignSubcommunityRoleMutation(success=True, message="Role assignment successful")




class JoinGeneratedCommunity(Mutation):
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
        
            return JoinGeneratedCommunity(all_membership=MembershipType.from_neomodel(membership), success=True,message=CommMessages.COMMUNITY_MEMBER_ADDED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return JoinGeneratedCommunity(all_membership=None, success=False,message=message)



class CreateCommunityPermission(Mutation):
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
                raise("Authentication Failure")

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

            post = CommunityPost(
                post_title=post_title,
                post_text=post_text,
                post_type=post_type,
                privacy=privacy,
                post_file_id=post_file_id
            )
            post.save()
            post.creator.connect(creator)
            if flag:
                community.community_post.connect(post)
                post.created_by.connect(community)
            else:
                community.community_post.connect(post)
                post.created_by_subcommunity.connect(community)


            

            return CreateCommunityPost(success=True, message=CommMessages.POST_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateCommunityPost(success=False, message=message)


class DeleteCommunityPost(Mutation):
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





class Mutation(graphene.ObjectType):
    create_community = CreateCommunity.Field()
    update_community = UpdateCommunity.Field()
    delete_community = DeleteCommunity.Field()

    update_community_group_info=UpdateCommunityGroupInfo.Field()

    create_community_message = CreateCommunityMessage.Field()
    edit_community_message= UpdateCommunityMessage.Field()

    add_member=AddMember.Field()
    remove_member=RemoveMember.Field()

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



