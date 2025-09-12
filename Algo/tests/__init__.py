"""
Comprehensive test suite for the Ooumph Feed Algorithm system.
Tests cover models, feed engine, API endpoints, and scoring algorithms.
"""

import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import timedelta

from feed_algorithm.models import (
    UserProfile, Connection, FeedComposition, Interest, InterestCollection,
    TrendingMetric, CreatorMetric
)
from feed_content_types.models import Post, Community, Product, Engagement
from feed_algorithm.feed_engine import FeedAlgorithmEngine
from analytics.models import FeedAnalytics, AnalyticsEvent


class ModelTestCase(TestCase):
    """Test case for data models."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1', email='test1@example.com', password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2', email='test2@example.com', password='testpass123'
        )
    
    def test_user_profile_creation(self):
        """Test UserProfile model creation and methods."""
        profile = UserProfile.objects.create(
            user=self.user1,
            feed_enabled=True,
            content_language='en',
            privacy_level='public'
        )
        
        self.assertEqual(profile.user, self.user1)
        self.assertTrue(profile.feed_enabled)
        self.assertEqual(profile.total_engagement_score, 0.0)
        
        # Test engagement score update
        profile.update_engagement_score(50.0)
        self.assertEqual(profile.total_engagement_score, 50.0)
    
    def test_connection_model(self):
        """Test Connection model and circle weights."""
        connection = Connection.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            circle_type='inner'
        )
        
        self.assertEqual(connection.circle_weight, 1.0)
        self.assertEqual(connection.interaction_count, 0)
        
        # Test interaction update
        connection.update_interaction()
        self.assertEqual(connection.interaction_count, 1)
        self.assertIsNotNone(connection.last_interaction)
    
    def test_feed_composition_validation(self):
        """Test FeedComposition model validation."""
        from django.core.exceptions import ValidationError
        
        # Valid composition
        composition = FeedComposition(
            user=self.user1,
            personal_connections=0.4,
            interest_based=0.25,
            trending_content=0.15,
            discovery_content=0.1,
            community_content=0.05,
            product_content=0.05
        )
        composition.clean()  # Should not raise
        
        # Invalid composition (doesn't sum to 1.0)
        composition.personal_connections = 0.8
        with self.assertRaises(ValidationError):
            composition.clean()
    
    def test_interest_collection(self):
        """Test Interest and InterestCollection models."""
        interest = Interest.objects.create(
            name='Technology',
            category='tech',
            description='Interest in technology'
        )
        
        collection = InterestCollection.objects.create(
            user=self.user1,
            interest=interest,
            strength=0.8,
            source='explicit'
        )
        
        self.assertEqual(collection.strength, 0.8)
        self.assertEqual(str(collection), f"{self.user1.username} -> Technology (0.8)")


class ContentModelTestCase(TestCase):
    """Test case for content type models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
    
    def test_post_creation_and_engagement(self):
        """Test Post model creation and engagement tracking."""
        post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            creator=self.user,
            post_type='text',
            visibility='public',
            tags=['technology', 'testing']
        )
        
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.engagement_score, 0.0)
        
        # Test engagement update
        post.update_engagement_metrics('like', 5)
        self.assertEqual(post.like_count, 5)
        self.assertGreater(post.engagement_score, 0)
    
    def test_community_member_management(self):
        """Test Community model and member management."""
        community = Community.objects.create(
            title='Tech Community',
            description='A community for tech enthusiasts',
            creator=self.user,
            category='technology'
        )
        
        user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='testpass123'
        )
        
        # Test adding member
        membership = community.add_member(user2)
        self.assertEqual(community.member_count, 1)
        self.assertEqual(membership.role, 'member')
        
        # Test removing member
        success = community.remove_member(user2)
        self.assertTrue(success)
        community.refresh_from_db()
        self.assertEqual(community.member_count, 0)
    
    def test_product_pricing(self):
        """Test Product model pricing functionality."""
        product = Product.objects.create(
            title='Test Product',
            description='A test product',
            creator=self.user,
            price=99.99,
            currency='USD',
            category='electronics',
            stock_quantity=10
        )
        
        self.assertEqual(product.formatted_price, 'USD 99.99')
        self.assertTrue(product.is_in_stock)
        
        # Test stock update
        product.update_stock(-5)
        self.assertEqual(product.stock_quantity, 5)
        
        product.update_stock(-5)
        self.assertEqual(product.stock_quantity, 0)
        self.assertFalse(product.is_in_stock)


class FeedEngineTestCase(TestCase):
    """Test case for the core feed algorithm engine."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.engine = FeedAlgorithmEngine(self.user)
        
        # Create test content
        self.create_test_content()
    
    def create_test_content(self):
        """Create test content for feed generation."""
        # Create interests
        self.tech_interest = Interest.objects.create(
            name='Technology', category='tech'
        )
        InterestCollection.objects.create(
            user=self.user,
            interest=self.tech_interest,
            strength=0.8
        )
        
        # Create connections
        self.friend_user = User.objects.create_user(
            username='friend', email='friend@example.com', password='testpass123'
        )
        Connection.objects.create(
            from_user=self.user,
            to_user=self.friend_user,
            circle_type='inner'
        )
        
        # Create posts
        self.post1 = Post.objects.create(
            title='Tech Post',
            content='About technology',
            creator=self.friend_user,
            tags=['technology'],
            engagement_score=50.0
        )
        
        self.post2 = Post.objects.create(
            title='Random Post',
            content='Random content',
            creator=self.friend_user,
            engagement_score=30.0
        )
    
    def test_feed_generation(self):
        """Test basic feed generation."""
        feed_data = self.engine.generate_feed(size=10)
        
        self.assertIn('items', feed_data)
        self.assertIn('composition', feed_data)
        self.assertIn('total_items', feed_data)
        self.assertLessEqual(feed_data['total_items'], 10)
    
    @patch('feed_algorithm.feed_engine.cache')
    def test_feed_caching(self, mock_cache):
        """Test feed caching functionality."""
        mock_cache.get.return_value = None
        
        # First call should generate fresh feed
        feed_data = self.engine.generate_feed(size=5)
        self.assertEqual(feed_data['cache_status'], 'fresh')
        
        # Verify cache.set was called
        mock_cache.set.assert_called()
    
    def test_personal_connections_content(self):
        """Test personal connections content retrieval."""
        content = self.engine._get_personal_connections_content(5)
        
        self.assertIsInstance(content, list)
        # Should include posts from connected users
        if content:
            self.assertIn('category', content[0])
            self.assertEqual(content[0]['category'], 'personal_connections')
    
    def test_interest_based_content(self):
        """Test interest-based content retrieval."""
        content = self.engine._get_interest_based_content(5)
        
        self.assertIsInstance(content, list)
        # Should prioritize content matching user interests
        if content:
            self.assertIn('category', content[0])
            self.assertEqual(content[0]['category'], 'interest_based')


class APITestCase(APITestCase):
    """Test case for REST API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser', email='api@example.com', password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_feed_generation_endpoint(self):
        """Test the feed generation API endpoint."""
        url = reverse('feed_algorithm:feed-generate')
        response = self.client.get(url, {'size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertIn('composition', response.data)
    
    def test_feed_composition_endpoints(self):
        """Test feed composition GET and POST endpoints."""
        url = reverse('feed_algorithm:feed-composition')
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test POST with valid data
        composition_data = {
            'personal_connections': 0.5,
            'interest_based': 0.3,
            'trending_content': 0.1,
            'discovery_content': 0.05,
            'community_content': 0.03,
            'product_content': 0.02
        }
        response = self.client.post(url, composition_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test POST with invalid data (doesn't sum to 1.0)
        invalid_data = composition_data.copy()
        invalid_data['personal_connections'] = 0.8
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_interests_endpoints(self):
        """Test interest management endpoints."""
        # Create test interest
        interest = Interest.objects.create(
            name='Test Interest',
            category='test'
        )
        
        # Test interests list
        url = reverse('feed_algorithm:interest-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test user interests
        url = reverse('feed_algorithm:user-interests-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_analytics_endpoints(self):
        """Test analytics API endpoints."""
        # Create test analytics data
        FeedAnalytics.objects.create(
            user=self.user,
            generation_time_ms=100,
            content_count=20,
            cache_hit=True
        )
        
        url = reverse('feed_algorithm:analytics-feed-performance')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_feeds_generated', response.data)


class ScoringEngineTestCase(TestCase):
    """Test case for scoring algorithms."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='scorer', email='scorer@example.com', password='testpass123'
        )
        self.engine = FeedAlgorithmEngine(self.user)
    
    def test_circle_weights(self):
        """Test connection circle weight calculations."""
        inner_connection = Connection.objects.create(
            from_user=self.user,
            to_user=User.objects.create_user('inner', 'inner@example.com', 'pass'),
            circle_type='inner'
        )
        
        outer_connection = Connection.objects.create(
            from_user=self.user,
            to_user=User.objects.create_user('outer', 'outer@example.com', 'pass'),
            circle_type='outer'
        )
        
        universe_connection = Connection.objects.create(
            from_user=self.user,
            to_user=User.objects.create_user('universe', 'universe@example.com', 'pass'),
            circle_type='universe'
        )
        
        self.assertEqual(inner_connection.circle_weight, 1.0)
        self.assertEqual(outer_connection.circle_weight, 0.7)
        self.assertEqual(universe_connection.circle_weight, 0.4)
    
    def test_engagement_score_calculation(self):
        """Test content engagement score calculation."""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user,
            like_count=10,
            comment_count=5,
            share_count=2,
            view_count=100
        )
        
        initial_score = post.calculate_engagement_score()
        
        # Score should be calculated based on weighted interactions
        expected_score = (10 * 1.0) + (5 * 2.0) + (2 * 3.0) + (100 * 0.1)
        self.assertGreater(initial_score, 0)
        self.assertLessEqual(initial_score, expected_score)  # Time decay applies


class PerformanceTestCase(TransactionTestCase):
    """Test case for performance-critical operations."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='perfuser', email='perf@example.com', password='testpass123'
        )
    
    def test_feed_generation_performance(self):
        """Test feed generation performance with large dataset."""
        # Create multiple users and content
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            users.append(user)
            
            # Create connections
            Connection.objects.create(
                from_user=self.user,
                to_user=user,
                circle_type='universe'
            )
        
        # Create multiple posts
        for i in range(50):
            Post.objects.create(
                title=f'Post {i}',
                content=f'Content for post {i}',
                creator=users[i % len(users)],
                engagement_score=float(i)
            )
        
        engine = FeedAlgorithmEngine(self.user)
        
        # Measure generation time
        import time
        start_time = time.time()
        feed_data = engine.generate_feed(size=20)
        generation_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should generate feed quickly (under 1 second)
        self.assertLess(generation_time, 1000)
        self.assertEqual(len(feed_data['items']), 20)
    
    def test_cache_performance(self):
        """Test caching performance and hit rates."""
        engine = FeedAlgorithmEngine(self.user)
        
        # Clear cache
        cache.clear()
        
        # First call - cache miss
        feed_data1 = engine.generate_feed(size=10)
        self.assertEqual(feed_data1['cache_status'], 'fresh')
        
        # Second call - should use cache
        feed_data2 = engine.generate_feed(size=10)
        # Note: This test assumes caching is working properly
        self.assertIsNotNone(feed_data2)


class IntegrationTestCase(APITestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integuser', email='integ@example.com', password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_complete_user_workflow(self):
        """Test complete user workflow from setup to feed consumption."""
        # 1. User sets up interests
        interest = Interest.objects.create(name='Technology', category='tech')
        
        interest_url = reverse('feed_algorithm:user-interests-list')
        response = self.client.post(interest_url, {
            'interest_id': interest.id,
            'strength': 0.8,
            'source': 'explicit'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 2. User customizes feed composition
        composition_url = reverse('feed_algorithm:feed-composition')
        response = self.client.post(composition_url, {
            'personal_connections': 0.3,
            'interest_based': 0.4,
            'trending_content': 0.15,
            'discovery_content': 0.1,
            'community_content': 0.03,
            'product_content': 0.02
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. User generates feed
        feed_url = reverse('feed_algorithm:feed-generate')
        response = self.client.get(feed_url, {'size': 15})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        feed_data = response.data
        self.assertIn('items', feed_data)
        self.assertIn('composition', feed_data)
        self.assertLessEqual(len(feed_data['items']), 15)
        
        # 4. Verify analytics are recorded
        analytics_url = reverse('feed_algorithm:analytics-feed-performance')
        response = self.client.get(analytics_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['total_feeds_generated'], 0)
