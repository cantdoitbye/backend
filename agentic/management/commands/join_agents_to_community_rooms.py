from django.core.management.base import BaseCommand
from django.db import transaction
import logging
from typing import List, Dict, Any

from agentic.models import Agent, AgentCommunityAssignment
from agentic.matrix_utils import join_agent_to_community_matrix_room, MatrixProfileUpdateError
from community.models import Community
from neomodel import DoesNotExist


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Join existing agents to their assigned community Matrix rooms'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually joining agents to rooms'
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
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        agent_uid = options.get('agent_uid')
        community_uid = options.get('community_uid')
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting agent-to-community Matrix room joining process..."
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No actual changes will be made")
            )
        
        try:
            # Get agent-community assignments that need Matrix room joining
            assignments = self._get_assignments_needing_room_join(agent_uid, community_uid)
            
            if not assignments:
                self.stdout.write(
                    self.style.WARNING("No agent-community assignments found that need Matrix room joining")
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {len(assignments)} agent-community assignments to process"
                )
            )
            
            # Process assignments in batches
            total_processed = 0
            total_success = 0
            total_failures = 0
            
            for i in range(0, len(assignments), batch_size):
                batch = assignments[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nProcessing batch {batch_num} ({len(batch)} assignments)..."
                    )
                )
                
                batch_results = self._process_batch(batch, dry_run)
                
                total_processed += batch_results['processed']
                total_success += batch_results['success']
                total_failures += batch_results['failures']
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Batch {batch_num} completed: {batch_results['success']} successful, "
                        f"{batch_results['failures']} failed"
                    )
                )
            
            # Final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n=== FINAL SUMMARY ==="
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Total assignments processed: {total_processed}"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully joined to rooms: {total_success}"
                )
            )
            if total_failures > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to join to rooms: {total_failures}"
                    )
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during processing: {e}")
            )
            logger.error(f"Error in join_agents_to_community_rooms command: {e}")
            raise
    
    def _get_assignments_needing_room_join(self, agent_uid: str = None, community_uid: str = None) -> List[Dict[str, Any]]:
        """
        Get agent-community assignments that need Matrix room joining.
        
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
                    
                    assignment_info = {
                        'assignment': assignment,
                        'agent': agent,
                        'community': community,
                        'agent_name': agent.name,
                        'agent_uid': agent.uid,
                        'community_name': community.name,
                        'community_uid': community.uid,
                        'has_matrix_credentials': has_matrix_credentials,
                        'has_matrix_room': has_matrix_room,
                        'matrix_user_id': agent.matrix_user_id,
                        'room_id': community.room_id,
                        'needs_room_join': has_matrix_credentials and has_matrix_room
                    }
                    
                    assignments.append(assignment_info)
                    
                except Exception as e:
                    logger.error(f"Error processing assignment {assignment.uid}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error getting assignments: {e}")
            raise
        
        return assignments
    
    def _process_batch(self, batch: List[Dict[str, Any]], dry_run: bool) -> Dict[str, int]:
        """
        Process a batch of agent-community assignments.
        
        Returns:
            Dictionary with processing statistics
        """
        results = {
            'processed': 0,
            'success': 0,
            'failures': 0
        }
        
        for assignment_info in batch:
            results['processed'] += 1
            
            agent = assignment_info['agent']
            community = assignment_info['community']
            agent_name = assignment_info['agent_name']
            community_name = assignment_info['community_name']
            has_matrix_credentials = assignment_info['has_matrix_credentials']
            has_matrix_room = assignment_info['has_matrix_room']
            
            self.stdout.write(
                f"  Processing: {agent_name} -> {community_name}"
            )
            
            # Check if this assignment needs room joining
            if not has_matrix_credentials:
                self.stdout.write(
                    self.style.WARNING(
                        f"    Skipped: Agent {agent_name} has no Matrix credentials"
                    )
                )
                continue
            
            if not has_matrix_room:
                self.stdout.write(
                    self.style.WARNING(
                        f"    Skipped: Community {community_name} has no Matrix room"
                    )
                )
                continue
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"    Would join agent {agent_name} to community {community_name} Matrix room"
                    )
                )
                results['success'] += 1
                continue
            
            # Actually join the agent to the community Matrix room
            try:
                success = join_agent_to_community_matrix_room(agent, community)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    ✓ Successfully joined {agent_name} to {community_name} Matrix room"
                        )
                    )
                    results['success'] += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"    ✗ Failed to join {agent_name} to {community_name} Matrix room"
                        )
                    )
                    results['failures'] += 1
                    
            except MatrixProfileUpdateError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"    ✗ Matrix error joining {agent_name} to {community_name}: {e}"
                    )
                )
                results['failures'] += 1
                logger.error(f"Matrix error joining agent {agent.uid} to community {community.uid}: {e}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"    ✗ Unexpected error joining {agent_name} to {community_name}: {e}"
                    )
                )
                results['failures'] += 1
                logger.error(f"Unexpected error joining agent {agent.uid} to community {community.uid}: {e}")
        
        return results