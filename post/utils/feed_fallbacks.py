"""
Feed Algorithm Fallback Mechanisms

This module provides fallback strategies when the main algorithm
fails or when users have insufficient data for personalization.
"""

import logging
from typing import List, Any, Optional
from neomodel import db

logger = logging.getLogger(__name__)


def apply_emergency_fallback_feed(user_id: str, limit: int = 20) -> List[Any]:
    """
    Emergency fallback feed for when the main algorithm fails.
    
    Provides a simple, reliable feed based on recent popular content
    that doesn't require complex user analysis.
    
    Args:
        user_id: User requesting the feed
        limit: Maximum number of items to return
        
    Returns:
        List of content items in simple chronological + popularity order
    """
    try:
        logger.warning(f"Applying emergency fallback feed for user {user_id}")
        
        # Simple query for recent popular content
        fallback_query = """
        MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
        WHERE user.user_id <> $user_id
        OPTIONAL MATCH (post)-[:HAS_LIKE]->(like:Like)
        OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
        WITH post, user, profile, count(like) as like_count, count(comment) as comment_count
        WITH post, user, profile, (like_count + comment_count * 2) as engagement_score
        ORDER BY post.created_at DESC, engagement_score DESC
        LIMIT $limit
        RETURN post, user, profile, [] as reactions, NULL as connection, 
               NULL as circle, 0 as share_count, 2.0 as score
        """
        
        results, _ = db.cypher_query(fallback_query, {
            'user_id': user_id,
            'limit': limit
        })
        
        logger.info(f"Emergency fallback returned {len(results)} items for user {user_id}")
        return results
        
    except Exception as e:
        logger.error(f"Emergency fallback feed failed for user {user_id}: {e}")
        return []


def apply_new_user_fallback_feed(user_id: str, limit: int = 20) -> List[Any]:
    """
    Specialized fallback for new users with no connections or interests.
    
    Focuses on trending content, popular posts, and diverse content types
    to help new users discover the platform.
    
    Args:
        user_id: New user requesting feed
        limit: Maximum number of items to return
        
    Returns:
        List of trending and popular content items
    """
    try:
        logger.info(f"Applying new user fallback feed for user {user_id}")
        
        # Query for trending and popular content with diversity
        new_user_query = """
        CALL {
            // Get trending content (last 7 days with high engagement)
            MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
            WHERE user.user_id <> $user_id 
            AND post.created_at > datetime() - duration('P7D')
            OPTIONAL MATCH (post)-[:HAS_LIKE]->(like:Like)
            OPTIONAL MATCH (post)-[:HAS_COMMENT]->(comment:Comment)
            WITH post, user, profile, count(like) + count(comment) * 2 as engagement
            WHERE engagement > 5
            RETURN post, user, profile, engagement, 'trending' as category
            ORDER BY engagement DESC
            LIMIT 10
            
            UNION ALL
            
            // Get popular content (all time popular)
            MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
            WHERE user.user_id <> $user_id
            OPTIONAL MATCH (post)-[:HAS_LIKE]->(like:Like)
            WITH post, user, profile, count(like) as total_likes
            WHERE total_likes > 10
            RETURN post, user, profile, total_likes as engagement, 'popular' as category
            ORDER BY total_likes DESC
            LIMIT 10
        }
        RETURN post, user, profile, [] as reactions, NULL as connection, 
               NULL as circle, 0 as share_count, 2.0 as score
        ORDER BY engagement DESC
        LIMIT $limit
        """
        
        results, _ = db.cypher_query(new_user_query, {
            'user_id': user_id,
            'limit': limit
        })
        
        logger.info(f"New user fallback returned {len(results)} items for user {user_id}")
        return results
        
    except Exception as e:
        logger.error(f"New user fallback failed for user {user_id}: {e}")
        # Fall back to emergency fallback
        return apply_emergency_fallback_feed(user_id, limit)


def apply_low_activity_fallback_feed(user_id: str, limit: int = 20) -> List[Any]:
    """
    Fallback for users with low activity requiring re-engagement.
    
    Focuses on suggestion content and trending topics to re-engage
    users who haven't been active recently.
    
    Args:
        user_id: Low-activity user requesting feed
        limit: Maximum number of items to return
        
    Returns:
        List of engaging and suggestion-based content
    """
    try:
        logger.info(f"Applying low activity fallback feed for user {user_id}")
        
        # Get user's basic profile for suggestions
        user_profile_query = """
        MATCH (u:Users {user_id: $user_id})-[:HAS_PROFILE]->(p:Profile)
        OPTIONAL MATCH (p)-[:HAS_INTEREST]->(i:Interest)
        RETURN collect(i.name) as interests, p.lives_in as location
        """
        
        profile_results, _ = db.cypher_query(user_profile_query, {'user_id': user_id})
        user_interests = profile_results[0][0] if profile_results else []
        user_location = profile_results[0][1] if profile_results else None
        
        # Build suggestion-focused query
        suggestion_query = """
        MATCH (post:Post {is_deleted: false})<-[:HAS_POST]-(user:Users)-[:HAS_PROFILE]->(profile:Profile)
        WHERE user.user_id <> $user_id
        
        // Score posts based on suggestion criteria
        WITH post, user, profile,
        CASE 
            WHEN any(hashtag IN post.hashtags WHERE hashtag IN $interests) THEN 0.8
            WHEN profile.lives_in = $location AND $location IS NOT NULL THEN 0.6
            ELSE 0.3
        END as suggestion_score
        
        OPTIONAL MATCH (post)-[:HAS_LIKE]->(like:Like)
        WITH post, user, profile, suggestion_score, count(like) as like_count
        
        // Boost engaging content
        WITH post, user, profile, suggestion_score + (like_count * 0.1) as final_score
        
        ORDER BY final_score DESC, post.created_at DESC
        LIMIT $limit
        
        RETURN post, user, profile, [] as reactions, NULL as connection, 
               NULL as circle, 0 as share_count, 2.0 as score
        """
        
        results, _ = db.cypher_query(suggestion_query, {
            'user_id': user_id,
            'interests': user_interests,
            'location': user_location,
            'limit': limit
        })
        
        logger.info(f"Low activity fallback returned {len(results)} items for user {user_id}")
        return results
        
    except Exception as e:
        logger.error(f"Low activity fallback failed for user {user_id}: {e}")
        # Fall back to new user fallback
        return apply_new_user_fallback_feed(user_id, limit)


def get_appropriate_fallback_feed(user_category: str, user_id: str, limit: int = 20) -> List[Any]:
    """
    Get appropriate fallback feed based on user category.
    
    Args:
        user_category: Category from validation (new_user, low_activity, etc.)
        user_id: User requesting feed
        limit: Maximum items to return
        
    Returns:
        Appropriate fallback feed for the user category
    """
    fallback_strategies = {
        'new_user': apply_new_user_fallback_feed,
        'low_activity': apply_low_activity_fallback_feed,
        'unknown': apply_emergency_fallback_feed
    }
    
    strategy = fallback_strategies.get(user_category, apply_emergency_fallback_feed)
    return strategy(user_id, limit)