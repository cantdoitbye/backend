
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

RETURN post, user, profile, reactions, 
       {uid: conn.uid, connection_status: conn.connection_status, timestamp: toString(conn.timestamp)} AS connection,
       {uid: circle.uid, circle_type: circle.circle_type, sub_relation: circle.sub_relation} AS circle, 
       post.created_at AS created_at, share_count, calculated_overall_score
LIMIT 25

        UNION ALL
        // Subquery 2: Fetch recent posts from non-connected users (LOWER PRIORITY)
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
RETURN post, user, profile, reactions, NULL AS connection, NULL AS circle, 
       post.created_at AS created_at, share_count, calculated_overall_score
ORDER BY post.created_at DESC
LIMIT 35

        UNION ALL
        // Subquery 3: Fetch Community Post
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
        RETURN community_post AS post, community AS user, community AS profile, NULL AS reactions, 
               NULL AS connection, NULL AS circle, community_post.created_at AS created_at, 
               share_count, calculated_overall_score
        LIMIT 5

        UNION ALL
        // Subquery 4: Fetch SubCommunity Post
        MATCH (community_post:CommunityPost {is_deleted: false})-[:HAS_SUBCOMMUNITY]->(community:SubCommunity)
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
        LIMIT 5

        }
        RETURN post, user, profile, reactions, connection, circle, share_count, calculated_overall_score
        ORDER BY 
            CASE WHEN connection IS NOT NULL THEN 1 ELSE 2 END,
            created_at DESC
        LIMIT 60;
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
