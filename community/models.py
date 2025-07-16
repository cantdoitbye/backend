from neomodel import StructuredNode, StringProperty, IntegerProperty, ArrayProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom, FloatProperty
from django_neomodel import DjangoNode
from datetime import datetime
from auth_manager.models import Users 
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta
from vibe_manager.models import CommunityVibe
from post.models import Like,Comment

class Community(DjangoNode, StructuredNode):
    CIRCLE_CHOICES = {
        'Outer': 'outer circle',
        'Inner': 'inner circle',
        'Universal': 'universal'
    }

    GROUP_CHOICES = {
    'PersonalGroup': 'personal group',
    'InterestGroup': 'interest group',
    'OfficialGroup': 'official group',
    'BusinessGroup': 'business group'
    }


    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    description = StringProperty()
    community_type = StringProperty()
    community_circle = StringProperty(choices=CIRCLE_CHOICES.items())
    room_id=StringProperty()
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)
    number_of_members = IntegerProperty(default=0)
    group_invite_link = StringProperty()
    group_icon_id = StringProperty()
    cover_image_id=StringProperty()
    category = StringProperty()
    generated_community=BooleanProperty(default=False)
    only_admin_can_message=BooleanProperty(default=False)
    only_admin_can_add_member=BooleanProperty(default=False)
    only_admin_can_remove_member=BooleanProperty(default=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    members = RelationshipTo('Membership', 'MEMBER_OF')
    community_review = RelationshipTo('CommunityReview', 'REVIEW_FOR')
    communitymessage = RelationshipTo('CommunityMessages', 'BELONGS_TO')
    communitygoal=RelationshipTo('CommunityGoal', 'HAS_GOAL')
    communityactivity=RelationshipTo('CommunityActivity', 'HAS_ACTIVITY')
    communityaffiliation=RelationshipTo('CommunityAffiliation', 'HAS_AFFILIATION')
    communityachievement=RelationshipTo('CommunityAchievement', 'HAS_ACHIEVEMENT')
    child_communities = RelationshipTo('SubCommunity', 'HAS_CHILD_COMMUNITY')
    sibling_communities = RelationshipTo('SubCommunity', 'HAS_SIBLING_COMMUNITY')
    community_post=RelationshipTo('CommunityPost', 'HAS_POST')


    def save(self, *args, **kwargs):
        self.updated_date = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'community' #this is the name of app registered in setting.py

    def __str__(self):
        return self.name


class CommunityMessages(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'BELONGS_TO')
    sender = RelationshipTo('Users', 'SENT_BY')
    content = StringProperty()
    file_id = StringProperty()
    title = StringProperty()
    is_read = BooleanProperty(default=False)
    is_deleted = BooleanProperty(default=False)
    timestamp = DateTimeProperty(default_now=True)
    is_public = BooleanProperty(default=True)

    def send_message(self):
        # Implementation for sending messages
        pass
    
    class Meta:
        app_label = 'community'

    def __str__(self):
        return self.title


class Membership(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    user = RelationshipTo('Users', 'MEMBER')
    community = RelationshipTo('Community', 'MEMBEROF')
    is_admin = BooleanProperty(default=False)
    is_leader = BooleanProperty(default=False)
    is_accepted = BooleanProperty(default=True)
    join_date = DateTimeProperty(default_now=True)
    can_message = BooleanProperty(default=True)
    is_blocked = BooleanProperty(default=False)
    is_notification_muted=BooleanProperty(default=False)
    can_add_member=BooleanProperty(default=False)
    can_remove_member=BooleanProperty(default=False)
    

    
    class Meta:
        app_label='community'

    def __str__(self):
        return self.uid





class CommunityProduct(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'HAS_PRODUCT')
    product_id = StringProperty(required=True)
    is_accepted = BooleanProperty(default=False)
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class CommunityStory(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'HAS_STORY')
    story_id = StringProperty(required=True)
    is_accepted = BooleanProperty(default=False)
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class Election(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'HAS_ELECTION')
    is_active = BooleanProperty(default=False)
    start_date = DateTimeProperty(required=True)
    nomination_duration = IntegerProperty(required=True)  # Duration in days
    voting_duration = IntegerProperty(required=True)  # Duration in days
    result_announcement = DateTimeProperty()

    def create_nomination(self, member):
        nomination = Nomination(election=self, member=member)
        nomination.save()

    def get_nominations(self):
        return self.nomination_set.all()

    def get_votes(self):
        return self.vote_set.all()


class Nomination(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    election = RelationshipTo('Election', 'NOMINATION_FOR')
    member = RelationshipTo('Membership', 'NOMINATED_MEMBER')
    vibes_received = IntegerProperty(default=0)
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class Vote(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    election = RelationshipTo('Election', 'VOTE_FOR')
    voter = RelationshipTo('Membership', 'VOTED_BY')
    nominee = RelationshipTo('Nomination', 'VOTED_TO')
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class Role(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'ROLE_IN')
    name = StringProperty(required=True)
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class CommunityRole(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    membership = RelationshipTo('Membership', 'ROLE_FOR')
    role = RelationshipTo('Role', 'ROLE_OF')
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class Message(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'MESSAGE_IN')
    sender = RelationshipTo('User', 'MESSAGE_FROM')
    content = StringProperty(required=True)
    timestamp = DateTimeProperty(default_now=True)
    is_hidden = BooleanProperty(default=False)
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class CommunityKeyword(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'KEYWORD_FOR')
    keyword = StringProperty(unique_index=True, required=True)
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class CommunityExit(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'EXIT_FROM')
    user = RelationshipTo('User', 'EXIT_BY')
    exit_date = DateTimeProperty(default_now=True)
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class CommunityRule(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    community = RelationshipTo('Community', 'RULE_FOR')
    rule_text = StringProperty(required=True)
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)


class CommunityReview(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    byuser = RelationshipTo('Users', 'REVIEW_BY')
    tocommunity = RelationshipTo('Community', 'REVIEW_FOR')
    tosubcommunity=RelationshipTo('SubCommunity', 'REVIEW_FOR')
    reaction = StringProperty(default='Like')
    vibe = FloatProperty(default=2.0)
    title = StringProperty()
    content = StringProperty()
    file_id = StringProperty()
    is_deleted = BooleanProperty(default=False)
    timestamp = DateTimeProperty(default_now=True)

    class Meta:
        app_label = 'community'

    def __str__(self):
        return self.reaction


class CommunityUserBlock(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    blocker = RelationshipTo('User', 'BLOCKER')
    blocked = RelationshipTo('User', 'BLOCKED')
    created_at = DateTimeProperty(default_now=True)

    def __str__(self):
        return "{} blocked by {}".format(self.blocked.username, self.blocker.username)

class CommunityGoal(DjangoNode,StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    description = StringProperty(required=True)
    file_id=ArrayProperty(base_property=StringProperty())
    created_by = RelationshipTo('Users', 'CREATED_BY')
    community = RelationshipTo('Community', 'GOAL_FOR')
    subcommunity = RelationshipTo('SubCommunity', 'GOAL_FOR')
    timestamp = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)

    class Meta:
        app_label = 'community'

    def __str__(self):
        return self.name
    

class CommunityActivity(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    description = StringProperty()
    activity_type = StringProperty()
    file_id=ArrayProperty(base_property=StringProperty())
    created_by = RelationshipTo('Users', 'CREATED_BY')
    community = RelationshipTo('Community', 'ACTIVITY_FOR')
    subcommunity = RelationshipTo('SubCommunity', 'ACTIVITY_FOR')
    date = DateTimeProperty()
    is_deleted = BooleanProperty(default=False)

    class Meta:
        app_label = 'community'

    def __str__(self):
        return self.name
    

class CommunityAffiliation(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    entity = StringProperty(required=True)
    date = DateTimeProperty(required=True)
    subject = StringProperty(required=True)
    file_id=ArrayProperty(base_property=StringProperty())
    created_by = RelationshipTo('Users', 'CREATED_BY')
    community = RelationshipTo('Community', 'AFFILIATION_FOR')
    subcommunity = RelationshipTo('SubCommunity', 'AFFILIATION_FOR')
    timestamp = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)

    class Meta:
        app_label = 'community'

    def __str__(self):
        return self.entity

class CommunityAchievement(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    entity = StringProperty(required=True)
    date = DateTimeProperty(required=True)
    subject = StringProperty(required=True)
    file_id=ArrayProperty(base_property=StringProperty())
    created_by = RelationshipTo('Users', 'CREATED_BY')
    community = RelationshipTo('Community', 'ACHIEVEMENT_FOR')
    subcommunity = RelationshipTo('SubCommunity', 'ACHIEVEMENT_FOR')
    timestamp = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)

    class Meta:
        app_label = 'community'

    def __str__(self):
        return self.entity
    

class CommunityRoleManager(models.Model):  

    community_uid = models.CharField(max_length=255, null=True, blank=True)  # Updated field name
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=timezone.now)
    roles = models.JSONField(default=list)  # Renamed field for clarity
    
    class Meta:
        verbose_name = 'Community Role Manager'
        verbose_name_plural = 'Community Role Managers'
        ordering = ['-created_on']

    def __str__(self):
        return f"CommunityRoleManager for {self.community_uid} by {self.created_by.username}"

    def add_roles(self, role_name, **permissions):
        """Add a role with an incremented ID and permissions to the roles list."""
        # Determine the next ID
        if self.roles:
            # Extract current IDs and find the max
            max_id = max(role.get('id', 0) for role in self.roles)
            next_id = max_id + 1
        else:
            # Start IDs from 1 if there are no existing roles
            next_id = 1

        role_info = {
            'id': next_id,  # Assign the next available ID
            'role_name': role_name,
            **permissions
        }
        
        self.roles.append(role_info)

    def get_roles(self):
        """Retrieve all roles and their permissions."""
        return self.roles

    def get_role_permissions(self, role_name):
        """Retrieve permissions for a specific role."""
        for role in self.roles:
            if role['role_name'] == role_name:
                return role
        return None  # Role not found

class CommunityRoleAssignment(models.Model):
    community_uid = models.CharField(max_length=255, null=True, blank=True)  # Community UID
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Who created the assignment
    created_on = models.DateTimeField(default=timezone.now)  # When the assignment was created
    assigned_to = models.JSONField(default=list)  # Stores role_id and user_uid list

    class Meta:
        verbose_name = 'Role Assignment'
        verbose_name_plural = 'Role Assignments'
        ordering = ['-created_on']

    def __str__(self):
        return f"RoleAssignment for {self.community_uid} by {self.created_by.username}"

    def assign_role(self, role_id, user_uid_list):
        """
        Assign a role to multiple users.
        Ensure the same user is not assigned to multiple roles within the same community.
        """
        # Collect all existing user_uids across all role assignments
        all_assigned_users = {user_uid for assignment in self.assigned_to for user_uid in assignment['user_uids']}

        # Check if any user_uid in user_uid_list is already assigned to a different role
        for user_uid in user_uid_list:
            if user_uid in all_assigned_users:
                raise ValueError(f"User with UID '{user_uid}' is already assigned to another role in this community.")

        # Check if the role_id already exists in the assigned_to list
        for assignment in self.assigned_to:
            if assignment['role_id'] == role_id:
                # Append new user_uids to the existing list if role_id exists
                assignment['user_uids'] = list(set(assignment['user_uids'] + user_uid_list))
                break
        else:
            # Add a new role assignment if role_id does not exist
            new_assignment = {
                'role_id': role_id,
                'user_uids': user_uid_list
            }
            self.assigned_to.append(new_assignment)

        self.save()

    def get_assigned_roles(self):
        """
        Retrieve all role assignments for this community.
        """
        return self.assigned_to

    def get_users_for_role(self, role_id):
        """
        Retrieve all users assigned to a specific role_id.
        """
        for assignment in self.assigned_to:
            if assignment['role_id'] == role_id:
                return assignment['user_uids']
        return []


class SubCommunity(DjangoNode, StructuredNode):
    CIRCLE_CHOICES = {
        'Outer': 'outer circle',
        'Inner': 'inner circle',
        'Universal': 'universal'
    }

    
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    description = StringProperty()
    sub_community_type = StringProperty()
    sub_community_group_type=StringProperty()
    sub_community_circle = StringProperty(choices=CIRCLE_CHOICES.items())
    room_id=StringProperty()
    created_date = DateTimeProperty(default_now=True)
    updated_date = DateTimeProperty(default_now=True)
    number_of_members = IntegerProperty(default=0)
    group_invite_link = StringProperty()
    group_icon_id = StringProperty()
    cover_image_id = StringProperty()
    category = StringProperty()
    only_admin_can_message=BooleanProperty(default=False)
    only_admin_can_add_member=BooleanProperty(default=False)
    only_admin_can_remove_member=BooleanProperty(default=True)
    created_by = RelationshipTo('Users', 'CREATED_BY')
    parent_community = RelationshipTo('Community', 'PARENT_COMMUNITY')
    sub_community_members=RelationshipTo('SubCommunityMembership', 'MEMBER_OF')

    # Self-referencing relationship for hierarchy
    sub_community_parent = RelationshipTo('SubCommunity', 'PARENT_OF')
    sub_community_children = RelationshipTo('SubCommunity', 'HAS_CHILD_COMMUNITY')
    sub_community_sibling = RelationshipTo('SubCommunity', 'HAS_SIBLING_COMMUNITY')
    community_post=RelationshipTo('CommunityPost', 'HAS_POST')
    communitygoal=RelationshipTo('CommunityGoal', 'HAS_GOAL')
    communityactivity=RelationshipTo('CommunityActivity', 'HAS_ACTIVITY')
    communityaffiliation=RelationshipTo('CommunityAffiliation', 'HAS_AFFILIATION')
    communityachievement=RelationshipTo('CommunityAchievement', 'HAS_ACHIEVEMENT')
    community_review = RelationshipTo('CommunityReview', 'REVIEW_FOR')

    def save(self, *args, **kwargs):
        self.updated_date = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'community' #this is the name of app registered in setting.py

    def __str__(self):
        return self.name
    


class SubCommunityMembership(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    user = RelationshipTo('Users', 'MEMBER')
    sub_community = RelationshipTo('SubCommunity', 'MEMBEROF')
    is_admin = BooleanProperty(default=False)
    is_accepted = BooleanProperty(default=True)
    join_date = DateTimeProperty(default_now=True)
    can_message = BooleanProperty(default=True)
    is_blocked = BooleanProperty(default=False)
    is_notification_muted=BooleanProperty(default=False)
    can_add_member=BooleanProperty(default=False)
    can_remove_member=BooleanProperty(default=False)
    room_id=StringProperty()
    

    
    class Meta:
        app_label='community'

    def __str__(self):
        return self.uid
    




    
# Model if we want to store in json all role of particular community
class SubCommunityRoleManager(models.Model):
    sub_community_uid = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=timezone.now)
    role_data = models.JSONField(default=list)  # Use list for multiple roles

    class Meta:
        verbose_name = 'Sub Community Role Manager'
        verbose_name_plural = 'Sub Community Role Managers'
        ordering = ['-created_on']

    def __str__(self):
        return f"SubCommunityRoleManager for {self.sub_community_uid} by {self.created_by.username}"

    def add_role(self, role_name, **permissions):
        """Add a role with an incremented ID and permissions to the role_data list."""
        # Determine the next available ID
        if self.role_data:
            # Extract current IDs and find the maximum
            max_id = max(role.get('id', 0) for role in self.role_data if 'id' in role)
            next_id = max_id + 1
        else:
            # Start IDs from 1 if there are no existing roles
            next_id = 1

        role_info = {
            'id': next_id,  # Assign the next available ID
            'role_name': role_name,  # Store the role name
            **permissions  # Include all provided permissions
        }
        
        # Append the new role information to the role_data list
        self.role_data.append(role_info)

    def get_roles(self):
        """Retrieve all roles and their permissions."""
        return self.role_data

    def get_role_permissions(self, role_name):
        """Retrieve permissions for a specific role."""
        for role in self.role_data:
            if role['role_name'] == role_name:
                return role
        return None  # Role not found


class SubCommunityRoleAssignment(models.Model):  # Renamed from CommunityRoleAssignment to SubcommunityRoleAssignment
    subcommunity_uid = models.CharField(max_length=255, null=True, blank=True)  # Updated field name to subcommunity_uid
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Who created the assignment
    created_on = models.DateTimeField(default=timezone.now)  # When the assignment was created
    assigned_to = models.JSONField(default=list)  # Stores role_id and user_uid list

    class Meta:
        verbose_name = 'Subcommunity Role Assignment'  # Updated verbose name
        verbose_name_plural = 'Subcommunity Role Assignments'  # Updated plural verbose name
        ordering = ['-created_on']

    def __str__(self):
        return f"SubcommunityRoleAssignment for {self.subcommunity_uid} by {self.created_by.username}"  # Updated string representation

    def assign_role(self, role_id, user_uid_list):
        """
        Assign a role to multiple users.
        Ensure the same user is not assigned to multiple roles within the same subcommunity.
        """
        # Collect all existing user_uids across all role assignments
        all_assigned_users = {user_uid for assignment in self.assigned_to for user_uid in assignment['user_uids']}

        # Check if any user_uid in user_uid_list is already assigned to a different role
        for user_uid in user_uid_list:
            if user_uid in all_assigned_users:
                raise ValueError(f"User with UID '{user_uid}' is already assigned to another role in this subcommunity.")

        # Check if the role_id already exists in the assigned_to list
        for assignment in self.assigned_to:
            if assignment['role_id'] == role_id:
                # Append new user_uids to the existing list if role_id exists
                assignment['user_uids'] = list(set(assignment['user_uids'] + user_uid_list))
                break
        else:
            # Add a new role assignment if role_id does not exist
            new_assignment = {
                'role_id': role_id,
                'user_uids': user_uid_list
            }
            self.assigned_to.append(new_assignment)

        self.save()

    def get_assigned_roles(self):
        """
        Retrieve all role assignments for this subcommunity.
        """
        return self.assigned_to

    def get_users_for_role(self, role_id):
        """
        Retrieve all users assigned to a specific role_id.
        """
        for assignment in self.assigned_to:
            if assignment['role_id'] == role_id:
                return assignment['user_uids']
        return []


class CommunityReactionManager(models.Model):
    community_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    community_vibe = models.JSONField(default=list)  # List to hold multiple reactions

    class Meta:
        verbose_name = 'Community Reaction Manager'
        verbose_name_plural = 'Community Reaction Managers'

    def __str__(self):
        return f"CommunityReactionManager for community {self.community_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = CommunityVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the IndividualVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.community_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_id exists
        for reaction in self.community_vibe:
            if reaction['vibes_name'] == vibes_name:
                # Update existing reaction with new count and cumulative score
                reaction['vibes_count'] += 1
                # Update cumulative vibe score (average score calculation)
                total_score = reaction['cumulative_vibe_score'] * (reaction['vibes_count'] - 1) + score
                reaction['cumulative_vibe_score'] = total_score / reaction['vibes_count']
                break
        else:
            # If no reaction exists, this should initialize (but this case shouldn't happen as we initialize 10 vibes)
            raise ValueError(f"No initialized reaction for vibes_id {vibes_name} found.")

    def get_reactions(self):
        """Retrieve all reactions with their vibe details."""
        return self.community_vibe

class GeneratedCommunityUserManager(models.Model):
    community_uid = models.CharField(max_length=255, unique=True)
    community_name = models.CharField(max_length=255)
    created_on = models.DateTimeField(default=timezone.now)
    user_ids = models.JSONField(default=list)  # To store user IDs as a list in JSON format

    class Meta:
        verbose_name = 'Generated Community User Manager'
        verbose_name_plural = 'Generated Community User Managers'
        ordering = ['-created_on']

    def __str__(self):
        return f"Community: {self.community_name} - UID: {self.community_uid}"

    def add_user_to_community(self, user_id):
        """Add a user to the community if they are not already in the user_ids list."""
        if user_id not in self.user_ids:
            self.user_ids.append(user_id)
            self.save()
        else:
            return False
        

class CommunityPost(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    PRIVACY_CHOICES = {
        'public': 'Public',
        'private': 'Private'
    }
    post_title = StringProperty()
    post_text = StringProperty() 
    post_type = StringProperty(required=True)
    post_file_id=ArrayProperty(base_property=StringProperty())
    privacy = StringProperty(default='public', choices=PRIVACY_CHOICES.items())
    vibe_score=FloatProperty(default=2.0)
    created_at = DateTimeProperty(default_now=True) 
    updated_at = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)  # Add the is_active flag
    created_by = RelationshipTo('Community', 'HAS_COMMUNITY')  # Define the relationship 
    created_by_subcommunity=RelationshipTo('SubCommunity','HAS_SUBCOMMUNITY')

    creator=RelationshipTo('Users', 'HAS_CREATOR')
    updated_by=RelationshipTo('Users','HAS_UPDATED_USER')
    comment_count = IntegerProperty(default=0)
    vibes_count=IntegerProperty(default=0)
    share_count=IntegerProperty(default=0)
    comment=RelationshipTo('Comment','HAS_COMMENT')
    like=RelationshipTo('Like','HAS_LIKE')

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label='community'
        
        
    
    def __str__(self):
        return self.post_title