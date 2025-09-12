from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, F, Count, Avg, Max, Min, Sum, Case, When, Value, FloatField
from django.db.models.functions import Coalesce
from .models import UserActivity, UserEngagementScore, ActivityType
from feed_algorithm.models import FeedComposition

User = get_user_model()

class ActivityBasedScorer:
    """
    Enhances feed algorithm with activity-based scoring.
    """
    
    def __init__(self, user):
        self.user = user
        self.engagement_score = self._get_engagement_score()
        self.recent_activities = self._get_recent_activities()
    
    def _get_engagement_score(self) -> float:
        """Get the user's engagement score."""
        try:
            return UserEngagementScore.objects.get(user=self.user).engagement_score
        except UserEngagementScore.DoesNotExist:
            return 0.0
    
    def _get_recent_activities(self, days: int = 30):
        """Get recent user activities with their frequencies."""
        month_ago = timezone.now() - timezone.timedelta(days=days)
        
        return (
            UserActivity.objects
            .filter(user=self.user, created_at__gte=month_ago)
            .values('activity_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
    
    def get_content_affinity_scores(self, content_items):
        """
        Calculate affinity scores for content items based on user activities.
        
        Args:
            content_items: QuerySet of content items to score
            
        Returns:
            Dict of {content_id: affinity_score}
        """
        if not content_items.exists():
            return {}
            
        # Get content types and IDs
        content_type = ContentType.objects.get_for_model(content_items.model)
        content_ids = list(content_items.values_list('id', flat=True))
        
        # Get user's activities on these content items
        user_activities = (
            UserActivity.objects
            .filter(
                user=self.user,
                content_type=content_type,
                object_id__in=content_ids
            )
            .values('object_id', 'activity_type')
            .annotate(count=Count('id'))
        )
        
        # Calculate scores based on activity types
        activity_weights = {
            ActivityType.VIBE: 1.0,
            ActivityType.COMMENT: 1.5,
            ActivityType.SHARE: 2.0,
            ActivityType.SAVE: 1.8,
            ActivityType.MEDIA_EXPAND: 0.8,
        }
        
        scores = {}
        
        # Initialize scores
        for item_id in content_ids:
            scores[item_id] = 0.0
        
        # Apply activity-based scoring
        for activity in user_activities:
            item_id = activity['object_id']
            activity_type = activity['activity_type']
            count = activity['count']
            
            # Skip if we don't have a weight for this activity type
            if activity_type not in activity_weights:
                continue
                
            # Apply the weight and count to the score
            scores[item_id] += activity_weights[activity_type] * count
        
        return scores
    
    def adjust_feed_composition(self, feed_composition: Dict[str, float]) -> Dict[str, float]:
        """
        Adjust feed composition based on user engagement level.
        
        Args:
            feed_composition: Current feed composition ratios
            
        Returns:
            Adjusted feed composition
        """
        if not feed_composition:
            return feed_composition
            
        # Make a copy to avoid modifying the original
        adjusted = feed_composition.copy()
        
        # Adjust based on engagement level
        engagement_level = self.engagement_score / 100.0  # Convert to 0-1 range
        
        # More engaged users get more personalized content
        if engagement_level > 0.7:  # Highly engaged
            adjusted['interest_based'] = min(0.6, adjusted.get('interest_based', 0.0) * 1.3)
            adjusted['personal_connections'] = min(0.7, adjusted.get('personal_connections', 0.0) * 1.2)
            adjusted['trending_content'] = max(0.05, adjusted.get('trending_content', 0.0) * 0.8)
            
        # Less engaged users get more trending/discovery content
        elif engagement_level < 0.3:  # Low engagement
            adjusted['trending_content'] = min(0.4, adjusted.get('trending_content', 0.0) * 1.5)
            adjusted['discovery_content'] = min(0.4, adjusted.get('discovery_content', 0.0) * 1.5)
            adjusted['interest_based'] = max(0.1, adjusted.get('interest_based', 0.0) * 0.7)
        
        # Normalize to ensure the sum is 1.0
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v/total for k, v in adjusted.items()}
        
        return adjusted
    
    def get_activity_based_boost_factors(self, content_items):
        """
        Calculate boost factors for content items based on recent activities.
        
        Args:
            content_items: QuerySet of content items to boost
            
        Returns:
            Dict of {content_id: boost_factor}
        """
        if not content_items.exists():
            return {}
            
        # Get content types and IDs
        content_type = ContentType.objects.get_for_model(content_items.model)
        content_ids = list(content_items.values_list('id', flat=True))
        
        # Get recent interactions with these content items
        recent_interactions = (
            UserActivity.objects
            .filter(
                user=self.user,
                content_type=content_type,
                object_id__in=content_ids,
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            )
            .values('object_id')
            .annotate(
                last_interaction=Max('created_at'),
                interaction_count=Count('id')
            )
        )
        
        # Calculate boost factors
        boosts = {}
        now = timezone.now()
        
        for interaction in recent_interactions:
            item_id = interaction['object_id']
            days_since = (now - interaction['last_interaction']).days
            
            # Higher boost for more recent and frequent interactions
            recency_factor = max(0.1, 1.0 - (days_since / 7.0))  # Linear decay over 7 days
            frequency_factor = min(2.0, 1.0 + (interaction['interaction_count'] * 0.1))  # Cap at 2x
            
            boosts[item_id] = recency_factor * frequency_factor
        
        return boosts
