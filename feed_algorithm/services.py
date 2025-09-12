import logging
import time
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import UserProfile, FeedComposition

logger = logging.getLogger(__name__)
User = get_user_model()

class FeedGenerationService:
    """
    Service for generating personalized feeds using the algorithm.
    This acts as an adapter between the Django backend and the algorithm.
    """
    
    def __init__(self, user):
        """Initialize with the target user."""
        self.user = user
        self.profile = self._get_or_create_profile()
        self.composition = self._get_or_create_composition()
        
        # Import algorithm components
        try:
            from Algo.feed_algorithm.feed_engine import FeedAlgorithmEngine
            from Algo.feed_algorithm.services import FeedGenerationService as AlgoFeedService
            self.algorithm_available = True
        except ImportError as e:
            logger.warning("Algorithm module not available: %s", str(e))
            self.algorithm_available = False
    
    def _get_or_create_profile(self):
        """Get or create user profile."""
        return UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'feed_enabled': True,
                'content_language': 'en',
                'privacy_level': 'public'
            }
        )[0]
    
    def _get_or_create_composition(self):
        """Get or create feed composition settings."""
        return FeedComposition.objects.get_or_create(
            user=self.user,
            defaults={
                'personal_connections': 0.40,
                'interest_based': 0.25,
                'trending_content': 0.15,
                'discovery_content': 0.10,
                'community_content': 0.05,
                'product_content': 0.05
            }
        )[0]
    
    def generate_feed(self, size=20, force_refresh=False):
        """
        Generate a personalized feed for the user.
        
        Args:
            size: Number of items to include in the feed
            force_refresh: Whether to bypass cache
            
        Returns:
            Dict containing feed items and metadata
        """
        if not self.algorithm_available:
            return self._get_fallback_feed(size)
        
        try:
            # Initialize algorithm engine
            algo_engine = self._get_algorithm_engine()
            
            # Generate feed using algorithm
            feed_data = algo_engine.generate_feed(size=size, force_refresh=force_refresh)
            
            # Process and return feed data
            return self._process_feed_data(feed_data)
            
        except Exception as e:
            logger.error("Error generating feed: %s", str(e), exc_info=True)
            return self._get_fallback_feed(size)
    
    def _get_algorithm_engine(self):
        """Initialize and return the algorithm engine."""
        from Algo.feed_algorithm.feed_engine import FeedAlgorithmEngine
        
        # Ensure algorithm has necessary user data
        self._sync_user_data()
        
        # Initialize algorithm engine
        return FeedAlgorithmEngine(self.user)
    
    def _sync_user_data(self):
        """Ensure algorithm has up-to-date user data."""
        # This is where you'd sync data between your main user model
        # and the algorithm's user model if they're different
        pass
    
    def _process_feed_data(self, algo_data):
        """Convert algorithm output to our standard format."""
        return {
            'items': algo_data.get('items', []),
            'total_count': algo_data.get('total_count', 0),
            'has_more': algo_data.get('has_more', False),
            'composition': algo_data.get('composition', {}),
            'generated_at': timezone.now().isoformat()
        }
    
    def _get_fallback_feed(self, size):
        """Generate a simple fallback feed when algorithm is not available."""
        from django.contrib.contenttypes.models import ContentType
        from post.models import Post  # Adjust import based on your actual model
        
        # Get recent posts as fallback
        posts = Post.objects.filter(
            is_published=True
        ).order_by('-created_at')[:size]
        
        # Convert to feed items
        items = [
            {
                'id': f"post_{post.id}",
                'content_type': 'post',
                'content_id': str(post.id),
                'score': 0.0,
                'ranking': idx,
                'metadata': {
                    'title': getattr(post, 'title', ''),
                    'preview': getattr(post, 'preview_text', ''),
                    'author': post.author.username if hasattr(post, 'author') else ''
                },
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat()
            }
            for idx, post in enumerate(posts, 1)
        ]
        
        return {
            'items': items,
            'total_count': len(items),
            'has_more': len(items) >= size,
            'composition': self.composition.composition_dict(),
            'generated_at': timezone.now().isoformat()
        }
