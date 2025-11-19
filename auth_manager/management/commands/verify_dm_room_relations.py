# auth_manager/management/commands/verify_dm_room_relations.py

from django.core.management.base import BaseCommand
from msg.models import MatrixProfile
import asyncio
import aiohttp
from django.conf import settings
import json


class Command(BaseCommand):
    help = 'Verify DM room relation data'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='Check specific user')
        parser.add_argument('--limit', type=int, default=10, help='Limit users to check')
        parser.add_argument('--show-sample', action='store_true', help='Show sample DM data')

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        limit = options['limit']
        show_sample = options['show_sample']

        self.stdout.write(self.style.SUCCESS('Verifying DM room relations...\n'))

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
            )[:limit]

        total_users = 0
        total_dm_rooms = 0
        total_with_data = 0
        total_without_data = 0
        total_with_avatar = 0
        total_without_avatar = 0

        for matrix_profile in matrix_profiles:
            total_users += 1
            self.stdout.write(f"\n[{total_users}] Checking user ID: {matrix_profile.user}")
            
            result = asyncio.run(self._check_user_dm_rooms(matrix_profile, show_sample))
            
            if result['dm_rooms']:
                total_dm_rooms += result['total_rooms']
                total_with_data += result['with_data']
                total_without_data += result['without_data']
                total_with_avatar += result['with_avatar']
                total_without_avatar += result['without_avatar']

                self.stdout.write(f"  Total DM rooms: {result['total_rooms']}")
                self.stdout.write(f"  With relation data: {self.style.SUCCESS(str(result['with_data']))}")
                self.stdout.write(f"  Without relation data: {self.style.ERROR(str(result['without_data']))}")
                
                if result['with_data'] > 0:
                    self.stdout.write(f"  With avatar: {self.style.SUCCESS(str(result['with_avatar']))}")
                    self.stdout.write(f"  Without avatar: {self.style.WARNING(str(result['without_avatar']))}")
                
                if show_sample and result['sample_data']:
                    self.stdout.write(f"  Sample data:")
                    self.stdout.write(f"    {json.dumps(result['sample_data'], indent=4)}")
            else:
                self.stdout.write("  No DM rooms found")

        # Print summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('VERIFICATION SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f"Total users checked: {total_users}")
        self.stdout.write(f"Total DM rooms: {total_dm_rooms}")
        self.stdout.write(f"DM rooms with relation data: {self.style.SUCCESS(str(total_with_data))}")
        self.stdout.write(f"DM rooms without relation data: {self.style.ERROR(str(total_without_data))}")
        
        if total_with_data > 0:
            coverage = (total_with_data / total_dm_rooms * 100) if total_dm_rooms > 0 else 0
            self.stdout.write(f"Coverage: {coverage:.1f}%")
            self.stdout.write(f"DM rooms with avatar: {self.style.SUCCESS(str(total_with_avatar))}")
            self.stdout.write(f"DM rooms without avatar: {self.style.WARNING(str(total_without_avatar))}")
        
        self.stdout.write(self.style.SUCCESS('='*60))

    async def _check_user_dm_rooms(self, matrix_profile, show_sample):
        """Check DM rooms for a user"""
        result = {
            'dm_rooms': False,
            'total_rooms': 0,
            'with_data': 0,
            'without_data': 0,
            'with_avatar': 0,
            'without_avatar': 0,
            'sample_data': None
        }

        try:
            headers = {
                "Authorization": f"Bearer {matrix_profile.access_token}",
                "Content-Type": "application/json"
            }

            # Get m.direct account data
            direct_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/user/{matrix_profile.matrix_user_id}/account_data/m.direct"

            async with aiohttp.ClientSession() as session:
                async with session.get(direct_url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        return result

                    direct_data = await response.json()
                    
                    # Extract all room IDs
                    all_rooms = []
                    for rooms in direct_data.values():
                        if isinstance(rooms, list):
                            all_rooms.extend(rooms)
                        else:
                            all_rooms.append(rooms)

                    if not all_rooms:
                        return result

                    result['dm_rooms'] = True
                    result['total_rooms'] = len(all_rooms)

                    # Check first 5 rooms for relation data
                    for room_id in all_rooms[:5]:
                        dm_data_url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.dm.data"
                        
                        try:
                            async with session.get(dm_data_url, headers=headers, timeout=5) as dm_response:
                                if dm_response.status == 200:
                                    dm_data = await dm_response.json()
                                    result['with_data'] += 1
                                    
                                    # Check if has avatar
                                    if dm_data.get('other_user_avatar_url'):
                                        result['with_avatar'] += 1
                                    else:
                                        result['without_avatar'] += 1
                                    
                                    # Save first sample
                                    if not result['sample_data']:
                                        result['sample_data'] = dm_data
                                else:
                                    result['without_data'] += 1
                        except Exception as e:
                            result['without_data'] += 1

        except Exception as e:
            print(f"Error checking DM rooms: {e}")

        return result