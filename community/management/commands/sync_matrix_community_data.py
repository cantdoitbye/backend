# community/management/commands/sync_matrix_community_data.py

from django.core.management.base import BaseCommand
from community.models import Community
from msg.models import MatrixProfile
from community.utils.matrix_avatar_manager import set_room_avatar_score_and_filter
import asyncio


class Command(BaseCommand):
    help = 'Sync all existing communities to Matrix room state'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=10, help='Process communities in batches')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        # Get all communities with Matrix rooms
        communities = Community.nodes.filter(room_id__isnull=False)
        total = len(communities)
        
        self.stdout.write(f"Found {total} communities with Matrix rooms")
        
        processed = 0
        failed = 0
        
        for i in range(0, total, batch_size):
            batch = communities[i:i+batch_size]
            
            for community in batch:
                try:
                    if dry_run:
                        self.stdout.write(f"Would sync: {community.name} (Room: {community.room_id})")
                        processed += 1
                        continue
                    
                    # Find a community admin with Matrix profile
                    admin_matrix_profile = self._find_community_admin_matrix_profile(community)
                    
                    if not admin_matrix_profile:
                        self.stdout.write(f"No Matrix profile found for community {community.name}")
                        failed += 1
                        continue
                    
                    
                    # Prepare complete community data to match create/update mutations
                    community_data = {
                        'community_type': community.community_type or '',
                        'community_circle': community.community_circle or '',
                        'category': community.category or '',  # Make sure key matches
                        'created_date': str(community.created_date) if community.created_date else '',
                        'uid': community.uid,  # Add uid field
                        }

                    
                    
                    # Sync to Matrix with all required fields
                    result = asyncio.run(set_room_avatar_score_and_filter(
                        access_token=admin_matrix_profile.access_token,
                        user_id=admin_matrix_profile.matrix_user_id,
                        room_id=community.room_id,
                        image_id=community.group_icon_id if community.group_icon_id else None,
                        community_data=community_data,
                        timeout=30
                    ))
                    
                    if result.get('success'):
                        self.stdout.write(f"✓ Synced: {community.name} (UID: {community.uid})")
                        processed += 1
                    else:
                        self.stdout.write(f"✗ Failed: {community.name} - {result.get('error')}")
                        failed += 1
                        
                except Exception as e:
                    self.stdout.write(f"✗ Error: {community.name} - {str(e)}")
                    failed += 1
            
            # Small delay between batches
            if not dry_run:
                import time
                time.sleep(1)
        
        self.stdout.write(f"\nCompleted: {processed} synced, {failed} failed")

    def _find_community_admin_matrix_profile(self, community):
        """Find a community admin with Matrix profile"""

        creator = community.created_by.single()
        if creator:
            try:
                matrix_profile = MatrixProfile.objects.get(user=creator.user_id)
                if matrix_profile.access_token and matrix_profile.matrix_user_id:
                    return matrix_profile
            except MatrixProfile.DoesNotExist:
                pass
        try:
            # Get community memberships
            memberships = community.members.all()
            
            for membership in memberships:
                if membership.is_admin:
                    user = membership.user.single()
                    if user:
                        try:
                            matrix_profile = MatrixProfile.objects.get(user=user.user_id)
                            if matrix_profile.access_token and matrix_profile.matrix_user_id:
                                return matrix_profile
                        except MatrixProfile.DoesNotExist:
                            continue
            
            # Fallback to OoumphLead user
            matrix_profile = MatrixProfile.objects.get(user=119)
            if matrix_profile.access_token and matrix_profile.matrix_user_id:
                return matrix_profile
                
        except Exception as e:
            print(f"Error finding admin profile: {e}")
        
        return None