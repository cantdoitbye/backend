
recommended_users_query = """
    MATCH (u:Users {uid: $uid})-[:HAS_CONNECTION]->(c:Connection {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(u2:Users)
    MATCH (u2)-[:HAS_PROFILE]->(p2:Profile)-[:HAS_ONBOARDING_STATUS]->(o2:OnboardingStatus {email_verified: true})
    RETURN u2,p2
    ORDER BY u2.created_at DESC;

"""

recommended_connected_users_query = """
    MATCH (u:Users {uid: $uid})-[:HAS_CONNECTION]->(c:Connection {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(u2:Users)
    MATCH (u2)-[:HAS_PROFILE]->(p2:Profile)
    RETURN u2,p2
    LIMIT 20;

"""

recommended_verified_users_query = """
    MATCH (u:Users)
    MATCH (u)-[:HAS_PROFILE]->(p:Profile)-[:HAS_ONBOARDING_STATUS]->(o:OnboardingStatus {email_verified: true})
    RETURN u,p
    LIMIT 20;


"""

recommended_recent_users_query = """
    MATCH (u:Users)
    MATCH (u)-[:HAS_PROFILE]->(p:Profile)-[:HAS_ONBOARDING_STATUS]->(o:OnboardingStatus {email_verified: true})
    RETURN u,p
    ORDER BY u.created_at DESC
    LIMIT 20;

"""


get_top_vibes_hobbies_query="""
                MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile) 
                RETURN u , p
                ORDER BY rand() 
                LIMIT 20
"""

get_top_vibes_trending_topics_query="""
                MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile) 
                RETURN u , p
                ORDER BY rand() 
                LIMIT 20
"""

get_top_vibes_country_query="""
                MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile) 
                RETURN u , p
                ORDER BY rand() 
                LIMIT 20
"""

get_top_vibes_organisation_query="""
                MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile) 
                RETURN u , p
                ORDER BY rand() 
                LIMIT 20
"""

get_top_vibes_sport_query="""
                MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile) 
                RETURN u , p
                ORDER BY rand() 
                LIMIT 20
"""




get_mutual_connected_user_query="""

    MATCH (u1:Users {uid: $login_user_uid})-[:HAS_CONNECTION]-(c1:Connection)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(u3:Users)
    MATCH (u2:Users {uid: $secondary_user_uid})-[:HAS_CONNECTION]-(c2:Connection)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(u3)
    MATCH (u3)-[:HAS_PROFILE]->(p:Profile)
    Where u1 <> u3 AND u2<>u3
    RETURN DISTINCT u3,p


"""

# get_common_interest_user_query="""

    
#     MATCH (u1:Users {uid: $secondary_user_uid})-[:HAS_CONNECTION]-(c1:Connection)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(otherUser:Users)

#     MATCH (currentUser:Users {uid: $login_user_uid })-[:HAS_PROFILE]->(currentProfile:Profile)-[:HAS_INTEREST]->(currentInterest:Interest)
#     MATCH (otherUser)-[:HAS_PROFILE]->(otherProfile:Profile)-[:HAS_INTEREST]->(otherInterest:Interest)
#     WHERE any(name IN currentInterest.names WHERE toLower(name) IN [item IN otherInterest.names | toLower(item)]) AND currentUser <> otherUser AND u1 <> otherUser
#     RETURN DISTINCT otherUser,otherProfile;


# """


get_common_interest_user_query = """
    // Get mutual connected users
    MATCH (u1:Users {uid: $secondary_user_uid})-[:HAS_CONNECTION]-(c1:Connection)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(mutualUser:Users)
    MATCH (u2:Users {uid: $login_user_uid})-[:HAS_CONNECTION]-(c2:Connection)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(mutualUser)

    WITH collect(mutualUser.uid) AS mutualUserIds

    // Get users with common interests, excluding mutual connections
    MATCH (u1:Users {uid: $secondary_user_uid})-[:HAS_CONNECTION]-(c1:Connection)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(otherUser:Users)
    MATCH (currentUser:Users {uid: $login_user_uid})-[:HAS_PROFILE]->(currentProfile:Profile)-[:HAS_INTEREST]->(currentInterest:Interest)
    MATCH (otherUser)-[:HAS_PROFILE]->(otherProfile:Profile)-[:HAS_INTEREST]->(otherInterest:Interest)
    WHERE any(name IN currentInterest.names WHERE toLower(name) IN [item IN otherInterest.names | toLower(item)])
      AND currentUser <> otherUser
      AND NOT otherUser.uid IN mutualUserIds

    RETURN DISTINCT otherUser, otherProfile;
"""


get_raw_data_from_user="""

    // Subquery 1: Get users in Inner, Outer, Universe circles
MATCH (u1:Users {uid: $uid})-[:HAS_CONNECTION]->(c1:Connection {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:Circle)
MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
WHERE secondaryUser.uid <> u1.uid
WITH circle.circle_type AS circleType, secondaryUser.uid AS uid, u1
WITH 
    COLLECT(CASE WHEN circleType = "Inner" THEN uid ELSE NULL END) AS InnerCircle,
    COLLECT(CASE WHEN circleType = "Outer" THEN uid ELSE NULL END) AS OuterCircle,
    COLLECT(CASE WHEN circleType = "Universal" THEN uid ELSE NULL END) AS UniverseCircle,
    u1

// Subquery 2: Get liked and commented posts
MATCH (likedPost:Post)-[:HAS_LIKE]->(Like:Like)-[:HAS_USER]->(u1)
MATCH (commentedPost:Post)-[:HAS_COMMENT]->(comment:Comment)-[:HAS_USER]->(u1)

// Combine liked and commented posts
WITH 
    InnerCircle, 
    OuterCircle, 
    UniverseCircle,
    u1,
    COLLECT(DISTINCT likedPost.uid) + COLLECT(DISTINCT commentedPost.uid) AS RecentPosts

// Match u1's profile
MATCH (u1)-[:HAS_PROFILE]->(profile:Profile)

// Sort the RecentPosts by uid (ascending or descending)
WITH InnerCircle, OuterCircle, UniverseCircle, RecentPosts, u1, profile
ORDER BY RecentPosts ASC // Change to DESC for descending order

// Return the final result
RETURN 
    u1 AS user,  // Returning u1 in the results
    profile,     // Returning u1's profile data
    [user IN InnerCircle WHERE user IS NOT NULL] AS InnerCircle,
    [user IN OuterCircle WHERE user IS NOT NULL] AS OuterCircle,
    [user IN UniverseCircle WHERE user IS NOT NULL] AS UniverseCircle,
    RecentPosts;



"""

get_raw_data_from_content="""
       MATCH (post:Post)-[:HAS_USER]->(author:Users)
        WHERE post.uid IN $postUids
        OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
        OPTIONAL MATCH (post)-[:HAS_LIKE]->(like:Like)
        RETURN 
            post,
            author AS post_author,
            COUNT(DISTINCT like) AS like_count,
            COUNT(DISTINCT comment) AS comment_count;



"""

get_mutual_connected_user_queryV2="""

    MATCH (u1:Users {uid: $login_user_uid})-[:HAS_CONNECTION]-(c1:ConnectionV2)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(u3:Users)
    MATCH (u2:Users {uid: $secondary_user_uid})-[:HAS_CONNECTION]-(c2:ConnectionV2)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(u3)
    MATCH (u3)-[:HAS_PROFILE]->(p:Profile)
    Where u1 <> u3 AND u2<>u3
    RETURN DISTINCT u3,p


"""

get_common_interest_user_queryV2 = """
    // Get mutual connected users
    MATCH (u1:Users {uid: $secondary_user_uid})-[:HAS_CONNECTION]-(c1:ConnectionV2)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(mutualUser:Users)
    MATCH (u2:Users {uid: $login_user_uid})-[:HAS_CONNECTION]-(c2:ConnectionV2)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(mutualUser)

    WITH collect(mutualUser.uid) AS mutualUserIds

    // Get users with common interests, excluding mutual connections
    MATCH (u1:Users {uid: $secondary_user_uid})-[:HAS_CONNECTION]-(c1:ConnectionV2)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(otherUser:Users)
    MATCH (currentUser:Users {uid: $login_user_uid})-[:HAS_PROFILE]->(currentProfile:Profile)-[:HAS_INTEREST]->(currentInterest:Interest)
    MATCH (otherUser)-[:HAS_PROFILE]->(otherProfile:Profile)-[:HAS_INTEREST]->(otherInterest:Interest)
    WHERE any(name IN currentInterest.names WHERE toLower(name) IN [item IN otherInterest.names | toLower(item)])
      AND currentUser <> otherUser
      AND NOT otherUser.uid IN mutualUserIds

    RETURN DISTINCT otherUser, otherProfile;
"""

get_connection_details_query="""

        MATCH (u1:Users {uid: $login_user_uid})-[:HAS_CONNECTION]-(c1:ConnectionV2)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]-(u2:Users{uid: $secondary_user_uid})
        Return c1;


"""