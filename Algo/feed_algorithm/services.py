"""
Core services for the Feed Algorithm system.

Contains the main business logic for feed generation, composition management,
and content ranking algorithms.
"""

from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, F, Count, Avg, Sum
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from typing import List, Dict, Any, Optional, Tuple
import random
import structlog
import time

from .models import (
    UserProfile, Connection, ContentItem, Post, Community, Product,
    Engagement, Interest, TrendingMetric, CreatorMetric,
    FeedComposition, FeedDebugEvent, UserInterestScore
)
from scoring_engines.services import ScoringEngineRegistry
from caching.utils import FeedCacheManager

logger = structlog.get_logger(__name__)


class FeedGenerationService:
    """
    Core service for generating personalized user feeds.
    
    Implements the dynamic feed composition algorithm with configurable
    ratios and multiple scoring engines.
    """
    
    def __init__(self, user_profile: UserProfile):
        """
        Initialize feed generation service for a specific user.
        
        Args:
            user_profile: UserProfile instance for the target user
        """
        self.user_profile = user_profile
        self.user = user_profile.user
        self.cache_manager = FeedCacheManager()
        self.config = settings.FEED_ALGORITHM_CONFIG
        
        # Initialize scoring engines
        self.scoring_registry = ScoringEngineRegistry()
        
        logger.info(
            "Feed generation service initialized",
            user_id=self.user.id,
            username=self.user.username
        )
    
    def generate_feed(self, size: int = 20) -> List[ContentItem]:
        """
        Generate a personalized feed for the user.
        
        Args:
            size: Number of items to return
        
        Returns:
            List of ContentItem instances with metadata
        """
        start_time = time.time()
        
        try:
            # Get user's feed composition
            composition = self.user_profile.get_feed_composition()
            
            logger.info(
                "Starting feed generation",
                user_id=self.user.id,
                feed_size=size,
                composition=composition
            )
            
            # Generate feed with user's composition
            feed_items = self.generate_feed_with_composition(
                composition=composition,
                size=size
            )
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Feed generation completed",
                user_id=self.user.id,
                feed_size=len(feed_items),
                execution_time_seconds=execution_time
            )
            
            return feed_items
            
        except Exception as e:
            logger.error(
                "Feed generation failed",
                user_id=self.user.id,
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )
            raise
    
    def generate_feed_with_composition(
        self, 
        composition: Dict[str, float], 
        size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate feed with specific composition ratios.
        
        Args:
            composition: Dictionary of factor names to percentages
            size: Total number of items to return
        
        Returns:
            List of feed items with metadata
        """
        feed_items = []
        
        # Calculate item counts for each factor
        factor_counts = self._calculate_factor_counts(composition, size)
        
        logger.debug(
            "Feed composition breakdown",
            user_id=self.user.id,
            factor_counts=factor_counts,
            total_size=size
        )
        
        # Generate content for each factor
        for factor_name, count in factor_counts.items():
            if count > 0:
                factor_items = self._generate_factor_content(
                    factor_name, count
                )
                feed_items.extend(factor_items)
        
        # Shuffle and limit to requested size
        random.shuffle(feed_items)
        feed_items = feed_items[:size]
        
        # Add final ranking scores
        feed_items = self._apply_final_ranking(feed_items)
        
        return feed_items
    
    def _calculate_factor_counts(
        self, 
        composition: Dict[str, float], 
        total_size: int
    ) -> Dict[str, int]:
        """
        Calculate how many items each factor should contribute.
        
        Args:
            composition: Factor percentages
            total_size: Total items needed
        
        Returns:
            Dictionary mapping factors to item counts
        """
        factor_counts = {}
        remaining_size = total_size
        
        # Sort factors by percentage (largest first)
        sorted_factors = sorted(
            composition.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for factor_name, percentage in sorted_factors[:-1]:
            count = int(total_size * percentage)
            factor_counts[factor_name] = count
            remaining_size -= count
        
        # Assign remaining items to last factor
        if sorted_factors:
            last_factor = sorted_factors[-1][0]
            factor_counts[last_factor] = remaining_size
        
        return factor_counts
    
    def _generate_factor_content(
        self, 
        factor_name: str, 
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate content items for a specific feed factor.
        
        Args:
            factor_name: Name of the feed factor
            count: Number of items to generate
        
        Returns:
            List of content items with metadata
        """
        method_map = {
            'personal_connections': self._get_personal_connections_content,
            'interest_based': self._get_interest_based_content,
            'trending_content': self._get_trending_content,
            'discovery_content': self._get_discovery_content,
            'community_content': self._get_community_content,
            'product_content': self._get_product_content,
        }
        
        method = method_map.get(factor_name)
        if not method:
            logger.warning(
                "Unknown feed factor",
                user_id=self.user.id,
                factor_name=factor_name
            )
            return []
        
        try:
            items = method(count)
            logger.debug(
                "Factor content generated",
                user_id=self.user.id,
                factor_name=factor_name,
                requested_count=count,
                actual_count=len(items)
            )
            return items
        except Exception as e:
            logger.error(
                "Factor content generation failed",
                user_id=self.user.id,
                factor_name=factor_name,
                error=str(e)
            )
            return []
    
    def _get_personal_connections_content(self, count: int) -> List[Dict[str, Any]]:
        """
        Get content from user's personal connections with circle weighting.
        """
        # Get user's connections by circle
        connections = Connection.objects.filter(
            from_user=self.user,
            is_active=True
        ).select_related('to_user')
        
        if not connections.exists():
            return []
        
        # Get content from connected users
        connected_user_ids = list(connections.values_list('to_user_id', flat=True))
        
        content_items = ContentItem.objects.filter(
            creator_id__in=connected_user_ids,
            is_active=True,
            published_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_subclasses().order_by('-published_at')[:count * 3]  # Get extra for scoring
        
        # Score items with personal connections scoring engine
        scored_items = []
        for item in content_items:
            # Get connection info
            connection = connections.filter(to_user=item.creator).first()
            if connection:
                score = self.scoring_registry.score_personal_connections(
                    item, self.user_profile, connection
                )
                scored_items.append({
                    'item': item,
                    'score': score,
                    'reason': f"From {connection.get_circle_type_display()} circle",
                    'factor': 'personal_connections'
                })
        
        # Sort by score and return top items
        scored_items.sort(key=lambda x: x['score'], reverse=True)
        return scored_items[:count]
    
    def _get_interest_based_content(self, count: int) -> List[Dict[str, Any]]:
        """
        Get content based on user's interests (explicit and inferred).
        """
        # Get user's interests
        explicit_interests = list(
            self.user_profile.interests_explicit.values_list('id', flat=True)
        )
        inferred_interests = list(
            UserInterestScore.objects.filter(
                user_profile=self.user_profile,
                score__gte=0.3  # Minimum threshold
            ).values_list('interest_id', flat=True)
        )
        
        all_interest_ids = list(set(explicit_interests + inferred_interests))
        
        if not all_interest_ids:
            return []
        
        # Find content tagged with user's interests
        # This is a simplified approach - in production you'd have more sophisticated matching
        interest_names = Interest.objects.filter(
            id__in=all_interest_ids
        ).values_list('name', flat=True)
        
        content_items = ContentItem.objects.filter(
            is_active=True,
            published_at__gte=timezone.now() - timezone.timedelta(days=14)
        ).select_subclasses()[:count * 3]
        
        # Score items with interest-based scoring
        scored_items = []
        for item in content_items:
            score = self.scoring_registry.score_interest_based(
                item, self.user_profile, all_interest_ids
            )
            if score > 0:
                scored_items.append({
                    'item': item,
                    'score': score,
                    'reason': "Matches your interests",
                    'factor': 'interest_based'
                })
        
        # Sort by score and return top items
        scored_items.sort(key=lambda x: x['score'], reverse=True)
        return scored_items[:count]
    
    def _get_trending_content(self, count: int) -> List[Dict[str, Any]]:
        """
        Get currently trending content.
        """
        # Get trending content from the last 24 hours
        trending_window = timezone.now() - timezone.timedelta(
            hours=self.config['TRENDING_WINDOW_HOURS']
        )
        
        trending_items = TrendingMetric.objects.filter(
            window_end__gte=trending_window
        ).select_related('content_object').order_by('-trending_score')[:count * 2]
        
        scored_items = []
        for trending_metric in trending_items:
            if trending_metric.content_object and trending_metric.content_object.is_active:
                score = self.scoring_registry.score_trending(
                    trending_metric.content_object, self.user_profile, trending_metric
                )
                scored_items.append({
                    'item': trending_metric.content_object,
                    'score': score,
                    'reason': f"Trending (score: {trending_metric.trending_score:.1f})",
                    'factor': 'trending_content'
                })
        
        # Apply user's trending boost
        for item in scored_items:
            item['score'] *= self.user_profile.trending_boost
        
        scored_items.sort(key=lambda x: x['score'], reverse=True)
        return scored_items[:count]
    
    def _get_discovery_content(self, count: int) -> List[Dict[str, Any]]:
        """
        Get discovery content for serendipity and exploration.
        """
        if not self.user_profile.allow_discovery:
            return []
        
        # Get a sample of diverse content the user hasn't seen
        # Exclude content from user's connections and interests for true discovery
        
        # Get connected user IDs to exclude
        connected_user_ids = list(
            Connection.objects.filter(
                from_user=self.user,
                is_active=True
            ).values_list('to_user_id', flat=True)
        )
        connected_user_ids.append(self.user.id)  # Exclude own content
        
        # Get a diverse sample of content
        discovery_pool = ContentItem.objects.filter(
            is_active=True,
            creator__profile__allow_discovery=True,  # Respect creator privacy
            published_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).exclude(
            creator_id__in=connected_user_ids
        ).select_subclasses().order_by('?')[:self.config['DISCOVERY_SAMPLE_SIZE']]
        
        scored_items = []
        for item in discovery_pool:
            score = self.scoring_registry.score_discovery(
                item, self.user_profile
            )
            scored_items.append({
                'item': item,
                'score': score,
                'reason': "Discovery content",
                'factor': 'discovery_content'
            })
        
        # Apply user's discovery boost
        for item in scored_items:
            item['score'] *= self.user_profile.discovery_boost
        
        scored_items.sort(key=lambda x: x['score'], reverse=True)
        return scored_items[:count]
    
    def _get_community_content(self, count: int) -> List[Dict[str, Any]]:
        """
        Get content from communities.
        """
        # Get popular communities
        communities = Community.objects.filter(
            is_active=True,
            is_public=True
        ).order_by('-member_count', '-engagement_score')[:count * 2]
        
        scored_items = []
        for community in communities:
            score = community.engagement_score * community.quality_score
            scored_items.append({
                'item': community,
                'score': score,
                'reason': f"Popular community ({community.member_count} members)",
                'factor': 'community_content'
            })
        
        scored_items.sort(key=lambda x: x['score'], reverse=True)
        return scored_items[:count]
    
    def _get_product_content(self, count: int) -> List[Dict[str, Any]]:
        """
        Get product/marketplace content.
        """
        # Get featured and high-rated products
        products = Product.objects.filter(
            is_active=True,
            availability__in=['available', 'limited']
        ).order_by('-is_featured', '-rating_average', '-engagement_score')[:count * 2]
        
        scored_items = []
        for product in products:
            # Score based on rating, engagement, and featured status
            score = (
                product.rating_average * 20 +  # Max 100 points for 5-star rating
                product.engagement_score * 10 +
                (50 if product.is_featured else 0)
            )
            
            reason = f"Rating: {product.rating_average:.1f}/5"
            if product.is_featured:
                reason += " (Featured)"
            
            scored_items.append({
                'item': product,
                'score': score,
                'reason': reason,
                'factor': 'product_content'
            })
        
        scored_items.sort(key=lambda x: x['score'], reverse=True)
        return scored_items[:count]
    
    def _apply_final_ranking(self, feed_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply final ranking and diversity algorithms to the feed.
        
        Args:
            feed_items: List of feed items with scores
        
        Returns:
            Reranked feed items
        """
        # Apply diversity to avoid too much content from same creator or type
        diversified_items = self._apply_diversity_filter(feed_items)
        
        # Final sort by score
        diversified_items.sort(key=lambda x: x['score'], reverse=True)
        
        return diversified_items
    
    def _apply_diversity_filter(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply diversity filtering to ensure varied content.
        
        Args:
            items: Feed items to diversify
        
        Returns:
            Diversified feed items
        """
        # Track content diversity
        creator_counts = {}
        type_counts = {}
        diversified_items = []
        
        for item_data in items:
            item = item_data['item']
            creator_id = item.creator_id
            content_type = item.__class__.__name__
            
            # Limit content per creator (max 3 items)
            creator_count = creator_counts.get(creator_id, 0)
            if creator_count >= 3:
                continue
            
            # Limit content per type (max 40% of feed)
            type_count = type_counts.get(content_type, 0)
            max_type_count = len(items) * 0.4
            if type_count >= max_type_count:
                continue
            
            # Add item to diversified feed
            diversified_items.append(item_data)
            creator_counts[creator_id] = creator_count + 1
            type_counts[content_type] = type_count + 1
        
        return diversified_items


class FeedCompositionService:
    """
    Service for managing feed composition configurations and A/B testing.
    """
    
    @staticmethod
    def get_user_composition(user: User) -> Dict[str, float]:
        """
        Get the effective feed composition for a user.
        
        Args:
            user: User instance
        
        Returns:
            Dictionary of composition percentages
        """
        try:
            profile = UserProfile.objects.get(user=user)
            return profile.get_feed_composition()
        except UserProfile.DoesNotExist:
            return settings.FEED_ALGORITHM_CONFIG['DEFAULT_COMPOSITION']
    
    @staticmethod
    def update_user_composition(
        user: User, 
        composition: Dict[str, float]
    ) -> UserProfile:
        """
        Update a user's feed composition preferences.
        
        Args:
            user: User instance
            composition: New composition ratios
        
        Returns:
            Updated UserProfile
        """
        # Validate composition
        total = sum(composition.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError("Composition ratios must sum to 1.0")
        
        # Update profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.feed_composition = composition
        profile.save()
        
        # Clear cache
        cache_manager = FeedCacheManager()
        cache_manager.invalidate_user_feed(user.id)
        
        # Log the change
        FeedDebugEvent.objects.create(
            user=user,
            event_type='composition_update',
            event_data={
                'old_composition': profile.get_feed_composition(),
                'new_composition': composition,
                'source': 'manual_update'
            }
        )
        
        logger.info(
            "User feed composition updated",
            user_id=user.id,
            new_composition=composition
        )
        
        return profile
    
    @staticmethod
    def create_ab_test_composition(
        name: str,
        description: str,
        composition: Dict[str, float],
        experiment_group: str
    ) -> FeedComposition:
        """
        Create a new feed composition for A/B testing.
        
        Args:
            name: Composition name
            description: Description
            composition: Composition ratios
            experiment_group: A/B test group identifier
        
        Returns:
            Created FeedComposition
        """
        # Validate composition
        total = sum(composition.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError("Composition ratios must sum to 1.0")
        
        feed_composition = FeedComposition.objects.create(
            name=name,
            description=description,
            composition_ratios=composition,
            experiment_group=experiment_group,
            is_active=True
        )
        
        logger.info(
            "A/B test composition created",
            composition_id=feed_composition.id,
            name=name,
            experiment_group=experiment_group
        )
        
        return feed_composition
    
    @staticmethod
    def assign_user_to_ab_test(
        user: User, 
        experiment_group: str
    ) -> Optional[FeedComposition]:
        """
        Assign a user to an A/B test group.
        
        Args:
            user: User to assign
            experiment_group: Experiment group name
        
        Returns:
            Assigned FeedComposition or None
        """
        # Check if user opts into A/B testing
        profile, created = UserProfile.objects.get_or_create(user=user)
        if not profile.enable_ab_testing:
            return None
        
        # Find active composition for the experiment group
        composition = FeedComposition.objects.filter(
            experiment_group=experiment_group,
            is_active=True
        ).first()
        
        if not composition:
            logger.warning(
                "No active composition found for experiment group",
                experiment_group=experiment_group
            )
            return None
        
        # Update user profile with test composition
        profile.feed_composition = composition.composition_ratios
        profile.save()
        
        # Clear cache
        cache_manager = FeedCacheManager()
        cache_manager.invalidate_user_feed(user.id)
        
        # Log assignment
        FeedDebugEvent.objects.create(
            user=user,
            event_type='ab_test_assignment',
            event_data={
                'experiment_group': experiment_group,
                'composition_id': composition.id,
                'composition': composition.composition_ratios
            }
        )
        
        logger.info(
            "User assigned to A/B test group",
            user_id=user.id,
            experiment_group=experiment_group,
            composition_id=composition.id
        )
        
        return composition
