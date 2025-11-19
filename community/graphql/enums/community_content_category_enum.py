# community/graphql/enums/community_content_category_enum.py
import graphene


class CommunityContentCategoryEnum(graphene.Enum):
    """
    Enum for community content categories that can receive vibes.
    
    This enum defines the different types of community content that users can
    send vibe reactions to. Each category corresponds to a specific community
    content model in the system.
    
    Values:
        ACHIEVEMENT: Community achievements and milestones
        ACTIVITY: Community activities and events
        GOAL: Community goals and objectives
        AFFILIATION: Community affiliations and partnerships
    
    Usage:
        Used in SendVibeToCommunityContent mutation to specify the content type
        being reacted to. This ensures type safety and validation of content
        categories in GraphQL queries.
    """
    ACHIEVEMENT = 'community_achievement'
    ACTIVITY = 'community_activity'
    GOAL = 'community_goal'
    AFFILIATION = 'community_affiliation'

