from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from activity_tracker.models import UserActivity, UserEngagementScore, ActivityType
from activity_tracker.handlers import ActivityTracker
from activity_tracker.feed_integration import ActivityBasedScorer

User = get_user_model()

class ActivityTrackerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test content type (using User as an example)
        self.content_type = ContentType.objects.get_for_model(User)
        self.content_object = User.objects.create_user(
            username='contentuser',
            email='content@example.com',
            password='testpass123'
        )
    
    def test_activity_creation(self):
        ""Test creating a new activity."""
        activity = UserActivity.objects.create(
            user=self.user,
            activity_type=ActivityType.VIBE,
            content_type=self.content_type,
            object_id=self.content_object.id,
            metadata={'value': 'positive'}
        )
        
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.activity_type, ActivityType.VIBE)
        self.assertEqual(activity.content_object, self.content_object)
        self.assertEqual(activity.metadata, {'value': 'positive'})
    
    def test_activity_tracker_helper(self):
        ""Test the ActivityTracker helper class."""
        activity = ActivityTracker.track_activity(
            user=self.user,
            activity_type=ActivityType.COMMENT,
            content_object=self.content_object,
            metadata={'text': 'Test comment'}
        )
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.activity_type, ActivityType.COMMENT)
        self.assertEqual(activity.content_object, self.content_object)
        
        # Test with invalid user
        activity = ActivityTracker.track_activity(
            user=None,
            activity_type=ActivityType.VIBE
        )
        self.assertIsNone(activity)
    
    def test_engagement_score_creation(self):
        ""Test engagement score creation and update."""
        # Create some activities
        for i in range(5):
            UserActivity.objects.create(
                user=self.user,
                activity_type=ActivityType.VIBE,
                content_type=self.content_type,
                object_id=self.content_object.id
            )
        
        # Get or create the score
        score = UserEngagementScore.objects.get_or_create(user=self.user)[0]
        score.update_scores()
        
        self.assertEqual(score.vibe_count, 5)
        self.assertGreater(score.engagement_score, 0)


class ActivityBasedScorerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testscorer',
            email='scorer@example.com',
            password='testpass123'
        )
        
        # Create some content objects (using User as example)
        self.content_objects = [
            User.objects.create_user(
                username=f'content{i}',
                email=f'content{i}@example.com',
                password='testpass123'
            ) for i in range(3)
        ]
        
        # Create some activities
        for i, obj in enumerate(self.content_objects):
            for _ in range(i + 1):  # 1, 2, 3 activities respectively
                UserActivity.objects.create(
                    user=self.user,
                    activity_type=ActivityType.VIBE,
                    content_object=obj
                )
    
    def test_content_affinity_scores(self):
        ""Test content affinity scoring."""
        scorer = ActivityBasedScorer(self.user)
        scores = scorer.get_content_affinity_scores(User.objects.all())
        
        # Should have scores for all content objects
        self.assertEqual(len(scores), 3)
        
        # More activities should result in higher scores
        self.assertGreater(
            scores[self.content_objects[2].id],
            scores[self.content_objects[1].id]
        )
        self.assertGreater(
            scores[self.content_objects[1].id],
            scores[self.content_objects[0].id]
        )
    
    def test_feed_composition_adjustment(self):
        ""Test feed composition adjustment based on engagement."""
        # Create engagement score for the user
        score = UserEngagementScore.objects.create(
            user=self.user,
            engagement_score=80.0,  # High engagement
            content_score=70.0,
            social_score=90.0,
            vibe_count=10,
            comment_count=5,
            share_count=3,
            save_count=2
        )
        
        scorer = ActivityBasedScorer(self.user)
        
        # Test with high engagement user
        composition = {
            'interest_based': 0.4,
            'personal_connections': 0.3,
            'trending_content': 0.2,
            'discovery_content': 0.1
        }
        
        adjusted = scorer.adjust_feed_composition(composition)
        
        # High engagement users should get more interest-based content
        self.assertGreater(adjusted['interest_based'], composition['interest_based'])
        self.assertGreater(adjusted['personal_connections'], composition['personal_connections'])
        self.assertLess(adjusted['trending_content'], composition['trending_content'])
        
        # Sum should still be approximately 1.0
        self.assertAlmostEqual(sum(adjusted.values()), 1.0, places=2)


@override_settings(ACTIVITY_TRACKING={'AUTO_TRACK': True})
class SignalTests(TestCase):
    def test_activity_signals(self):
        ""Test that signals create engagement scores."""
        user = User.objects.create_user(
            username='signaltest',
            email='signal@example.com',
            password='testpass123'
        )
        
        # Creating an activity should create an engagement score
        activity = UserActivity.objects.create(
            user=user,
            activity_type=ActivityType.VIBE
        )
        
        # Check that engagement score was created
        self.assertTrue(UserEngagementScore.objects.filter(user=user).exists())
        
        # Check that the score was updated
        score = UserEngagementScore.objects.get(user=user)
        self.assertEqual(score.vibe_count, 1)
