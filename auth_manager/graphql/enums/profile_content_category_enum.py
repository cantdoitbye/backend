# auth_manager/graphql/enums/profile_content_category_enum.py
import graphene


class ProfileContentCategoryEnum(graphene.Enum):
    """
    Enum for profile content categories that can receive vibes.
    
    This enum defines the different types of profile content that users can
    send vibe reactions to. Each category corresponds to a specific profile
    data model in the system.
    
    Values:
        ACHIEVEMENT: User achievements and accomplishments
        EDUCATION: Educational background and qualifications
        SKILL: User skills and competencies
        EXPERIENCE: Professional work experience
    
    Usage:
        Used in SendVibeToProfileContent mutation to specify the content type
        being reacted to. This ensures type safety and validation of content
        categories in GraphQL queries.
    """
    ACHIEVEMENT = 'achievement'
    EDUCATION = 'education'
    SKILL = 'skill'
    EXPERIENCE = 'experience'

