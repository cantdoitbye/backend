from django.core.cache import cache
from neomodel import db
import logging

logger = logging.getLogger(__name__)

def _cache_key(user_id: str) -> str:
    return f"interest_vector:{user_id}"

def get_user_interest_vector(user_id: str) -> dict:
    key = _cache_key(user_id)
    v = cache.get(key)
    if v:
        logger.info(f"interest_vector cache_hit user={user_id} pt={len(v.get('post_types', {}))} tags={len(v.get('tags', {}))} kw={len(v.get('keywords', {}))}")
        return v
    v = _compute_user_interest_vector(user_id)
    cache.set(key, v, 3600)
    logger.info(f"interest_vector cache_miss user={user_id} pt={len(v.get('post_types', {}))} tags={len(v.get('tags', {}))} kw={len(v.get('keywords', {}))}")
    return v

def _compute_user_interest_vector(user_id: str) -> dict:
    try:
        post_type_counts = {}
        tag_counts = {}
        kw_counts = {}

        q1 = (
            "CALL { MATCH (u:Users {user_id:$uid})<-[:HAS_USER]-(l:Like)-[:HAS_POST]->(p:Post) RETURN p.post_type as k, count(*) as c } "
            "UNION ALL CALL { MATCH (u:Users {user_id:$uid})<-[:HAS_USER]-(c:Comment)-[:HAS_POST]->(p:Post) RETURN p.post_type as k, count(*) as c } "
            "UNION ALL CALL { MATCH (u:Users {user_id:$uid})<-[:HAS_USER]-(s:PostShare)-[:HAS_POST]->(p:Post) RETURN p.post_type as k, count(*) as c } "
            "UNION ALL CALL { MATCH (u:Users {user_id:$uid})<-[:HAS_USER]-(sv:SavedPost)-[:HAS_POST]->(p:Post) RETURN p.post_type as k, count(*) as c }"
        )
        rows, _ = db.cypher_query(q1, {"uid": str(user_id)})
        for r in rows:
            k, c = r[0], r[1]
            if k:
                post_type_counts[k] = post_type_counts.get(k, 0) + int(c or 0)

        q2 = (
            "MATCH (u:Users {user_id:$uid})<-[:HAS_USER]-(i)-[:HAS_POST]->(p:Post)-[:TAG_BELONG_TO]->(t:Tag) "
            "RETURN t.names"
        )
        rows, _ = db.cypher_query(q2, {"uid": str(user_id)})
        for r in rows:
            names = r[0]
            if names and isinstance(names, list):
                for n in names:
                    if n:
                        tag_counts[n.lower()] = tag_counts.get(n.lower(), 0) + 1

        q3 = (
            "MATCH (u:Users {user_id:$uid})-[:HAS_MEMBERSHIP]->(:Membership)-[:MEMBEROF]->(c:Community) "
            "OPTIONAL MATCH (kw:CommunityKeyword)-[:KEYWORD_FOR]->(c) "
            "RETURN kw.keyword"
        )
        rows, _ = db.cypher_query(q3, {"uid": str(user_id)})
        for r in rows:
            k = r[0]
            if k:
                kw_counts[k.lower()] = kw_counts.get(k.lower(), 0) + 1

        def normalize(d: dict) -> dict:
            if not d:
                return {}
            m = max(d.values())
            if m <= 0:
                return {}
            return {k: (v / m) for k, v in d.items()}

        return {
            "post_types": normalize(post_type_counts),
            "tags": normalize(tag_counts),
            "keywords": normalize(kw_counts),
        }
    except Exception:
        return {"post_types": {}, "tags": {}, "keywords": {}}
