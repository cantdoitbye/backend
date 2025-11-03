from django.core.management.base import BaseCommand
from django.db import transaction
import asyncio
import aiohttp
from django.conf import settings
from community.models import Community, SubCommunity
from community import matrix_logger
from auth_manager.Utils.generate_presigned_url import generate_file_info
from concurrent.futures import ThreadPoolExecutor
from msg.models import MatrixProfile
import json
from typing import Dict, Any, Optional


class Command(BaseCommand):
    help = 'Force update Matrix room avatar and filter data for all existing communities and sub-communities using Matrix admin API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--community-only',
            action='store_true',
            help='Update only communities (skip sub-communities)',
        )
        parser.add_argument(
            '--sub-community-only',
            action='store_true',
            help='Update only sub-communities (skip communities)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of communities/sub-communities to process',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        community_only = options['community_only']
        sub_community_only = options['sub_community_only']
        limit = options['limit']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        self.stdout.write(self.style.SUCCESS('Using individual Matrix profiles for updates'))

        # Process communities
        if not sub_community_only:
            self.stdout.write('Processing communities...')
            communities_processed = self.process_communities(limit, dry_run)
            self.stdout.write(
                self.style.SUCCESS(f'Processed {communities_processed} communities')
            )

        # Process sub-communities
        if not community_only:
            self.stdout.write('Processing sub-communities...')
            sub_communities_processed = self.process_sub_communities(limit, dry_run)
            self.stdout.write(
                self.style.SUCCESS(f'Processed {sub_communities_processed} sub-communities')
            )

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

    async def update_matrix_room_data(
        self,
        access_token: str,
        user_id: str,
        room_id: str,
        image_id: str = None,
        community_data: Dict[str, Any] = None,
        timeout: int = 30
    ) -> dict:
        """
        Update Matrix room data using user access token.
        """
        print(f"DEBUG: Updating room data for room {room_id}")
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare combined room data
            room_data = {
                "overall_score": "4.0",
                "room_type": "community",
                "updated_at": str(int(asyncio.get_event_loop().time()))
            }
            
            # Add avatar URL if image_id provided
            if image_id:
                try:
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        file_info = await loop.run_in_executor(
                            executor,
                            generate_file_info,
                            image_id
                        )
                    
                    if file_info and file_info.get('url'):
                        room_data["avatar_url"] = file_info['url']
                        print(f"DEBUG: Avatar URL added: {file_info['url']}")
                except Exception as e:
                    print(f"DEBUG: Error getting avatar URL: {e}")
            
            # Add community filter data if provided
            if community_data:
                room_data.update({
                    "community_type": community_data.get('community_type', ''),
                    "community_circle": community_data.get('community_circle', ''),
                    "community_category": community_data.get('category', ''),
                    "created_date": str(community_data.get('created_date', '')),
                    "community_uid": community_data.get('community_uid', ''),
                    "community_name": community_data.get('community_name', '')
                })
                print(f"DEBUG: Community filter data added")
            
            # Use admin API to set room state
            room_state_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.room.data"
            
            print(f"DEBUG: Setting room data in Matrix: {room_data}")
            
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    room_state_url,
                    headers=headers,
                    json=room_data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"DEBUG: Successfully updated room data: {result}")
                        return {"success": True, "data": result}
                    else:
                        error_text = await response.text()
                        print(f"DEBUG: Failed to update room data: {response.status} - {error_text}")
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            print(f"DEBUG: Error updating room data: {e}")
            return {"success": False, "error": str(e)}

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
                # Prepare community data with all required fields (matching mutations exactly)
                community_data = {
                    'community_type': community.community_type or '',
                    'community_circle': community.community_circle or '',
                    'category': community.category or '',
                    'created_date': str(community.created_date) if community.created_date else '',
                    'community_uid': community.uid,
                    'community_name': community.name or '',
                }

                # Update Matrix room data using user access token
                result = asyncio.run(self.update_matrix_room_data(
                    access_token=admin_matrix_profile.access_token,
                    user_id=admin_matrix_profile.matrix_user_id,
                    room_id=community.room_id,
                    image_id=community.group_icon_id if community.group_icon_id else None,
                    community_data=community_data,
                    timeout=30
                ))

                if result.get('success'):
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Successfully updated Matrix room {community.room_id}')
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to update Matrix room {community.room_id}: {result.get("error", "Unknown error")}')
                    )
                    error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error processing community {community.uid}: {str(e)}')
                )
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
                # Prepare sub-community data with all required fields (matching mutations exactly)
                sub_community_data = {
                    'community_type': sub_community.sub_community_type or '',
                    'community_circle': sub_community.sub_community_circle or '',
                    'category': sub_community.category or '',
                    'created_date': str(sub_community.created_date) if sub_community.created_date else '',
                    'community_uid': sub_community.uid,
                    'community_name': sub_community.name or '',
                }

                # Update Matrix room data using user access token
                result = asyncio.run(self.update_matrix_room_data(
                    access_token=admin_matrix_profile.access_token,
                    user_id=admin_matrix_profile.matrix_user_id,
                    room_id=sub_community.room_id,
                    image_id=sub_community.group_icon_id if sub_community.group_icon_id else None,
                    community_data=sub_community_data,
                    timeout=30
                ))

                if result.get('success'):
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Successfully updated Matrix room {sub_community.room_id}')
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to update Matrix room {sub_community.room_id}: {result.get("error", "Unknown error")}')
                    )
                    error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error processing sub-community {sub_community.uid}: {str(e)}')
                )
                error_count += 1

        self.stdout.write(f'\nSub-communities Summary:')
        self.stdout.write(f'  Total processed: {processed_count}')
        self.stdout.write(f'  Successful: {success_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write(f'  No Matrix profile: {no_profile_count}')
        
        return processed_count
