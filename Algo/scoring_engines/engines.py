"""Core scoring engine implementations for the feed algorithm."""

from typing import Dict, Any, Optional, List
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from .registry import BaseScoringEngine
from .models import TrendingMetric, CreatorMetric
import math
import structlog

logger = structlog.get_logger(__name__)


class PersonalConnectionsScoring(BaseScoringEngine):
    """Scoring based on personal connections and social graph."""
    
    def get_name(self) -> str:
        return "Personal Connections"
    
    def calculate_score(self, content, user=None, context=None) -> float:
        """Score content based on creator's relationship to user."""
        if not user or not hasattr(content, 'creator'):
            return 0.0
        
        # If user is the creator, give high score
        if content.creator == user:
            return 1.0
        
        from users.models import Connection
        
        try:
            # Find connection between user and content creator
            connection = Connection.objects.get(
                from_user=user,
                to_user=content.creator,
                status='accepted'
            )
            
            # Get circle weight from config
            circle_weights = self.config.get('circle_weights', {
                'inner': 1.0,
                'outer': 0.7,
                'universe': 0.4
            })
            
            base_score = circle_weights.get(connection.circle_type, 0.0)
            
            # Adjust based on interaction frequency
            if connection.interaction_count > 0:
                # Logarithmic bonus for interaction frequency
                interaction_bonus = min(0.2, 0.05 * math.log10(connection.interaction_count + 1))
                base_score += interaction_bonus
            
            # Time decay for last interaction
            if connection.last_interaction:
                days_since = (timezone.now() - connection.last_interaction).days
                if days_since > 30:
                    time_penalty = min(0.3, 0.01 * days_since)
                    base_score = max(0.0, base_score - time_penalty)
            
            return min(1.0, base_score)
            
        except Connection.DoesNotExist:
            return 0.0
    
    def get_required_data(self) -> List[str]:
        return ['creator', 'user_connections']


class InterestBasedScoring(BaseScoringEngine):
    """Scoring based on user interests and content relevance."""
    
    def get_name(self) -> str:
        return "Interest Based"
    
    def calculate_score(self, content, user=None, context=None) -> float:
        """Score content based on user's interests."""
        if not user:
            return 0.5  # Neutral score for anonymous users
        
        from users.models import UserInterest
        from content_types.models import ContentTagging
        from django.contrib.contenttypes.models import ContentType
        
        try:
            # Get user's interests
            user_interests = UserInterest.objects.filter(
                user=user
            ).select_related('interest')
            
            if not user_interests.exists():
                return 0.3  # Low score if user has no interests
            
            # Get content tags
            content_type = ContentType.objects.get_for_model(content)
            content_tags = ContentTagging.objects.filter(
                content_type=content_type,
                object_id=content.id
            ).select_related('tag')
            
            if not content_tags.exists():
                return 0.4  # Neutral-low score for untagged content
            
            # Calculate interest overlap
            total_interest_strength = 0.0
            matched_interests = 0
            explicit_weight = self.config.get('explicit_weight', 1.0)
            inferred_weight = self.config.get('inferred_weight', 0.6)
            
            for user_interest in user_interests:
                for content_tag in content_tags:
                    # Check if tag matches interest (simplified matching)
                    if (user_interest.interest.name.lower() in content_tag.tag.name.lower() or
                        content_tag.tag.name.lower() in user_interest.interest.name.lower()):
                        
                        weight = (explicit_weight if user_interest.interest_type == 'explicit'
                                else inferred_weight)
                        
                        total_interest_strength += user_interest.strength * weight
                        matched_interests += 1
            
            if matched_interests == 0:
                # Check category/topic matching
                return self._calculate_category_match(content, user_interests)
            
            # Normalize by number of matches and user's total interests
            max_possible_score = len(user_interests) * explicit_weight
            normalized_score = min(1.0, total_interest_strength / max_possible_score)
            
            return normalized_score
            
        except Exception as e:
            logger.error(
                "Error in interest-based scoring",
                error=str(e),
                content_id=getattr(content, 'id', None),
                user_id=getattr(user, 'id', None)
            )
            return 0.3
    
    def _calculate_category_match(self, content, user_interests) -> float:
        """Calculate score based on category/topic matching."""
        # This is a simplified implementation
        # In practice, you'd use more sophisticated NLP/ML techniques
        
        content_category = getattr(content, 'category', '')
        if not content_category:
            return 0.3
        
        for interest in user_interests:
            if interest.interest.category.lower() == content_category.lower():
                return 0.6 * interest.strength
        
        return 0.2
    
    def get_required_data(self) -> List[str]:
        return ['user_interests', 'content_tags', 'content_category']


class TrendingScoring(BaseScoringEngine):
    """Scoring based on trending metrics and viral potential."""
    
    def get_name(self) -> str:
        return "Trending"
    
    def calculate_score(self, content, user=None, context=None) -> float:
        """Score content based on trending metrics."""
        try:
            # Get trending metrics for this content
            trending_metric = TrendingMetric.objects.filter(
                metric_type='content',
                metric_id=str(content.id)
            ).first()
            
            if not trending_metric:
                # Calculate basic trending score from content attributes
                return self._calculate_basic_trending(content)
            
            velocity_weight = self.config.get('velocity_weight', 0.6)
            volume_weight = self.config.get('volume_weight', 0.4)
            
            # Combine velocity and volume scores
            velocity_score = min(1.0, trending_metric.velocity_score / 100.0)
            volume_score = min(1.0, trending_metric.engagement_volume / 1000.0)
            
            final_score = (
                velocity_score * velocity_weight +
                volume_score * volume_weight
            )
            
            # Apply viral coefficient boost
            if trending_metric.viral_coefficient > 1.0:
                viral_bonus = min(0.3, (trending_metric.viral_coefficient - 1.0) * 0.1)
                final_score += viral_bonus
            
            return min(1.0, final_score)
            
        except Exception as e:
            logger.error(
                "Error in trending scoring",
                error=str(e),
                content_id=getattr(content, 'id', None)
            )
            return 0.0
    
    def _calculate_basic_trending(self, content) -> float:
        """Calculate basic trending score without stored metrics."""
        if not hasattr(content, 'created_at'):
            return 0.0
        
        # Time-based freshness
        now = timezone.now()
        age_hours = (now - content.created_at).total_seconds() / 3600
        
        # Engagement velocity (simplified)
        engagement_score = getattr(content, 'engagement_score', 0.0)
        
        if age_hours > 0:
            velocity = engagement_score / max(1.0, age_hours)
        else:
            velocity = engagement_score
        
        # Normalize velocity to 0-1 range
        return min(1.0, velocity / 10.0)
    
    def get_required_data(self) -> List[str]:
        return ['trending_metrics', 'engagement_score', 'created_at']


class EngagementScoring(BaseScoringEngine):
    """Scoring based on content engagement metrics."""
    
    def get_name(self) -> str:
        return "Engagement"
    
    def calculate_score(self, content, user=None, context=None) -> float:
        """Score content based on engagement metrics."""
        from content_types.models import Engagement
        from django.contrib.contenttypes.models import ContentType
        
        try:
            content_type = ContentType.objects.get_for_model(content)
            
            # Get engagement breakdown
            engagements = Engagement.objects.filter(
                content_type=content_type,
                object_id=content.id
            ).values('engagement_type').annotate(
                count=Count('id'),
                avg_score=Avg('score')
            )
            
            engagement_weights = self.config.get('engagement_weights', {
                'like': 1.0,
                'share': 2.0,
                'comment': 1.5,
                'save': 2.5,
                'view': 0.1
            })
            
            total_weighted_score = 0.0
            total_engagements = 0
            
            for engagement in engagements:
                eng_type = engagement['engagement_type']
                count = engagement['count']
                avg_score = engagement['avg_score'] or 1.0
                
                weight = engagement_weights.get(eng_type, 1.0)
                weighted_score = count * avg_score * weight
                
                total_weighted_score += weighted_score
                total_engagements += count
            
            if total_engagements == 0:
                return 0.0
            
            # Normalize based on content age
            if hasattr(content, 'created_at'):
                age_days = (timezone.now() - content.created_at).days + 1
                daily_engagement = total_weighted_score / age_days
            else:
                daily_engagement = total_weighted_score
            
            # Logarithmic scaling to prevent outliers
            normalized_score = math.log10(daily_engagement + 1) / math.log10(101)
            
            return min(1.0, normalized_score)
            
        except Exception as e:
            logger.error(
                "Error in engagement scoring",
                error=str(e),
                content_id=getattr(content, 'id', None)
            )
            return 0.0
    
    def get_required_data(self) -> List[str]:
        return ['engagements', 'created_at']


class QualityScoring(BaseScoringEngine):
    """Scoring based on content quality metrics."""
    
    def get_name(self) -> str:
        return "Quality"
    
    def calculate_score(self, content, user=None, context=None) -> float:
        """Score content based on quality indicators."""
        try:
            # Base quality score from content
            quality_score = getattr(content, 'quality_score', 0.5)
            
            # Creator reputation factor
            creator_reputation_weight = self.config.get('creator_reputation_weight', 0.5)
            
            if hasattr(content, 'creator'):
                creator_metrics = CreatorMetric.objects.filter(
                    creator=content.creator
                ).first()
                
                if creator_metrics:
                    reputation_score = creator_metrics.reputation_score
                    consistency_score = creator_metrics.consistency_score
                    
                    # Weighted combination
                    creator_factor = (
                        reputation_score * 0.6 +
                        consistency_score * 0.4
                    )
                    
                    # Combine content quality with creator reputation
                    final_score = (
                        quality_score * (1 - creator_reputation_weight) +
                        creator_factor * creator_reputation_weight
                    )
                else:
                    # Default creator score for new creators
                    final_score = quality_score * 0.8
            else:
                final_score = quality_score
            
            return min(1.0, max(0.0, final_score))
            
        except Exception as e:
            logger.error(
                "Error in quality scoring",
                error=str(e),
                content_id=getattr(content, 'id', None)
            )
            return 0.5
    
    def get_required_data(self) -> List[str]:
        return ['quality_score', 'creator_metrics']


class FreshnessScoring(BaseScoringEngine):
    """Scoring based on content freshness/recency."""
    
    def get_name(self) -> str:
        return "Freshness"
    
    def calculate_score(self, content, user=None, context=None) -> float:
        """Score content based on how fresh/recent it is."""
        if not hasattr(content, 'created_at'):
            return 0.5
        
        try:
            now = timezone.now()
            age = now - content.created_at
            
            # Get user's freshness preference if available
            freshness_preference = 0.5  # Default
            if user and hasattr(user, 'scoring_preferences'):
                prefs = getattr(user, 'scoring_preferences', None)
                if prefs:
                    freshness_preference = prefs.freshness_preference
            
            # Decay rate configuration
            decay_rate = self.config.get('decay_rate', 0.1)
            
            # Exponential decay based on age
            age_days = age.total_seconds() / (24 * 3600)
            
            # Adjust decay based on user preference
            adjusted_decay = decay_rate * (2 - freshness_preference)
            
            # Calculate freshness score
            freshness = math.exp(-adjusted_decay * age_days)
            
            return max(0.0, min(1.0, freshness))
            
        except Exception as e:
            logger.error(
                "Error in freshness scoring",
                error=str(e),
                content_id=getattr(content, 'id', None)
            )
            return 0.5
    
    def get_required_data(self) -> List[str]:
        return ['created_at', 'user_preferences']


class DiversityScoring(BaseScoringEngine):
    """Scoring to promote content diversity in feed."""
    
    def get_name(self) -> str:
        return "Diversity"
    
    def calculate_score(self, content, user=None, context=None) -> float:
        """Score content to promote diversity in the feed."""
        try:
            # This scoring engine works differently - it penalizes similar content
            # that appears too frequently in the user's recent feed
            
            if not context or 'recent_content' not in context:
                return 1.0  # No penalty without context
            
            recent_content = context['recent_content']
            penalty_threshold = self.config.get('penalty_threshold', 0.7)
            
            # Analyze similarity with recent content
            similarity_scores = []
            
            for recent_item in recent_content:
                similarity = self._calculate_similarity(content, recent_item)
                similarity_scores.append(similarity)
            
            # Calculate diversity penalty
            if similarity_scores:
                avg_similarity = sum(similarity_scores) / len(similarity_scores)
                max_similarity = max(similarity_scores)
                
                # Apply penalty if too similar to recent content
                if max_similarity > penalty_threshold:
                    penalty = (max_similarity - penalty_threshold) / (1.0 - penalty_threshold)
                    diversity_score = 1.0 - (penalty * 0.5)
                else:
                    diversity_score = 1.0
                
                # Additional penalty for high average similarity
                if avg_similarity > 0.5:
                    avg_penalty = (avg_similarity - 0.5) * 0.3
                    diversity_score -= avg_penalty
            else:
                diversity_score = 1.0
            
            return max(0.0, min(1.0, diversity_score))
            
        except Exception as e:
            logger.error(
                "Error in diversity scoring",
                error=str(e),
                content_id=getattr(content, 'id', None)
            )
            return 1.0
    
    def _calculate_similarity(self, content1, content2) -> float:
        """Calculate similarity between two content items."""
        # Simplified similarity calculation
        similarity = 0.0
        
        # Same creator
        if (hasattr(content1, 'creator') and hasattr(content2, 'creator') and
            content1.creator == content2.creator):
            similarity += 0.3
        
        # Same content type
        if type(content1) == type(content2):
            similarity += 0.2
        
        # Same category (if applicable)
        category1 = getattr(content1, 'category', None)
        category2 = getattr(content2, 'category', None)
        if category1 and category2 and category1 == category2:
            similarity += 0.3
        
        # Similar engagement patterns (simplified)
        eng1 = getattr(content1, 'engagement_score', 0)
        eng2 = getattr(content2, 'engagement_score', 0)
        if abs(eng1 - eng2) < 2.0:  # Similar engagement levels
            similarity += 0.2
        
        return min(1.0, similarity)
    
    def get_required_data(self) -> List[str]:
        return ['recent_content', 'content_type', 'creator', 'category']


class DiscoveryScoring(BaseScoringEngine):
    """Scoring for content discovery and serendipity."""
    
    def get_name(self) -> str:
        return "Discovery"
    
    def calculate_score(self, content, user=None, context=None) -> float:
        """Score content for discovery potential."""
        try:
            # Base score from collaborative filtering or content-based recommendations
            base_score = 0.5
            
            # Serendipity factor - boost for content outside user's normal interests
            serendipity_factor = self.config.get('serendipity_factor', 0.3)
            
            if user:
                # Check if content is from unfamiliar creators or topics
                novelty_score = self._calculate_novelty(content, user)
                
                # Boost score for novel content
                discovery_boost = novelty_score * serendipity_factor
                base_score += discovery_boost
            
            # Penalize overly popular content to promote diversity
            if hasattr(content, 'engagement_score'):
                popularity_penalty = min(0.2, content.engagement_score / 100.0)
                base_score -= popularity_penalty
            
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error(
                "Error in discovery scoring",
                error=str(e),
                content_id=getattr(content, 'id', None)
            )
            return 0.3
    
    def _calculate_novelty(self, content, user) -> float:
        """Calculate how novel this content is for the user."""
        novelty = 0.0
        
        # Novel creator
        if hasattr(content, 'creator'):
            from users.models import Connection
            from content_types.models import Engagement
            from django.contrib.contenttypes.models import ContentType
            
            # Check if user has interacted with this creator before
            has_connection = Connection.objects.filter(
                from_user=user,
                to_user=content.creator
            ).exists()
            
            if not has_connection:
                novelty += 0.4
            
            # Check previous engagements with this creator's content
            creator_content_type = ContentType.objects.get_for_model(content)
            creator_content_ids = content.__class__.objects.filter(
                creator=content.creator
            ).values_list('id', flat=True)[:20]  # Sample recent content
            
            previous_engagements = Engagement.objects.filter(
                user=user,
                content_type=creator_content_type,
                object_id__in=creator_content_ids
            ).count()
            
            if previous_engagements == 0:
                novelty += 0.3
            elif previous_engagements < 3:
                novelty += 0.1
        
        # Novel topic/category
        content_category = getattr(content, 'category', None)
        if content_category:
            from users.models import UserInterest
            
            user_categories = UserInterest.objects.filter(
                user=user
            ).values_list('interest__category', flat=True)
            
            if content_category not in user_categories:
                novelty += 0.3
        
        return min(1.0, novelty)
    
    def get_required_data(self) -> List[str]:
        return ['creator', 'user_connections', 'user_interests', 'category']