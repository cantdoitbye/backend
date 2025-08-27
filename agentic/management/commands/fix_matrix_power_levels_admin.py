import asyncio
from django.core.management.base import BaseCommand, CommandError
from community.models import Community
from agentic.models import Agent
from agentic.matrix_utils import set_power_level_with_server_admin
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix Matrix power levels using server admin privileges for community admins and agents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--community-uid',
            type=str,
            help='Specific community UID to fix power levels for'
        )
        parser.add_argument(
            '--agent-uid',
            type=str,
            help='Specific agent UID to fix power levels for'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--fix-admins-only',
            action='store_true',
            help='Only fix community admin power levels'
        )
        parser.add_argument(
            '--fix-agents-only',
            action='store_true',
            help='Only fix agent power levels'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of operations to process in each batch (default: 10)'
        )

    def handle(self, *args, **options):
        community_uid = options.get('community_uid')
        agent_uid = options.get('agent_uid')
        dry_run = options.get('dry_run', False)
        fix_admins_only = options.get('fix_admins_only', False)
        fix_agents_only = options.get('fix_agents_only', False)
        batch_size = options.get('batch_size', 10)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            # Get communities to process
            if community_uid:
                try:
                    community = Community.nodes.get(uid=community_uid)
                    if community.room_id:
                        communities = [community]
                    else:
                        communities = []
                except Community.DoesNotExist:
                    communities = []
            else:
                # Get all communities with matrix room IDs
                communities = [c for c in Community.nodes.all() if c.room_id]
            
            if not communities:
                self.stdout.write(self.style.WARNING('No communities found with Matrix rooms'))
                return

            self.stdout.write(f'Found {len(communities)} communities to process')

            total_fixed = 0
            total_errors = 0

            for i, community in enumerate(communities):
                self.stdout.write(f'\nProcessing community {i+1}/{len(communities)}: {community.name} ({community.uid})')
                self.stdout.write(f'Matrix Room ID: {community.room_id}')

                # Fix community admin power level
                if not fix_agents_only:
                    admin_fixed = self._fix_community_admin_power_level(
                        community, dry_run
                    )
                    if admin_fixed:
                        total_fixed += 1
                    elif admin_fixed is False:
                        total_errors += 1

                # Fix agent power levels
                if not fix_admins_only:
                    # Get agents assigned to this community
                    agents = []
                    for assignment in community.leader_agent.all():
                        agent = assignment.agent.single()
                        if agent and agent.matrix_user_id:
                            if not agent_uid or agent.uid == agent_uid:
                                agents.append(agent)
                    
                    if agents:
                        self.stdout.write(f'  Found {len(agents)} agents to fix power levels for')
                        
                        for j, agent in enumerate(agents):
                            if j > 0 and j % batch_size == 0:
                                self.stdout.write(f'  Processed {j} agents, continuing...')
                            
                            agent_fixed = self._fix_agent_power_level(
                                community, agent, dry_run
                            )
                            if agent_fixed:
                                total_fixed += 1
                            elif agent_fixed is False:
                                total_errors += 1
                    else:
                        self.stdout.write('  No agents found with Matrix user IDs')

            # Summary
            self.stdout.write(f'\n{"=" * 50}')
            self.stdout.write(f'SUMMARY:')
            self.stdout.write(f'Total power levels fixed: {total_fixed}')
            self.stdout.write(f'Total errors: {total_errors}')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('This was a dry run - no actual changes were made'))
            else:
                self.stdout.write(self.style.SUCCESS('Power level fixes completed'))

        except Exception as e:
            logger.exception(f"Error in fix_matrix_power_levels_admin command: {e}")
            raise CommandError(f'Command failed: {e}')

    def _fix_community_admin_power_level(self, community, dry_run=False):
        """
        Fix power level for community admin.
        Returns: True if fixed, False if error, None if skipped
        """
        try:
            # Get community creator/admin - handle the relationship properly
            admin_users = community.created_by.all()
            if not admin_users:
                self.stdout.write(f'  Skipping admin fix: No creator found for community {community.uid}')
                return None
                
            admin_user = admin_users[0]  # Get the first creator
            if not admin_user or not hasattr(admin_user, 'user_id'):
                self.stdout.write(f'  Skipping admin fix: Creator has no user_id for community {community.uid}')
                return None
                
            # Get Matrix profile for the admin
            try:
                from msg.models import MatrixProfile
                admin_matrix_profile = MatrixProfile.objects.get(user=admin_user.user_id)
                
                if not admin_matrix_profile.matrix_user_id:
                    self.stdout.write(f'  Skipping admin fix: Admin {admin_user.user_id} has no Matrix user ID')
                    return None
                    
                admin_matrix_id = admin_matrix_profile.matrix_user_id
                
            except MatrixProfile.DoesNotExist:
                self.stdout.write(f'  Skipping admin fix: No Matrix profile found for admin {admin_user.user_id}')
                return None
            
            if dry_run:
                self.stdout.write(f'  [DRY RUN] Would fix admin power level for {admin_matrix_id} in room {community.room_id}')
                return None

            self.stdout.write(f'  Fixing admin power level for {admin_matrix_id}...')
            
            # Use server admin to set power level
            success = asyncio.run(
                set_power_level_with_server_admin(
                    room_id=community.room_id,
                    user_matrix_id=admin_matrix_id,
                    power_level=100
                )
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Successfully fixed admin power level for {admin_matrix_id}'))
                return True
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed to fix admin power level for {admin_matrix_id}'))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error fixing admin power level: {e}'))
            logger.exception(f"Error fixing admin power level for community {community.uid}: {e}")
            return False

    def _fix_agent_power_level(self, community, agent, dry_run=False):
        """
        Fix power level for an agent.
        Returns: True if fixed, False if error, None if skipped
        """
        try:
            if dry_run:
                self.stdout.write(f'    [DRY RUN] Would fix agent power level for {agent.matrix_user_id} in room {community.room_id}')
                return None

            self.stdout.write(f'    Fixing agent power level for {agent.matrix_user_id}...')
            
            # Use server admin to set power level
            success = asyncio.run(
                set_power_level_with_server_admin(
                    room_id=community.room_id,
                    user_matrix_id=agent.matrix_user_id,
                    power_level=100
                )
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'    ✓ Successfully fixed agent power level for {agent.matrix_user_id}'))
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    ✗ Failed to fix agent power level for {agent.matrix_user_id}'))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    ✗ Error fixing agent power level: {e}'))
            logger.exception(f"Error fixing agent power level for agent {agent.uid}: {e}")
            return False