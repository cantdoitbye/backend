"""
Feed Algorithm Validation Utilities

This module handles validation of user data and algorithm requirements
to ensure optimal feed generation.
"""

import logging
import time
from typing import Dict, Any, List
from neomodel import db
from auth_manager.models import Users

logger = logging.getLogger(__name__)


def validate_feed_algorithm_requirements(user_id: str) -> Dict[str, Any]:
    """
    Validate that all requirements for the feed algorithm are met.
    
    This function analyzes user data to determine the best algorithm
    configuration and identifies potential issues.
    
    Args:
        user_id: User identifier to validate
        
    Returns:
        Dictionary with validation results and recommendations
    """
    try:
        user_node = Users.nodes.get(user_id=user_id)
        profile_node = user_node.profile.single() if user_node else None
        
        # Check user connections
        connection_query = """
        MATCH (u:Users {user_id: $user_id})-[:HAS_CONNECTION]->
              (c:Connection {connection_status: "Accepted"})
        RETURN count(c) as connection_count
        """
        connection_results, _ = db.cypher_query(connection_query, {'user_id': user_id})
        connection_count = connection_results[0][0] if connection_results else 0
        
        # Check user interests
        interest_count = 0
        if profile_node:
            interests = list(profile_node.interest.all())
            interest_count = len([i for i in interests if i.names])
        
        # Check interaction history
        interaction_query = """
        MATCH (u:Users {user_id: $user_id})
        OPTIONAL MATCH (u)-[:HAS_LIKE]->(like:Like)
        OPTIONAL MATCH (u)-[:HAS_COMMENT]->(comment:Comment)
        RETURN count(like) + count(comment) as interaction_count
        """
        interaction_results, _ = db.cypher_query(interaction_query, {'user_id': user_id})
        interaction_count = interaction_results[0][0] if interaction_results else 0
        
        # Determine user category and recommendations
        user_category = "regular"
        recommendations = []
        algorithm_config = {}
        
        if connection_count == 0 and interest_count == 0:
            user_category = "new_user"
            recommendations = [
                "prioritize_trending_content",
                "show_popular_posts",
                "suggest_interest_onboarding"
            ]
            algorithm_config = {
                "trending_weight_boost": 0.3,
                "popular_content_boost": 0.4,
                "suggestion_boost": 0.2
            }
        elif interaction_count < 5:
            user_category = "low_activity"
            recommendations = [
                "boost_suggestion_content",
                "increase_trending_weight",
                "send_engagement_notifications"
            ]
            algorithm_config = {
                "suggestion_boost": 0.3,
                "trending_weight_boost": 0.2,
                "enable_reengagement": True
            }
        elif connection_count > 100:
            user_category = "super_connected"
            recommendations = [
                "apply_strong_diversity_filter",
                "limit_posts_per_connection",
                "enable_feed_customization"
            ]
            algorithm_config = {
                "diversity_enforcement": True,
                "max_posts_per_author": 1,
                "enable_advanced_filtering": True
            }
        
        return {
            "user_category": user_category,
            "connection_count": connection_count,
            "interest_count": interest_count,
            "interaction_count": interaction_count,
            "recommendations": recommendations,
            "algorithm_config": algorithm_config,
            "algorithm_ready": True,
            "validation_timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error validating feed algorithm requirements: {e}")
        return {
            "user_category": "unknown",
            "algorithm_ready": False,
            "error": str(e),
            "recommendations": ["fallback_to_simple_feed"],
            "validation_timestamp": time.time()
        }


def validate_feed_quality(feed_items: List[Any]) -> Dict[str, Any]:
    """
    Validate the quality of generated feed content.
    
    Args:
        feed_items: List of feed items to validate
        
    Returns:
        Dictionary with quality metrics and recommendations
    """
    if not feed_items:
        return {
            "quality_score": 0.0,
            "issues": ["empty_feed"],
            "recommendations": ["check_content_availability", "review_algorithm_parameters"]
        }
    
    # Analyze feed diversity
    authors = set()
    content_types = set()
    
    for item in feed_items:
        if hasattr(item, 'created_by') and item.created_by:
            authors.add(item.created_by.user_id)
        if hasattr(item, 'post_type'):
            content_types.add(item.post_type)
    
    diversity_score = len(authors) / len(feed_items) if feed_items else 0
    type_diversity = len(content_types) / min(len(feed_items), 5)  # Max 5 content types
    
    quality_score = (diversity_score + type_diversity) / 2
    
    issues = []
    recommendations = []
    
    if diversity_score < 0.3:
        issues.append("low_author_diversity")
        recommendations.append("increase_diversity_filtering")
    
    if type_diversity < 0.5:
        issues.append("low_content_type_diversity")
        recommendations.append("balance_content_types")
    
    if len(feed_items) < 5:
        issues.append("insufficient_content")
        recommendations.append("expand_content_sources")
    
    return {
        "quality_score": quality_score,
        "diversity_score": diversity_score,
        "type_diversity": type_diversity,
        "author_count": len(authors),
        "content_type_count": len(content_types),
        "total_items": len(feed_items),
        "issues": issues,
        "recommendations": recommendations
    }