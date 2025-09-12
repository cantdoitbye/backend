from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import UserProfile, FeedComposition
from .services import FeedGenerationService

User = get_user_model()

class FeedAlgorithmTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get or create user profile and composition
        self.profile = UserProfile.objects.get(user=self.user)
        self.composition = FeedComposition.objects.get(user=self.user)
    
    def test_user_profile_creation(self):
        """Test that a UserProfile is created when a User is created."""
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.user, self.user)
        self.assertTrue(self.profile.feed_enabled)
    
    def test_feed_composition_creation(self):
        """Test that a FeedComposition is created when a User is created."""
        self.assertIsNotNone(self.composition)
        self.assertEqual(self.composition.user, self.user)
        self.assertAlmostEqual(
            sum([
                self.composition.personal_connections,
                self.composition.interest_based,
                self.composition.trending_content,
                self.composition.discovery_content,
                self.composition.community_content,
                self.composition.product_content
            ]),
            1.0,
            places=2
        )
    
    def test_feed_generation_service(self):
        """Test the feed generation service."""
        service = FeedGenerationService(self.user)
        
        # Test feed generation
        feed_data = service.generate_feed(size=10)
        
        # Check basic structure
        self.assertIn('items', feed_data)
        self.assertIn('total_count', feed_data)
        self.assertIn('has_more', feed_data)
        self.assertIn('composition', feed_data)
        self.assertIn('generated_at', feed_data)
        
        # Check items
        self.assertIsInstance(feed_data['items'], list)
        
        # Check composition
        composition = feed_data['composition']
        self.assertIn('personal_connections', composition)
        self.assertIn('interest_based', composition)
        self.assertIn('trending_content', composition)
        self.assertIn('discovery_content', composition)
        self.assertIn('community_content', composition)
        self.assertIn('product_content', composition)
    
    def test_feed_composition_validation(self):
        """Test that feed composition validation works."""
        from django.core.exceptions import ValidationError
        
        # Test valid composition
        self.composition.personal_connections = 0.5
        self.composition.interest_based = 0.5
        self.composition.trending_content = 0.0
        self.composition.discovery_content = 0.0
        self.composition.community_content = 0.0
        self.composition.product_content = 0.0
        self.composition.save()
        
        # Test invalid composition
        self.composition.personal_connections = 2.0  # This should make the sum > 1.0
        with self.assertRaises(ValidationError):
            self.composition.full_clean()
    
    def test_feed_profile_update(self):
        """Test updating feed profile settings."""
        # Update profile
        self.profile.feed_enabled = False
        self.profile.content_language = 'es'
        self.profile.privacy_level = 'friends'
        self.profile.save()
        
        # Refresh from db
        updated_profile = UserProfile.objects.get(pk=self.profile.pk)
        
        # Assert updates
        self.assertFalse(updated_profile.feed_enabled)
        self.assertEqual(updated_profile.content_language, 'es')
        self.assertEqual(updated_profile.privacy_level, 'friends')
