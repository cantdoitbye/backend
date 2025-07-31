# post/utils/feed_config.py

"""
Feed Algorithm Configuration and Utilities

This module contains configuration settings, constants, and utility functions
for the feed algorithm. It provides centralized management of algorithm
parameters and helper functions for feed processing.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Enumeration of supported content types."""
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    PRODUCT = "product"
    COMMUNITY_POST = "community_post"
    BRAND_POST = "brand_post"


class UserCategory(Enum):
    """User categories for algorithm optimization."""
    NEW_USER = "new_user"
    LOW_ACTIVITY = "low_activity"
    REGULAR = "regular"
    HIGH_ACTIVITY = "high_activity"
    SUPER_CONNECTED = "super_connected"


@dataclass
class AlgorithmWeights:
    """Configuration class for algorithm weights."""
    connection_score: float = 0.7
    interest_relevance: float = 0.6
    interaction_score: float = 0.8
    content_type_preference: float = 0.5
    trending_hashtag: float = 0.6
    suggestion_weight_community: float = 0.5
    suggestion_weight_brand: float = 0.5
    suggestion_weight_product: float = 0.3
    time_decay_factor: float = 0.1
    diversity_factor: float = 0.3
    
    def to_dict(self) -> Dict[str, float]:
        """Convert weights to dictionary format."""
        return {
            'connection_score': self.connection_score,
            'interest_relevance': self.interest_relevance,
            'interaction_score': self.interaction_score,
            'content_type_preference': self.content_type_preference,
            'trending_hashtag': self.trending_hashtag,
            'suggestion_weight_community': self.suggestion_weight_community,
            'suggestion_weight_brand': self.suggestion_weight_brand,
            'suggestion_weight_product': self.suggestion_weight_product,
            'time_decay_factor': self.time_decay_factor,
            'diversity_factor': self.diversity_factor
        }


@dataclass
class FeedLimits:
    """Configuration for feed size and content limits."""
    max_feed_size: int = 20
    max_posts_per_author: int = 3
    max_trending_posts: int = 5
    max_suggestion_posts: int = 8
    min_engagement_threshold: int = 1
    
    # Time-based limits
    trending_days_window: int = 7
    interaction_days_window: int = 30
    content_freshness_hours: int = 168  # 1 week
    
    # User categorization thresholds
    low_activity_threshold: int = 5
    high_activity_threshold: int = 50
    super_connected_threshold: int = 100


@dataclass
class ContentTypeScores:
    """Base scores for different content types."""
    image: float = 0.8
    video: float = 0.9
    text: float = 0.6
    product: float = 0.7
    community_post: float = 0.8
    brand_post: float = 0.7
    
    def get_score(self, content_type: str) -> float:
        """Get score for a content type."""
        return getattr(self, content_type.lower(), 0.5)


class FeedAlgorithmConfig:
    """Central configuration class for the feed algorithm."""
    
    def __init__(self):
        self.weights = AlgorithmWeights()
        self.limits = FeedLimits()
        self.content_scores = ContentTypeScores()
        self.debug_mode = False
        self.performance_logging = True
        
    def update_weights(self, **kwargs):
        """Update algorithm weights dynamically."""
        for key, value in kwargs.items():
            if hasattr(self.weights, key):
                setattr(self.weights, key, value)
                logger.info(f"Updated weight {key} to {value}")
    
    def update_limits(self, **kwargs):
        """Update feed limits dynamically."""
        for key, value in kwargs.items():
            if hasattr(self.limits, key):
                setattr(self.limits, key, value)
                logger.info(f"Updated limit {key} to {value}")
    
    def get_user_category_config(self, category: UserCategory) -> Dict[str, Any]:
        """Get configuration overrides for specific user categories."""
        configs = {
            UserCategory.NEW_USER: {
                'trending_weight_boost': 0.3,
                'popular_content_boost': 0.4,
                'suggestion_boost': 0.2,
                'max_suggestion_posts': 12
            },
            UserCategory.LOW_ACTIVITY: {
                'trending_weight_boost': 0.2,
                'suggestion_boost': 0.3,
                'notification_trigger': True,
                'max_suggestion_posts': 10
            },
            UserCategory.HIGH_ACTIVITY: {
                'diversity_enforcement': True,
                'max_posts_per_author': 2,
                'content_freshness_boost': 0.2
            },
            UserCategory.SUPER_CONNECTED: {
                'diversity_enforcement': True,
                'max_posts_per_author': 1,
                'connection_weight_reduction': 0.2,
                'enable_advanced_filtering': True
            }
        }
        return configs.get(category, {})


# Global configuration instance
FEED_CONFIG = FeedAlgorithmConfig()


class FeedMetrics:
    """Class for tracking and analyzing feed performance metrics."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_generation_time(self, user_id: str, duration: float):
        """Record feed generation time."""
        if user_id not in self.metrics:
            self.metrics[user_id] = {}
        self.metrics[user_id]['generation_time'] = duration
    
    def record_algorithm_effectiveness(self, user_id: str, original_count: int, 
                                     final_count: int, diversity_score: float):
        """Record algorithm effectiveness metrics."""
        if user_id not in self.metrics:
            self.metrics[user_id] = {}
        
        self.metrics[user_id].update({
            'original_count': original_count,
            'final_count': final_count,
            'diversity_score': diversity_score,
            'effectiveness_ratio': final_count / max(original_count, 1)
        })
    
    def get_user_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get metrics for a specific user."""
        return self.metrics.get(user_id, {})
    
    def get_average_performance(self) -> Dict[str, float]:
        """Calculate average performance metrics across all users."""
        if not self.metrics:
            return {}
        
        total_users = len(self.metrics)
        avg_generation_time = sum(
            m.get('generation_time', 0) for m in self.metrics.values()
        ) / total_users
        
        avg_effectiveness = sum(
            m.get('effectiveness_ratio', 0) for m in self.metrics.values()
        ) / total_users
        
        return {
            'average_generation_time': avg_generation_time,
            'average_effectiveness': avg_effectiveness,
            'total_users_tracked': total_users
        }


# Global metrics instance
FEED_METRICS = FeedMetrics()


class HashtagProcessor:
    """Utility class for processing hashtags and interests."""
    
    @staticmethod
    def normalize_hashtag(hashtag: str) -> str:
        """Normalize hashtag format."""
        if not hashtag:
            return ""
        return hashtag.lower().replace('#', '').replace(' ', '').strip()
    
    @staticmethod
    def extract_hashtags_from_text(text: str) -> List[str]:
        """Extract hashtags from text content."""
        if not text:
            return []
        
        import re
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text)
        return [HashtagProcessor.normalize_hashtag(tag) for tag in hashtags]
    
    @staticmethod
    def calculate_hashtag_similarity(hashtags1: List[str], hashtags2: List[str]) -> float:
        """Calculate similarity between two hashtag lists."""
        if not hashtags1 or not hashtags2:
            return 0.0
        
        set1 = set(HashtagProcessor.normalize_hashtag(tag) for tag in hashtags1)
        set2 = set(HashtagProcessor.normalize_hashtag(tag) for tag in hashtags2)
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0


class ContentProcessor:
    """Utility class for processing content data."""
    
    @staticmethod
    def extract_content_features(content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key features from content for algorithm processing."""
        return {
            'has_media': bool(content.get('post_file_id')),
            'text_length': len(content.get('post_text', '')),
            'hashtag_count': len(content.get('hashtags', [])),
            'engagement_rate': ContentProcessor.calculate_engagement_rate(content),
            'content_age_hours': ContentProcessor.calculate_content_age(content),
            'is_trending': ContentProcessor.is_trending_content(content)
        }
    
    @staticmethod
    def calculate_engagement_rate(content: Dict[str, Any]) -> float:
        """Calculate engagement rate for content."""
        vibes = content.get('vibes_count', 0)
        comments = content.get('comment_count', 0)
        shares = content.get('share_count', 0)
        
        total_engagement = vibes + (comments * 2) + (shares * 3)
        return min(total_engagement / 100.0, 1.0)  # Normalize to 0-1
    
    @staticmethod
    def calculate_content_age(content: Dict[str, Any]) -> float:
        """Calculate content age in hours."""
        from datetime import datetime
        
        created_at = content.get('created_at')
        if not created_at:
            return 168.0  # Default to 1 week old
        
        try:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            age = datetime.now() - created_at.replace(tzinfo=None)
            return age.total_seconds() / 3600
        except:
            return 168.0
    
    @staticmethod
    def is_trending_content(content: Dict[str, Any]) -> bool:
        """Determine if content is trending based on engagement velocity."""
        age_hours = ContentProcessor.calculate_content_age(content)
        engagement_rate = ContentProcessor.calculate_engagement_rate(content)
        
        # Content is trending if it has high engagement relative to its age
        if age_hours < 6 and engagement_rate > 0.3:
            return True
        if age_hours < 24 and engagement_rate > 0.5:
            return True
        if age_hours < 72 and engagement_rate > 0.7:
            return True
        
        return False


class FeedValidator:
    """Utility class for validating feed algorithm results."""
    
    @staticmethod
    def validate_feed_diversity(feed_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that feed has good diversity."""
        if not feed_content:
            return {'is_diverse': False, 'diversity_score': 0.0}
        
        # Check author diversity
        authors = [content.get('author_id') for content in feed_content]
        unique_authors = len(set(authors))
        author_diversity = unique_authors / len(feed_content)
        
        # Check content type diversity
        content_types = [content.get('post_type') for content in feed_content]
        unique_types = len(set(content_types))
        type_diversity = unique_types / min(len(ContentType), len(feed_content))
        
        # Check temporal diversity
        creation_times = [content.get('created_at') for content in feed_content if content.get('created_at')]
        time_diversity = FeedValidator._calculate_temporal_diversity(creation_times)
        
        overall_diversity = (author_diversity + type_diversity + time_diversity) / 3
        
        return {
            'is_diverse': overall_diversity > 0.5,
            'diversity_score': overall_diversity,
            'author_diversity': author_diversity,
            'type_diversity': type_diversity,
            'time_diversity': time_diversity,
            'unique_authors': unique_authors,
            'unique_content_types': unique_types
        }
    
    @staticmethod
    def _calculate_temporal_diversity(timestamps: List[Any]) -> float:
        """Calculate temporal diversity of content."""
        if len(timestamps) < 2:
            return 0.5
        
        try:
            from datetime import datetime
            
            # Convert to datetime objects
            datetimes = []
            for ts in timestamps:
                if isinstance(ts, str):
                    try:
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        datetimes.append(dt)
                    except:
                        continue
                elif hasattr(ts, 'replace'):  # Already datetime
                    datetimes.append(ts)
            
            if len(datetimes) < 2:
                return 0.5
            
            # Calculate time span coverage
            datetimes.sort()
            total_span = (datetimes[-1] - datetimes[0]).total_seconds()
            
            # Good diversity if content spans more than 6 hours
            return min(total_span / (6 * 3600), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating temporal diversity: {e}")
            return 0.5
    
    @staticmethod
    def validate_algorithm_requirements(user_data: Dict[str, Any]) -> List[str]:
        """Validate that all algorithm requirements are met."""
        warnings = []
        
        if not user_data.get('user_connections'):
            warnings.append("No user connections found - algorithm may prioritize trending content")
        
        if not user_data.get('user_interests'):
            warnings.append("No user interests found - interest-based scoring will be minimal")
        
        if not user_data.get('user_interactions'):
            warnings.append("No interaction history found - interaction scoring will be minimal")
        
        return warnings


# Export key components for easy importing
__all__ = [
    'FEED_CONFIG',
    'FEED_METRICS',
    'ContentType',
    'UserCategory',
    'AlgorithmWeights',
    'FeedLimits',
    'HashtagProcessor',
    'ContentProcessor',
    'FeedValidator'
]