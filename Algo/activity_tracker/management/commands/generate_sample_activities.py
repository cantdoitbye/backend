import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from activity_tracker.models import UserActivity, ActivityType
from activity_tracker.handlers import ActivityTracker

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample user activities for testing and development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to generate activities for'
        )
        parser.add_argument(
            '--activities-per-user',
            type=int,
            default=50,
            help='Average number of activities per user'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to spread activities over'
        )
        parser.add_argument(
            '--user-ids',
            type=str,
            help='Comma-separated list of user IDs to generate activities for (overrides --users)'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        avg_activities = options['activities_per_user']
        days = options['days']
        user_ids = options['user_ids']
        
        # Get or create users
        if user_ids:
            user_ids = [int(uid.strip()) for uid in user_ids.split(',')]
            users = list(User.objects.filter(id__in=user_ids))
            self.stdout.write(self.style.SUCCESS(f'Generating activities for {len(users)} specific users'))
        else:
            # Get existing users or create some if none exist
            users = list(User.objects.all()[:num_users])
            if not users:
                self.stdout.write('No users found, creating sample users...')
                users = []
                for i in range(num_users):
                    user = User.objects.create_user(
                        username=f'testuser_{i}',
                        email=f'testuser_{i}@example.com',
                        password='testpass123'
                    )
                    users.append(user)
        
        if not users:
            self.stderr.write('No users available to generate activities for')
            return
        
        # Get content types for activities
        user_content_type = ContentType.objects.get_for_model(User)
        
        # Activity type weights (some activities are more common than others)
        activity_weights = {
            ActivityType.VIBE: 30,
            ActivityType.COMMENT: 20,
            ActivityType.SHARE: 10,
            ActivityType.SAVE: 15,
            ActivityType.MEDIA_EXPAND: 25,
            ActivityType.PROFILE_VISIT: 40,
            ActivityType.EXPLORE_CLICK: 20,
            ActivityType.REPORT: 2,
        }
        
        # Generate activities
        total_activities = 0
        start_date = timezone.now() - timedelta(days=days)
        
        for user in users:
            # Randomize number of activities for this user
            num_activities = random.randint(
                int(avg_activities * 0.5),  # 50% below average
                int(avg_activities * 1.5)   # 50% above average
            )
            
            self.stdout.write(f'Generating {num_activities} activities for user {user.username}...')
            
            for _ in range(num_activities):
                # Random timestamp within the date range
                random_days = random.uniform(0, days)
                random_seconds = random.uniform(0, 86400)  # Seconds in a day
                created_at = start_date + timedelta(
                    days=random_days,
                    seconds=random_seconds
                )
                
                # Choose a random activity type based on weights
                activity_type = random.choices(
                    list(activity_weights.keys()),
                    weights=list(activity_weights.values()),
                    k=1
                )[0]
                
                # Choose a random content object (another user)
                content_user = random.choice([u for u in users if u != user])
                
                # Create the activity
                activity = UserActivity.objects.create(
                    user=user,
                    activity_type=activity_type,
                    content_type=user_content_type,
                    object_id=content_user.id,
                    created_at=created_at
                )
                
                # Add some metadata for certain activity types
                if activity_type == ActivityType.VIBE:
                    activity.metadata = {
                        'value': random.choice(['positive', 'negative', 'neutral']),
                        'intensity': random.randint(1, 5)
                    }
                elif activity_type == ActivityType.COMMENT:
                    activity.metadata = {
                        'length': random.randint(10, 200),
                        'has_mentions': random.random() > 0.8,
                        'has_hashtags': random.random() > 0.7
                    }
                
                activity.save()
                total_activities += 1
                
                # Update engagement scores periodically
                if random.random() < 0.1:  # 10% chance to update scores
                    ActivityTracker._update_engagement_scores(user)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated {total_activities} activities for {len(users)} users'
        ))
