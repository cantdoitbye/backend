from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from activity_tracker.models import UserActivity
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Prune old activity records based on PRUNE_AFTER_DAYS setting'

    def handle(self, *args, **options):
        days = settings.ACTIVITY_TRACKING.get('PRUNE_AFTER_DAYS', 90)
        if not days or days <= 0:
            logger.info('Activity pruning is disabled (PRUNE_AFTER_DAYS <= 0)')
            return

        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        logger.info(f'Pruning activities older than {cutoff_date}')
        
        # Delete in batches to avoid timeouts
        batch_size = 1000
        total_deleted = 0
        
        while True:
            # Get primary keys of activities to delete
            pks = list(UserActivity.objects.filter(
                created_at__lt=cutoff_date
            ).values_list('pk', flat=True)[:batch_size])
            
            if not pks:
                break
                
            # Delete the batch
            deleted_count, _ = UserActivity.objects.filter(
                pk__in=pks
            ).delete()
            
            total_deleted += deleted_count
            logger.info(f'Deleted {deleted_count} activities in this batch')
            
            # Small delay to prevent database contention
            time.sleep(0.1)
        
        logger.info(f'Successfully pruned {total_deleted} activities')
