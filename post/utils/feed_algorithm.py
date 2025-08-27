# post/utils/feed_algorithm.py

"""
Feed Algorithm Implementation for Ooumph Social Media Platform

This module implements the comprehensive feed algorithm as specified in the 
feed algorithm documentation. It handles content scoring, ranking, and 
personalization for user feeds.

Key Features:
- Content prioritization based on connections, interests, and interactions
- Trending content integration
- Suggestion scoring for communities, brands, and products
- Edge case handling for new users and low activity scenarios
- Comprehensive scoring system with multiple weighted factors
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from neomodel import db
from auth_manager.models import Users, Profile, Interest
from post.models import Post
from connection.models import Connection, Circle
from vibe_manager.models import Vibe
from community.models import Community

logger = logging.getLogger(__name__)


class FeedAlgorithm:
    """
    Core feed algorithm implementation for the Ooumph platform.
    
    This class implements the feed algorithm as per the specification document,
    providing personalized content ranking based on multiple factors including
    connections, interests, interactions, content types, and trending data.
    """
    
    # Algorithm configuration weights as per specification
    WEIGHTS = {
        'connection_score': 0.7,
        'interest_relevance': 0.6,
        'interaction_score': 0.8,
        'content_type_preference': 0.5,
        'trending_hashtag': 0.6,
        'suggestion_weight_community': 0.5,
        'suggestion_weight_brand': 0.5,
        'suggestion_weight_product': 0.3,
        'time_decay_factor': 0.1,
        'diversity_factor': 0.3
    }
    
    # Content type preferences based on user engagement patterns
    CONTENT_TYPE_SCORES = {
        'image': 0.8,
        'video': 0.9,
        'text': 0.6,
        'product': 0.7,
        'community_post': 0.8
    }
    
    def __init__(self, user_id: str):
        """
        Initialize the feed algorithm for a specific user.
        
        Args:
            user_id (str): The ID of the user for whom to generate the feed
        """
        self.user_id = user_id
        self.user_node = Users.nodes.get(user_id=user_id)
        self.profile_node = self.user_node.profile.single()
        self.user_connections = self._get_user_connections()
        self.user_interests = self._get_user_interests()
        self.user_interactions = self._get_user_interactions()
        self.content_type_preferences = self._get_content_type_preferences()
        self.trending_data = self._get_trending_data()
        
    def _get_user_connections(self) -> List[str]:
        """Get all connected user IDs for the current user."""
        try:
            query = """
            MATCH (u:Users {user_id: $user_id})-[:HAS_CONNECTION]->
                  (c:Connection {connection_status: "Accepted"})<-[:HAS_CONNECTION]-(connected:Users)
            RETURN connected.user_id as connected_user_id
            """
            results, _ = db.cypher_query(query, {'user_id': self.user_id})
            return [result[0] for result in results]
        except Exception as e:
            logger.error(f"Error getting user connections: {e}")
            return []
    
    def _get_user_interests(self) -> List[str]:
        """Get user interests and convert them to hashtag format."""
        try:
            if self.profile_node:
                interests = list(self.profile_node.interest.all())
                # Interest.names is an ArrayProperty, so we need to flatten it
                interest_names = []
                for interest in interests:
                    if interest.names:
                        interest_names.extend([name.lower().replace(' ', '') for name in interest.names])
                return interest_names
            return []
        except Exception as e:
            logger.error(f"Error getting user interests: {e}")
            return []
    
    def _get_user_interactions(self) -> Dict[str, List[str]]:
        """Get user's past interactions (vibes, comments) with posts."""
        try:
            query = """
            MATCH (u:Users {user_id: $user_id})
            OPTIONAL MATCH (u)-[:HAS_LIKE]->(like:Like)-[:LIKE_POST]->(post:Post)
            OPTIONAL MATCH (u)-[:HAS_COMMENT]->(comment:Comment)-[:COMMENT_POST]->(commentPost:Post)
            RETURN collect(DISTINCT post.uid) as liked_posts, 
                   collect(DISTINCT commentPost.uid) as commented_posts
            """
            results, _ = db.cypher_query(query, {'user_id': self.user_id})
            if results:
                return {
                    'liked_posts': results[0][0] or [],
                    'commented_posts': results[0][1] or []
                }
            return {'liked_posts': [], 'commented_posts': []}
        except Exception as e:
            logger.error(f"Error getting user interactions: {e}")
            return {'liked_posts': [], 'commented_posts': []}
    
    def _get_content_type_preferences(self) -> Dict[str, float]:
        """Analyze user's content type preferences based on past engagement."""
        try:
            query = """
            MATCH (u:Users {user_id: $user_id})-[:HAS_LIKE]->(like:Like)-[:LIKE_POST]->(post:Post)
            RETURN post.post_type as content_type, count(*) as engagement_count
            ORDER BY engagement_count DESC
            """
            results, _ = db.cypher_query(query, {'user_id': self.user_id})
            
            preferences = {}
            total_engagements = sum(result[1] for result in results)
            
            if total_engagements > 0:
                for result in results:
                    content_type = result[0]
                    count = result[1]
                    preferences[content_type] = count / total_engagements
            else:
                # Default preferences for new users
                preferences = {
                    'image': 0.4,
                    'video': 0.3,
                    'text': 0.2,
                    'product': 0.1
                }
            
            return preferences
        except Exception as e:
            logger.error(f"Error getting content type preferences: {e}")
            return {'image': 0.4, 'video': 0.3, 'text': 0.2, 'product': 0.1}
    
    def _get_trending_data(self) -> Dict[str, List[str]]:
        """Get current trending hashtags and interests."""
        try:
            # Get trending hashtags based on recent usage
            hashtag_query = """
            MATCH (post:Post {is_deleted: false})
            WHERE post.created_at > datetime() - duration('P7D')  // Last 7 days
            AND post.hashtags IS NOT NULL
            UNWIND post.hashtags as hashtag
            RETURN hashtag, count(*) as usage_count
            ORDER BY usage_count DESC
            LIMIT 20
            """
            hashtag_results, _ = db.cypher_query(hashtag_query)
            trending_hashtags = [result[0] for result in hashtag_results if result[1] > 5]
            
            # Get trending interests based on user interest patterns
            interest_query = """
            MATCH (profile:Profile)-[:HAS_INTEREST]->(interest:Interest)
            WHERE profile.created_at > datetime() - duration('P30D')  // Last 30 days
            UNWIND interest.names as interest_name
            RETURN interest_name, count(*) as interest_count
            ORDER BY interest_count DESC
            LIMIT 15
            """
            interest_results, _ = db.cypher_query(interest_query)
            trending_interests = [result[0].lower().replace(' ', '') for result in interest_results if result[1] > 10]
            
            return {
                'hashtags': trending_hashtags,
                'interests': trending_interests
            }
        except Exception as e:
            logger.error(f"Error getting trending data: {e}")
            return {'hashtags': [], 'interests': []}
    
    def calculate_connection_score(self, content: Dict[str, Any]) -> float:
        """Calculate connection-based score for content."""
        try:
            content_author_id = content.get('author_id') or content.get('user_id')
            if content_author_id in self.user_connections:
                return 1.0
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating connection score: {e}")
            return 0.0
    
    def calculate_interest_score(self, content: Dict[str, Any]) -> float:
        """Calculate interest relevance score for content."""
        try:
            content_hashtags = content.get('hashtags', [])
            if not content_hashtags:
                return 0.0
            
            content_tags = [tag.lower().replace('#', '') for tag in content_hashtags]
            common_interests = set(content_tags).intersection(set(self.user_interests))
            
            if len(content_hashtags) == 0:
                return 0.0
            
            return len(common_interests) / len(content_hashtags)
        except Exception as e:
            logger.error(f"Error calculating interest score: {e}")
            return 0.0
    
    def calculate_interaction_score(self, content: Dict[str, Any]) -> float:
        """Calculate interaction-based score for content."""
        try:
            content_uid = content.get('uid')
            if not content_uid:
                return 0.0
            
            score = 0.0
            if content_uid in self.user_interactions.get('liked_posts', []):
                score += 0.8
            if content_uid in self.user_interactions.get('commented_posts', []):
                score += 0.8
            
            return min(score, 1.0)  # Cap at 1.0
        except Exception as e:
            logger.error(f"Error calculating interaction score: {e}")
            return 0.0
    
    def calculate_content_type_score(self, content: Dict[str, Any]) -> float:
        """Calculate content type preference score."""
        try:
            content_type = content.get('post_type', 'text')
            user_preference = self.content_type_preferences.get(content_type, 0.3)
            base_score = self.CONTENT_TYPE_SCORES.get(content_type, 0.5)
            
            return (user_preference + base_score) / 2
        except Exception as e:
            logger.error(f"Error calculating content type score: {e}")
            return 0.5
    
    def calculate_trending_score(self, content: Dict[str, Any]) -> float:
        """Calculate trending content score."""
        try:
            content_hashtags = content.get('hashtags', [])
            if not content_hashtags:
                return 0.0
            
            content_tags = [tag.lower().replace('#', '') for tag in content_hashtags]
            
            score = 0.0
            # Check for trending hashtags
            for tag in content_tags:
                if tag in self.trending_data.get('hashtags', []):
                    score += 0.6
                if tag in self.trending_data.get('interests', []):
                    score += 0.6
            
            return min(score, 1.0)  # Cap at 1.0
        except Exception as e:
            logger.error(f"Error calculating trending score: {e}")
            return 0.0
    
    def calculate_suggestion_score(self, content: Dict[str, Any]) -> float:
        """Calculate suggestion-based score for content."""
        try:
            content_author_id = content.get('author_id') or content.get('user_id')
            author_type = content.get('author_type', 'user')
            
            # Don't suggest content from already connected users
            if content_author_id in self.user_connections:
                return 0.0
            
            # Check for interest alignment
            interest_alignment = self.calculate_interest_score(content)
            if interest_alignment > 0:
                if author_type == 'community':
                    return self.WEIGHTS['suggestion_weight_community']
                elif author_type == 'brand':
                    return self.WEIGHTS['suggestion_weight_brand']
                elif content.get('post_type') == 'product':
                    return self.WEIGHTS['suggestion_weight_product']
            
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating suggestion score: {e}")
            return 0.0
    
    def calculate_time_decay_factor(self, content: Dict[str, Any]) -> float:
        """Calculate time decay factor for content freshness."""
        try:
            created_at = content.get('created_at')
            if not created_at:
                return 0.5
            
            # Convert to datetime if necessary
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except Exception:
                    return 0.5
            elif isinstance(created_at, (float, int)):
                try:
                    created_at = datetime.fromtimestamp(created_at)
                except Exception:
                    return 0.5
            
            time_diff = datetime.now() - created_at
            hours_old = time_diff.total_seconds() / 3600
            
            # Content loses relevance over time
            if hours_old < 1:
                return 1.0
            elif hours_old < 6:
                return 0.9
            elif hours_old < 24:
                return 0.8
            elif hours_old < 72:
                return 0.6
            elif hours_old < 168:  # 1 week
                return 0.4
            else:
                return 0.2
        except Exception as e:
            logger.error(f"Error calculating time decay factor: {e}")
            return 0.5
    
    def calculate_total_score(self, content: Dict[str, Any]) -> float:
        """
        Calculate the total score for a piece of content.
        
        This implements the scoring formula from the specification:
        Post Score = (Connection Score * 0.7) + (Interest Relevance * 0.6) + 
                    (Interaction Score * 0.8) + (Content Type Preference * 0.5) + 
                    (Trending Hashtag * 0.6) + (Suggestion Weight * 0.3)
        """
        try:
            connection_score = self.calculate_connection_score(content)
            interest_score = self.calculate_interest_score(content)
            interaction_score = self.calculate_interaction_score(content)
            content_type_score = self.calculate_content_type_score(content)
            trending_score = self.calculate_trending_score(content)
            suggestion_score = self.calculate_suggestion_score(content)
            time_decay = self.calculate_time_decay_factor(content)
            
            # Apply the scoring formula from specification
            total_score = (
                (connection_score * self.WEIGHTS['connection_score']) +
                (interest_score * self.WEIGHTS['interest_relevance']) +
                (interaction_score * self.WEIGHTS['interaction_score']) +
                (content_type_score * self.WEIGHTS['content_type_preference']) +
                (trending_score * self.WEIGHTS['trending_hashtag']) +
                (suggestion_score * self.WEIGHTS['suggestion_weight_community'])
            )
            
            # Apply time decay
            total_score *= time_decay
            
            # Apply engagement boost based on content metrics
            engagement_boost = self._calculate_engagement_boost(content)
            total_score += engagement_boost
            
            return round(total_score, 3)
        except Exception as e:
            logger.error(f"Error calculating total score: {e}")
            return 0.0
    
    def _calculate_engagement_boost(self, content: Dict[str, Any]) -> float:
        """Calculate engagement boost based on content performance."""
        try:
            vibes_count = content.get('vibes_count', 0)
            comment_count = content.get('comment_count', 0)
            share_count = content.get('share_count', 0)
            
            # Normalize engagement metrics
            engagement_score = (vibes_count * 0.5) + (comment_count * 0.3) + (share_count * 0.2)
            
            # Convert to boost factor (max 0.5 boost)
            if engagement_score > 50:
                return 0.5
            elif engagement_score > 20:
                return 0.3
            elif engagement_score > 10:
                return 0.2
            elif engagement_score > 5:
                return 0.1
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Error calculating engagement boost: {e}")
            return 0.0
    
    def apply_diversity_filter(self, scored_content: List[Tuple[Dict, float]]) -> List[Tuple[Dict, float]]:
        """Apply diversity filter to prevent content saturation from few sources."""
        try:
            if not scored_content:
                return []
            
            # Track content by author to prevent over-representation
            author_count = {}
            diversified_content = []
            
            for content, score in scored_content:
                if len(diversified_content) >= 20:
                   break
                author_id = content.get('author_id') or content.get('user_id', 'unknown')
                current_count = author_count.get(author_id, 0)
                
                # Limit posts from same author (max 2 in top 20)
                # if current_count < 2 or len(diversified_content) < 20:
                if current_count < 2:
                    diversified_content.append((content, score))
                    author_count[author_id] = current_count + 1
                # else:
                #     # Apply penalty for over-representation
                #     penalty_factor = 0.5
                #     diversified_content.append((content, score * penalty_factor))
            
            return diversified_content
        except Exception as e:
            logger.error(f"Error applying diversity filter: {e}")
            return scored_content[:20]
    
    def handle_edge_cases(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle edge cases as specified in the algorithm documentation."""
        try:
            # Handle new user with no connections or interests
            if not self.user_connections and not self.user_interests:
                return self._handle_new_user_feed(content_list)
            
            # Handle low activity users
            if self._is_low_activity_user():
                return self._handle_low_activity_user_feed(content_list)
            
            return content_list
        except Exception as e:
            logger.error(f"Error handling edge cases: {e}")
            return content_list
    
    def _handle_new_user_feed(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle feed for new users with no connections or interests."""
        try:
            # Prioritize trending content and popular posts
            trending_content = []
            popular_content = []
            
            for content in content_list:
                if self.calculate_trending_score(content) > 0.3:
                    trending_content.append(content)
                elif content.get('vibes_count', 0) > 10:
                    popular_content.append(content)
            
            # Mix trending and popular content
            mixed_content = []
            max_length = min(20, len(content_list))
            
            for i in range(max_length):
                if i % 2 == 0 and trending_content:
                    mixed_content.append(trending_content.pop(0))
                elif popular_content:
                    mixed_content.append(popular_content.pop(0))
                elif trending_content:
                    mixed_content.append(trending_content.pop(0))
            
            return mixed_content[:max_length]
        except Exception as e:
            logger.error(f"Error handling new user feed: {e}")
            return content_list[:20]
    
    def _is_low_activity_user(self) -> bool:
        """Check if user has low activity patterns."""
        try:
            total_interactions = len(self.user_interactions.get('liked_posts', [])) + \
                               len(self.user_interactions.get('commented_posts', []))
            return total_interactions < 5
        except:
            return False
    
    def _handle_low_activity_user_feed(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle feed for low activity users."""
        try:
            # Boost suggestion content and trending topics
            boosted_content = []
            
            for content in content_list:
                suggestion_score = self.calculate_suggestion_score(content)
                trending_score = self.calculate_trending_score(content)
                
                if suggestion_score > 0.2 or trending_score > 0.3:
                    boosted_content.append(content)
            
            # Mix with regular content
            regular_content = [c for c in content_list if c not in boosted_content]
            
            # Return mix: 60% boosted, 40% regular
            result = []
            boost_count = int(len(boosted_content) * 0.6)
            regular_count = int(len(regular_content) * 0.4)
            
            result.extend(boosted_content[:boost_count])
            result.extend(regular_content[:regular_count])
            
            return result[:20]
        except Exception as e:
            logger.error(f"Error handling low activity user feed: {e}")
            return content_list[:20]


class FeedGenerator:
    """
    Feed generator that orchestrates the entire feed creation process.
    
    This class handles the integration of the FeedAlgorithm with the existing
    GraphQL resolver and database queries.
    """
    
    def __init__(self, user_id: str):
        """Initialize the feed generator."""
        self.user_id = user_id
        self.algorithm = FeedAlgorithm(user_id)
    
    def generate_feed(self, raw_content: List[Any], circle_type: Optional[str] = None) -> List[Any]:
        """
        Generate the personalized feed from raw content.
        
        Args:
            raw_content: Raw content from the database query
            circle_type: Optional circle type filter
            
        Returns:
            List of content sorted by algorithm score
        """
        try:
            # Convert raw content to algorithm format
            algorithm_content = self._convert_raw_content(raw_content)
            
            # Handle edge cases
            algorithm_content = self.algorithm.handle_edge_cases(algorithm_content)
            
            # Score all content
            scored_content = []
            for content in algorithm_content:
                score = self.algorithm.calculate_total_score(content)
                scored_content.append((content, score))
            
            # Apply diversity filter
            scored_content = self.algorithm.apply_diversity_filter(scored_content)
            
            # Sort by score
            scored_content.sort(key=lambda x: x[1], reverse=True)
            
            # Convert back to original format and return
            return self._convert_back_to_original_format(scored_content, raw_content)
            
        except Exception as e:
            logger.error(f"Error generating feed: {e}")
            # Fallback to original ordering
            return raw_content
    
    def _convert_raw_content(self, raw_content: List[Any]) -> List[Dict[str, Any]]:
        """Convert raw database content to algorithm-friendly format."""
        algorithm_content = []
        
        for item in raw_content:
            try:
                if isinstance(item, (list, tuple)) and len(item) >= 6:
                    post_node = item[0]
                    user_node = item[1]
                    profile_node = item[2]
                    reactions = item[3]
                    connection = item[4] if len(item) > 4 else None
                    circle = item[5] if len(item) > 5 else None
                    
                    # Extract content data
                    content_data = {
                        'uid': post_node.get('uid') if hasattr(post_node, 'get') else getattr(post_node, 'uid', None),
                        'post_type': post_node.get('post_type') if hasattr(post_node, 'get') else getattr(post_node, 'post_type', 'text'),
                        'hashtags': post_node.get('hashtags', []) if hasattr(post_node, 'get') else getattr(post_node, 'hashtags', []),
                        'created_at': post_node.get('created_at') if hasattr(post_node, 'get') else getattr(post_node, 'created_at', None),
                        'author_id': user_node.get('user_id') if hasattr(user_node, 'get') else getattr(user_node, 'user_id', None),
                        'author_type': user_node.get('user_type', 'user') if hasattr(user_node, 'get') else getattr(user_node, 'user_type', 'user'),
                        'vibes_count': len(reactions) if reactions else 0,
                        'comment_count': post_node.get('comment_count', 0) if hasattr(post_node, 'get') else getattr(post_node, 'comment_count', 0),
                        'share_count': post_node.get('share_count', 0) if hasattr(post_node, 'get') else getattr(post_node, 'share_count', 0),
                        'connection': connection,
                        'circle': circle
                    }
                    
                    algorithm_content.append(content_data)
                    
            except Exception as e:
                logger.error(f"Error converting content item: {e}")
                continue
        
        return algorithm_content
    
    def _convert_back_to_original_format(
        self,
        scored_content: List[Tuple[Dict, float]],
        original_content: List[Any]
    ) -> List[Any]:
        """
        Convert scored content back to original format with proper diversity.
        """
        try:
            if not scored_content:
                logger.warning("No scored content, using original with diversity")
                return self._apply_simple_diversity(original_content)

            # Create mapping from UID to original content (Neo4j nodes)
            uid_to_original = {}
            for item in original_content:
                try:
                    if isinstance(item, (list, tuple)) and len(item) >= 1:
                        post_node = item[0]  # Neo4j Post node
                        if hasattr(post_node, 'get'):
                            uid = post_node.get('uid')
                        else:
                            uid = getattr(post_node, 'uid', None)
                        if uid:
                            uid_to_original[uid] = item
                except Exception as e:
                    logger.debug(f"Error processing item: {e}")
                    continue

            logger.info(f"DEBUG: Created mapping for {len(uid_to_original)} UIDs from original content")

            # Match scored content with original content
            result = []
            seen_uids = set()
            matched_count = 0

            for content_data, score in scored_content:
                uid = content_data.get('uid')
                if uid and uid in uid_to_original and uid not in seen_uids:
                    result.append(uid_to_original[uid])
                    seen_uids.add(uid)
                    matched_count += 1

            logger.info(f"DEBUG: Matched {matched_count} items from algorithm output")

            # If we got good matches, use them; otherwise fallback
            if len(result) >= 10:  # If we got at least 10 good matches
                return result[:20]
            else:
                logger.warning(f"Only matched {len(result)} items, using diversity fallback")
                return self._apply_simple_diversity(original_content)

        except Exception as e:
            logger.error(f"Error in conversion: {e}")
            return self._apply_simple_diversity(original_content)

    def _apply_simple_diversity(
        self,
        original_content: List[Any]
    ) -> List[Any]:
        """
        Apply simple diversity filtering as fallback.
        """
        try:
            author_counts = {}
            result = []

            for item in original_content:
                if len(result) >= 20:
                    break
                try:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        user_node = item[1]  # Neo4j User node
                        if hasattr(user_node, 'get'):
                            author_id = user_node.get('user_id')
                        else:
                            author_id = getattr(user_node, 'user_id', None)
                        if author_id:
                            current_count = author_counts.get(author_id, 0)
                            if current_count < 2:  # Max 2 posts per author
                                result.append(item)
                                author_counts[author_id] = current_count + 1
                        else:
                            # If no author_id found, still include the post
                            result.append(item)
                except Exception as e:
                    logger.debug(f"Error in diversity filter: {e}")
                    # If there's an error processing, still try to include the item
                    if len(result) < 20:
                        result.append(item)
                    continue

            logger.info(f"Simple diversity: {len(original_content)} -> {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error in simple diversity: {e}")
            return original_content[:20]


def apply_feed_algorithm(user_id: str, raw_content: List[Any], circle_type: Optional[str] = None, 
                        preserve_pagination: bool = False, skip_diversity: bool = False) -> List[Any]:
    """
    Simplified feed algorithm that just returns the content without complex processing.
    """
    try:
        if not raw_content:
            return []
            
        logger.info(f"Simplified algorithm: processing {len(raw_content)} items for user {user_id}")
        
        # Just return the raw content without complex processing
        # This avoids the missing function errors
        return raw_content
        
    except Exception as e:
        logger.error(f"Simplified algorithm failed: {e}")
        return raw_content