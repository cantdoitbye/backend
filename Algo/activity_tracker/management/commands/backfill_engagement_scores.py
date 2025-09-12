from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from activity_tracker.models import UserEngagementScore, UserActivity
from activity_tracker.tasks import update_engagement_scores
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Backfill engagement scores for existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of users to process in each batch'
        )
        parser.add_argument(
            '--min-activities',
            type=int,
            default=1,
            help='Only process users with at least this many activities'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Only consider activities from the last N days'
        )
        parser.add_argument(
            '--user-ids',
            type=str,
            help='Comma-separated list of user IDs to process (overrides other filters)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        min_activities = options['min_activities']
        days = options['days']
        user_ids = options['user_ids']
        
        # Get base queryset
        users = User.objects.all()
        
        # Apply filters
        if user_ids:
            # Process specific users
            user_id_list = [int(uid.strip()) for uid in user_ids.split(',')]
            users = users.filter(id__in=user_id_list)
            self.stdout.write(self.style.SUCCESS(f'Processing {len(user_id_list)} specific users'))
        else:
            # Filter by activity count
            since_date = timezone.now() - timedelta(days=days)
            
            # Get users with activities
            active_users = (
                UserActivity.objects
                .filter(created_at__gte=since_date)
                .values('user')
                .annotate(activity_count=Count('id'))
                .filter(activity_count__gte=min_activities)
                .values_list('user', flat=True)
            )
            
            users = users.filter(id__in=active_users)
            self.stdout.write(self.style.SUCCESS(
                f'Found {users.count()} users with at least {min_activities} activities in the last {days} days'
            ))
        
        # Process in batches
        total_processed = 0
        batch_num = 1
        
        while True:
            # Get a batch of users
            user_batch = list(users[total_processed:total_processed + batch_size])
            if not user_batch:
                break
                
            self.stdout.write(f'Processing batch {batch_num} ({len(user_batch)} users)...')
            
            # Update scores for this batch
            for user in user_batch:
                try:
                    update_engagement_scores(user.id)
                    total_processed += 1
                    
                    if total_processed % 100 == 0:
                        self.stdout.write(f'Processed {total_processed} users...')
                        
                except Exception as e:
                    logger.error(f'Error processing user {user.id}: {e}')
            
            batch_num += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed engagement scores for {total_processed} users'
        ))
