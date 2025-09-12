"""
Core feed algorithm engine for Ooumph social media platform.
Implements dynamic content composition with configurable ratios.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from django.db.models import Q, F, Count
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .models import (
    UserProfile, Connection, FeedComposition, Interest, InterestCollection,
    TrendingMetric, CreatorMetric, FeedDebugEvent
)
from feed_content_types.models import ContentItem, Post, Community, Product, Engagement
from scoring_engines.models import (
    PersonalConnectionsScore, InterestBasedScore, TrendingScore, DiscoveryScore
)
from caching.models import FeedCache, ConnectionCache
from analytics.models import FeedAnalytics, AnalyticsEvent

logger = logging.getLogger('feed_algorithm')


class FeedAlgorithmEngine:
    """
    Main feed algorithm engine that orchestrates content selection and scoring.
    """
    
    def __init__(self, user: User):
        self.user = user
        self.user_profile = self._get_or_create_user_profile()
        self.feed_composition = self._get_feed_composition()
        self.feed_size = 20  # Default feed size
        
    def _get_or_create_user_profile(self) -> UserProfile:
        """Get or create user profile."""
        profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'feed_enabled': True,
                'content_language': 'en',
                'privacy_level': 'public'
            }
        )
        return profile
    
    def _get_feed_composition(self) -> FeedComposition:
        """Get user's feed composition settings."""
        composition, created = FeedComposition.objects.get_or_create(
            user=self.user,
            defaults={
                'personal_connections': 0.40,
                'interest_based': 0.25,
                'trending_content': 0.15,
                'discovery_content': 0.10,
                'community_content': 0.05,
                'product_content': 0.05
            }
        )
        return composition
    
    def generate_feed(self, size: int = 20, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Generate personalized feed for the user.
        
        Args:
            size: Number of items to include in feed
            force_refresh: Whether to bypass cache
            
        Returns:
            Dictionary containing feed items and metadata
        """
        start_time = time.time()
        
        # Check cache first
        if not force_refresh:
            cached_feed = self._get_cached_feed(size)
            if cached_feed:
                self._log_feed_event('cache_hit', {'size': size})
                return cached_feed
        
        # Generate fresh feed
        feed_items = self._generate_fresh_feed(size)
        
        # Calculate composition breakdown
        composition_breakdown = self._calculate_composition_breakdown(feed_items)
        
        # Create feed response
        feed_data = {
            'user_id': self.user.id,
            'items': feed_items,
            'composition': composition_breakdown,
            'generated_at': timezone.now().isoformat(),
            'total_items': len(feed_items),
            'cache_status': 'fresh'
        }
        
        # Cache the feed
        self._cache_feed(feed_data, size)
        
        # Log analytics
        generation_time_ms = int((time.time() - start_time) * 1000)
        self._log_feed_analytics(feed_data, generation_time_ms)
        
        self._log_feed_event('feed_generated', {
            'size': size,
            'generation_time_ms': generation_time_ms
        })
        
        return feed_data
    
    def _generate_fresh_feed(self, size: int) -> List[Dict[str, Any]]:
        """Generate fresh feed content based on composition."""
        composition = self.feed_composition.composition_dict
        feed_items = []
        
        # Calculate target counts for each content type
        targets = {
            content_type: int(size * ratio)
            for content_type, ratio in composition.items()
        }
        
        # Ensure we have enough items
        remaining = size - sum(targets.values())
        if remaining > 0:
            targets['personal_connections'] += remaining
        
        # Generate content for each category
        if targets['personal_connections'] > 0:
            personal_content = self._get_personal_connections_content(
                targets['personal_connections']
            )
            feed_items.extend(personal_content)
        
        if targets['interest_based'] > 0:
            interest_content = self._get_interest_based_content(
                targets['interest_based']
            )
            feed_items.extend(interest_content)
        
        if targets['trending_content'] > 0:
            trending_content = self._get_trending_content(
                targets['trending_content']
            )
            feed_items.extend(trending_content)
        
        if targets['discovery_content'] > 0:
            discovery_content = self._get_discovery_content(
                targets['discovery_content']
            )
            feed_items.extend(discovery_content)
        
        if targets['community_content'] > 0:
            community_content = self._get_community_content(
                targets['community_content']
            )
            feed_items.extend(community_content)
        
        if targets['product_content'] > 0:
            product_content = self._get_product_content(
                targets['product_content']
            )
            feed_items.extend(product_content)
        
        # Sort by final score and limit to requested size
        feed_items.sort(key=lambda x: x.get('score', 0), reverse=True)
        return feed_items[:size]
    
    def _get_personal_connections_content(self, count: int) -> List[Dict[str, Any]]:
        """Get content from user's personal connections."""
        connections = self._get_user_connections()
        if not connections:
            return []
        
        # Get content from connected users
        connected_user_ids = [conn.to_user_id for conn in connections]
        
        # Query posts from connections
        posts = Post.objects.filter(
            creator_id__in=connected_user_ids,
            is_active=True,
            visibility='public'
        ).select_related('creator').order_by('-created_at')[:count * 2]
        
        items = []
        for post in posts:
            connection = next(
                (c for c in connections if c.to_user_id == post.creator_id), 
                None
            )
            circle_weight = connection.circle_weight if connection else 0.4
            
            score = post.engagement_score * circle_weight
            
            items.append({
                'id': post.id,
                'type': 'post',
                'title': post.title,
                'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'creator': post.creator.username,
                'created_at': post.created_at.isoformat(),
                'engagement': {
                    'likes': post.like_count,
                    'comments': post.comment_count,
                    'shares': post.share_count
                },
                'score': score,
                'category': 'personal_connections',
                'circle_type': connection.circle_type if connection else 'universe'
            })
        
        return items[:count]
    
    def _get_interest_based_content(self, count: int) -> List[Dict[str, Any]]:
        """Get content based on user's interests."""
        user_interests = InterestCollection.objects.filter(
            user=self.user
        ).select_related('interest').order_by('-strength')[:10]
        
        if not user_interests:
            return []
        
        interest_names = [ui.interest.name.lower() for ui in user_interests]
        
        # Find content with matching tags
        posts = Post.objects.filter(
            is_active=True,
            tags__overlap=interest_names
        ).exclude(
            creator=self.user
        ).select_related('creator').order_by('-engagement_score')[:count * 2]
        
        items = []
        for post in posts:
            # Calculate interest match score
            matching_tags = set(post.tags) & set(interest_names)
            interest_strength = sum(
                ui.strength for ui in user_interests 
                if ui.interest.name.lower() in matching_tags
            )
            
            score = post.engagement_score * (0.5 + interest_strength)
            
            items.append({
                'id': post.id,
                'type': 'post',
                'title': post.title,
                'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'creator': post.creator.username,
                'created_at': post.created_at.isoformat(),
                'engagement': {
                    'likes': post.like_count,
                    'comments': post.comment_count,
                    'shares': post.share_count
                },
                'score': score,
                'category': 'interest_based',
                'matched_interests': list(matching_tags)
            })
        
        return items[:count]
    
    def _get_trending_content(self, count: int) -> List[Dict[str, Any]]:
        """Get currently trending content."""
        # Get trending metrics from last 24 hours
        trending_metrics = TrendingMetric.objects.filter(
            trending_window='24h',
            calculated_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-velocity_score')[:count * 2]
        
        items = []
        for metric in trending_metrics:
            # Get the actual content item
            if metric.content_type == 'post':
                try:
                    post = Post.objects.get(id=metric.content_id, is_active=True)
                    score = metric.velocity_score * metric.viral_coefficient
                    
                    items.append({
                        'id': post.id,
                        'type': 'post',
                        'title': post.title,
                        'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                        'creator': post.creator.username,
                        'created_at': post.created_at.isoformat(),
                        'engagement': {
                            'likes': post.like_count,
                            'comments': post.comment_count,
                            'shares': post.share_count
                        },
                        'score': score,
                        'category': 'trending',
                        'trending_metrics': {
                            'velocity': metric.velocity_score,
                            'viral_coefficient': metric.viral_coefficient
                        }
                    })
                except Post.DoesNotExist:
                    continue
        
        return items[:count]
    
    def _get_discovery_content(self, count: int) -> List[Dict[str, Any]]:
        """Get discovery content for serendipity."""
        # Get random high-quality content from creators user doesn't follow
        following_ids = Connection.objects.filter(
            from_user=self.user
        ).values_list('to_user_id', flat=True)
        
        posts = Post.objects.filter(
            is_active=True,
            quality_score__gte=0.7  # High quality threshold
        ).exclude(
            creator_id__in=following_ids
        ).exclude(
            creator=self.user
        ).select_related('creator').order_by('?')[:count * 2]
        
        items = []
        for post in posts:
            score = post.quality_score * 0.8  # Discovery penalty
            
            items.append({
                'id': post.id,
                'type': 'post',
                'title': post.title,
                'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'creator': post.creator.username,
                'created_at': post.created_at.isoformat(),
                'engagement': {
                    'likes': post.like_count,
                    'comments': post.comment_count,
                    'shares': post.share_count
                },
                'score': score,
                'category': 'discovery',
                'reason': 'serendipity'
            })
        
        return items[:count]
    
    def _get_community_content(self, count: int) -> List[Dict[str, Any]]:
        """Get content from user's communities."""
        # Get user's community memberships
        from feed_content_types.models import CommunityMembership
        
        memberships = CommunityMembership.objects.filter(
            user=self.user,
            status='active'
        ).select_related('community')[:10]
        
        if not memberships:
            return []
        
        community_ids = [m.community.id for m in memberships]
        
        # Get recent posts from these communities (assuming posts can be linked to communities)
        posts = Post.objects.filter(
            is_active=True,
            tags__overlap=[f'community_{cid}' for cid in community_ids]
        ).select_related('creator').order_by('-created_at')[:count * 2]
        
        items = []
        for post in posts:
            score = post.engagement_score * 0.9  # Community boost
            
            items.append({
                'id': post.id,
                'type': 'post',
                'title': post.title,
                'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'creator': post.creator.username,
                'created_at': post.created_at.isoformat(),
                'engagement': {
                    'likes': post.like_count,
                    'comments': post.comment_count,
                    'shares': post.share_count
                },
                'score': score,
                'category': 'community'
            })
        
        return items[:count]
    
    def _get_product_content(self, count: int) -> List[Dict[str, Any]]:
        """Get product recommendations."""
        products = Product.objects.filter(
            is_active=True,
            is_in_stock=True
        ).select_related('creator').order_by('-engagement_score')[:count]
        
        items = []
        for product in products:
            score = product.engagement_score * 0.6  # Product penalty
            
            items.append({
                'id': product.id,
                'type': 'product',
                'title': product.title,
                'description': product.description[:150] + '...' if len(product.description) > 150 else product.description,
                'creator': product.creator.username,
                'created_at': product.created_at.isoformat(),
                'price': product.formatted_price,
                'category': product.category,
                'engagement': {
                    'likes': product.like_count,
                    'comments': product.comment_count,
                    'shares': product.share_count
                },
                'score': score,
                'category': 'product'
            })
        
        return items
    
    def _get_user_connections(self) -> List[Connection]:
        """Get user's connections with caching."""
        cache_key = f'user_connections_{self.user.id}'
        connections = cache.get(cache_key)
        
        if connections is None:
            connections = list(Connection.objects.filter(
                from_user=self.user
            ).select_related('to_user').order_by('-last_interaction'))
            cache.set(cache_key, connections, 1800)  # 30 minutes
        
        return connections
    
    def _get_cached_feed(self, size: int) -> Optional[Dict[str, Any]]:
        """Get cached feed if available and valid."""
        cache_key = f'user_feed_{self.user.id}_{size}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            cached_data['cache_status'] = 'hit'
            return cached_data
        
        return None
    
    def _cache_feed(self, feed_data: Dict[str, Any], size: int) -> None:
        """Cache feed data."""
        cache_key = f'user_feed_{self.user.id}_{size}'
        cache.set(cache_key, feed_data, 600)  # 10 minutes
    
    def _calculate_composition_breakdown(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate actual composition breakdown."""
        breakdown = {}
        for item in items:
            category = item.get('category', 'unknown')
            breakdown[category] = breakdown.get(category, 0) + 1
        return breakdown
    
    def _log_feed_analytics(self, feed_data: Dict[str, Any], generation_time_ms: int) -> None:
        """Log feed generation analytics."""
        try:
            FeedAnalytics.objects.create(
                user=self.user,
                generation_time_ms=generation_time_ms,
                content_count=feed_data['total_items'],
                composition_used=self.feed_composition.composition_dict,
                cache_hit=(feed_data.get('cache_status') == 'hit'),
                experiment_group=self.feed_composition.experiment_group
            )
        except Exception as e:
            logger.error(f'Failed to log feed analytics: {e}')
    
    def _log_feed_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log feed debug event."""
        try:
            FeedDebugEvent.objects.create(
                user=self.user,
                event_type=event_type,
                event_data=data
            )
        except Exception as e:
            logger.error(f'Failed to log feed event: {e}')
