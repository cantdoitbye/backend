# auth_manager/management/commands/sync_matrix_user_data.py

from django.core.management.base import BaseCommand
from auth_manager.models import Users
from msg.models import MatrixProfile
from auth_manager.Utils.matrix_avatar_manager import set_user_avatar_and_score, get_user_relations
import asyncio

class Command(BaseCommand):
    help = 'Sync all existing users to Matrix profile state'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=20, help='Process users in batches')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        # Get all users with Matrix profiles
        matrix_profiles = MatrixProfile.objects.filter(
            access_token__isnull=False,
            matrix_user_id__isnull=False
        )
        total = matrix_profiles.count()
        
        self.stdout.write(f"Found {total} users with Matrix profiles")
        
        processed = 0
        failed = 0
        
        for i in range(0, total, batch_size):
            batch = matrix_profiles[i:i+batch_size]
            
            for matrix_profile in batch:
                try:
                    user_node = Users.nodes.get(user_id=matrix_profile.user.id)
                    
                    if dry_run:
                        self.stdout.write(f"Would sync: {user_node.email} (Matrix: {matrix_profile.matrix_user_id})")
                        processed += 1
                        continue

                    if int(user_node.user_id) < 113:
                        processed += 1
                        continue
                    
                    # Get user relations
                    user_relations = get_user_relations(user_node)
                    
                    # Prepare additional data
                    additional_data = {
                        'user_type': getattr(user_node, 'user_type', ''),
                        'profile_complete': bool(getattr(user_node, 'full_name', '')),
                    }
                    
                    # Get user's profile image if available
                    profile_image_id = getattr(user_node, 'profile_image_id', None)
                    
                    # Sync avatar and score
                    result = asyncio.run(set_user_avatar_and_score(
                        access_token=matrix_profile.access_token,
                        user_id=matrix_profile.matrix_user_id,
                        database_user_id=user_node.user_id,
                        user_uid=user_node.uid,
                        image_id=profile_image_id,
                        score=4.0,
                        additional_data=additional_data,
                        timeout=30
                    ))
                    
                    if result.get('success'):
                        self.stdout.write(f"✓ Synced: {user_node.email}")
                        processed += 1
                    else:
                        self.stdout.write(f"✗ Failed: {user_node.email} - {result.get('error')}")
                        failed += 1
                        
                except Exception as e:
                    self.stdout.write(f"✗ Error: {matrix_profile.matrix_user_id} - {str(e)}")
                    failed += 1
            
            # Small delay between batches
            if not dry_run:
                import time
                time.sleep(0.5)
        
        self.stdout.write(f"\nCompleted: {processed} synced, {failed} failed")