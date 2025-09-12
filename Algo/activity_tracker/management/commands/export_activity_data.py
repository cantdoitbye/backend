import csv
import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, F, Q
from django.contrib.contenttypes.models import ContentType
from activity_tracker.models import UserActivity, UserEngagementScore, ActivityType

User = get_user_model()

class Command(BaseCommand):
    help = 'Export user activity data for analysis'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='activity_export.csv',
            help='Output file path (default: activity_export.csv)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            default='csv',
            help='Output format (csv or json)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of data to export (default: 90)'
        )
        parser.add_argument(
            '--sample-size',
            type=int,
            help='Maximum number of records to export (random sample)'
        )
        parser.add_argument(
            '--include-metadata',
            action='store_true',
            help='Include full metadata in the export (may increase file size significantly)'
        )
    
    def handle(self, *args, **options):
        output_file = options['output']
        export_format = options['format']
        days = options['days']
        sample_size = options['sample_size']
        include_metadata = options['include_metadata']
        
        self.stdout.write(self.style.SUCCESS(
            f'Exporting activity data from the last {days} days to {output_file}...'
        ))
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get base queryset
        activities = UserActivity.objects.filter(
            created_at__range=(start_date, end_date)
        ).select_related('user', 'content_type')
        
        # Apply sampling if requested
        if sample_size and activities.count() > sample_size:
            activities = activities.order_by('?')[:sample_size]
        
        self.stdout.write(f'Found {activities.count()} activities to export')
        
        # Export data
        if export_format == 'csv':
            self.export_to_csv(activities, output_file, include_metadata)
        else:
            self.export_to_json(activities, output_file, include_metadata)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully exported {activities.count()} activities to {output_file}'
        ))
    
    def export_to_csv(self, queryset, output_file, include_metadata):
        """Export activities to CSV format."""
        fieldnames = [
            'id',
            'user_id',
            'username',
            'activity_type',
            'content_type',
            'object_id',
            'created_at',
            'updated_at',
            'metadata'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for activity in queryset.iterator(chunk_size=1000):
                row = {
                    'id': activity.id,
                    'user_id': activity.user_id,
                    'username': activity.user.username if activity.user else '',
                    'activity_type': activity.activity_type,
                    'content_type': f"{activity.content_type.app_label}.{activity.content_type.model}",
                    'object_id': activity.object_id,
                    'created_at': activity.created_at.isoformat(),
                    'updated_at': activity.updated_at.isoformat(),
                    'metadata': json.dumps(activity.metadata) if include_metadata and activity.metadata else ''
                }
                writer.writerow(row)
    
    def export_to_json(self, queryset, output_file, include_metadata):
        """Export activities to JSON format."""
        data = []
        
        for activity in queryset.iterator(chunk_size=1000):
            item = {
                'id': activity.id,
                'user': {
                    'id': activity.user_id,
                    'username': activity.user.username if activity.user else None
                },
                'activity_type': activity.activity_type,
                'content_type': {
                    'app': activity.content_type.app_label,
                    'model': activity.content_type.model
                },
                'object_id': activity.object_id,
                'created_at': activity.created_at.isoformat(),
                'updated_at': activity.updated_at.isoformat(),
            }
            
            if include_metadata and activity.metadata:
                item['metadata'] = activity.metadata
            
            data.append(item)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
