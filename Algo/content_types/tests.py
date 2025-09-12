from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from .models import (
    Post, Community, Product, Engagement,
    CommunityMembership, ContentTag, ContentTagging
)
from .registry import ContentTypeRegistry

User = get_user_model()


class PostModelTest(TestCase):
    """Test Post model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_post_creation(self):
        """Test post creation."""
        post = Post.objects.create(
            title='Test Post',
            content='This is a test post.',
            creator=self.user,
            post_type='text'
        )
        
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.content, 'This is a test post.')
        self.assertEqual(post.creator, self.user)
        self.assertEqual(post.post_type, 'text')
        self.assertEqual(post.visibility, 'public')
        self.assertTrue(post.is_active)
        self.assertEqual(post.engagement_score, 0.0)
    
    def test_post_visibility(self):
        """Test post visibility logic."""
        # Public post
        public_post = Post.objects.create(
            title='Public Post',
            content='Public content',
            creator=self.user,
            visibility='public'
        )
        
        # Private post
        private_post = Post.objects.create(
            title='Private Post',
            content='Private content',
            creator=self.user,
            visibility='private'
        )
        
        # Test creator can see all posts
        self.assertTrue(public_post.is_visible_to_user(self.user))
        self.assertTrue(private_post.is_visible_to_user(self.user))
        
        # Test other user can only see public posts
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.assertTrue(public_post.is_visible_to_user(other_user))
        self.assertFalse(private_post.is_visible_to_user(other_user))


class CommunityModelTest(TestCase):
    """Test Community model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_community_creation(self):
        """Test community creation."""
        community = Community.objects.create(
            title='Test Community',
            description='A test community',
            creator=self.user,
            community_type='public'
        )
        
        self.assertEqual(community.title, 'Test Community')
        self.assertEqual(community.creator, self.user)
        self.assertEqual(community.community_type, 'public')
        self.assertEqual(community.member_count, 0)
        self.assertTrue(community.allow_posts)
    
    def test_can_user_join(self):
        """Test community join logic."""
        # Public community
        public_community = Community.objects.create(
            title='Public Community',
            creator=self.user,
            community_type='public'
        )
        
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.assertTrue(public_community.can_user_join(other_user))
        
        # Test max members limit
        public_community.max_members = 1
        public_community.member_count = 1
        public_community.save()
        
        self.assertFalse(public_community.can_user_join(other_user))


class EngagementModelTest(TestCase):
    """Test Engagement model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user
        )
    
    def test_engagement_creation(self):
        """Test engagement creation."""
        content_type = ContentType.objects.get_for_model(Post)
        
        engagement = Engagement.objects.create(
            user=self.user,
            content_type=content_type,
            object_id=self.post.id,
            engagement_type='like',
            score=1.0
        )
        
        self.assertEqual(engagement.user, self.user)
        self.assertEqual(engagement.content_object, self.post)
        self.assertEqual(engagement.engagement_type, 'like')
        self.assertEqual(engagement.score, 1.0)
    
    def test_engagement_uniqueness(self):
        """Test engagement uniqueness constraint."""
        content_type = ContentType.objects.get_for_model(Post)
        
        # Create first engagement
        Engagement.objects.create(
            user=self.user,
            content_type=content_type,
            object_id=self.post.id,
            engagement_type='like'
        )
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(Exception):
            Engagement.objects.create(
                user=self.user,
                content_type=content_type,
                object_id=self.post.id,
                engagement_type='like'
            )


class ContentTypeRegistryTest(TestCase):
    """Test ContentTypeRegistry functionality."""
    
    def setUp(self):
        self.registry = ContentTypeRegistry()
    
    def test_registry_singleton(self):
        """Test registry is singleton."""
        registry2 = ContentTypeRegistry()
        self.assertIs(self.registry, registry2)
    
    def test_builtin_types_registered(self):
        """Test built-in content types are registered."""
        self.registry.register_builtin_types()
        
        self.assertTrue(self.registry.is_registered('post'))
        self.assertTrue(self.registry.is_registered('community'))
        self.assertTrue(self.registry.is_registered('product'))
        
        self.assertEqual(self.registry.get_content_type('post'), Post)
        self.assertEqual(self.registry.get_content_type('community'), Community)
        self.assertEqual(self.registry.get_content_type('product'), Product)
    
    def test_custom_content_type_registration(self):
        """Test custom content type registration."""
        # This would be a custom content type in a real scenario
        class CustomContent(Post):
            class Meta:
                proxy = True
        
        self.registry.register_content_type('custom', CustomContent)
        
        self.assertTrue(self.registry.is_registered('custom'))
        self.assertEqual(self.registry.get_content_type('custom'), CustomContent)


class PostAPITest(APITestCase):
    """Test Post API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_post(self):
        """Test creating a post via API."""
        data = {
            'title': 'API Test Post',
            'content': 'This is a test post created via API.',
            'post_type': 'text',
            'visibility': 'public'
        }
        
        response = self.client.post('/api/content-types/posts/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'API Test Post')
        self.assertEqual(response.data['creator'], self.user.id)
    
    def test_list_posts(self):
        """Test listing posts via API."""
        # Create some posts
        Post.objects.create(
            title='Public Post',
            content='Public content',
            creator=self.user,
            visibility='public'
        )
        
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        Post.objects.create(
            title='Other User Post',
            content='Content from other user',
            creator=other_user,
            visibility='public'
        )
        
        response = self.client.get('/api/content-types/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_engage_with_post(self):
        """Test engaging with a post via API."""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user
        )
        
        response = self.client.post(
            f'/api/content-types/posts/{post.id}/engage/',
            {'engagement_type': 'like'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['engagement_type'], 'like')
        
        # Check engagement was created
        engagement_count = Engagement.objects.filter(
            object_id=post.id,
            engagement_type='like'
        ).count()
        self.assertEqual(engagement_count, 1)
    
    def test_duplicate_engagement(self):
        """Test duplicate engagement prevention."""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            creator=self.user
        )
        
        # First engagement
        self.client.post(
            f'/api/content-types/posts/{post.id}/engage/',
            {'engagement_type': 'like'}
        )
        
        # Second identical engagement
        response = self.client.post(
            f'/api/content-types/posts/{post.id}/engage/',
            {'engagement_type': 'like'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Engagement already exists')