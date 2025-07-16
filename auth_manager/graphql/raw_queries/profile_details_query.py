

# while collectind data from cypher query always use Distinct keyword otherwise you end up with duplicate data
get_profile_details_query = """
MATCH (profile:Profile {uid: $log_in_user_profile_uid})
OPTIONAL MATCH (profile)-[:HAS_USER]->(user:Users)
OPTIONAL MATCH (profile)-[:HAS_ONBOARDING_STATUS]->(onboardingStatus:OnboardingStatus)
OPTIONAL MATCH (profile)-[:HAS_SCORE]->(score:Score)
OPTIONAL MATCH (profile)-[:HAS_INTEREST]->(interest:Interest{is_deleted:false})
OPTIONAL MATCH (profile)-[:HAS_ACHIEVEMENT]->(achievement:Achievement{is_deleted:false})
OPTIONAL MATCH (profile)-[:HAS_EDUCATION]->(education:Education{is_deleted:false})
OPTIONAL MATCH (profile)-[:HAS_SKILL]->(skill:Skill{is_deleted:false})
OPTIONAL MATCH (profile)-[:HAS_EXPERIENCE]->(experience:Experience{is_deleted:false})
OPTIONAL MATCH (user)-[:HAS_POST]->(posts:Post{is_deleted:false})
OPTIONAL MATCH (user)-[:HAS_COMMUNITY]->(communities:Community)
OPTIONAL MATCH (user)-[:HAS_CONNECTION]->(connections:Connection{connection_status:'Accepted'})
WITH profile, user, onboardingStatus, score,
     COLLECT(DISTINCT interest) AS interests,
     COLLECT(DISTINCT achievement) AS achievements,
     COLLECT(DISTINCT education) AS educations,
     COLLECT(DISTINCT skill) AS skills,
     COLLECT(DISTINCT experience) AS experiences,
     COUNT(DISTINCT posts) AS post_count,
     COUNT(DISTINCT communities) AS community_count,
     COUNT(DISTINCT connections) AS connection_count
RETURN
    profile,
    user,
    onboardingStatus,
    score,
    interests,
    achievements,
    educations,
    skills,
    experiences,
    post_count,
    community_count,
    connection_count
"""

# Query to get profile data comments
def get_profile_data_comments_query(relationship, category):
    return f"""
    MATCH (comment:ProfileDataComment)-[:{relationship}]->({category} {{uid: $uid}})
    WHERE NOT comment.is_deleted
    MATCH (comment)-[:HAS_USER]->(user:Users)
    MATCH (user)-[:HAS_PROFILE]->(profile:Profile)
    RETURN comment, user, profile
    LIMIT 10
    """

