from django.core.management.base import BaseCommand
import asyncio
from community.models import Community, SubCommunity
from msg.models import MatrixProfile
from community.utils.matrix_avatar_manager import set_room_avatar_score_and_filter
from community import matrix_logger


class Command(BaseCommand):
    help = 'Force update Matrix room avatar and filter data for all existing communities and sub-communities'

    def add_arguments(self, parser):
        parser.add_argument('--community-only', action='store_true', help='Update only communities')
        parser.add_argument('--sub-community-only', action='store_true', help='Update only sub-communities')
        parser.add_argument('--limit', type=int, help='Limit the number to process')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated')

    def handle(self, *args, **options):
        community_only = options['community_only']
        sub_community_only = options['sub_community_only']
        limit = options['limit']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Process communities
        if not sub_community_only:
            self.stdout.write('Processing communities...')
            communities_processed = self.process_communities(limit, dry_run)
            self.stdout.write(self.style.SUCCESS(f'Processed {communities_processed} communities'))

        # Process sub-communities
        if not community_only:
            self.stdout.write('Processing sub-communities...')
            sub_communities_processed = self.process_sub_communities(limit, dry_run)
            self.stdout.write(self.style.SUCCESS(f'Processed {sub_communities_processed} sub-communities'))

        self.stdout.write(self.style.SUCCESS('Matrix room data update completed!'))

    def _find_matrix_profile_for_community(self, community):
        """Find Matrix profile for community creator or admin"""
        try:
            # First try: Get community creator
            creator = community.created_by.single()
            if creator:
                try:
                    matrix_profile = MatrixProfile.objects.get(user=creator.user_id)
                    if matrix_profile.access_token and matrix_profile.matrix_user_id:
                        return matrix_profile
                except MatrixProfile.DoesNotExist:
                    pass

            # Second try: Get any admin member
            try:
                members = community.members.all()
                for membership in members:
                    if membership.is_admin:
                        user = membership.user.single()
                        if user:
                            try:
                                matrix_profile = MatrixProfile.objects.get(user=user.user_id)
                                if matrix_profile.access_token and matrix_profile.matrix_user_id:
                                    return matrix_profile
                            except MatrixProfile.DoesNotExist:
                                continue
            except:
                pass

            # Final fallback: OoumphLead
            try:
                matrix_profile = MatrixProfile.objects.get(user=771)
                if matrix_profile.access_token and matrix_profile.matrix_user_id:
                    return matrix_profile
            except MatrixProfile.DoesNotExist:
                pass

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error finding Matrix profile: {e}'))

        return None

    def process_communities(self, limit=None, dry_run=False):
        """Process all communities"""
        communities = Community.nodes.filter(room_id__isnull=False)
        
        if limit:
            communities = list(communities)[:limit]

        processed_count = 0
        success_count = 0
        error_count = 0
        no_profile_count = 0

        for community in communities:
            processed_count += 1
            
            self.stdout.write(f'Processing community {processed_count}: {community.name} (UID: {community.uid})')

            # Find Matrix profile for this specific community
            admin_matrix_profile = self._find_matrix_profile_for_community(community)
            
            if not admin_matrix_profile:
                self.stdout.write(self.style.WARNING(f'  ⚠ No Matrix profile found for community {community.name}'))
                no_profile_count += 1
                continue

            if dry_run:
                self.stdout.write(f'  [DRY RUN] Would update Matrix room {community.room_id}')
                success_count += 1
                continue

            try:
                # Prepare complete community data - FIX: Include uid and name
                community_data = {
                    'community_type': community.community_type or '',
                    'community_circle': community.community_circle or '',
                    'category': community.category or '',
                    'created_date': str(community.created_date) if community.created_date else '',
                    'uid': community.uid,  # FIX: This was missing
                    'name': community.name or '',  # FIX: This was missing
                    'description': community.description or '',
                    'member_count': getattr(community, 'number_of_members', 0) or 0,
                    'tags': getattr(community, 'tags', []) or [],
                    'ai_generated': getattr(community, 'ai_generated', False),
                }

                # Update Matrix room data
                result = asyncio.run(set_room_avatar_score_and_filter(
                    access_token=admin_matrix_profile.access_token,
                    user_id=admin_matrix_profile.matrix_user_id,
                    room_id=community.room_id,
                    image_id=community.group_icon_id if community.group_icon_id else None,
                    community_data=community_data,
                    timeout=30
                ))

                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Successfully updated Matrix room {community.room_id}'))
                    success_count += 1
                else:
                    error_msg = result.get('error', 'Unknown error')
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed: {error_msg}'))
                    error_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error processing community {community.uid}: {str(e)}'))
                error_count += 1

        self.stdout.write(f'\nCommunities Summary:')
        self.stdout.write(f'  Total processed: {processed_count}')
        self.stdout.write(f'  Successful: {success_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write(f'  No Matrix profile: {no_profile_count}')
        
        return processed_count

    def process_sub_communities(self, limit=None, dry_run=False):
        """Process all sub-communities"""
        sub_communities = SubCommunity.nodes.filter(room_id__isnull=False)
        
        if limit:
            sub_communities = list(sub_communities)[:limit]

        processed_count = 0
        success_count = 0
        error_count = 0
        no_profile_count = 0

        for sub_community in sub_communities:
            processed_count += 1
            
            self.stdout.write(f'Processing sub-community {processed_count}: {sub_community.name} (UID: {sub_community.uid})')

            # Find Matrix profile for parent community or sub-community creator
            admin_matrix_profile = self._find_matrix_profile_for_community(sub_community)
            
            if not admin_matrix_profile:
                # Try parent community
                try:
                    parent = sub_community.parent_community.single()
                    if parent:
                        admin_matrix_profile = self._find_matrix_profile_for_community(parent)
                except:
                    pass
            
            if not admin_matrix_profile:
                self.stdout.write(self.style.WARNING(f'  ⚠ No Matrix profile found for sub-community {sub_community.name}'))
                no_profile_count += 1
                continue

            if dry_run:
                self.stdout.write(f'  [DRY RUN] Would update Matrix room {sub_community.room_id}')
                success_count += 1
                continue

            try:
                # Prepare complete sub-community data
                sub_community_data = {
                    'community_type': sub_community.sub_community_type or '',
                    'community_circle': sub_community.sub_community_circle or '',
                    'category': sub_community.category or '',
                    'created_date': str(sub_community.created_date) if sub_community.created_date else '',
                    'uid': sub_community.uid,
                    'name': sub_community.name or '',
                    'description': sub_community.description or '',
                    'member_count': getattr(sub_community, 'number_of_members', 0) or 0,
                }

                # Update Matrix room data
                result = asyncio.run(set_room_avatar_score_and_filter(
                    access_token=admin_matrix_profile.access_token,
                    user_id=admin_matrix_profile.matrix_user_id,
                    room_id=sub_community.room_id,
                    image_id=sub_community.group_icon_id if sub_community.group_icon_id else None,
                    community_data=sub_community_data,
                    timeout=30
                ))

                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Successfully updated Matrix room {sub_community.room_id}'))
                    success_count += 1
                else:
                    error_msg = result.get('error', 'Unknown error')
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed: {error_msg}'))
                    error_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error processing sub-community {sub_community.uid}: {str(e)}'))
                error_count += 1

        self.stdout.write(f'\nSub-communities Summary:')
        self.stdout.write(f'  Total processed: {processed_count}')
        self.stdout.write(f'  Successful: {success_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write(f'  No Matrix profile: {no_profile_count}')
        
        return processed_count