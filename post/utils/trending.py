from neomodel import db

def fetch_trending(limit: int, exclude_uids: set[str] = set()):
    print("fetching trending...")
    q = (
        "MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile) "
        "OPTIONAL MATCH (post)-[:HAS_LIKE]->(like:Like) "
        "OPTIONAL MATCH (post)-[:HAS_POST_SHARE]->(share:PostShare) "
        "OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment) "
        "WITH post, user, profile, collect(like) AS reactions, "
        "     COUNT(DISTINCT share) AS share_count, "
        "     COUNT(DISTINCT comment) AS comment_count, "
        "     COUNT(DISTINCT like) AS like_count, toFloat(post.created_at) AS created_at "
        "WITH post, user, profile, reactions, share_count, comment_count, like_count, created_at, "
        "     (comment_count + like_count + share_count) AS engagement_score "
        "WITH post, user, profile, reactions, share_count, engagement_score, created_at, "
        "     CASE WHEN post.vibe_score IS NOT NULL THEN round(post.vibe_score + (engagement_score * 0.1), 1) ELSE 2.0 END AS calculated_overall_score "
        "RETURN post { .uid, .post_title, .post_text, .post_type, .post_file_id, .privacy, vibe_score: post.vibe_score, created_at: created_at, updated_at: toString(post.updated_at), is_deleted: post.is_deleted, share_count: share_count } AS post, "
        "       user, profile, reactions, NULL AS connection, NULL AS circle, share_count, calculated_overall_score, created_at "
        "UNION ALL "
        "MATCH (community_post:CommunityPost {is_deleted: false})<-[:HAS_POST]-(community:Community) "
        "OPTIONAL MATCH (community_post)-[:HAS_POST_SHARE]->(share:PostShare) "
        "OPTIONAL MATCH (community_post)-[:HAS_COMMENT]->(comment:Comment) "
        "OPTIONAL MATCH (community_post)-[:HAS_LIKE]->(like:Like) "
        "WITH community_post, community, "
        "     COUNT(DISTINCT share) AS share_count, "
        "     COUNT(DISTINCT comment) AS comment_count, "
        "     COUNT(DISTINCT like) AS like_count, toFloat(community_post.created_at) AS created_at "
        "WITH community_post, community, share_count, comment_count, like_count, created_at, "
        "     (comment_count + like_count + share_count) AS engagement_score "
        "WITH community_post AS cp, community AS cm, share_count AS sc, engagement_score AS es, created_at AS ca "
        "WITH cp, cm, sc, es, ca, CASE WHEN cp.vibe_score IS NOT NULL THEN round(cp.vibe_score + (es * 0.1), 1) ELSE 2.0 END AS calculated_overall_score "
        "RETURN cp { .uid, .post_title, .post_text, .post_type, .post_file_id, .privacy, vibe_score: cp.vibe_score, created_at: ca, updated_at: toString(cp.updated_at), is_deleted: cp.is_deleted, share_count: sc } AS post, "
        "       cm AS user, cm AS profile, [] AS reactions, NULL AS connection, NULL AS circle, sc AS share_count, calculated_overall_score, ca AS created_at "
        "ORDER BY calculated_overall_score DESC, created_at DESC "
        "LIMIT $limit"
    )
    rows, _ = db.cypher_query(q, {"limit": int(limit)})
    if exclude_uids:
        filtered = []
        for r in rows:
            pd = r[0] if r else {}
            puid = None
            if isinstance(pd, dict):
                puid = pd.get('uid') or pd.get('post_uid')
            else:
                puid = getattr(pd, 'uid', None) or getattr(pd, 'post_uid', None)
            if puid and puid not in exclude_uids:
                filtered.append(r)
        return filtered
    return rows
