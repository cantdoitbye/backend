
recommended_post_from_connected_user_query = """
        MATCH (u:Users {uid: $uid})-[:HAS_CONNECTION]->(c:Connection {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(p_user:Users)
        MATCH (p_user)-[:HAS_POST]->(post:Post{is_deleted: false})
        RETURN post
        ORDER BY post.created_at DESC LIMIT 20;

"""

recommended_post_highest_engagement_score_query = """
        MATCH (post:Post {is_deleted: false})
        OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
        OPTIONAL MATCH (post)-[:HAS_LIKE]->(like:Like)
        WITH post, 
            COUNT(comment) AS comment_count, 
            COUNT(like) AS like_count
        WITH post,
            comment_count + like_count AS engagement_score
        RETURN post, engagement_score
        ORDER BY engagement_score DESC LIMIT 20;

"""

recommended_recent_post_query = """
        MATCH (post:Post {is_deleted: false})
        RETURN post
        ORDER BY post.created_at DESC LIMIT 20;

"""

# post_feed_query="""
#         CALL {
#         // Subquery 1: Fetch recent posts from other users except the logged-in user
#         MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
#         WHERE  user.user_id <> $log_in_user_node_id
#         AND NOT EXISTS {
#         MATCH (log_in_user:Users {user_id:$log_in_user_node_id})-[:HAS_CONNECTION]->(:Connection)-[:HAS_CIRCLE]->(:Circle),
#               (user:Users)-[:HAS_CONNECTION]->(:Connection {connection_status: "Accepted"})
#         }
#         OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
#         OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
#         OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
#         WITH post, user, profile, collect(vibe) AS reactions, 
#              COUNT(DISTINCT share) AS share_count,
#              COUNT(DISTINCT comment) AS comment_count,
#              COUNT(DISTINCT vibe) AS like_count
#         WITH post, user, profile, reactions, share_count, comment_count, like_count,
#              // Calculate engagement score for overall_score
#              (comment_count + like_count + share_count) AS engagement_score
#         WITH post, user, profile, reactions, share_count, comment_count, like_count, engagement_score,
#              // Calculate overall_score (base vibe_score + engagement bonus, capped at 5.0)
#              CASE 
#                 WHEN post.vibe_score IS NOT NULL 
#                 THEN round(post.vibe_score + (engagement_score * 0.1), 1)
#                 ELSE 2.0 
#              END AS calculated_overall_score
#         RETURN post, user, profile, reactions, NULL AS connection, NULL AS circle, 
#                post.created_at AS created_at, share_count, calculated_overall_score
#         ORDER BY post.created_at DESC
#         LIMIT 60
        
#         UNION ALL
#         // Subquery 2: Fetch posts from connected users
#         MATCH (log_in_user:Users {user_id: $log_in_user_node_id})-[:HAS_CONNECTION]->(connection:Connection)-[:HAS_CIRCLE]->(circle:Circle),
#                 (user:Users)-[:HAS_CONNECTION]->(connection{connection_status:"Accepted"}),
#                 (post:Post {is_deleted: false})<-[:HAS_POST]-(user)-[:HAS_PROFILE]->(profile:Profile)
        
#         OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
#         OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
#         OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
#         WITH post, user, profile, collect(vibe) AS reactions, connection, circle,
#              COUNT(DISTINCT share) AS share_count,
#              COUNT(DISTINCT comment) AS comment_count,
#              COUNT(DISTINCT vibe) AS like_count
#         WITH post, user, profile, reactions, connection, circle, share_count, comment_count, like_count,
#              (comment_count + like_count + share_count) AS engagement_score
#         WITH post, user, profile, reactions, connection, circle, share_count, comment_count, like_count, engagement_score,
#              CASE 
#                 WHEN post.vibe_score IS NOT NULL 
#                 THEN round(post.vibe_score + (engagement_score * 0.1), 1)
#                 ELSE 2.0 
#              END AS calculated_overall_score
#         RETURN post, user, profile, reactions, connection, circle, 
#                post.created_at AS created_at, share_count, calculated_overall_score
#         LIMIT 25

#         UNION ALL
#         // Subquery 3: Fetch Community Post
#         MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_COMMUNITY]->(community:Community)
#         OPTIONAL MATCH (community_post)-[:HAS_POST_SHARE]->(share:PostShare)
#         OPTIONAL MATCH (community_post)-[:HAS_COMMENT]->(comment:Comment)
#         OPTIONAL MATCH (community_post)-[:HAS_LIKE]->(like:Like)
#         WITH community_post, community, 
#              COUNT(DISTINCT share) AS share_count,
#              COUNT(DISTINCT comment) AS comment_count,
#              COUNT(DISTINCT like) AS like_count
#         WITH community_post, community, share_count, comment_count, like_count,
#              (comment_count + like_count + share_count) AS engagement_score
#         WITH community_post, community, share_count, comment_count, like_count, engagement_score,
#              CASE 
#                 WHEN community_post.vibe_score IS NOT NULL 
#                 THEN round(community_post.vibe_score + (engagement_score * 0.1), 1)
#                 ELSE 2.0 
#              END AS calculated_overall_score
#         RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, 
#                NULL AS connection, NULL AS circle, community_post.created_at AS created_at, 
#                share_count, calculated_overall_score
#         LIMIT 5

#         UNION ALL
#         // Subquery 4: Fetch SubCommunity Post
#         MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(community:SubCommunity)
#         OPTIONAL MATCH (community_post)-[:HAS_POST_SHARE]->(share:PostShare)
#         OPTIONAL MATCH (community_post)-[:HAS_COMMENT]->(comment:Comment)
#         OPTIONAL MATCH (community_post)-[:HAS_LIKE]->(like:Like)
#         WITH community_post, community,
#              COUNT(DISTINCT share) AS share_count,
#              COUNT(DISTINCT comment) AS comment_count,
#              COUNT(DISTINCT like) AS like_count
#         WITH community_post, community, share_count, comment_count, like_count,
#              (comment_count + like_count + share_count) AS engagement_score
#         WITH community_post, community, share_count, comment_count, like_count, engagement_score,
#              CASE 
#                 WHEN community_post.vibe_score IS NOT NULL 
#                 THEN round(community_post.vibe_score + (engagement_score * 0.1), 1)
#                 ELSE 2.0 
#              END AS calculated_overall_score
#         RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, 
#                NULL AS connection, NULL AS circle, community_post.created_at AS created_at, 
#                share_count, calculated_overall_score
#         LIMIT 5

#         }
#         RETURN post, user, profile, reactions, connection, circle, share_count, calculated_overall_score
#         ORDER BY created_at DESC
#         LIMIT 60;

# """
# post/graphql/raw_queries/post_queries.py - FIXED VERSION

# post_feed_query="""
#         CALL {
#         // Subquery 1: Fetch recent posts from other users except the logged-in user
#         MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
#         WHERE  user.user_id <> $log_in_user_node_id
#         AND NOT EXISTS {
#         MATCH (log_in_user:Users {user_id:$log_in_user_node_id})-[:HAS_CONNECTION]->(:Connection)-[:HAS_CIRCLE]->(:Circle),
#               (user:Users)-[:HAS_CONNECTION]->(:Connection {connection_status: "Accepted"})
#         }
#         OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
#         OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
#         OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
#         WITH post, user, profile, collect(vibe) AS reactions, 
#              COUNT(DISTINCT share) AS share_count,
#              COUNT(DISTINCT comment) AS comment_count,
#              COUNT(DISTINCT vibe) AS like_count
#         // Calculate engagement_score and calculated_overall_score in same WITH clause
#         WITH post, user, profile, reactions, share_count, comment_count, like_count,
#              (comment_count + like_count + share_count) AS engagement_score
#         WITH post, user, profile, reactions, share_count, comment_count, like_count, engagement_score,
#              CASE 
#                 WHEN post.vibe_score IS NOT NULL 
#                 THEN round(post.vibe_score + (engagement_score * 0.1), 1)
#                 ELSE 2.0 
#              END AS calculated_overall_score
#         RETURN post, user, profile, reactions, NULL AS connection, NULL AS circle, 
#                post.created_at AS created_at, share_count, calculated_overall_score
#         ORDER BY post.created_at DESC
#         LIMIT 60
        
#         UNION ALL
#         // Subquery 2: Fetch posts from connected users
#         MATCH (log_in_user:Users {user_id: $log_in_user_node_id})-[:HAS_CONNECTION]->(connection:Connection)-[:HAS_CIRCLE]->(circle:Circle),
#                 (user:Users)-[:HAS_CONNECTION]->(connection{connection_status:"Accepted"}),
#                 (post:Post {is_deleted: false})<-[:HAS_POST]-(user)-[:HAS_PROFILE]->(profile:Profile)
        
#         OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
#         OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
#         OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
#         WITH post, user, profile, collect(vibe) AS reactions, connection, circle,
#              COUNT(DISTINCT share) AS share_count,
#              COUNT(DISTINCT comment) AS comment_count,
#              COUNT(DISTINCT vibe) AS like_count
#         // Calculate engagement_score and calculated_overall_score in same WITH clause
#         WITH post, user, profile, reactions, connection, circle, share_count, comment_count, like_count,
#              (comment_count + like_count + share_count) AS engagement_score
#         WITH post, user, profile, reactions, connection, circle, share_count, comment_count, like_count, engagement_score,
#              CASE 
#                 WHEN post.vibe_score IS NOT NULL 
#                 THEN round(post.vibe_score + (engagement_score * 0.1), 1)
#                 ELSE 2.0 
#              END AS calculated_overall_score
#      //    RETURN post, user, profile, reactions, connection, circle, 
#      //           post.created_at AS created_at, share_count, calculated_overall_score
#        RETURN post, user, profile, reactions, connection, 
#               {uid: circle.uid, circle_type: circle.circle_type, sub_relation: circle.sub_relation} AS circle, 
#        post.created_at AS created_at, share_count, calculated_overall_score
#        LIMIT 25

#         UNION ALL
#         // Subquery 3: Fetch Community Post
#         MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_COMMUNITY]->(community:Community)
#         OPTIONAL MATCH (community_post)-[:HAS_POST_SHARE]->(share:PostShare)
#         OPTIONAL MATCH (community_post)-[:HAS_COMMENT]->(comment:Comment)
#         OPTIONAL MATCH (community_post)-[:HAS_LIKE]->(like:Like)
#         WITH community_post, community, 
#              COUNT(DISTINCT share) AS share_count,
#              COUNT(DISTINCT comment) AS comment_count,
#              COUNT(DISTINCT like) AS like_count
#         // Calculate engagement_score and calculated_overall_score in same WITH clause
#         WITH community_post, community, share_count, comment_count, like_count,
#              (comment_count + like_count + share_count) AS engagement_score
#         WITH community_post, community, share_count, comment_count, like_count, engagement_score,
#              CASE 
#                 WHEN community_post.vibe_score IS NOT NULL 
#                 THEN round(community_post.vibe_score + (engagement_score * 0.1), 1)
#                 ELSE 2.0 
#              END AS calculated_overall_score
#         RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, 
#                NULL AS connection, NULL AS circle, community_post.created_at AS created_at, 
#                share_count, calculated_overall_score
#         LIMIT 5

#         UNION ALL
#         // Subquery 4: Fetch SubCommunity Post
#         MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(community:SubCommunity)
#         OPTIONAL MATCH (community_post)-[:HAS_POST_SHARE]->(share:PostShare)
#         OPTIONAL MATCH (community_post)-[:HAS_COMMENT]->(comment:Comment)
#         OPTIONAL MATCH (community_post)-[:HAS_LIKE]->(like:Like)
#         WITH community_post, community,
#              COUNT(DISTINCT share) AS share_count,
#              COUNT(DISTINCT comment) AS comment_count,
#              COUNT(DISTINCT like) AS like_count
#         // Calculate engagement_score and calculated_overall_score in same WITH clause
#         WITH community_post, community, share_count, comment_count, like_count,
#              (comment_count + like_count + share_count) AS engagement_score
#         WITH community_post, community, share_count, comment_count, like_count, engagement_score,
#              CASE 
#                 WHEN community_post.vibe_score IS NOT NULL 
#                 THEN round(community_post.vibe_score + (engagement_score * 0.1), 1)
#                 ELSE 2.0 
#              END AS calculated_overall_score
#         RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, 
#                NULL AS connection, NULL AS circle, community_post.created_at AS created_at, 
#                share_count, calculated_overall_score
#         LIMIT 5

#         }
#         RETURN post, user, profile, reactions, connection, circle, share_count, calculated_overall_score
#         ORDER BY created_at DESC
#         LIMIT 60;

# """
post_feed_query="""
        CALL {
        // Subquery 1: Fetch posts from connected users (PRIORITIZE THIS)
        MATCH (me:Users {user_id: $log_in_user_node_id})-[:HAS_CONNECTION]->(conn:Connection {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(friend:Users)-[:HAS_POST]->(post:Post {is_deleted: false}),
              (friend)-[:HAS_PROFILE]->(profile:Profile)
        OPTIONAL MATCH (conn)-[:HAS_CIRCLE]->(circle:Circle)

        OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
        OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
        OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
        WITH post, friend as user, profile, collect(vibe) AS reactions, conn, circle,
             COUNT(DISTINCT share) AS share_count,
             COUNT(DISTINCT comment) AS comment_count,
             COUNT(DISTINCT vibe) AS like_count
        WITH post, user, profile, reactions, conn, circle, share_count, comment_count, like_count,
             (comment_count + like_count + share_count) AS engagement_score
        WITH post, user, profile, reactions, conn, circle, share_count, comment_count, like_count, engagement_score,
             CASE 
                WHEN post.vibe_score IS NOT NULL 
                THEN round(post.vibe_score + (engagement_score * 0.1), 1)
                ELSE 2.0 
             END AS calculated_overall_score
        // Apply optional cursor filter for pagination (first page passes NULLs)
        WHERE (
    $cursor_timestamp IS NULL 
    OR post.created_at < toFloat($cursor_timestamp)
    OR (post.created_at = toFloat($cursor_timestamp) AND post.uid > $cursor_post_uid)
)
        RETURN post, user, profile, reactions, 
               {uid: conn.uid, connection_status: conn.connection_status, timestamp: toString(conn.timestamp)} AS connection,
               {uid: circle.uid, circle_type: circle.circle_type, sub_relation: circle.sub_relation} AS circle, 
               post.created_at AS created_at, share_count, calculated_overall_score
        ORDER BY post.created_at DESC  // Add this line      
        LIMIT toInteger($limit * 0.8)

        UNION ALL
        // Subquery 2: Fetch Community Post (FIXED - Removed non-existent profile relationship)
        MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_COMMUNITY]->(community:Community)
        OPTIONAL MATCH (community_post)-[:HAS_POST_SHARE]->(share:PostShare)
        OPTIONAL MATCH (community_post)-[:HAS_COMMENT]->(comment:Comment)
        OPTIONAL MATCH (community_post)-[:HAS_LIKE]->(like:Like)
        WITH community_post, community, 
             COUNT(DISTINCT share) AS share_count,
             COUNT(DISTINCT comment) AS comment_count,
             COUNT(DISTINCT like) AS like_count
        WITH community_post, community, share_count, comment_count, like_count,
             (comment_count + like_count + share_count) AS engagement_score
        WITH community_post, community, share_count, comment_count, like_count, engagement_score,
             CASE 
                WHEN community_post.vibe_score IS NOT NULL 
                THEN round(community_post.vibe_score + (engagement_score * 0.1), 1)
                ELSE 2.0 
             END AS calculated_overall_score
        // Apply optional cursor filter for pagination
        WHERE (
            $cursor_timestamp IS NULL 
            OR community_post.created_at < toFloat($cursor_timestamp)
            OR (community_post.created_at = toFloat($cursor_timestamp) AND community_post.uid > $cursor_post_uid)
        )
        RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, 
               NULL AS connection, NULL AS circle, community_post.created_at AS created_at, 
               share_count, calculated_overall_score
        ORDER BY community_post.created_at DESC       
        LIMIT toInteger($limit * 0.4)

        UNION ALL
// Subquery 3: Fetch ALL SubCommunity Posts (Direct, Child, and Sibling) - CORRECTED
CALL {
    // Direct SubCommunity posts
    MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(subcommunity:SubCommunity)
    RETURN community_post, subcommunity, subcommunity AS subcommunity_profile
    
    UNION ALL
    
    // Child SubCommunity posts - CORRECTED DIRECTION
    MATCH (parent_community:Community)-[:HAS_CHILD_COMMUNITY]->(child_subcommunity:SubCommunity)
    MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(child_subcommunity)
    RETURN community_post, child_subcommunity as subcommunity, child_subcommunity AS subcommunity_profile
    
    UNION ALL
    
    // Sibling SubCommunity posts - CORRECTED DIRECTION
    MATCH (parent_community:Community)-[:HAS_SIBLING_COMMUNITY]->(sibling_subcommunity:SubCommunity)
    MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(sibling_subcommunity)
    RETURN community_post, sibling_subcommunity as subcommunity, sibling_subcommunity AS subcommunity_profile
    
    UNION ALL
    
    // ADDED: SubCommunity to SubCommunity child relationships
    MATCH (parent_subcommunity:SubCommunity)-[:HAS_CHILD_COMMUNITY]->(child_subcommunity:SubCommunity)
    MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(child_subcommunity)
    RETURN community_post, child_subcommunity as subcommunity, child_subcommunity AS subcommunity_profile
    
    UNION ALL
    
    // ADDED: SubCommunity to SubCommunity sibling relationships
    MATCH (parent_subcommunity:SubCommunity)-[:HAS_SIBLING_COMMUNITY]->(sibling_subcommunity:SubCommunity)
    MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(sibling_subcommunity)
    RETURN community_post, sibling_subcommunity as subcommunity, sibling_subcommunity AS subcommunity_profile
}

// Apply engagement scoring to all SubCommunity posts
OPTIONAL MATCH (community_post)-[:HAS_POST_SHARE]->(share:PostShare)
OPTIONAL MATCH (community_post)-[:HAS_COMMENT]->(comment:Comment)
OPTIONAL MATCH (community_post)-[:HAS_LIKE]->(like:Like)
WITH community_post, subcommunity, subcommunity_profile,
     COUNT(DISTINCT share) AS share_count,
     COUNT(DISTINCT comment) AS comment_count,
     COUNT(DISTINCT like) AS like_count
WITH community_post, subcommunity, subcommunity_profile, share_count, comment_count, like_count,
     (comment_count + like_count + share_count) AS engagement_score
WITH community_post, subcommunity, subcommunity_profile, share_count, comment_count, like_count, engagement_score,
     CASE
        WHEN community_post.vibe_score IS NOT NULL
        THEN round(community_post.vibe_score + (engagement_score * 0.1), 1)
        ELSE 2.0
     END AS calculated_overall_score
WHERE ($cursor_timestamp IS NULL OR community_post.created_at < toFloat($cursor_timestamp))
RETURN community_post AS post, subcommunity AS user,
       CASE WHEN subcommunity_profile IS NOT NULL THEN subcommunity_profile ELSE subcommunity END AS profile,
       NULL AS reactions,
       NULL AS connection, NULL AS circle, community_post.created_at AS created_at,
       share_count, calculated_overall_score
ORDER BY community_post.created_at DESC
LIMIT toInteger($limit * 0.4)

        UNION ALL
        // Subquery 4: Fetch recent posts from non-connected users (LOWER PRIORITY)
        MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
        WHERE user.user_id <> $log_in_user_node_id
        AND NOT EXISTS {
            MATCH (me:Users {user_id:$log_in_user_node_id})-[:HAS_CONNECTION]->(conn:Connection {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(user)
        }
        OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
        OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
        OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
        WITH post, user, profile, collect(vibe) AS reactions, 
             COUNT(DISTINCT share) AS share_count,
             COUNT(DISTINCT comment) AS comment_count,
             COUNT(DISTINCT vibe) AS like_count
        WITH post, user, profile, reactions, share_count, comment_count, like_count,
             (comment_count + like_count + share_count) AS engagement_score
        WITH post, user, profile, reactions, share_count, comment_count, like_count, engagement_score,
             CASE 
                WHEN post.vibe_score IS NOT NULL 
                THEN round(post.vibe_score + (engagement_score * 0.1), 1)
                ELSE 2.0 
             END AS calculated_overall_score
        WHERE ($cursor_timestamp IS NULL OR post.created_at < toFloat($cursor_timestamp))
        RETURN post, user, profile, reactions, NULL AS connection, NULL AS circle, 
               post.created_at AS created_at, share_count, calculated_overall_score
        ORDER BY post.created_at DESC
        LIMIT toInteger($limit * 0.6)

        }
        RETURN post, user, profile, reactions, connection, circle, share_count, calculated_overall_score, created_at
        ORDER BY 
              created_at DESC,
              CASE WHEN connection IS NOT NULL THEN 1 ELSE 2 END
        LIMIT $limit;
"""

get_top_vibes_meme_query="""
                MATCH (p:Post) 
                RETURN p 
                ORDER BY rand() 
                LIMIT 20

"""

get_top_vibes_podcasts_query="""
                MATCH (p:Post) 
                RETURN p 
                ORDER BY rand() 
                LIMIT 20

"""

get_top_vibes_videos_query="""
                MATCH (p:Post) 
                RETURN p 
                ORDER BY rand() 
                LIMIT 20

"""

get_top_vibes_music_query="""
                MATCH (p:Post) 
                RETURN p 
                ORDER BY rand() 
                LIMIT 20

"""

get_top_vibes_articles_query="""
                MATCH (p:Post) 
                RETURN p 
                ORDER BY rand() 
                LIMIT 20

"""


post_feed_queryV2="""
        CALL {
        // Subquery 1: Fetch 15 recent posts from other users except the logged-in user
        MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
        WHERE  user.user_id <> $log_in_user_node_id
        AND NOT EXISTS {
        MATCH (log_in_user:Users {user_id:$log_in_user_node_id})-[:HAS_CONNECTION]->(:ConnectionV2)-[:HAS_CIRCLE]->(:CircleV2),
              (user:Users)-[:HAS_CONNECTION]->(:ConnectionV2 {connection_status: "Accepted"})
        }
        OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
        RETURN post, user, profile, collect(vibe) AS reactions, NULL AS connection, NULL AS circle, post.created_at AS created_at
        ORDER BY post.created_at DESC
        LIMIT 6
        UNION ALL
        // Subquery 2: Fetch posts from connected users
        MATCH (log_in_user:Users {user_id: $log_in_user_node_id})-[:HAS_CONNECTION]->(connection:ConnectionV2)-[:HAS_CIRCLE]->(circle:CircleV2),
                (user:Users)-[:HAS_CONNECTION]->(connection{connection_status:"Accepted"}),
                (post:Post {is_deleted: false})<-[:HAS_POST]-(user)-[:HAS_PROFILE]->(profile:Profile)
        
        OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
        RETURN post, user, profile, collect(vibe) AS reactions, connection, circle, post.created_at AS created_at
        LIMIT 2

        UNION ALL
        // Subquery 3: Fetch Community Post
        Match (community_post:CommunityPost {is_deleted: false})-[:HAS_COMMUNITY]->(community:Community)
        RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, NULL AS connection, NULL AS circle, community_post.created_at AS created_at
        LIMIT 5

        UNION ALL
        // Subquery 4: Fetch SubCommunity Post
        Match (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(community:SubCommunity)
        RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, NULL AS connection, NULL AS circle, community_post.created_at AS created_at
        LIMIT 5

        }
        RETURN post, user, profile, reactions, connection, circle
        ORDER BY created_at DESC
        LIMIT 20;

"""

recommended_post_from_connected_user_queryV2 = """
        MATCH (u:Users {uid: $uid})-[:HAS_CONNECTION]->(c:ConnectionV2 {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(p_user:Users)
        MATCH (p_user)-[:HAS_POST]->(post:Post{is_deleted: false})
        RETURN post
        ORDER BY post.created_at DESC LIMIT 20;

"""

post_comments_with_metrics_query = """
        CALL {
        // Try to get Post first
        MATCH (post:Post {uid: $post_uid})-[:HAS_COMMENT]->(comment:Comment)-[:HAS_USER]->(user:Users)
        WHERE comment.is_deleted = false
        RETURN post, comment, user, 'Post' as post_type
        
        UNION ALL
        
        // Try to get CommunityPost if Post not found
        MATCH (post:CommunityPost {uid: $post_uid})-[:HAS_COMMENT]->(comment:Comment)-[:HAS_USER]->(user:Users)
        WHERE comment.is_deleted = false
        RETURN post, comment, user, 'CommunityPost' as post_type
        }
        
        // Get post metrics for all found posts
        WITH post, comment, user, post_type
        
        OPTIONAL MATCH (post)-[:HAS_LIKE]->(like:Like)
        WHERE like.is_deleted = false
        
        OPTIONAL MATCH (post)-[:HAS_COMMENT]->(all_comments:Comment)
        WHERE all_comments.is_deleted = false
        
        OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
        WHERE share.is_deleted = false
        
        OPTIONAL MATCH (post)-[:HAS_VIEW]->(view:PostView)
        
        WITH comment, user, post, post_type,
             COUNT(DISTINCT like) as vibes_count,
             COUNT(DISTINCT all_comments) as comments_count,
             COUNT(DISTINCT share) as shares_count,
             COUNT(DISTINCT view) as views_count
        
        // Calculate overall score
        WITH comment, user, post, post_type, vibes_count, comments_count, shares_count, views_count,
             CASE 
                WHEN post.vibe_score IS NOT NULL 
                THEN round(post.vibe_score + ((vibes_count + comments_count + shares_count) * 0.1), 1)
                ELSE 2.0 
             END as calculated_score
        
        RETURN comment, user, post, post_type, vibes_count, comments_count, shares_count, views_count, calculated_score
        ORDER BY comment.timestamp DESC
"""


# Add these queries to your existing post/graphql/raw_queries.py file
# Add these queries to your existing post/graphql/raw_queries.py file

# Enhanced version of your existing post_comments_with_metrics_query with nested support
post_comments_with_metrics_nested_query = """
MATCH (post:Post {uid: $post_uid})-[:HAS_COMMENT]->(comment:Comment)
WHERE NOT comment.is_deleted

// Check if this is a top-level comment or reply
OPTIONAL MATCH (comment)-[:REPLIED_TO]->(parent_comment:Comment)

// Get comment metrics using the same logic as your original query
OPTIONAL MATCH (comment)-[:HAS_REACTION]->(reaction)
WHERE NOT reaction.is_deleted

OPTIONAL MATCH (post)-[:HAS_VIEW]->(view)
WHERE NOT view.is_deleted

OPTIONAL MATCH (post)-[:HAS_COMMENT]->(all_comments)
WHERE NOT all_comments.is_deleted

OPTIONAL MATCH (post)-[:HAS_SHARE]->(share)
WHERE NOT share.is_deleted

OPTIONAL MATCH (post)-[:HAS_LIKE]->(like)
WHERE NOT like.is_deleted

// Count replies to this specific comment
OPTIONAL MATCH (comment)<-[:REPLIED_TO]-(reply:Comment)
WHERE NOT reply.is_deleted

WITH comment, parent_comment, post,
     COUNT(DISTINCT reaction) as vibes_count,
     COUNT(DISTINCT view) as views_count,
     COUNT(DISTINCT all_comments) as comments_count,
     COUNT(DISTINCT share) as shares_count,
     COUNT(DISTINCT like) as likes_count,
     COUNT(DISTINCT reply) as reply_count,
     CASE WHEN parent_comment IS NULL THEN 0 ELSE 1 END as is_reply

// Calculate score (your existing logic)
WITH comment, parent_comment, post, vibes_count, views_count, comments_count, shares_count, likes_count, reply_count, is_reply,
     CASE 
       WHEN (vibes_count + views_count + comments_count + shares_count) > 0 
       THEN (vibes_count * 2.0 + views_count * 0.5 + comments_count * 1.5 + shares_count * 3.0) / (vibes_count + views_count + comments_count + shares_count)
       ELSE 2.0 
     END as calculated_score

// Order by: top-level comments first, then by timestamp
ORDER BY is_reply ASC, comment.timestamp DESC

RETURN comment, parent_comment, post, vibes_count, views_count, comments_count, shares_count, likes_count, calculated_score, reply_count, is_reply
"""

# Query to get replies for a specific comment
comment_replies_with_metrics_query = """
MATCH (parent_comment:Comment {uid: $parent_comment_uid})<-[:REPLIED_TO]-(reply:Comment)
WHERE NOT reply.is_deleted

// Get metrics for each reply
OPTIONAL MATCH (reply)-[:HAS_REACTION]->(reaction)
WHERE NOT reaction.is_deleted

OPTIONAL MATCH (reply)<-[:HAS_COMMENT]-(related_post)
OPTIONAL MATCH (related_post)-[:HAS_VIEW]->(view)
WHERE NOT view.is_deleted

OPTIONAL MATCH (related_post)-[:HAS_COMMENT]->(all_comments)
WHERE NOT all_comments.is_deleted

OPTIONAL MATCH (related_post)-[:HAS_SHARE]->(share)
WHERE NOT share.is_deleted

OPTIONAL MATCH (related_post)-[:HAS_LIKE]->(like)
WHERE NOT like.is_deleted

// Count nested replies to each reply
OPTIONAL MATCH (reply)<-[:REPLIED_TO]-(nested_reply:Comment)
WHERE NOT nested_reply.is_deleted

WITH reply,
     COUNT(DISTINCT reaction) as vibes_count,
     COUNT(DISTINCT view) as views_count,
     COUNT(DISTINCT all_comments) as comments_count,
     COUNT(DISTINCT share) as shares_count,
     COUNT(DISTINCT like) as likes_count,
     COUNT(DISTINCT nested_reply) as reply_count

// Calculate score
WITH reply, vibes_count, views_count, comments_count, shares_count, likes_count, reply_count,
     CASE 
       WHEN (vibes_count + views_count + comments_count + shares_count) > 0 
       THEN (vibes_count * 2.0 + views_count * 0.5 + comments_count * 1.5 + shares_count * 3.0) / (vibes_count + views_count + comments_count + shares_count)
       ELSE 2.0 
     END as calculated_score

ORDER BY reply.timestamp ASC

RETURN reply, vibes_count, views_count, comments_count, shares_count, likes_count, calculated_score, reply_count
"""

# Query to get only top-level comments (no replies) - for better performance
top_level_comments_with_metrics_query = """
MATCH (post:Post {uid: $post_uid})-[:HAS_COMMENT]->(comment:Comment)
WHERE NOT comment.is_deleted
AND NOT EXISTS((comment)-[:REPLIED_TO]->())  // Only top-level comments

// Get comment metrics using the same logic as your original query
OPTIONAL MATCH (comment)-[:HAS_REACTION]->(reaction)
WHERE NOT reaction.is_deleted

OPTIONAL MATCH (post)-[:HAS_VIEW]->(view)
WHERE NOT view.is_deleted

OPTIONAL MATCH (post)-[:HAS_COMMENT]->(all_comments)
WHERE NOT all_comments.is_deleted

OPTIONAL MATCH (post)-[:HAS_SHARE]->(share)
WHERE NOT share.is_deleted

OPTIONAL MATCH (post)-[:HAS_LIKE]->(like)
WHERE NOT like.is_deleted

// Count replies to this comment
OPTIONAL MATCH (comment)<-[:REPLIED_TO]-(reply:Comment)
WHERE NOT reply.is_deleted

WITH comment, post,
     COUNT(DISTINCT reaction) as vibes_count,
     COUNT(DISTINCT view) as views_count,
     COUNT(DISTINCT all_comments) as comments_count,
     COUNT(DISTINCT share) as shares_count,
     COUNT(DISTINCT like) as likes_count,
     COUNT(DISTINCT reply) as reply_count

// Calculate score
WITH comment, post, vibes_count, views_count, comments_count, shares_count, likes_count, reply_count,
     CASE 
       WHEN (vibes_count + views_count + comments_count + shares_count) > 0 
       THEN (vibes_count * 2.0 + views_count * 0.5 + comments_count * 1.5 + shares_count * 3.0) / (vibes_count + views_count + comments_count + shares_count)
       ELSE 2.0 
     END as calculated_score

ORDER BY comment.timestamp DESC

RETURN comment, post, vibes_count, views_count, comments_count, shares_count, likes_count, calculated_score, reply_count
"""



# File: post/graphql/raw_queries/post_queries.py
# REPLACE the post_feed_query_cursor with this FIXED version:

post_feed_query_cursor = """
        CALL {
        // Subquery 1: Fetch posts from connected users (PRIORITIZE THIS)
        MATCH (me:Users {user_id: $log_in_user_node_id})-[:HAS_CONNECTION]->(conn:Connection {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(friend:Users)-[:HAS_POST]->(post:Post {is_deleted: false}),
              (friend)-[:HAS_PROFILE]->(profile:Profile)
        
        // Apply cursor filter for pagination - FIXED SYNTAX
        WHERE (
            $cursor_timestamp IS NULL 
            OR post.created_at < toFloat($cursor_timestamp)
            OR (post.created_at = toFloat($cursor_timestamp) AND post.uid > $cursor_post_uid)
        )
        
        OPTIONAL MATCH (conn)-[:HAS_CIRCLE]->(circle:Circle)
        OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
        OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
        OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
        
        WITH post, friend as user, profile, collect(vibe) AS reactions, conn, circle,
             COUNT(DISTINCT share) AS share_count,
             COUNT(DISTINCT comment) AS comment_count,
             COUNT(DISTINCT vibe) AS like_count
        WITH post, user, profile, reactions, conn, circle, share_count, comment_count, like_count,
             (comment_count + like_count + share_count) AS engagement_score
        WITH post, user, profile, reactions, conn, circle, share_count, comment_count, like_count, engagement_score,
             CASE 
                WHEN post.vibe_score IS NOT NULL 
                THEN round(post.vibe_score + (engagement_score * 0.1), 1)
                ELSE 2.0 
             END AS calculated_overall_score
        
        RETURN post, user, profile, reactions, conn as connection, circle, post.created_at AS created_at, 
               share_count, calculated_overall_score
        ORDER BY post.created_at DESC, post.uid ASC
        LIMIT toInteger($limit * 0.4)

        UNION ALL
        
        // Subquery 2: Fetch posts from non-connected users
        MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
        WHERE user.user_id <> $log_in_user_node_id
        AND NOT EXISTS {
            MATCH (me:Users {user_id: $log_in_user_node_id})-[:HAS_CONNECTION]->(:Connection {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(user)
        }
        // Apply cursor filter - FIXED SYNTAX
        AND (
            $cursor_timestamp IS NULL 
            OR post.created_at < toFloat($cursor_timestamp)
            OR (post.created_at = toFloat($cursor_timestamp) AND post.uid > $cursor_post_uid)
        )
        
        OPTIONAL MATCH (post)-[reaction:HAS_LIKE]->(vibe:Like)
        OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare)
        OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
        
        WITH post, user, profile, collect(vibe) AS reactions,
             COUNT(DISTINCT share) AS share_count,
             COUNT(DISTINCT comment) AS comment_count,
             COUNT(DISTINCT vibe) AS like_count
        WITH post, user, profile, reactions, share_count, comment_count, like_count,
             (comment_count + like_count + share_count) AS engagement_score
        WITH post, user, profile, reactions, share_count, comment_count, like_count, engagement_score,
             CASE 
                WHEN post.vibe_score IS NOT NULL 
                THEN round(post.vibe_score + (engagement_score * 0.1), 1)
                ELSE 2.0 
             END AS calculated_overall_score
        
        RETURN post, user, profile, reactions, NULL AS connection, NULL AS circle, post.created_at AS created_at, 
               share_count, calculated_overall_score
        ORDER BY post.created_at DESC, post.uid ASC
        LIMIT toInteger($limit * 0.5)

        UNION ALL
        
        // Subquery 3: Fetch Community Posts
        MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_COMMUNITY]->(community:Community)
        WHERE (
            $cursor_timestamp IS NULL 
            OR community_post.created_at < toFloat($cursor_timestamp)
            OR (community_post.created_at = toFloat($cursor_timestamp) AND community_post.uid > $cursor_post_uid)
        )
        
        OPTIONAL MATCH (community_post)-[:HAS_POST_SHARE]->(share:PostShare)
        OPTIONAL MATCH (community_post)-[:HAS_COMMENT]->(comment:Comment)
        OPTIONAL MATCH (community_post)-[:HAS_LIKE]->(like:Like)
        
        WITH community_post, community,
             COUNT(DISTINCT share) AS share_count,
             COUNT(DISTINCT comment) AS comment_count,
             COUNT(DISTINCT like) AS like_count
        WITH community_post, community, share_count, comment_count, like_count,
             (comment_count + like_count + share_count) AS engagement_score
        WITH community_post, community, share_count, comment_count, like_count, engagement_score,
             CASE 
                WHEN community_post.vibe_score IS NOT NULL 
                THEN round(community_post.vibe_score + (engagement_score * 0.1), 1)
                ELSE 2.0 
             END AS calculated_overall_score
        
        RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, 
               NULL AS connection, NULL AS circle, community_post.created_at AS created_at, 
               share_count, calculated_overall_score
        ORDER BY community_post.created_at DESC, community_post.uid ASC
        LIMIT toInteger($limit * 0.1)

        }
        
        // Final ordering and limit
        WITH post, user, profile, reactions, connection, circle, created_at, share_count, calculated_overall_score
        ORDER BY created_at DESC, post.uid ASC
        LIMIT $limit
        RETURN post, user, profile, reactions, connection, circle, share_count, calculated_overall_score;
"""
