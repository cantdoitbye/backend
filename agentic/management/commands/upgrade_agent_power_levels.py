from django.core.management.base import BaseCommand
from django.db import transaction
import asyncio
import logging
from typing import List, Dict, Any

from agentic.models import Agent, AgentCommunityAssignment
from agentic.matrix_utils import set_agent_power_level, MatrixProfileUpdateError
from community.models import Community
from msg.models import MatrixProfile
from neomodel import DoesNotExist


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Upgrade existing agents\' power levels to 100 (full admin) in their assigned community Matrix rooms'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually upgrading power levels'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of agents to process in each batch (default: 10)'
        )
        parser.add_argument(
            '--agent-uid',
            type=str,
            help='Process only a specific agent by UID'
        )
        parser.add_argument(
            '--community-uid',
            type=str,
            help='Process only agents assigned to a specific community by UID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force power level upgrade even if agent already has high privileges'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        agent_uid = options.get('agent_uid')
        community_uid = options.get('community_uid')
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting agent power level upgrade {'(DRY RUN)' if dry_run else ''}"
            )
        )
        
        try:
            # Get assignments that need power level upgrade
            assignments = self._get_assignments_needing_upgrade(
                agent_uid=agent_uid,
                community_uid=community_uid,
                force=force
            )
            
            if not assignments:
                self.stdout.write(
                    self.style.WARNING("No agent assignments found that need power level upgrade")
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {len(assignments)} agent assignments that need power level upgrade"
                )
            )
            
            # Process assignments in batches
            total_processed = 0
            total_successful = 0
            total_failed = 0
            
            for i in range(0, len(assignments), batch_size):
                batch = assignments[i:i + batch_size]
                
                self.stdout.write(
                    f"Processing batch {i // batch_size + 1} "
                    f"({len(batch)} assignments)..."
                )
                
                batch_results = self._process_batch(batch, dry_run)
                
                total_processed += batch_results['processed']
                total_successful += batch_results['successful']
                total_failed += batch_results['failed']
                
                # Show batch results
                self.stdout.write(
                    f"Batch completed: {batch_results['successful']} successful, "
                    f"{batch_results['failed']} failed"
                )
            
            # Show final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nUpgrade completed {'(DRY RUN)' if dry_run else ''}:\n"
                    f"  Total processed: {total_processed}\n"
                    f"  Successful: {total_successful}\n"
                    f"  Failed: {total_failed}"
                )
            )
            
        except Exception as e:
            logger.error(f"Error during agent power level upgrade: {e}")
            raise CommandError(f"Failed to upgrade agent power levels: {e}")
    
    def _get_assignments_needing_upgrade(self, agent_uid: str = None, community_uid: str = None, force: bool = False) -> List[Dict[str, Any]]:
        """
        Get agent-community assignments that need power level upgrade.
        
        Returns:
            List of dictionaries containing assignment info
        """
        assignments = []
        
        try:
            # Get all active agent-community assignments
            query_filters = {'status': 'ACTIVE'}
            
            if agent_uid:
                # Filter by specific agent
                try:
                    agent = Agent.nodes.get(uid=agent_uid)
                    agent_assignments = agent.assigned_communities.filter(**query_filters)
                except DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"Agent with UID {agent_uid} not found")
                    )
                    return []
            else:
                # Get all assignments
                agent_assignments = AgentCommunityAssignment.nodes.filter(**query_filters)
            
            for assignment in agent_assignments:
                try:
                    # Get the agent and community for this assignment
                    agent = assignment.agent.single()
                    community = assignment.community.single()
                    
                    if not agent or not community:
                        continue
                    
                    # Filter by community if specified
                    if community_uid and community.uid != community_uid:
                        continue
                    
                    # Check if agent has Matrix credentials
                    has_matrix_credentials = bool(agent.matrix_user_id and agent.access_token)
                    
                    # Check if community has a Matrix room
                    has_matrix_room = bool(community.room_id)
                    
                    if not (has_matrix_credentials and has_matrix_room):
                        continue
                    
                    assignment_info = {
                        'assignment': assignment,
                        'agent': agent,
                        'community': community,
                        'agent_name': agent.name,
                        'agent_uid': agent.uid,
                        'community_name': community.name,
                        'community_uid': community.uid,
                        'matrix_user_id': agent.matrix_user_id,
                        'room_id': community.room_id,
                        'needs_upgrade': True
                    }
                    
                    assignments.append(assignment_info)
                    
                except Exception as e:
                    logger.error(f"Error processing assignment {assignment.uid}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error getting assignments: {e}")
            raise
        
        return assignments
    
    def _process_batch(self, assignments: List[Dict[str, Any]], dry_run: bool) -> Dict[str, int]:
        """
        Process a batch of agent assignments for power level upgrade.
        
        Returns:
            Dictionary with counts of processed, successful, and failed upgrades
        """
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0
        }
        
        for assignment_info in assignments:
            results['processed'] += 1
            
            agent = assignment_info['agent']
            community = assignment_info['community']
            agent_name = assignment_info['agent_name']
            community_name = assignment_info['community_name']
            room_id = assignment_info['room_id']
            agent_matrix_id = assignment_info['matrix_user_id']
            
            try:
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would upgrade power level for agent {agent_name} "
                        f"in community {community_name} (room: {room_id})"
                    )
                    results['successful'] += 1
                    continue
                
                # Find a community admin with Matrix credentials
                admin_matrix_profile = self._find_community_admin(community)
                
                if not admin_matrix_profile:
                    self.stdout.write(
                        self.style.ERROR(
                            f"No community admin with Matrix credentials found for "
                            f"community {community_name}"
                        )
                    )
                    results['failed'] += 1
                    continue
                
                # Upgrade agent power level to 100 (full admin)
                success = asyncio.run(set_agent_power_level(
                    admin_access_token=admin_matrix_profile.access_token,
                    admin_matrix_id=admin_matrix_profile.matrix_user_id,
                    room_id=room_id,
                    agent_matrix_id=agent_matrix_id,
                    power_level=100,  # Full admin privileges
                    timeout=10
                ))
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Upgraded power level for agent {agent_name} "
                            f"in community {community_name}"
                        )
                    )
                    results['successful'] += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Failed to upgrade power level for agent {agent_name} "
                            f"in community {community_name}"
                        )
                    )
                    results['failed'] += 1
                
            except MatrixProfileUpdateError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Matrix error upgrading agent {agent_name} "
                        f"in community {community_name}: {e}"
                    )
                )
                results['failed'] += 1
                
            except Exception as e:
                logger.error(
                    f"Unexpected error upgrading agent {agent_name} "
                    f"in community {community_name}: {e}"
                )
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Unexpected error upgrading agent {agent_name} "
                        f"in community {community_name}: {e}"
                    )
                )
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