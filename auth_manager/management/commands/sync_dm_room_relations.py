# auth_manager/management/commands/sync_dm_room_relations.py

from django.core.management.base import BaseCommand
from auth_manager.models import Users
from connection.models import Connection
from msg.models import MatrixProfile
from auth_manager.Utils import generate_presigned_url
import asyncio
import aiohttp
from django.conf import settings
from asgiref.sync import sync_to_async
import logging

matrix_logger = logging.getLogger("matrix_logger")


class Command(BaseCommand):
    help = 'Sync relation data and user profile data to all existing DM rooms'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=10, help='Process users in batches')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
        parser.add_argument('--user-id', type=int, help='Process only specific user ID')
        parser.add_argument('--limit', type=int, help='Limit number of users to process')
        parser.add_argument('--update-profile-only', action='store_true', help='Update only user profile data, skip DM rooms')
        parser.add_argument('--verbose', action='store_true', help='Show detailed output')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        user_id = options.get('user_id')
        limit = options.get('limit')
        update_profile_only = options['update_profile_only']
        self.verbose = options.get('verbose', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get users with Matrix profiles
        if user_id:
            matrix_profiles = MatrixProfile.objects.filter(
                user=user_id,
                access_token__isnull=False,
                matrix_user_id__isnull=False
            )
        else:
            matrix_profiles = MatrixProfile.objects.filter(
                access_token__isnull=False,
                matrix_user_id__isnull=False
            ).order_by('user')

        if limit:
            matrix_profiles = list(matrix_profiles)[:limit]

        total = len(matrix_profiles) if isinstance(matrix_profiles, list) else matrix_profiles.count()
        self.stdout.write(f"Found {total} users with Matrix profiles")

        processed = 0
        success = 0
        failed = 0
        no_connections = 0
        no_dm_rooms = 0

        for i in range(0, total, batch_size):
            if isinstance(matrix_profiles, list):
                batch = matrix_profiles[i:i+batch_size]
            else:
                batch = list(matrix_profiles[i:i+batch_size])

            for matrix_profile in batch:
                try:
                    user_node = Users.nodes.get(user_id=matrix_profile.user.id)
                    processed += 1

                    self.stdout.write(f"\n[{processed}/{total}] Processing user: {user_node.email} (ID: {matrix_profile.user.id})")

                    if dry_run:
                        self.stdout.write(f"  [DRY RUN] Would update user profile and DM rooms")
                        success += 1
                        continue

                    # Step 1: Update user profile in Matrix account data
                    profile_result = asyncio.run(self._update_user_profile(
                        matrix_profile=matrix_profile,
                        user_node=user_node
                    ))

                    if profile_result.get('success'):
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Updated user profile"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  ⚠ Profile update: {profile_result.get('error')}"))

                    # Step 2: Update DM rooms
                    if not update_profile_only:
                        connections = user_node.connection.filter(connection_status='Accepted')
                        
                        if not connections:
                            self.stdout.write(f"  ⚠ No accepted connections")
                            no_connections += 1
                            continue

                        # Update DM rooms
                        result = asyncio.run(self._update_user_dm_rooms(
                            matrix_profile=matrix_profile,
                            user_node=user_node,
                            connections=connections
                        ))

                        if result['updated_rooms'] > 0:
                            self.stdout.write(self.style.SUCCESS(f"  ✓ Updated {result['updated_rooms']} DM rooms"))
                            success += 1
                        elif result['no_dm_rooms']:
                            self.stdout.write(f"  ⚠ No DM rooms found")
                            no_dm_rooms += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"  ⚠ No rooms updated"))

                        if result.get('errors'):
                            for error in result['errors'][:3]:
                                self.stdout.write(self.style.ERROR(f"    Error: {error}"))
                            if len(result['errors']) > 3:
                                self.stdout.write(self.style.ERROR(f"    ... and {len(result['errors']) - 3} more errors"))
                            failed += 1
                    else:
                        success += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
                    import traceback
                    if self.verbose:
                        self.stdout.write(traceback.format_exc())
                    failed += 1

            # Small delay between batches
            if not dry_run:
                import time
                time.sleep(0.5)

        # Print summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SYNC SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f"Total processed: {processed}")
        self.stdout.write(f"Successfully updated: {self.style.SUCCESS(str(success))}")
        self.stdout.write(f"No connections: {no_connections}")
        self.stdout.write(f"No DM rooms: {no_dm_rooms}")
        self.stdout.write(f"Failed: {self.style.ERROR(str(failed))}")
        self.stdout.write(self.style.SUCCESS('='*60))

    @sync_to_async
    def _get_matrix_profile_sync(self, user_id):
        """Get MatrixProfile in sync context"""
        try:
            return MatrixProfile.objects.get(user=user_id)
        except MatrixProfile.DoesNotExist:
            return None

    @sync_to_async
    def _generate_file_info_sync(self, image_id):
        """Generate file info in sync context"""
        try:
            return generate_presigned_url.generate_file_info(image_id)
        except Exception as e:
            return None

    async def _update_user_profile(self, matrix_profile, user_node):
        """Update user profile in Matrix account data"""
        try:
            headers = {
                "Authorization": f"Bearer {matrix_profile.access_token}",
                "Content-Type": "application/json"
            }

            # Prepare profile data with avatar
            profile_data = {
                "user_id": user_node.user_id,
                "uid": user_node.uid,
                "overall_score": 4.0,
                "user_type": getattr(user_node, 'user_type', ''),
                "full_name": getattr(user_node, 'full_name', ''),
                "email": user_node.email,
                "updated_at": int(asyncio.get_event_loop().time())
            }

            # Get avatar URL if profile image exists
            profile_image_id = getattr(user_node, 'profile_image_id', None)
            if profile_image_id:
                try:
                    file_info = await self._generate_file_info_sync(profile_image_id)
                    if file_info and file_info.get('url'):
                        profile_data["avatar_url"] = file_info['url']
                except Exception as e:
                    pass

            # Set profile data
            profile_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/user/{matrix_profile.matrix_user_id}/account_data/com.ooumph.user.profile"

            async with aiohttp.ClientSession() as session:
                async with session.put(profile_url, json=profile_data, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return {"success": True}
                    else:
                        response_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {response_text}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _update_user_dm_rooms(self, matrix_profile, user_node, connections):
        """Update all DM rooms for a user with relation and user data"""
        result = {
            'updated_rooms': 0,
            'failed_rooms': 0,
            'no_dm_rooms': False,
            'errors': []
        }

        try:
            # Get all DM rooms for this user
            dm_rooms_map = await self._get_user_dm_rooms(
                matrix_profile.access_token,
                matrix_profile.matrix_user_id
            )

            if not dm_rooms_map:
                result['no_dm_rooms'] = True
                return result

            total_rooms = sum(len(rooms) if isinstance(rooms, list) else 1 for rooms in dm_rooms_map.values())
            self.stdout.write(f"  Found {total_rooms} DM rooms")

            # Process each connection
            for connection in connections:
                try:
                    # Get the other user in connection
                    created_by = connection.created_by.single()
                    receiver = connection.receiver.single()
                    
                    other_user = receiver if created_by.user_id == user_node.user_id else created_by

                    # Get other user's Matrix profile
                    other_matrix_profile = await self._get_matrix_profile_sync(other_user.user_id)
                    if not other_matrix_profile:
                        if self.verbose:
                            self.stdout.write(f"    ⚠ No Matrix profile for {other_user.email}")
                        continue

                    other_user_matrix_id = other_matrix_profile.matrix_user_id

                    # Get current user's avatar
                    current_user_avatar = None
                    current_user_profile_image_id = getattr(user_node, 'profile_image_id', None)
                    if current_user_profile_image_id:
                        try:
                            file_info = await self._generate_file_info_sync(current_user_profile_image_id)
                            if file_info and file_info.get('url'):
                                current_user_avatar = file_info['url']
                        except:
                            pass

                    # Get other user's avatar
                    other_user_avatar = None
                    other_user_profile_image_id = getattr(other_user, 'profile_image_id', None)
                    if other_user_profile_image_id:
                        try:
                            file_info = await self._generate_file_info_sync(other_user_profile_image_id)
                            if file_info and file_info.get('url'):
                                other_user_avatar = file_info['url']
                        except:
                            pass

                    # Find DM room with this user
                    dm_room_id = dm_rooms_map.get(other_user_matrix_id)
                    if not dm_room_id:
                        if self.verbose:
                            self.stdout.write(f"    ⚠ No DM room with {other_user.email}")
                        continue

                    # If dm_room_id is a list, take the first room
                    if isinstance(dm_room_id, list):
                        dm_room_id = dm_room_id[0]

                    # Get relation from circle
                    circle = connection.circle.single()
                    if not circle or not circle.relation:
                        if self.verbose:
                            self.stdout.write(f"    ⚠ No relation for connection with {other_user.email}")
                        continue

                    # CRITICAL FIX: Update room state event with BOTH users' data
                    # This creates a single source of truth visible to both users
                    update_result = await self._set_dm_room_state_event(
                        access_token=matrix_profile.access_token,
                        room_id=dm_room_id,
                        relation=circle.relation,
                        user1_matrix_id=matrix_profile.matrix_user_id,
                        user1_uid=user_node.uid,
                        user1_name=getattr(user_node, 'full_name', '') or user_node.email,
                        user1_email=user_node.email,
                        user1_avatar=current_user_avatar,
                        user2_matrix_id=other_user_matrix_id,
                        user2_uid=other_user.uid,
                        user2_name=getattr(other_user, 'full_name', '') or other_user.email,
                        user2_email=other_user.email,
                        user2_avatar=other_user_avatar
                    )

                    if update_result.get('success'):
                        result['updated_rooms'] += 1
                        avatar_status = ""
                        if current_user_avatar and other_user_avatar:
                            avatar_status = " (both avatars)"
                        elif current_user_avatar or other_user_avatar:
                            avatar_status = " (one avatar)"
                        self.stdout.write(f"    ✓ Updated DM with {other_user.email} - relation: '{circle.relation}'{avatar_status}")
                    else:
                        result['failed_rooms'] += 1
                        error_msg = update_result.get('error', 'Unknown')[:150]
                        result['errors'].append(f"DM with {other_user.email}: {error_msg}")
                        if self.verbose:
                            self.stdout.write(self.style.ERROR(f"    ✗ Failed: {error_msg}"))

                except Exception as e:
                    error_msg = str(e)[:150]
                    result['errors'].append(f"Connection error: {error_msg}")
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f"    ✗ Exception: {error_msg}"))
                        import traceback
                        self.stdout.write(traceback.format_exc())

        except Exception as e:
            result['errors'].append(f"DM rooms error: {str(e)}")

        return result

    async def _get_user_dm_rooms(self, access_token, user_id):
        """Get all DM rooms for a user from m.direct"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            direct_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/user/{user_id}/account_data/m.direct"

            async with aiohttp.ClientSession() as session:
                async with session.get(direct_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        if self.verbose:
                            response_text = await response.text()
                            self.stdout.write(f"    Failed to get m.direct: {response.status} - {response_text}")
                        return {}

        except Exception as e:
            if self.verbose:
                self.stdout.write(f"    Exception getting m.direct: {str(e)}")
            return {}

    async def _set_dm_room_state_event(self, access_token, room_id, relation,
                                      user1_matrix_id, user1_uid, user1_name, user1_email, user1_avatar,
                                      user2_matrix_id, user2_uid, user2_name, user2_email, user2_avatar):
        """
        Set room state event with BOTH users' data.
        This is the key fix - storing both users' data in the room state
        makes it accessible to both participants without needing separate tokens.
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # Store BOTH users' data in the room state event
            dm_data = {
                "relation": relation,
                "room_type": "dm",
                "updated_at": str(int(asyncio.get_event_loop().time())),
                "users": {
                    user1_matrix_id: {
                        "matrix_id": user1_matrix_id,
                        "uid": user1_uid or '',
                        "name": user1_name or '',
                        "email": user1_email or '',
                        "avatar_url": user1_avatar or '',
                        "overall_score": "4.0"
                    },
                    user2_matrix_id: {
                        "matrix_id": user2_matrix_id,
                        "uid": user2_uid or '',
                        "name": user2_name or '',
                        "email": user2_email or '',
                        "avatar_url": user2_avatar or '',
                        "overall_score": "4.0"
                    }
                }
            }

            # Use room state event - visible to all room members
            dm_data_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.dm.data"

            async with aiohttp.ClientSession() as session:
                async with session.put(dm_data_url, json=dm_data, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return {"success": True}
                    else:
                        response_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {response_text}"}

        except Exception as e:
            return {"success": False, "error": str(e)[:150]}
