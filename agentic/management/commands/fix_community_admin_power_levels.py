from django.core.management.base import BaseCommand
from django.db import transaction
import asyncio
import logging
from typing import List, Dict, Any

from agentic.matrix_utils import set_agent_power_level, MatrixProfileUpdateError
from community.models import Community
from msg.models import MatrixProfile
from neomodel import DoesNotExist


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix community admin power levels to ensure they have full admin privileges (100) in their Matrix rooms'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually upgrading power levels'
        )
        parser.add_argument(
            '--community-uid',
            type=str,
            help='Process only a specific community by UID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force power level upgrade even if admin already has high privileges'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        community_uid = options.get('community_uid')
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting community admin power level fix {'(DRY RUN)' if dry_run else ''}"
            )
        )
        
        try:
            # Get communities that need admin power level fixes
            communities_to_fix = self._get_communities_to_fix(community_uid)
            
            if not communities_to_fix:
                self.stdout.write(
                    self.style.WARNING("No communities found that need admin power level fixes")
                )
                return
            
            self.stdout.write(
                f"Found {len(communities_to_fix)} communities that need admin power level fixes"
            )
            
            # Process communities
            results = self._process_communities(communities_to_fix, dry_run, force)
            
            # Print summary
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("SUMMARY:")
            self.stdout.write(f"Communities processed: {results['processed']}")
            self.stdout.write(
                self.style.SUCCESS(f"Successful fixes: {results['successful']}")
            )
            if results['failed'] > 0:
                self.stdout.write(
                    self.style.ERROR(f"Failed fixes: {results['failed']}")
                )
            self.stdout.write("=" * 50)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during community admin power level fix: {e}")
            )
            logger.error(f"Error during community admin power level fix: {e}")
            raise
    
    def _get_communities_to_fix(self, community_uid: str = None) -> List[Dict[str, Any]]:
        """
        Get communities that need admin power level fixes.
        
        Returns:
            List of community info dictionaries
        """
        communities = []
        
        try:
            # Get all communities with Matrix rooms
            all_communities = Community.nodes.all()
            
            for community in all_communities:
                try:
                    # Filter by community UID if specified
                    if community_uid and community.uid != community_uid:
                        continue
                    
                    # Check if community has a Matrix room
                    if not community.room_id:
                        continue
                    
                    # Find community admin with Matrix credentials
                    admin_matrix_profile = self._find_community_admin(community)
                    
                    if not admin_matrix_profile:
                        self.stdout.write(
                            self.style.WARNING(
                                f"No admin with Matrix credentials found for community {community.name}"
                            )
                        )
                        continue
                    
                    community_info = {
                        'community': community,
                        'community_name': community.name,
                        'community_uid': community.uid,
                        'room_id': community.room_id,
                        'admin_matrix_profile': admin_matrix_profile,
                        'admin_matrix_id': admin_matrix_profile.matrix_user_id,
                        'admin_access_token': admin_matrix_profile.access_token
                    }
                    
                    communities.append(community_info)
                    
                except Exception as e:
                    logger.error(f"Error processing community {community.uid}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error getting communities: {e}")
            raise
        
        return communities
    
    def _process_communities(self, communities: List[Dict[str, Any]], dry_run: bool, force: bool) -> Dict[str, int]:
        """
        Process communities for admin power level fixes.
        
        Returns:
            Dictionary with counts of processed, successful, and failed fixes
        """
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0
        }
        
        for community_info in communities:
            results['processed'] += 1
            
            community_name = community_info['community_name']
            room_id = community_info['room_id']
            admin_matrix_id = community_info['admin_matrix_id']
            admin_access_token = community_info['admin_access_token']
            
            try:
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would fix admin power level for community {community_name} "
                        f"(admin: {admin_matrix_id}, room: {room_id})"
                    )
                    results['successful'] += 1
                    continue
                
                # Set admin power level to 100 (full admin)
                success = asyncio.run(set_agent_power_level(
                    admin_access_token=admin_access_token,
                    admin_matrix_id=admin_matrix_id,
                    room_id=room_id,
                    agent_matrix_id=admin_matrix_id,  # Setting power level for the admin themselves
                    power_level=100,  # Full admin privileges
                    timeout=10
                ))
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Fixed admin power level for community {community_name} "
                            f"(admin: {admin_matrix_id})"
                        )
                    )
                    results['successful'] += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Failed to fix admin power level for community {community_name} "
                            f"(admin: {admin_matrix_id})"
                        )
                    )
                    results['failed'] += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error fixing admin power level for community {community_name}: {e}"
                    )
                )
                logger.error(f"Error fixing admin power level for community {community_name}: {e}")
                results['failed'] += 1
        
        return results
    
    def _find_community_admin(self, community):
        """
        Find a community admin with Matrix credentials.
        
        Returns:
            MatrixProfile instance or None
        """
        try:
            # Get community memberships where user is admin
            for membership in community.members.all():
                if membership.is_admin:
                    try:
                        # Get the user's Django user_id from their Neo4j relationship
                        user_node = membership.user.single()
                        if user_node and hasattr(user_node, 'user_id'):
                            admin_matrix_profile = MatrixProfile.objects.get(user=user_node.user_id)
                            if admin_matrix_profile.matrix_user_id and admin_matrix_profile.access_token:
                                return admin_matrix_profile
                    except (MatrixProfile.DoesNotExist, AttributeError):
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding community admin: {e}")
            return None