from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status
from .models import UserProfile, Connection, Interest, UserInterest
from .serializers import UserProfileSerializer

User = get_user_model()


class UserProfileModelTest(TestCase):
    """Test UserProfile model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_creation(self):
        """Test user profile is created correctly."""
        self.assertIsInstance(self.user, UserProfile)
        self.assertEqual(self.user.total_connections, 0)
        self.assertEqual(self.user.engagement_score, 0.0)
        self.assertFalse(self.user.is_private)
        self.assertTrue(self.user.allow_recommendations)
    
    def test_get_feed_composition_default(self):
        """Test default feed composition is returned."""
        composition = self.user.get_feed_composition()
        self.assertIsInstance(composition, dict)
        self.assertAlmostEqual(sum(composition.values()), 1.0, places=2)
    
    def test_get_feed_composition_custom(self):
        """Test custom feed composition is returned."""
        custom_composition = {
            'personal_connections': 0.5,
            'interest_based': 0.3,
            'trending_content': 0.2
        }
        self.user.feed_composition = custom_composition
        self.user.save()
        
        self.assertEqual(self.user.get_feed_composition(), custom_composition)


class ConnectionModelTest(TestCase):
    """Test Connection model functionality."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
    
    def test_connection_creation(self):
        """Test connection is created correctly."""
        connection = Connection.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            circle_type='outer',
            status='accepted'
        )
        
        self.assertEqual(connection.from_user, self.user1)
        self.assertEqual(connection.to_user, self.user2)
        self.assertEqual(connection.circle_type, 'outer')
        self.assertEqual(connection.status, 'accepted')
        self.assertEqual(connection.interaction_count, 0)
    
    def test_circle_weight(self):
        """Test circle weight calculation."""
        connection = Connection.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            circle_type='inner'
        )
        
        self.assertEqual(connection.get_circle_weight(), 1.0)
        
        connection.circle_type = 'outer'
        self.assertEqual(connection.get_circle_weight(), 0.7)
        
        connection.circle_type = 'universe'
        self.assertEqual(connection.get_circle_weight(), 0.4)
    
    def test_update_interaction(self):
        """Test interaction update functionality."""
        connection = Connection.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            circle_type='universe'
        )
        
        # Simulate interactions
        for _ in range(60):
            connection.update_interaction()
        
        connection.refresh_from_db()
        self.assertEqual(connection.circle_type, 'outer')  # Should auto-upgrade
        self.assertEqual(connection.interaction_count, 60)
        self.assertIsNotNone(connection.last_interaction)


class UserInterestModelTest(TestCase):
    """Test UserInterest model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.interest = Interest.objects.create(
            name='Technology',
            category='Tech'
        )
    
    def test_user_interest_creation(self):
        """Test user interest is created correctly."""
        user_interest = UserInterest.objects.create(
            user=self.user,
            interest=self.interest,
            strength=0.7
        )
        
        self.assertEqual(user_interest.user, self.user)
        self.assertEqual(user_interest.interest, self.interest)
        self.assertEqual(user_interest.strength, 0.7)
        self.assertEqual(user_interest.engagement_count, 0)
    
    def test_update_engagement(self):
        """Test engagement update functionality."""
        user_interest = UserInterest.objects.create(
            user=self.user,
            interest=self.interest,
            strength=0.5
        )
        
        initial_strength = user_interest.strength
        user_interest.update_engagement()
        
        user_interest.refresh_from_db()
        self.assertEqual(user_interest.engagement_count, 1)
        self.assertGreater(user_interest.strength, initial_strength)
        self.assertIsNotNone(user_interest.last_engaged)


class UserProfileAPITest(APITestCase):
    """Test UserProfile API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_own_profile(self):
        """Test getting own profile."""
        response = self.client.get('/api/users/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_update_feed_composition(self):
        """Test updating feed composition."""
        new_composition = {
            'personal_connections': 0.4,
            'interest_based': 0.3,
            'trending_content': 0.2,
            'discovery_content': 0.1
        }
        
        response = self.client.patch(
            '/api/users/profiles/update_feed_composition/',
            {'feed_composition': new_composition}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.feed_composition, new_composition)
    
    def test_update_feed_composition_invalid_sum(self):
        """Test feed composition validation."""
        invalid_composition = {
            'personal_connections': 0.4,
            'interest_based': 0.3,
            'trending_content': 0.5  # Sum > 1.0
        }
        
        response = self.client.patch(
            '/api/users/profiles/update_feed_composition/',
            {'feed_composition': invalid_composition}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def tearDown(self):
        cache.clear()