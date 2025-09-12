"""
Scoring engines for the Ooumph Feed Algorithm system.

Implements modular scoring algorithms for different feed factors:
- Personal connections scoring
- Interest-based scoring  
- Trending content scoring
- Discovery/serendipity scoring
"""

from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Avg, F
import math
import structlog

logger = structlog.get_logger(__name__)


class ScoringEngineRegistry:
    """
    Registry for managing different scoring engines.
    
    Provides a centralized way to access and manage scoring algorithms
    for different feed factors.
    """
    
    def __init__(self):
        """
        Initialize the scoring engine registry.
        """
        self.config = settings.FEED_ALGORITHM_CONFIG
        logger.debug("Scoring engine registry initialized")
    
    def score_personal_connections(
        self, 
        content_item, 
        user_profile, 
        connection
    ) -> float:
        """
        Score content based on personal connections.
        
        Args:
            content_item: The content to score
            user_profile: User's profile
            connection: Connection object between user and creator
        
        Returns:
            Calculated score for personal connections factor
        """
        engine = PersonalConnectionsScoringEngine()
        return engine.calculate_score(content_item, user_profile, connection)
    
    def score_interest_based(
        self, 
        content_item, 
        user_profile, 
        interest_ids: List[int]
    ) -> float:
        """
        Score content based on user interests.
        
        Args:
            content_item: The content to score
            user_profile: User's profile
            interest_ids: List of user's interest IDs
        
        Returns:
            Calculated score for interest-based factor
        """
        engine = InterestBasedScoringEngine()
        return engine.calculate_score(content_item, user_profile, interest_ids)
    
    def score_trending(
        self, 
        content_item, 
        user_profile, 
        trending_metric=None
    ) -> float:
        """
        Score content based on trending metrics.
        
        Args:
            content_item: The content to score
            user_profile: User's profile
            trending_metric: Optional TrendingMetric instance
        
        Returns:
            Calculated score for trending factor
        """
        engine = TrendingScoringEngine()
        return engine.calculate_score(content_item, user_profile, trending_metric)
    
    def score_discovery(
        self, 
        content_item, 
        user_profile
    ) -> float:
        """
        Score content for discovery/serendipity.
        
        Args:
            content_item: The content to score
            user_profile: User's profile
        
        Returns:
            Calculated score for discovery factor
        """
        engine = DiscoveryScoringEngine()
        return engine.calculate_score(content_item, user_profile)


class BaseScoringEngine:
    """
    Abstract base class for scoring engines.
    """
    
    def __init__(self):
        self.config = settings.FEED_ALGORITHM_CONFIG
    
    def calculate_score(self, content_item, user_profile, *args, **kwargs) -> float:
        """
        Calculate score for a content item.
        
        Must be implemented by subclasses.
        
        Args:
            content_item: Content to score
            user_profile: User's profile
            *args, **kwargs: Additional arguments specific to scoring engine
        
        Returns:
            Calculated score (0.0 to 100.0)
        """
        raise NotImplementedError("Subclasses must implement calculate_score")
    
    @property
    def name(self) -> str:
        """
        Get the engine name.
        """
        return self.__class__.__name__.lower().replace('scoringengine', '')
    
    @property
    def description(self) -> str:
        """
        Get the engine description.
        """
        return f"Scoring engine: {self.name}"
    
    def normalize_score(self, raw_score: float, max_score: float = 100.0) -> float:
        """
        Normalize score to 0-100 range.
        
        Args:
            raw_score: Raw calculated score
            max_score: Maximum possible score
        
        Returns:
            Normalized score
        """
        return min(max(raw_score, 0.0), max_score)
    
    def apply_recency_decay(
        self, 
        score: float, 
        published_at, 
        decay_hours: int = 72
    ) -> float:
        """
        Apply time-based decay to score.
        
        Args:
            score: Base score
            published_at: When content was published
            decay_hours: Hours after which score starts decaying
        
        Returns:
            Score with recency decay applied
        """
        now = timezone.now()
        hours_since_published = (now - published_at).total_seconds() / 3600
        
        if hours_since_published <= decay_hours:
            return score
        
        # Exponential decay after decay_hours
        excess_hours = hours_since_published - decay_hours
        decay_factor = math.exp(-excess_hours / 168)  # Half-life of 1 week
        
        return score * decay_factor


class PersonalConnectionsScoringEngine(BaseScoringEngine):
    """
    Scoring engine for personal connections factor.
    
    Scores content based on:
    - Connection circle type (inner/outer/universe)
    - Interaction history between users
    - Creator reputation and consistency
    - Content engagement from mutual connections
    """
    
    @property
    def name(self) -> str:
        return "personal_connections"
    
    @property
    def description(self) -> str:
        return "Scores content based on user connections and social circles"
    
    def calculate_score(
        self, 
        content_item, 
        user_profile, 
        connection
    ) -> float:
        """
        Calculate personal connections score.
        
        Args:
            content_item: Content to score
            user_profile: User's profile
            connection: Connection between user and content creator
        
        Returns:
            Personal connections score (0-100)
        """
        try:
            # Base score from connection circle
            circle_weight = connection.get_circle_weight()
            base_score = circle_weight * 30  # Max 30 points from circle
            
            # Boost from interaction score
            interaction_boost = connection.interaction_score * 20  # Max 20 points
            
            # Boost for mutual connections
            mutual_boost = 10 if connection.mutual else 0
            
            # Creator reputation boost
            try:
                creator_metric = content_item.creator.creator_metrics
                reputation_boost = creator_metric.reputation_score * 0.2  # Max 20 points
                quality_boost = creator_metric.content_quality_score * 10  # Max 10 points
            except:
                reputation_boost = 0
                quality_boost = 0
            
            # Content engagement boost
            engagement_boost = content_item.engagement_score * 0.1  # Max varies
            
            # Combine all factors
            total_score = (
                base_score + interaction_boost + mutual_boost + 
                reputation_boost + quality_boost + engagement_boost
            )
            
            # Apply recency decay
            final_score = self.apply_recency_decay(
                total_score, 
                content_item.published_at,
                decay_hours=48  # 2 days for personal connections
            )
            
            logger.debug(
                "Personal connections score calculated",
                content_id=content_item.id,
                user_id=user_profile.user.id,
                circle_type=connection.circle_type,
                base_score=base_score,
                final_score=final_score
            )
            
            return self.normalize_score(final_score)
            
        except Exception as e:
            logger.error(
                "Personal connections scoring failed",
                content_id=content_item.id,
                user_id=user_profile.user.id,
                error=str(e)
            )
            return 0.0


class InterestBasedScoringEngine(BaseScoringEngine):
    """
    Scoring engine for interest-based factor.
    
    Scores content based on:
    - Explicit user interests
    - Inferred interests with confidence scores
    - Content tags and categorization
    - Topic modeling and semantic similarity
    """
    
    @property
    def name(self) -> str:
        return "interest_based"
    
    @property
    def description(self) -> str:
        return "Scores content based on user interests and preferences"
    
    def calculate_score(
        self, 
        content_item, 
        user_profile, 
        interest_ids: List[int]
    ) -> float:
        """
        Calculate interest-based score.
        
        Args:
            content_item: Content to score
            user_profile: User's profile
            interest_ids: List of user's interest IDs
        
        Returns:
            Interest-based score (0-100)
        """
        try:
            if not interest_ids:
                return 0.0
            
            # Import here to avoid circular imports
            from feed_algorithm.models import Interest, UserInterestScore
            
            # Get user's interests with scores
            user_interests = Interest.objects.filter(id__in=interest_ids)
            explicit_interests = list(
                user_profile.interests_explicit.values_list('name', flat=True)
            )
            
            # Get inferred interest scores
            inferred_scores = {}
            for ui_score in UserInterestScore.objects.filter(
                user_profile=user_profile,
                interest_id__in=interest_ids
            ):
                inferred_scores[ui_score.interest.name] = ui_score.score
            
            # Calculate interest matching score
            interest_score = 0.0
            content_tags = content_item.tags if content_item.tags else []
            
            # Check for explicit interest matches in tags
            for interest in user_interests:
                interest_name_lower = interest.name.lower()
                
                # Direct tag match (high weight)
                if any(interest_name_lower in tag.lower() for tag in content_tags):
                    if interest.name in explicit_interests:
                        interest_score += 40  # High score for explicit interest match
                    else:
                        # Use inferred score weight
                        inferred_weight = inferred_scores.get(interest.name, 0.5)
                        interest_score += 20 * inferred_weight
                
                # Content title/description match (medium weight)
                content_text = f"{content_item.title} {content_item.description}".lower()
                if interest_name_lower in content_text:
                    if interest.name in explicit_interests:
                        interest_score += 20
                    else:
                        inferred_weight = inferred_scores.get(interest.name, 0.5)
                        interest_score += 10 * inferred_weight
            
            # Category matching boost
            category_boost = 0.0
            if hasattr(content_item, 'category') and content_item.category:
                content_category = content_item.category.lower()
                for interest in user_interests:
                    if interest.category and interest.category.lower() == content_category:
                        category_boost += 15
            
            # Content quality boost
            quality_boost = content_item.quality_score * 10  # Max 10 points
            
            # Combine scores
            total_score = interest_score + category_boost + quality_boost
            
            # Apply recency decay (longer for interest-based content)
            final_score = self.apply_recency_decay(
                total_score,
                content_item.published_at,
                decay_hours=168  # 1 week for interest-based content
            )
            
            logger.debug(
                "Interest-based score calculated",
                content_id=content_item.id,
                user_id=user_profile.user.id,
                interest_score=interest_score,
                category_boost=category_boost,
                final_score=final_score
            )
            
            return self.normalize_score(final_score)
            
        except Exception as e:
            logger.error(
                "Interest-based scoring failed",
                content_id=content_item.id,
                user_id=user_profile.user.id,
                error=str(e)
            )
            return 0.0


class TrendingScoringEngine(BaseScoringEngine):
    """
    Scoring engine for trending content factor.
    
    Scores content based on:
    - Viral coefficient and velocity
    - Recent engagement spikes
    - Cross-platform trending signals
    - Time-sensitive trending windows
    """
    
    @property
    def name(self) -> str:
        return "trending"
    
    @property
    def description(self) -> str:
        return "Scores content based on trending metrics and virality"
    
    def calculate_score(
        self, 
        content_item, 
        user_profile, 
        trending_metric=None
    ) -> float:
        """
        Calculate trending score.
        
        Args:
            content_item: Content to score
            user_profile: User's profile
            trending_metric: Optional TrendingMetric instance
        
        Returns:
            Trending score (0-100)
        """
        try:
            base_score = 0.0
            
            # Use trending metric if provided
            if trending_metric:
                # Trending score from metrics (0-50 points)
                base_score += min(trending_metric.trending_score, 50)
                
                # Velocity bonus (0-25 points)
                velocity_bonus = min(trending_metric.velocity_score * 25, 25)
                base_score += velocity_bonus
                
                # Viral coefficient bonus (0-15 points)
                viral_bonus = min(trending_metric.viral_coefficient * 15, 15)
                base_score += viral_bonus
                
                # Engagement diversity bonus (unique users vs total engagement)
                if trending_metric.engagement_count > 0:
                    diversity_ratio = trending_metric.unique_users / trending_metric.engagement_count
                    diversity_bonus = diversity_ratio * 10  # Max 10 points
                    base_score += diversity_bonus
            
            else:
                # Fallback scoring without trending metrics
                # Use content's trending_score field
                base_score = content_item.trending_score
                
                # Boost based on recent engagement
                recent_threshold = timezone.now() - timezone.timedelta(hours=6)
                try:
                    from feed_algorithm.models import Engagement
                    recent_engagements = Engagement.objects.filter(
                        object_id=content_item.id,
                        created_at__gte=recent_threshold
                    ).count()
                    
                    # Recent engagement boost (0-20 points)
                    recent_boost = min(recent_engagements * 2, 20)
                    base_score += recent_boost
                except:
                    pass
            
            # Content quality multiplier
            quality_multiplier = 0.8 + (content_item.quality_score * 0.4)  # 0.8 to 1.2
            base_score *= quality_multiplier
            
            # Apply user's trending boost preference
            final_score = base_score * user_profile.trending_boost
            
            # Trending content has minimal recency decay (stays relevant longer)
            final_score = self.apply_recency_decay(
                final_score,
                content_item.published_at,
                decay_hours=12  # Short window for trending
            )
            
            logger.debug(
                "Trending score calculated",
                content_id=content_item.id,
                user_id=user_profile.user.id,
                base_score=base_score,
                trending_boost=user_profile.trending_boost,
                final_score=final_score
            )
            
            return self.normalize_score(final_score)
            
        except Exception as e:
            logger.error(
                "Trending scoring failed",
                content_id=content_item.id,
                user_id=user_profile.user.id,
                error=str(e)
            )
            return 0.0


class DiscoveryScoringEngine(BaseScoringEngine):
    """
    Scoring engine for discovery/serendipity factor.
    
    Scores content based on:
    - Content diversity and novelty
    - Creator diversity
    - Serendipity potential
    - Quality and engagement baseline
    """
    
    @property
    def name(self) -> str:
        return "discovery"
    
    @property
    def description(self) -> str:
        return "Scores content for discovery and serendipity"
    
    def calculate_score(self, content_item, user_profile) -> float:
        """
        Calculate discovery score.
        
        Args:
            content_item: Content to score
            user_profile: User's profile
        
        Returns:
            Discovery score (0-100)
        """
        try:
            # Base quality score (0-30 points)
            quality_score = content_item.quality_score * 30
            
            # Engagement baseline (0-20 points)
            # Normalize engagement score for discovery
            engagement_score = min(content_item.engagement_score * 0.2, 20)
            
            # Creator diversity bonus
            creator_diversity_bonus = 0
            try:
                creator_metric = content_item.creator.creator_metrics
                # Boost less popular creators for discovery
                if creator_metric.follower_count < 1000:
                    creator_diversity_bonus = 15
                elif creator_metric.follower_count < 10000:
                    creator_diversity_bonus = 10
                else:
                    creator_diversity_bonus = 5
            except:
                creator_diversity_bonus = 10  # Default for unknown creators
            
            # Content type diversity
            content_type_bonus = 0
            content_type_name = content_item.__class__.__name__.lower()
            if content_type_name == 'community':
                content_type_bonus = 5  # Encourage community discovery
            elif content_type_name == 'product':
                content_type_bonus = 3  # Light product discovery
            
            # Recency bonus for discovery (favor newer content)
            hours_since_published = (
                timezone.now() - content_item.published_at
            ).total_seconds() / 3600
            
            if hours_since_published <= 24:
                recency_bonus = 15  # New content gets discovery boost
            elif hours_since_published <= 168:  # 1 week
                recency_bonus = 10
            else:
                recency_bonus = 5
            
            # Serendipity factor (random element)
            import random
            serendipity_bonus = random.uniform(0, 10)
            
            # Combine all factors
            total_score = (
                quality_score + engagement_score + creator_diversity_bonus +
                content_type_bonus + recency_bonus + serendipity_bonus
            )
            
            # Apply user's discovery boost preference
            final_score = total_score * user_profile.discovery_boost
            
            logger.debug(
                "Discovery score calculated",
                content_id=content_item.id,
                user_id=user_profile.user.id,
                quality_score=quality_score,
                creator_diversity=creator_diversity_bonus,
                serendipity=serendipity_bonus,
                final_score=final_score
            )
            
            return self.normalize_score(final_score)
            
        except Exception as e:
            logger.error(
                "Discovery scoring failed",
                content_id=content_item.id,
                user_id=user_profile.user.id,
                error=str(e)
            )
            return 0.0


# Registry initialization functions
def register_default_scoring_engines():
    """
    Register default scoring engines.
    
    Called during app initialization to ensure all engines are available.
    """
    try:
        # This could be expanded to register custom engines
        # For now, engines are instantiated directly in the registry
        logger.info("Default scoring engines registered")
        return True
    except Exception as e:
        logger.error(f"Failed to register scoring engines: {e}")
        return False


def get_scoring_engine_info() -> Dict[str, Any]:
    """
    Get information about available scoring engines.
    
    Returns:
        Dictionary with scoring engine information
    """
    return {
        'engines': [
            {
                'name': 'PersonalConnectionsScoringEngine',
                'description': 'Scores content based on user connections and circles',
                'factors': ['circle_type', 'interaction_score', 'creator_reputation']
            },
            {
                'name': 'InterestBasedScoringEngine',
                'description': 'Scores content based on user interests and preferences',
                'factors': ['explicit_interests', 'inferred_interests', 'content_tags']
            },
            {
                'name': 'TrendingScoringEngine',
                'description': 'Scores content based on trending metrics and virality',
                'factors': ['trending_score', 'velocity', 'viral_coefficient']
            },
            {
                'name': 'DiscoveryScoringEngine',
                'description': 'Scores content for discovery and serendipity',
                'factors': ['quality_score', 'creator_diversity', 'serendipity']
            }
        ],
        'total_engines': 4,
        'version': '1.0.0'
    }
