from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import (
    ScoringFactor, UserScoringPreference, ContentScore,
    TrendingMetric, CreatorMetric
)
from .registry import ScoringEngineRegistry, BaseScoringEngine
from .engines import PersonalConnectionsScoring, InterestBasedScoring
from .utils import calculate_user_engagement, calculate_creator_metrics
from content_types.models import Post
from users.models import Connection

User = get_user_model()


class ScoringFactorModelTest(TestCase):
    """Test ScoringFactor model functionality."""
    
    def test_scoring_factor_creation(self):
        """Test scoring factor creation."""
        factor = ScoringFactor.objects.create(
            name='Test Factor',
            factor_type='engagement',
            description='A test scoring factor',
            weight=1.5,
            config={'param1': 'value1'}
        )
        
        self.assertEqual(factor.name, 'Test Factor')
        self.assertEqual(factor.factor_type, 'engagement')
        self.assertEqual(factor.weight, 1.5)
        self.assertTrue(factor.is_active)
        self.assertTrue(factor.is_global)
        self.assertEqual(factor.config, {'param1': 'value1'})


class UserScoringPreferenceModelTest(TestCase):
    """Test UserScoringPreference model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_scoring_preference_creation(self):
        """Test user scoring preference creation."""
        prefs = UserScoringPreference.objects.create(
            user=self.user,
            custom_weights={'engine1': 1.0, 'engine2': 0.8},
            freshness_preference=0.7,
            diversity_preference=0.6
        )
        
        self.assertEqual(prefs.user, self.user)
        self.assertEqual(prefs.freshness_preference, 0.7)
        self.assertEqual(prefs.diversity_preference, 0.6)
        self.assertEqual(prefs.get_factor_weight('engine1'), 1.0)
        self.assertEqual(prefs.get_factor_weight('engine2'), 0.8)
        self.assertEqual(prefs.get_factor_weight('nonexistent'), 1.0)


class ContentScoreModelTest(TestCase):
    """Test ContentScore model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_content_score_creation(self):
        """Test content score creation."""
        from django.utils import timezone
        from datetime import timedelta
        
        expires_at = timezone.now() + timedelta(hours=1)
        
        score = ContentScore.objects.create(
            content_type='post',
            content_id='123e4567-e89b-12d3-a456-426614174000',
            user=self.user,
            final_score=0.85,
            factor_scores={'engagement': 0.9, 'quality': 0.8},
            expires_at=expires_at
        )
        
        self.assertEqual(score.content_type, 'post')
        self.assertEqual(score.user, self.user)
        self.assertEqual(score.final_score, 0.85)
        self.assertFalse(score.is_expired())
        self.assertEqual(score.factor_scores['engagement'], 0.9)
    
    def test_content_score_expiration(self):
        """Test content score expiration logic."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create expired score
        expires_at = timezone.now() - timedelta(hours=1)
        
        score = ContentScore.objects.create(
            content_type='post',
            content_id='123e4567-e89b-12d3-a456-426614174000',
            final_score=0.85,
            expires_at=expires_at
        )
        
        self.assertTrue(score.is_expired())


class ScoringEngineRegistryTest(TestCase):
    """Test ScoringEngineRegistry functionality."""
    
    def setUp(self):
        self.registry = ScoringEngineRegistry()
    
    def test_registry_singleton(self):
        """Test registry is singleton."""
        registry2 = ScoringEngineRegistry()
        self.assertIs(self.registry, registry2)
    
    def test_engine_registration(self):
        """Test engine registration."""
        class TestEngine(BaseScoringEngine):
            def get_name(self):
                return "Test Engine"
            
            def calculate_score(self, content, user=None, context=None):
                return 0.5
        
        self.registry.register_engine('test_engine', TestEngine)
        
        self.assertTrue(self.registry.is_registered('test_engine'))
        self.assertIn('test_engine', self.registry.get_engine_names())
        
        engine = self.registry.get_engine('test_engine')
        self.assertIsInstance(engine, TestEngine)
        self.assertEqual(engine.get_name(), "Test Engine")
    
    def test_builtin_engines_registered(self):
        """Test built-in engines are registered."""
        self.registry.register_builtin_engines()
        
        expected_engines = [
            'personal_connections', 'interest_based', 'trending',
            'discovery', 'engagement', 'quality', 'freshness', 'diversity'
        ]
        
        for engine_name in expected_engines:
            self.assertTrue(self.registry.is_registered(engine_name))
        
        # Test getting an engine
        engine = self.registry.get_engine('personal_connections')
        self.assertIsInstance(engine, PersonalConnectionsScoring)


class PersonalConnectionsScoringTest(TestCase):
    """Test PersonalConnectionsScoring engine."""
    
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
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user2
        )
        
        self.engine = PersonalConnectionsScoring()
    
    def test_own_content_scoring(self):
        """Test scoring of user's own content."""
        own_post = Post.objects.create(
            title='Own Post',
            content='Own content',
            creator=self.user1
        )
        
        score = self.engine.calculate_score(own_post, self.user1)
        self.assertEqual(score, 1.0)
    
    def test_connected_user_scoring(self):
        """Test scoring of connected user's content."""
        # Create connection
        Connection.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            circle_type='inner',
            status='accepted'
        )
        
        score = self.engine.calculate_score(self.post, self.user1)
        self.assertEqual(score, 1.0)  # Inner circle weight
    
    def test_no_connection_scoring(self):
        """Test scoring with no connection."""
        score = self.engine.calculate_score(self.post, self.user1)
        self.assertEqual(score, 0.0)


class InterestBasedScoringTest(TestCase):
    """Test InterestBasedScoring engine."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Tech Post',
            content='Technology content',
            creator=self.user
        )
        
        self.engine = InterestBasedScoring()
    
    def test_no_user_scoring(self):
        """Test scoring without user context."""
        score = self.engine.calculate_score(self.post)
        self.assertEqual(score, 0.5)  # Neutral score
    
    def test_no_interests_scoring(self):
        """Test scoring for user with no interests."""
        score = self.engine.calculate_score(self.post, self.user)
        self.assertEqual(score, 0.3)  # Low score for no interests


class UtilityFunctionsTest(TestCase):
    """Test utility functions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_calculate_user_engagement(self):
        """Test user engagement calculation."""
        # Create some content for the user
        Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user
        )
        
        engagement_score = calculate_user_engagement(self.user)
        self.assertIsInstance(engagement_score, float)
        self.assertGreaterEqual(engagement_score, 0.0)
        self.assertLessEqual(engagement_score, 10.0)
    
    def test_calculate_creator_metrics(self):
        """Test creator metrics calculation."""
        # Create some content
        Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user
        )
        
        metrics = calculate_creator_metrics(self.user)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('reputation_score', metrics)
        self.assertIn('total_content_created', metrics)
        self.assertEqual(metrics['total_content_created'], 1)
        self.assertGreaterEqual(metrics['reputation_score'], 0.0)
        self.assertLessEqual(metrics['reputation_score'], 1.0)


class ScoringEngineAPITest(APITestCase):
    """Test scoring engine API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_available_engines(self):
        """Test getting available scoring engines."""
        response = self.client.get('/api/scoring/engines/available/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('engines', response.data)
        self.assertIsInstance(response.data['engines'], list)
    
    def test_user_preferences_creation(self):
        """Test creating user scoring preferences."""
        data = {
            'freshness_preference': 0.8,
            'diversity_preference': 0.6,
            'custom_weights': {
                'engagement': 1.2,
                'quality': 0.9
            }
        }
        
        response = self.client.post('/api/scoring/user-preferences/my_preferences/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['freshness_preference'], 0.8)
        self.assertEqual(response.data['diversity_preference'], 0.6)
    
    def test_get_personalized_weights(self):
        """Test getting personalized scoring weights."""
        # Create preferences first
        UserScoringPreference.objects.create(
            user=self.user,
            custom_weights={'engagement': 1.5}
        )
        
        response = self.client.get('/api/scoring/user-preferences/weights/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('weights', response.data)
        self.assertIsInstance(response.data['weights'], dict)
    
    def test_content_score_calculation(self):
        """Test content score calculation via API."""
        # Create content first
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user
        )
        
        data = {
            'content_type': 'post',
            'content_id': str(post.id),
            'force_recalculate': True
        }
        
        response = self.client.post('/api/scoring/content-scores/calculate/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('final_score', response.data)
        self.assertIn('breakdown', response.data)
        self.assertIsInstance(response.data['final_score'], float)


class TrendingMetricModelTest(TestCase):
    """Test TrendingMetric model functionality."""
    
    def test_trending_metric_creation(self):
        """Test trending metric creation."""
        metric = TrendingMetric.objects.create(
            metric_type='content',
            metric_id='test-content-123',
            velocity_score=15.5,
            viral_coefficient=2.1,
            engagement_volume=500,
            trending_score=0.85
        )
        
        self.assertEqual(metric.metric_type, 'content')
        self.assertEqual(metric.metric_id, 'test-content-123')
        self.assertEqual(metric.velocity_score, 15.5)
        self.assertEqual(metric.viral_coefficient, 2.1)
        self.assertEqual(metric.engagement_volume, 500)
        self.assertEqual(metric.trending_score, 0.85)


class CreatorMetricModelTest(TestCase):
    """Test CreatorMetric model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_creator_metric_creation(self):
        """Test creator metric creation."""
        metric = CreatorMetric.objects.create(
            creator=self.user,
            reputation_score=0.85,
            authority_score=0.7,
            consistency_score=0.9,
            total_engagements=150,
            avg_engagement_rate=12.5,
            total_content_created=25
        )
        
        self.assertEqual(metric.creator, self.user)
        self.assertEqual(metric.reputation_score, 0.85)
        self.assertEqual(metric.authority_score, 0.7)
        self.assertEqual(metric.total_content_created, 25)
    
    def test_update_metrics(self):
        """Test metric update functionality."""
        metric = CreatorMetric.objects.create(
            creator=self.user,
            reputation_score=0.5
        )
        
        # Create some content to affect metrics
        Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user
        )
        
        # Update metrics (this would normally be done by a task)
        metric.update_metrics()
        
        metric.refresh_from_db()
        self.assertEqual(metric.total_content_created, 1)