import graphene
from graphene_django import DjangoObjectType
from user_activity.models import (
    UserActivity,
    ContentInteraction,
    ProfileActivity,
    MediaInteraction,
    SocialInteraction,
    SessionActivity,
    ActivityAggregation
)
from graphene import ObjectType, String, Int, Float, List, DateTime, Boolean, JSONString


class UserActivityType(DjangoObjectType):
    class Meta:
        model = UserActivity
        fields = '__all__'


class ContentInteractionType(DjangoObjectType):
    class Meta:
        model = ContentInteraction
        fields = '__all__'


class ProfileActivityType(DjangoObjectType):
    class Meta:
        model = ProfileActivity
        fields = '__all__'


class MediaInteractionType(DjangoObjectType):
    class Meta:
        model = MediaInteraction
        fields = '__all__'


class SocialInteractionType(DjangoObjectType):
    class Meta:
        model = SocialInteraction
        fields = '__all__'


class SessionActivityType(DjangoObjectType):
    class Meta:
        model = SessionActivity
        fields = '__all__'


class ActivityAggregationType(DjangoObjectType):
    class Meta:
        model = ActivityAggregation
        fields = '__all__'


# Custom types for analytics
class UserActivitySummaryType(ObjectType):
    activity_counts = JSONString()
    engagement_score = Float()
    time_range = String()
    start_date = String()
    end_date = String()
    total_activities = Int()
    most_active_day = String()
    average_daily_activities = Float()


class EngagementTrendsType(ObjectType):
    dates = List(String)
    engagement_scores = List(Float)
    activity_counts = List(Int)
    period = String()
    trend_direction = String()  # 'increasing', 'decreasing', 'stable'
    peak_engagement_date = String()
    lowest_engagement_date = String()


class ContentEngagementType(ObjectType):
    content_type = String()
    content_id = String()
    total_views = Int()
    total_likes = Int()
    total_comments = Int()
    total_shares = Int()
    engagement_rate = Float()
    average_time_spent = Float()
    unique_viewers = Int()


class UserBehaviorInsightsType(ObjectType):
    most_active_hours = List(Int)
    preferred_content_types = List(String)
    engagement_patterns = JSONString()
    social_activity_score = Float()
    content_creation_frequency = String()
    average_session_duration = Float()
    device_preferences = JSONString()


class ActivityHeatmapType(ObjectType):
    hour = Int()
    day_of_week = Int()
    activity_count = Int()
    engagement_score = Float()


# Input types
class TimeRangeInput(graphene.InputObjectType):
    start_date = DateTime()
    end_date = DateTime()
    period = String()  # 'day', 'week', 'month', 'year'


class SessionDataInput(graphene.InputObjectType):
    session_id = String(required=True)
    start_time = DateTime()
    end_time = DateTime()
    pages_visited = Int()
    actions_performed = Int()
    device_info = JSONString()
    location_data = JSONString()


class ContentTypeEnum(graphene.Enum):
    POST = 'post'
    STORY = 'story'
    COMMENT = 'comment'
    COMMUNITY_POST = 'community_post'
    REVIEW = 'review'


class InteractionTypeEnum(graphene.Enum):
    VIEW = 'view'
    LIKE = 'like'
    UNLIKE = 'unlike'
    COMMENT = 'comment'
    SHARE = 'share'
    SAVE = 'save'
    UNSAVE = 'unsave'
    PIN = 'pin'
    UNPIN = 'unpin'
    REPORT = 'report'
    HIDE = 'hide'
    REACT = 'react'
    UNREACT = 'unreact'
    RATE = 'rate'
    SCROLL_DEPTH = 'scroll_depth'
    TIME_SPENT = 'time_spent'


class ActivityTypeEnum(graphene.Enum):
    LOGIN = 'login'
    LOGOUT = 'logout'
    PROFILE_UPDATE = 'profile_update'
    PASSWORD_CHANGE = 'password_change'
    EMAIL_CHANGE = 'email_change'
    ACCOUNT_DEACTIVATION = 'account_deactivation'
    ACCOUNT_REACTIVATION = 'account_reactivation'
    SETTINGS_UPDATE = 'settings_update'
    PRIVACY_UPDATE = 'privacy_update'
    NOTIFICATION_UPDATE = 'notification_update'
    SEARCH = 'search'
    NAVIGATION = 'navigation'
    ERROR = 'error'
    FEATURE_USAGE = 'feature_usage'


class MediaTypeEnum(graphene.Enum):
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    GIF = 'gif'
    THUMBNAIL = 'thumbnail'


class SocialInteractionTypeEnum(graphene.Enum):
    CONNECTION_REQUEST = 'connection_request'
    CONNECTION_ACCEPT = 'connection_accept'
    CONNECTION_DECLINE = 'connection_decline'
    CONNECTION_REMOVE = 'connection_remove'
    MESSAGE_SEND = 'message_send'
    MESSAGE_READ = 'message_read'
    GROUP_JOIN = 'group_join'
    GROUP_LEAVE = 'group_leave'
    GROUP_INVITE = 'group_invite'
    MENTION = 'mention'
    TAG = 'tag'
    RECOMMENDATION_VIEW = 'recommendation_view'
    RECOMMENDATION_DISMISS = 'recommendation_dismiss'


# Analytics aggregation types
class DailyActivityStatsType(ObjectType):
    date = String()
    total_activities = Int()
    unique_users = Int()
    engagement_score = Float()
    top_activities = List(String)
    peak_hour = Int()


class WeeklyActivityStatsType(ObjectType):
    week_start = String()
    week_end = String()
    total_activities = Int()
    daily_averages = List(Float)
    growth_rate = Float()
    most_active_day = String()


class MonthlyActivityStatsType(ObjectType):
    month = String()
    year = Int()
    total_activities = Int()
    weekly_averages = List(Float)
    growth_rate = Float()
    seasonal_trends = JSONString()


class PopularContentType(ObjectType):
    content_type = String()
    content_id = String()
    title = String()
    total_interactions = Int()
    unique_users = Int()
    engagement_rate = Float()
    trending_score = Float()


class UserSegmentType(ObjectType):
    segment_name = String()
    user_count = Int()
    characteristics = JSONString()
    engagement_metrics = JSONString()
    recommended_actions = List(String)