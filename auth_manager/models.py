# auth_manager/models.py
from neomodel import StructuredNode , StringProperty,IntegerProperty, FloatProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, OneOrMore, RelationshipTo,RelationshipFrom,ArrayProperty,ZeroOrMore
from django_neomodel import DjangoNode
from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .enums.otp_purpose_enum import OtpPurposeEnum
from django.db import models
from vibe_manager.models import IndividualVibe
import uuid
import hashlib


class Users(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    user_id = StringProperty(unique_index=True, required=True)
    username = StringProperty(unique_index=True) 
    password = StringProperty(required=False)
    email = StringProperty(unique_index=True)
    first_name=StringProperty()
    last_name=StringProperty()
    user_type=StringProperty(default="personal")
    created_at = DateTimeProperty(default_now=True) 
    created_by = StringProperty() 
    updated_at = DateTimeProperty(default_now=True)
    updated_by = StringProperty()
    is_active = BooleanProperty(default=False)  # Add the is_active flag
    
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Define the relationship 
    story=RelationshipTo('story.models.Story','HAS_STORY')
    post=RelationshipTo('post.models.Post','HAS_POST')
    connection=RelationshipTo('connection.models.Connection','HAS_CONNECTION')
    connectionv2=RelationshipTo('connection.models.ConnectionV2','HAS_CONNECTION')
    community=RelationshipTo('community.models.Community','HAS_COMMUNITY')
    conversation=RelationshipTo('msg.models.Conversation','HAS_CONVERSATION')
    service=RelationshipTo('service.models.Service','HAS_SERVICE')
    meetings=RelationshipTo('dairy.models.Meeting','HAS_MEETING')
    todo=RelationshipTo('dairy.models.ToDo','HAS_TODO')
    note=RelationshipTo('dairy.models.Note','HAS_NOTE')
    reminder=RelationshipTo('dairy.models.Reminder','HAS_REMINDER')
    product=RelationshipTo('shop.models.Product','HAS_PRODUCT')
    user_review=RelationshipTo('UsersReview','HAS_USER_REVIEW')
    vibe=RelationshipTo('vibe_manager.models.Vibe','HAS_VIBES')
    userviberepo=RelationshipTo('UserVibeRepo','HAS_REPO')
    connection_stat=RelationshipTo('ConnectionStats','HAS_CONNECTION_STAT')
    company=RelationshipTo('job.models.Company','HAS_COMPANY')
    job=RelationshipTo('job.models.Job','HAS_JOB')
    blocked=RelationshipTo('msg.models.Block','HAS_BLOCK')
    user_back_profile_review=RelationshipTo('BackProfileUsersReview','HAS_USER_REVIEW')

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'auth_manager'
        
        
    
    def __str__(self):
        return self.username


class Profile(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    user_id = StringProperty(unique_index=True, required=True)
    gender = StringProperty()
    device_id = StringProperty()
    fcm_token = StringProperty()
    bio = StringProperty()
    designation = StringProperty()
    worksat = StringProperty()
    phone_number = StringProperty()
    born = DateTimeProperty()
    dob = DateTimeProperty()
    school = StringProperty()
    college = StringProperty()
    lives_in = StringProperty()
    state = StringProperty()
    city = StringProperty()
    profile_pic_id = StringProperty()
    cover_image_id = StringProperty()
    user = RelationshipTo('Users', 'HAS_USER')
    onboarding=RelationshipTo('OnboardingStatus','HAS_ONBOARDING_STATUS')
    contactinfo=RelationshipTo('ContactInfo','HAS_CONTACT_INFO')
    score=RelationshipTo('Score','HAS_SCORE')
    interest=RelationshipTo('Interest','HAS_INTEREST')
    achievement=RelationshipTo('Achievement','HAS_ACHIEVEMENT')
    education=RelationshipTo('Education','HAS_EDUCATION')
    skill=RelationshipTo('Skill','HAS_SKILL')
    experience=RelationshipTo('Experience','HAS_EXPERIENCE')
    
    
    class Meta:
        app_label = 'auth_manager'


class OnboardingStatus(DjangoNode,StructuredNode):
    uid=UniqueIdProperty()
    email_verified = BooleanProperty(default=False)
    phone_verified = BooleanProperty(default=False)
    username_selected = BooleanProperty(default=False)
    first_name_set = BooleanProperty(default=False)
    last_name_set = BooleanProperty(default=False)
    gender_set = BooleanProperty(default=False)
    bio_set = BooleanProperty(default=False)
    state = BooleanProperty(default=False)
    city = BooleanProperty(default=False)
    profile = RelationshipTo('Profile', 'HAS_PROFILE')

    class Meta:
        app_label = 'auth_manager'


class ContactInfo(DjangoNode,StructuredNode):
    uid=UniqueIdProperty()
    type = StringProperty(required=True)  
    value = StringProperty(required=True) 
    platform = StringProperty() 
    link = StringProperty() 
    profile = RelationshipTo('Profile', 'HAS_PROFILE')
    is_deleted = BooleanProperty(default=False)

    class Meta:
        app_label = 'auth_manager'


class Score(DjangoNode,StructuredNode):
    uid = UniqueIdProperty()
    vibers_count = FloatProperty(default=2.0)
    cumulative_vibescore = FloatProperty(default=2.0)
    intelligence_score = FloatProperty(default=2.0)
    appeal_score = FloatProperty(default=2.0)
    social_score = FloatProperty(default=2.0)
    human_score = FloatProperty(default=2.0)
    repo_score = FloatProperty(default=2.0)
    profile = RelationshipTo('Profile', 'HAS_SCORE')


    class Meta:
        app_label = 'auth_manager'


class Interest(DjangoNode,StructuredNode):
    uid=UniqueIdProperty()
    names = ArrayProperty(base_property=StringProperty(), required=True)
    profile = RelationshipTo('Profile', 'HAS_PROFILE')
    is_deleted = BooleanProperty(default=False)



class OTP(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=255, choices=[(tag.value, tag.name) for tag in OtpPurposeEnum],default=OtpPurposeEnum.EMAIL_VERIFICATION)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP {self.otp} for {self.user}"
    

class UsersReview(DjangoNode,StructuredNode):
    uid=UniqueIdProperty()
    byuser = RelationshipTo('Users','REVIEW_BY_USER' )
    touser = RelationshipTo('Users','REVIEW_TO_USER' )
    reaction = StringProperty()
    vibe = FloatProperty(default=2.0)
    title = StringProperty()
    content =StringProperty()
    file_id = StringProperty()
    is_deleted = BooleanProperty(default=False)
    timestamp=DateTimeProperty(default_now=True)
    
    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        return self.reaction
    

class UserVibeRepo(DjangoNode,StructuredNode):
    uid=UniqueIdProperty()
    user = RelationshipTo('Users','VIBE_REPO' )
    category = StringProperty()
    custom_value = FloatProperty()
    created_at = DateTimeProperty(default_now=True)
    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        return ""
    
class ConnectionStats(DjangoNode, StructuredNode):
    uid=UniqueIdProperty()
    received_connections_count = IntegerProperty(default=0)
    accepted_connections_count = IntegerProperty(default=0)
    rejected_connections_count = IntegerProperty(default=0)
    sent_connections_count = IntegerProperty(default=0)
    inner_circle_count=IntegerProperty(default=0)
    outer_circle_count=IntegerProperty(default=0)
    universal_circle_count=IntegerProperty(default=0)

    class Meta:
        app_label = 'connection'


class WelcomeScreenMessage(models.Model):
    BRAND = 'brand'
    PERSONAL = 'personal'

    CONTENT_TYPE_CHOICES = [
        (BRAND, 'Brand'),
        (PERSONAL, 'Personal Account'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.FileField(upload_to='welcomescreenimages/', blank=True, null=True)
    rank = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    is_visible = models.BooleanField(default=False)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES, default=PERSONAL)

    class Meta:
        ordering = ['rank', '-timestamp']
        verbose_name = 'Welcome Screen Message'
        verbose_name_plural = 'Welcome Screen Messages'

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"

    def save(self, *args, **kwargs):
        if not self.rank:
            self.rank = WelcomeScreenMessage.objects.count() + 1
        super().save(*args, **kwargs)


class UploadContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ForeignKey to User model
    contact = models.JSONField() # Array field to store contacts
    created_on = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Upload Contact'
        verbose_name_plural = 'Upload Contact'
        ordering = ['-created_on']

    def __str__(self):
        return f"UploadContact for {self.user.username} with contacts {self.contact}"

    def save(self, *args, **kwargs):
        if not self.created_on:
            self.created_on = timezone.now()
        super().save(*args, **kwargs)

    
class ProfileReactionManager(models.Model):
    profile_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_vibe = models.JSONField(default=list)  # List to hold multiple reactions

    class Meta:
        verbose_name = 'Profile Reaction Manager'
        verbose_name_plural = 'Profile Reaction Managers'

    def __str__(self):
        return f"ProfileReactionManager for profile {self.profile_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the ProfileVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.profile_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.profile_vibe:
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
        return self.profile_vibe

class InterestList(models.Model):
    name = models.CharField(max_length=255, unique=True)
    sub_interests = models.JSONField(default=list)  # Store sub-interests as a JSON list

    def __str__(self):
        return self.name
    

class BackProfileUsersReview(DjangoNode,StructuredNode):
    uid=UniqueIdProperty()
    byuser = RelationshipTo('Users','REVIEW_BY_USER' )
    touser = RelationshipTo('Users','REVIEW_TO_USER' )
    reaction = StringProperty()
    vibe = FloatProperty(default=2.0)
    title = StringProperty()
    content =StringProperty()
    file_id = StringProperty()
    is_deleted = BooleanProperty(default=False)
    timestamp=DateTimeProperty(default_now=True)
    
    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        return self.reaction
    


class BackProfileReactionManager(models.Model):
    profile_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_vibe = models.JSONField(default=list)  # List to hold multiple reactions

    class Meta:
        verbose_name = 'Profile Reaction Manager'
        verbose_name_plural = 'Profile Reaction Managers'

    def __str__(self):
        return f"ProfileReactionManager for profile {self.profile_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the ProfileVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.profile_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.profile_vibe:
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
        return self.profile_vibe
    

# This model is not used in the project
class Country(models.Model):
    country = models.CharField(max_length=255, unique=True)
    states = models.JSONField(default=list)  # Stores a list of states as JSON

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return f"Country: {self.country}"

    def update_state_name(self, old_state_name, new_state_name):
        """
        Rename a state inside the `states` JSON field and update it in the State model.
        """
        updated = False
        for state in self.states:
            if state == old_state_name:
                state_index = self.states.index(old_state_name)
                self.states[state_index] = new_state_name
                updated = True
                break

        if updated:
            self.save()

            # Rename the state in the State table
            try:
                state_obj = State.objects.get(state=old_state_name)
                state_obj.state = new_state_name
                state_obj.save()
            except State.DoesNotExist:
                return f"Warning: State '{old_state_name}' not found in State table."

            return f"State '{old_state_name}' renamed to '{new_state_name}' in both Country and State tables."

        return f"Error: State '{old_state_name}' not found in Country."

# This model is not used in the project
class State(models.Model):
    state = models.CharField(max_length=255, unique=True)
    cities = models.JSONField(default=list)  # Stores a list of cities as JSON

    class Meta:
        verbose_name = 'State'
        verbose_name_plural = 'States'

    def __str__(self):
        return f"State: {self.state}"
    

class CountryInfo(models.Model):
    id = models.AutoField(primary_key=True)
    country_name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Country Information"
        verbose_name_plural = "Countries Information"

    def __str__(self):
        return self.country_name


class StateInfo(models.Model):
    id = models.AutoField(primary_key=True)
    state_name = models.CharField(max_length=255, unique=True)
    country = models.ForeignKey(CountryInfo, on_delete=models.CASCADE, related_name="states")

    class Meta:
        verbose_name = "State Information"
        verbose_name_plural = "States Information"

    def __str__(self):
        return self.state_name


class CityInfo(models.Model):
    id = models.AutoField(primary_key=True)
    city_name = models.CharField(max_length=255)
    state = models.ForeignKey(StateInfo, on_delete=models.CASCADE, related_name="cities")

    class Meta:
        verbose_name = "City Information"
        verbose_name_plural = "Cities Information"

    def __str__(self):
        return self.city_name


# These Models are used in V2 version of api


def generate_hashed_uuid():
    """Generate a secure hashed UUID."""
    raw_uuid = str(uuid.uuid4())  # Generate raw UUID
    return hashlib.sha256(raw_uuid.encode()).hexdigest()  # Hash it


def default_expiry_date():
    """Returns the default expiry date (30 days from now)."""
    return timezone.now() + timedelta(days=30)


class Invite(models.Model):
    class OriginType(models.TextChoices):
        MENU = "menu", "Menu"
        COMMUNITY = "community", "Community"
        TRUTH_SECTION = "truth_section", "Truth Section"

    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invites")
    invite_token = models.CharField(max_length=64, unique=True, editable=False, default=generate_hashed_uuid)
    origin_type = models.CharField(max_length=20, choices=OriginType.choices)
    creation_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(default=default_expiry_date)
    usage_count = models.PositiveIntegerField(default=0)
    last_used_timestamp = models.DateTimeField(null=True, blank=True)
    login_users = models.ManyToManyField(User, related_name="used_invites", blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Invite"
        verbose_name_plural = "Invites"
        ordering = ["-creation_date"]

    def __str__(self):
        return f"Invite {self.invite_token[:8]}... by {self.inviter.username}"  # Shortened token for readability

    def save(self, *args, **kwargs):
        """Ensure default values before saving."""
        if not self.expiry_date:
            self.expiry_date = default_expiry_date()
        super().save(*args, **kwargs)

# This is of no use. I tried it so that we can reduce line of codes but it 
# results in greater complexities
class ProfileDataReactionManager(models.Model):
    profile_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)

    education_vibe = models.JSONField(default=list)  
    achievement_vibe = models.JSONField(default=list)  
    skill_vibe = models.JSONField(default=list)  
    experience_vibe = models.JSONField(default=list)  # Added experience category

    class Meta:
        verbose_name = 'Profile Data Reaction Manager'
        verbose_name_plural = 'Profile Data Reaction Managers'

    def __str__(self):
        return f"ProfileDataReactionManager for profile {self.profile_uid}"

    def initialize_reactions(self, category):
        """
        Initialize the first 10 vibes for the specified category with `vibes_count=0` and `cumulative_vibe_score=0`.
        """
        category_map = {
            "education": "education_vibe",
            "achievement": "achievement_vibe",
            "skill": "skill_vibe",
            "experience": "experience_vibe"  # Added experience category
        }

        if category not in category_map:
            raise ValueError("Invalid category. Choose from 'education', 'achievement', 'skill', or 'experience'.")

        first_10_vibes = IndividualVibe.objects.all()[:10]  

        setattr(self, category_map[category], [
            {
                'id': vibe.id,
                'vibes_id': vibe.id,
                'vibes_name': vibe.name_of_vibe,
                'vibes_count': 0,
                'cumulative_vibe_score': 0
            } for vibe in first_10_vibes
        ])
        self.save()  

    def add_reaction(self, category, vibes_name, score):
        """
        Add or update a reaction for a specific category (education, achievement, skill, experience).
        """
        category_map = {
            "education": self.education_vibe,
            "achievement": self.achievement_vibe,
            "skill": self.skill_vibe,
            "experience": self.experience_vibe  # Added experience category
        }

        if category not in category_map:
            raise ValueError("Invalid category. Choose from 'education', 'achievement', 'skill', or 'experience'.")

        vibe_list = category_map[category]

        for reaction in vibe_list:
            if reaction['vibes_name'] == vibes_name:
                reaction['vibes_count'] += 1
                total_score = reaction['cumulative_vibe_score'] * (reaction['vibes_count'] - 1) + score
                reaction['cumulative_vibe_score'] = total_score / reaction['vibes_count']
                break
        else:
            raise ValueError(f"No initialized reaction for vibes_name {vibes_name} found in {category}.")

        setattr(self, category + "_vibe", vibe_list)
        self.save()

    def get_reactions(self, category):
        """
        Retrieve all reactions for a specific category (education, achievement, skill, experience).
        """
        category_map = {
            "education": self.education_vibe,
            "achievement": self.achievement_vibe,
            "skill": self.skill_vibe,
            "experience": self.experience_vibe  # Added experience category
        }

        if category not in category_map:
            raise ValueError("Invalid category. Choose from 'education', 'achievement', 'skill', or 'experience'.")

        return category_map[category]


class Achievement(DjangoNode,StructuredNode):
    uid = UniqueIdProperty()
    profile = RelationshipTo('Profile', 'HAS_PROFILE')
    like= RelationshipTo('ProfileDataReaction', 'HAS_LIKE')
    comment= RelationshipTo('ProfileDataComment', 'HAS_COMMENT')
    what = StringProperty(required=True) 
    description = StringProperty(required=True)
    from_source = StringProperty(required=True) 
    created_on = DateTimeProperty(default_now=True)
    from_date=DateTimeProperty()
    to_date=DateTimeProperty()
    is_deleted = BooleanProperty(default=False)
    file_id=ArrayProperty(base_property=StringProperty())
    
    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'auth_manager'

class Education(DjangoNode,StructuredNode):
    uid = UniqueIdProperty()
    profile = RelationshipTo('Profile', 'HAS_PROFILE')
    like= RelationshipTo('ProfileDataReaction', 'HAS_LIKE')
    comment= RelationshipTo('ProfileDataComment', 'HAS_COMMENT')
    what = StringProperty(required=True) 
    field_of_study = StringProperty(required=True) 
    from_source = StringProperty(required=True) 
    from_date=DateTimeProperty()
    to_date=DateTimeProperty()
    created_on = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)
    file_id=ArrayProperty(base_property=StringProperty())

    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'auth_manager'

class Experience(DjangoNode,StructuredNode):
    uid = UniqueIdProperty()
    profile = RelationshipTo('Profile', 'HAS_PROFILE')
    like= RelationshipTo('ProfileDataReaction', 'HAS_LIKE')
    comment= RelationshipTo('ProfileDataComment', 'HAS_COMMENT')
    what =StringProperty(required=True)
    from_source = StringProperty(required=True)
    from_date=DateTimeProperty()
    to_date=DateTimeProperty()
    description =  StringProperty(default_now=True)
    created_on = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)
    file_id=ArrayProperty(base_property=StringProperty())

    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'auth_manager'

class Skill(DjangoNode,StructuredNode):
    uid = UniqueIdProperty()
    profile = RelationshipTo('Profile', 'HAS_PROFILE')
    like= RelationshipTo('ProfileDataReaction', 'HAS_LIKE')
    comment= RelationshipTo('ProfileDataComment', 'HAS_COMMENT')
    what = StringProperty(required=True)
    from_source = StringProperty(required=True) 
    from_date=DateTimeProperty()
    to_date=DateTimeProperty()
    created_on = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)
    file_id=ArrayProperty(base_property=StringProperty())

    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'auth_manager'

class AchievementReactionManager(models.Model):
    achievement_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    achievement_vibe = models.JSONField(default=list)  # List to hold multiple reactions

    class Meta:
        verbose_name = 'Achievement Reaction Manager'
        verbose_name_plural = 'Achievement Reaction Managers'

    def __str__(self):
        return f"AchievementReactionManager for achievement {self.achievement_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the AchievementVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.achievement_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.achievement_vibe:
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
        return self.achievement_vibe

class EducationReactionManager(models.Model):
    education_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    education_vibe = models.JSONField(default=list)  # List to hold multiple reactions

    class Meta:
        verbose_name = 'Education Reaction Manager'
        verbose_name_plural = 'Education Reaction Managers'

    def __str__(self):
        return f"EducationReactionManager for education {self.education_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the EducationVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.education_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.education_vibe:
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
        return self.education_vibe

class SkillReactionManager(models.Model):
    skill_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    skill_vibe = models.JSONField(default=list)  # List to hold multiple reactions

    class Meta:
        verbose_name = 'Skill Reaction Manager'
        verbose_name_plural = 'Skill Reaction Managers'

    def __str__(self):
        return f"SkillReactionManager for skill {self.skill_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the SkillVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.skill_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.skill_vibe:
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
        return self.skill_vibe

class ExperienceReactionManager(models.Model):
    experience_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    experience_vibe = models.JSONField(default=list)  # List to hold multiple reactions

    class Meta:
        verbose_name = 'Experience Reaction Manager'
        verbose_name_plural = 'Experience Reaction Managers'

    def __str__(self):
        return f"ExperienceReactionManager for experience {self.experience_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the ExperienceVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.experience_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.experience_vibe:
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
        return self.experience_vibe


class ProfileDataReaction(DjangoNode,StructuredNode):
    uid=UniqueIdProperty()
    achievement=RelationshipTo('Achievement','HAS_ACHIEVEMENT')
    education=RelationshipTo('Education','HAS_EDUCATION')
    skill=RelationshipTo('Skill','HAS_SKILL')
    experience=RelationshipTo('Experience','HAS_EXPERIENCE')
    user = RelationshipTo('Users','HAS_USER')
    reaction = StringProperty(default='Like')
    vibe = FloatProperty(default=2.0)
    timestamp = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)

    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        return self.reaction
    

class ProfileDataComment(DjangoNode,StructuredNode):
    uid=UniqueIdProperty()
    achievement=RelationshipTo('Achievement','HAS_ACHIEVEMENT')
    education=RelationshipTo('Education','HAS_EDUCATION')
    skill=RelationshipTo('Skill','HAS_SKILL')
    experience=RelationshipTo('Experience','HAS_EXPERIENCE')
    user = RelationshipTo('Users','HAS_USER')
    content = StringProperty()
    timestamp = DateTimeProperty(default_now=True)
    is_deleted = BooleanProperty(default=False)

    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        return self.reaction
