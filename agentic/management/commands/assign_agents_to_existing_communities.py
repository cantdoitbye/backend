# Management Command: Assign Agents to Existing Communities
# This command assigns default agents to existing communities that don't have leader agents.

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import logging

from community.models import Community
from agentic.services.agent_service import AgentService, AgentServiceError
from agentic.services.auth_service import AgentAuthService


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command to assign agents to existing communities.
    
    This command is useful for migrating existing communities to support
    the new agentic management system.
    
    Usage:
        python manage.py assign_agents_to_existing_communities [options]
    """
    
    help = 'Assign default agents to existing communities that do not have leader agents'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--community-uid',
            type=str,
            help='Assign agent to a specific community by UID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force assignment even if community already has an agent',
        )
        parser.add_argument(
            '--agent-uid',
            type=str,
            help='Use a specific agent UID instead of the default agent',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of communities to process in each batch (default: 100)',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(
            self.style.SUCCESS('Starting agent assignment to existing communities...')
        )
        
        dry_run = options['dry_run']
        community_uid = options['community_uid']
        force = options['force']
        agent_uid = options['agent_uid']
        batch_size = options['batch_size']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE: No changes will be made')
            )
        
        try:
            # Initialize services
            agent_service = AgentService()
            auth_service = AgentAuthService()
            
            # Get the agent to assign
            if agent_uid:
                try:
                    agent = agent_service.get_agent_by_uid(agent_uid)
                    self.stdout.write(f"Using specified agent: {agent.name} ({agent.uid})")
                except Exception as e:
                    raise CommandError(f"Failed to get specified agent {agent_uid}: {str(e)}")
            else:
                agent = agent_service.get_default_community_agent()
                if not agent:
                    raise CommandError("No default agent available for assignment")
                self.stdout.write(f"Using default agent: {agent.name} ({agent.uid})")
            
            # Get communities to process
            if community_uid:
                try:
                    communities = [Community.nodes.get(uid=community_uid)]
                    self.stdout.write(f"Processing specific community: {community_uid}")
                except Community.DoesNotExist:
                    raise CommandError(f"Community {community_uid} not found")
            else:
                communities = list(Community.nodes.all())
                self.stdout.write(f"Found {len(communities)} total communities")
            
            # Filter communities that need agent assignment
            communities_to_process = []
            for community in communities:
                has_agent = community.has_leader_agent()
                
                if force or not has_agent:
                    communities_to_process.append(community)
                elif has_agent:
                    self.stdout.write(
                        f"Skipping {community.name} ({community.uid}) - already has agent"
                    )
            
            self.stdout.write(
                f"Will process {len(communities_to_process)} communities"
            )
            
            if dry_run:
                for community in communities_to_process:
                    self.stdout.write(
                        f"Would assign agent {agent.name} to community {community.name} ({community.uid})"
                    )
                self.stdout.write(
                    self.style.SUCCESS(f'DRY RUN: Would assign agents to {len(communities_to_process)} communities')
                )
                return
            
            # Process communities in batches
            successful_assignments = 0
            failed_assignments = 0
            
            for i in range(0, len(communities_to_process), batch_size):
                batch = communities_to_process[i:i + batch_size]
                self.stdout.write(f"Processing batch {i//batch_size + 1} ({len(batch)} communities)...")
                
                for community in batch:
                    try:
                        # Get community creator as the assigning user
                        creator = community.created_by.single()
                        if not creator:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Skipping {community.name} - no creator found"
                                )
                            )
                            continue
                        
                        # Assign agent to community
                        assignment = agent_service.assign_agent_to_community(
                            agent_uid=agent.uid,
                            community_uid=community.uid,
                            assigned_by_uid=creator.uid,
                            allow_multiple_leaders=force
                        )
                        
                        # Log the assignment
                        auth_service.log_agent_action(
                            agent_uid=agent.uid,
                            community_uid=community.uid,
                            action_type="migration_assignment",
                            details={
                                "assigned_during": "existing_community_migration",
                                "community_name": community.name,
                                "assigned_by": creator.uid,
                                "migration_command": True
                            },
                            success=True
                        )
                        
                        successful_assignments += 1
                        self.stdout.write(
                            f"✓ Assigned agent to {community.name} ({community.uid})"
                        )
                        
                    except Exception as e:
                        failed_assignments += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Failed to assign agent to {community.name} ({community.uid}): {str(e)}"
                            )
                        )
                        logger.error(f"Failed to assign agent to community {community.uid}: {str(e)}")
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nAssignment completed:'
                    f'\n  Successful: {successful_assignments}'
                    f'\n  Failed: {failed_assignments}'
                    f'\n  Total processed: {successful_assignments + failed_assignments}'
                )
            )
            
            if failed_assignments > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'Some assignments failed. Check logs for details.'
                    )
                )
        
        except Exception as e:
            logger.error(f"Command failed: {str(e)}")
            raise CommandError(f"Command failed: {str(e)}")
    
    def _get_system_user_id(self):
        """
        Get a system user ID for assignments where no creator is available.
        
        Returns:
            str: System user ID or None if not available
        """
        try:
            # Try to find a system or admin user
            from auth_manager.models import Users
            
            # Look for a system user or the first superuser
            system_users = Users.nodes.filter(username__in=['system', 'admin', 'root'])
            if system_users:
                return system_users[0].uid
            
            # Fallback to any user (not ideal but better than failing)
            all_users = list(Users.nodes.all())
            if all_users:
                return all_users[0].uid
            
            return None
        except Exception:
            return None