# community/management/commands/verify_matrix_room_data.py

from django.core.management.base import BaseCommand
import asyncio
import aiohttp
from django.conf import settings
from community.models import Community, SubCommunity
from msg.models import MatrixProfile
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Verify Matrix room data for all communities and sub-communities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--community-only',
            action='store_true',
            help='Verify only communities (skip sub-communities)',
        )
        parser.add_argument(
            '--sub-community-only',
            action='store_true',
            help='Verify only sub-communities (skip communities)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number to verify',
        )
        parser.add_argument(
            '--show-full-data',
            action='store_true',
            help='Show complete Matrix data for each room',
        )
        parser.add_argument(
            '--export-json',
            type=str,
            help='Export results to JSON file',
        )
        parser.add_argument(
            '--check-missing-only',
            action='store_true',
            help='Only show rooms with missing or incomplete data',
        )

    def handle(self, *args, **options):
        community_only = options['community_only']
        sub_community_only = options['sub_community_only']
        limit = options['limit']
        show_full_data = options['show_full_data']
        export_json = options['export_json']
        check_missing_only = options['check_missing_only']

        results = {
            'timestamp': str(datetime.now()),
            'communities': [],
            'sub_communities': [],
            'summary': {
                'total_communities': 0,
                'communities_with_data': 0,
                'communities_without_data': 0,
                'communities_with_complete_data': 0,
                'communities_with_inconsistent_data': 0,
                'total_sub_communities': 0,
                'sub_communities_with_data': 0,
                'sub_communities_without_data': 0,
                'sub_communities_with_complete_data': 0,
                'sub_communities_with_inconsistent_data': 0,
            }
        }

        # Get a valid Matrix profile for API calls
        matrix_profile = self._get_any_matrix_profile()
        if not matrix_profile:
            self.stdout.write(self.style.ERROR('No valid Matrix profile found for verification'))
            return

        # Verify communities
        if not sub_community_only:
            self.stdout.write(self.style.SUCCESS('Verifying communities...'))
            community_results = asyncio.run(
                self.verify_communities(matrix_profile, limit, show_full_data, check_missing_only)
            )
            results['communities'] = community_results
            results['summary']['total_communities'] = len(community_results)
            results['summary']['communities_with_data'] = sum(1 for c in community_results if c['has_matrix_data'])
            results['summary']['communities_without_data'] = sum(1 for c in community_results if not c['has_matrix_data'])
            results['summary']['communities_with_complete_data'] = sum(1 for c in community_results if c['has_matrix_data'] and c['data_completeness']['complete'])
            results['summary']['communities_with_inconsistent_data'] = sum(1 for c in community_results if c['has_matrix_data'] and not c['data_consistency']['consistent'])

        # Verify sub-communities
        if not community_only:
            self.stdout.write(self.style.SUCCESS('Verifying sub-communities...'))
            sub_community_results = asyncio.run(
                self.verify_sub_communities(matrix_profile, limit, show_full_data, check_missing_only)
            )
            results['sub_communities'] = sub_community_results
            results['summary']['total_sub_communities'] = len(sub_community_results)
            results['summary']['sub_communities_with_data'] = sum(1 for s in sub_community_results if s['has_matrix_data'])
            results['summary']['sub_communities_without_data'] = sum(1 for s in sub_community_results if not s['has_matrix_data'])
            results['summary']['sub_communities_with_complete_data'] = sum(1 for s in sub_community_results if s['has_matrix_data'] and s['data_completeness']['complete'])
            results['summary']['sub_communities_with_inconsistent_data'] = sum(1 for s in sub_community_results if s['has_matrix_data'] and not s['data_consistency']['consistent'])

        # Print summary
        self._print_summary(results['summary'])

        # Export to JSON if requested
        if export_json:
            self._export_to_json(results, export_json)

        self.stdout.write(self.style.SUCCESS('\nVerification completed!'))

    def _get_any_matrix_profile(self):
        """Get any valid Matrix profile for API calls"""
        try:
            return MatrixProfile.objects.filter(
                access_token__isnull=False,
                matrix_user_id__isnull=False
            ).exclude(access_token='').first()
        except:
            return None

    async def verify_communities(self, matrix_profile, limit=None, show_full_data=False, check_missing_only=False):
        """Verify all communities"""
        communities = Community.nodes.filter(room_id__isnull=False)
        
        if limit:
            communities = list(communities)[:limit]

        results = []
        count = 0

        for community in communities:
            count += 1
            self.stdout.write(f'Checking community {count}: {community.name}')

            matrix_data = await self._fetch_room_data(
                matrix_profile.access_token,
                community.room_id
            )

            has_data = matrix_data is not None and 'error' not in matrix_data
            
            result = {
                'name': community.name,
                'uid': community.uid,
                'room_id': community.room_id,
                'has_matrix_data': has_data,
                'matrix_data': matrix_data if show_full_data else None,
                'database_data': {
                    'community_type': community.community_type,
                    'community_circle': community.community_circle,
                    'category': community.category,
                    'created_date': str(community.created_date) if community.created_date else '',
                    'community_uid': community.uid,
                    'community_name': community.name,
                    'group_icon_id': community.group_icon_id,
                    'member_count': getattr(community, 'number_of_members', 0),
                }
            }

            # Check data completeness
            if has_data and matrix_data:
                result['data_completeness'] = self._check_data_completeness(matrix_data, 'community')
                result['data_consistency'] = self._check_data_consistency(matrix_data, result['database_data'], 'community')
            else:
                result['data_completeness'] = {'complete': False, 'missing_fields': []}
                result['data_consistency'] = {'consistent': False, 'inconsistencies': []}

            # Only show if missing data or show all
            if not check_missing_only or not has_data or not result['data_completeness']['complete']:
                results.append(result)
                self._print_community_status(result, show_full_data)

        return results

    async def verify_sub_communities(self, matrix_profile, limit=None, show_full_data=False, check_missing_only=False):
        """Verify all sub-communities"""
        sub_communities = SubCommunity.nodes.filter(room_id__isnull=False)
        
        if limit:
            sub_communities = list(sub_communities)[:limit]

        results = []
        count = 0

        for sub_community in sub_communities:
            count += 1
            self.stdout.write(f'Checking sub-community {count}: {sub_community.name}')

            matrix_data = await self._fetch_room_data(
                matrix_profile.access_token,
                sub_community.room_id
            )

            has_data = matrix_data is not None and 'error' not in matrix_data
            
            result = {
                'name': sub_community.name,
                'uid': sub_community.uid,
                'room_id': sub_community.room_id,
                'has_matrix_data': has_data,
                'matrix_data': matrix_data if show_full_data else None,
                'database_data': {
                    'community_type': sub_community.sub_community_type,
                    'community_circle': sub_community.sub_community_circle,
                    'category': sub_community.category,
                    'created_date': str(sub_community.created_date) if sub_community.created_date else '',
                    'community_uid': sub_community.uid,
                    'community_name': sub_community.name,
                    'group_icon_id': sub_community.group_icon_id,
                    'member_count': getattr(sub_community, 'number_of_members', 0),
                }
            }

            # Check data completeness
            if has_data and matrix_data:
                result['data_completeness'] = self._check_data_completeness(matrix_data, 'sub_community')
                result['data_consistency'] = self._check_data_consistency(matrix_data, result['database_data'], 'sub_community')
            else:
                result['data_completeness'] = {'complete': False, 'missing_fields': []}
                result['data_consistency'] = {'consistent': False, 'inconsistencies': []}

            # Only show if missing data or show all
            if not check_missing_only or not has_data or not result['data_completeness']['complete']:
                results.append(result)
                self._print_community_status(result, show_full_data)

        return results

    async def _fetch_room_data(self, access_token, room_id):
        """Fetch Matrix room data from API"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{settings.MATRIX_SERVER_URL}/_matrix/client/r0/rooms/{room_id}/state/com.ooumph.room.data"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return {'error': 'No Matrix data found'}
                    else:
                        return {'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'error': str(e)}

    def _check_data_completeness(self, matrix_data, entity_type):
        """Check if Matrix data has all required fields"""
        required_fields = [
            'overall_score',
            'room_type',
            'community_type',
            'community_circle',
            'community_category',
            'created_date',
            'community_uid',
            'community_name',
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in matrix_data or not matrix_data[field]:
                missing_fields.append(field)
        
        return {
            'complete': len(missing_fields) == 0,
            'missing_fields': missing_fields
        }

    def _check_data_consistency(self, matrix_data, database_data, entity_type):
        """Check if Matrix data matches database data"""
        inconsistencies = []
        
        # Map database fields to Matrix fields
        field_mapping = {
            'community_type': 'community_type',
            'community_circle': 'community_circle', 
            'category': 'community_category',
            'created_date': 'created_date',
            'community_uid': 'community_uid',
            'community_name': 'community_name',
        }
        
        for db_field, matrix_field in field_mapping.items():
            db_value = str(database_data.get(db_field, '')).strip()
            matrix_value = str(matrix_data.get(matrix_field, '')).strip()
            
            if db_value != matrix_value:
                inconsistencies.append({
                    'field': matrix_field,
                    'database_value': db_value,
                    'matrix_value': matrix_value
                })
        
        return {
            'consistent': len(inconsistencies) == 0,
            'inconsistencies': inconsistencies
        }

    def _print_community_status(self, result, show_full_data):
        """Print status for a single community"""
        if result['has_matrix_data']:
            if result['data_completeness']['complete']:
                if result['data_consistency']['consistent']:
                    self.stdout.write(f"  ✓ {self.style.SUCCESS('Has complete and consistent Matrix data')}")
                else:
                    self.stdout.write(f"  ⚠ {self.style.WARNING('Has complete Matrix data but with inconsistencies')}")
                    for inconsistency in result['data_consistency']['inconsistencies']:
                        self.stdout.write(f"    - {inconsistency['field']}: DB='{inconsistency['database_value']}' vs Matrix='{inconsistency['matrix_value']}'")
            else:
                missing = ', '.join(result['data_completeness']['missing_fields'])
                self.stdout.write(f"  ⚠ {self.style.WARNING(f'Incomplete data. Missing: {missing}')}")
                
                # Also show inconsistencies if any
                if not result['data_consistency']['consistent']:
                    for inconsistency in result['data_consistency']['inconsistencies']:
                        self.stdout.write(f"    - {inconsistency['field']}: DB='{inconsistency['database_value']}' vs Matrix='{inconsistency['matrix_value']}'")
        else:
            error = result['matrix_data'].get('error', 'Unknown error') if result['matrix_data'] else 'No data'
            self.stdout.write(f"  ✗ {self.style.ERROR(f'No Matrix data: {error}')}")

        if show_full_data and result['matrix_data']:
            self.stdout.write(f"  Matrix Data: {json.dumps(result['matrix_data'], indent=2)}")
            self.stdout.write(f"  Database Data: {json.dumps(result['database_data'], indent=2)}")

    def _print_summary(self, summary):
        """Print verification summary"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('VERIFICATION SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write(f"\nCommunities:")
        self.stdout.write(f"  Total: {summary['total_communities']}")
        self.stdout.write(f"  With Matrix data: {self.style.SUCCESS(str(summary['communities_with_data']))}")
        self.stdout.write(f"  Without Matrix data: {self.style.ERROR(str(summary['communities_without_data']))}")
        self.stdout.write(f"  With complete data: {self.style.SUCCESS(str(summary['communities_with_complete_data']))}")
        self.stdout.write(f"  With inconsistent data: {self.style.WARNING(str(summary['communities_with_inconsistent_data']))}")
        
        if summary['total_communities'] > 0:
            percentage = (summary['communities_with_data'] / summary['total_communities']) * 100
            self.stdout.write(f"  Coverage: {percentage:.1f}%")
            
            if summary['communities_with_data'] > 0:
                consistency_percentage = ((summary['communities_with_data'] - summary['communities_with_inconsistent_data']) / summary['communities_with_data']) * 100
                self.stdout.write(f"  Data consistency: {consistency_percentage:.1f}%")
        
        self.stdout.write(f"\nSub-communities:")
        self.stdout.write(f"  Total: {summary['total_sub_communities']}")
        self.stdout.write(f"  With Matrix data: {self.style.SUCCESS(str(summary['sub_communities_with_data']))}")
        self.stdout.write(f"  Without Matrix data: {self.style.ERROR(str(summary['sub_communities_without_data']))}")
        self.stdout.write(f"  With complete data: {self.style.SUCCESS(str(summary['sub_communities_with_complete_data']))}")
        self.stdout.write(f"  With inconsistent data: {self.style.WARNING(str(summary['sub_communities_with_inconsistent_data']))}")
        
        if summary['total_sub_communities'] > 0:
            percentage = (summary['sub_communities_with_data'] / summary['total_sub_communities']) * 100
            self.stdout.write(f"  Coverage: {percentage:.1f}%")
            
            if summary['sub_communities_with_data'] > 0:
                consistency_percentage = ((summary['sub_communities_with_data'] - summary['sub_communities_with_inconsistent_data']) / summary['sub_communities_with_data']) * 100
                self.stdout.write(f"  Data consistency: {consistency_percentage:.1f}%")
        
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

    def _export_to_json(self, results, filename):
        """Export results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f'\nResults exported to {filename}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to export to JSON: {e}'))