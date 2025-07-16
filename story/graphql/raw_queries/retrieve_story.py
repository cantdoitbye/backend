get_inner_story = """

    MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:Connection {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:Circle {circle_type: "Inner"})
    MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
    Match(secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
    MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
    WHERE secondaryUser.uid <> u1.uid AND "Inner" IN story.privacy 
    WITH secondaryUser, profile,story
    ORDER BY story.created_at DESC
    WITH secondaryUser,profile, COLLECT(story)[0] AS latest_story
    RETURN secondaryUser,profile,latest_story;

"""

get_outer_story = """

    MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:Connection {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:Circle {circle_type: "Outer"})
    MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
    Match(secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
    MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
    WHERE secondaryUser.uid <> u1.uid AND "Outer" IN story.privacy 
    WITH secondaryUser, profile,story
    ORDER BY story.created_at DESC
    WITH secondaryUser,profile, COLLECT(story)[0] AS latest_story
    RETURN secondaryUser,profile,latest_story;

"""

get_universe_story = """

    MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:Connection {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:Circle {circle_type: "Universal"})
    MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
    Match(secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
    MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
    WHERE secondaryUser.uid <> u1.uid AND "Universal" IN story.privacy
    WITH secondaryUser, profile,story
    ORDER BY story.created_at DESC
    WITH secondaryUser,profile, COLLECT(story)[0] AS latest_story
    RETURN secondaryUser,profile,latest_story;

"""

get_user_story = """

    MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:Connection {connection_status: "Accepted"})-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users {uid: $secondaryuseruid})
    MATCH (c1)-[:HAS_CIRCLE]->(circle:Circle)
    MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
    WHERE circle.circle_type IN story.privacy
    WITH secondaryUser, story
    ORDER BY story.created_at DESC
    RETURN secondaryUser, story;

"""

get_user_storyV2 = """

    MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:ConnectionV2 {connection_status: "Accepted"})-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users {uid: $secondaryuseruid})
    MATCH (c1)-[:HAS_CIRCLE]->(circle:CircleV2)
    MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
    WITH secondaryUser, story
    ORDER BY story.created_at DESC
    RETURN secondaryUser, story;

"""

get_inner_storyV2="""

    MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:ConnectionV2 {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:CircleV2)
    WITH u1, c1, circle, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
    WHERE $log_in_user_uid IN keys(user_relations_map) 
    AND user_relations_map[$log_in_user_uid].circle_type = "Inner"

    MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
    MATCH (secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
    MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
    WITH u1, secondaryUser, profile, story, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
    WHERE secondaryUser.uid <> u1.uid 
    AND user_relations_map[secondaryUser.uid].circle_type IN story.privacy

    WITH secondaryUser, profile, story
    ORDER BY story.created_at DESC
    WITH secondaryUser, profile, COLLECT(story)[0] AS latest_story
    RETURN secondaryUser, profile, latest_story;


"""



# get_inner_storyV2 = """

#     MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:ConnectionV2 {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:CircleV2)
#     WITH u1, c1,circle, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
#     WHERE $log_in_user_uid IN keys(user_relations_map) 
#         AND user_relations_map[$log_in_user_uid].circle_type = "Inner"

#     MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
#     MATCH (secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
#     MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
#     WHERE secondaryUser.uid <> u1.uid AND "Inner" IN story.privacy 

#     WITH secondaryUser, profile, story
#     ORDER BY story.created_at DESC
#     WITH secondaryUser, profile, COLLECT(story)[0] AS latest_story
#     RETURN secondaryUser, profile, latest_story;


# """

# get_outer_storyV2 = """

#     MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:ConnectionV2 {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:CircleV2)
#     WITH u1,c1,circle, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
#     WHERE $log_in_user_uid IN keys(user_relations_map) 
#         AND user_relations_map[$log_in_user_uid].circle_type = "Outer"
#     MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
#     Match(secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
#     MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
#     WHERE secondaryUser.uid <> u1.uid AND "Outer" IN story.privacy 
#     WITH secondaryUser, profile,story
#     ORDER BY story.created_at DESC
#     WITH secondaryUser,profile, COLLECT(story)[0] AS latest_story
#     RETURN secondaryUser,profile,latest_story;

# """


get_outer_storyV2="""

    MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:ConnectionV2 {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:CircleV2)
    WITH u1, c1, circle, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
    WHERE $log_in_user_uid IN keys(user_relations_map) 
    AND user_relations_map[$log_in_user_uid].circle_type = "Outer"

    MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
    MATCH (secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
    MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
    WITH u1, secondaryUser, profile, story, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
    WHERE secondaryUser.uid <> u1.uid 
    AND user_relations_map[secondaryUser.uid].circle_type IN story.privacy

    WITH secondaryUser, profile, story
    ORDER BY story.created_at DESC
    WITH secondaryUser, profile, COLLECT(story)[0] AS latest_story
    RETURN secondaryUser, profile, latest_story;


"""



# get_universe_storyV2 = """

#     MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:ConnectionV2 {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:CircleV2)
#     WITH u1,c1,circle, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
#     WHERE $log_in_user_uid IN keys(user_relations_map) 
#         AND user_relations_map[$log_in_user_uid].circle_type = "Universe"
#     MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
#     Match(secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
#     MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
#     WHERE secondaryUser.uid <> u1.uid AND "Universe" IN story.privacy 
#     WITH secondaryUser, profile,story
#     ORDER BY story.created_at DESC
#     WITH secondaryUser,profile, COLLECT(story)[0] AS latest_story
#     RETURN secondaryUser,profile,latest_story;

# """

get_universe_storyV2="""

    MATCH (u1:Users {uid: $log_in_user_uid})-[:HAS_CONNECTION]->(c1:ConnectionV2 {connection_status: "Accepted"})-[:HAS_CIRCLE]->(circle:CircleV2)
    WITH u1, c1, circle, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
    WHERE $log_in_user_uid IN keys(user_relations_map) 
    AND user_relations_map[$log_in_user_uid].circle_type = "Universe"

    MATCH (c1)-[:HAS_RECIEVED_CONNECTION|HAS_SEND_CONNECTION]->(secondaryUser:Users)
    MATCH (secondaryUser)-[:HAS_PROFILE]->(profile:Profile)
    MATCH (secondaryUser)-[:HAS_STORY]->(story:Story)
    WITH u1, secondaryUser, profile, story, apoc.convert.fromJsonMap(circle.user_relations) AS user_relations_map
    WHERE secondaryUser.uid <> u1.uid 
    AND user_relations_map[secondaryUser.uid].circle_type IN story.privacy

    WITH secondaryUser, profile, story
    ORDER BY story.created_at DESC
    WITH secondaryUser, profile, COLLECT(story)[0] AS latest_story
    RETURN secondaryUser, profile, latest_story;


"""