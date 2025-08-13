# Management command for cleaning up old audit logs
# This command removes audit logs older than the specified retention period.

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import logging

from agentic.services.audit_service import audit_service


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to clean up old audit logs.
    
    This command removes audit logs older than the specified retention period
    to prevent the database from growing too large.
    """
    
    help = 'Clean up old agent audit logs based on retention policy'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--retention-days',
            type=int,
            default=90,
            help='Number of days to retain audit logs (default: 90)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        retention_days = options['retention_days']
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting audit log cleanup (retention: {retention_days} days)')
        )
        
        try:
            # Calculate cutoff date
            cutoff_date = timezone.now() - timedelta(days=retention_days)
            
            # Import here to avoid circular imports
            from agentic.models import AgentActionLog
            
            # Count logs to be deleted
            logs_to_delete = AgentActionLog.objects.filter(timestamp__lt=cutoff_date)
            count_to_delete = logs_to_delete.count()
            
            if count_to_delete == 0:
                self.stdout.write(
                    self.style.SUCCESS('No audit logs found that are older than retention period')
                )
                return
            
            self.stdout.write(
                f'Found {count_to_delete} audit logs older than {cutoff_date.strftime(\"%Y-%m-%d %H:%M:%S\")}'
            )
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN: Would delete the above logs (use --force to actually delete)')
                )
                return
            
            # Confirm deletion unless force is used
            if not force:
                confirm = input(f'Are you sure you want to delete {count_to_delete} audit logs? (yes/no): ')
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.ERROR('Operation cancelled'))
                    return
            
            # Perform cleanup
            cleanup_result = audit_service.cleanup_old_logs(retention_days)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {cleanup_result[\"logs_deleted\"]} audit logs'
                )
            )
            
            # Log summary
            self.stdout.write('Cleanup Summary:')
            self.stdout.write(f'  - Retention period: {retention_days} days')
            self.stdout.write(f'  - Cutoff date: {cleanup_result[\"cutoff_date\"]}')
            self.stdout.write(f'  - Logs deleted: {cleanup_result[\"logs_deleted\"]}')
            self.stdout.write(f'  - Cleanup completed at: {cleanup_result[\"cleanup_date\"]}')
            
        except Exception as e:
            logger.error(f'Audit log cleanup failed: {str(e)}')
            raise CommandError(f'Audit log cleanup failed: {str(e)}')