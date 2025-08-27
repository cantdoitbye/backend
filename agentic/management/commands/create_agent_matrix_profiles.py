# Django Management Command: Create Matrix Profiles for Existing Agents
# This command creates Matrix profiles for agents that don't have them yet.
# It can be run to retroactively add Matrix integration to existing agents.

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from agentic.models import Agent
from agentic.matrix_utils import create_agent_matrix_profile, retry_agent_matrix_registration
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create Matrix profiles for existing agents that do not have them'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--agent-uid',
            type=str,
            help='Create Matrix profile for a specific agent UID'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating profiles'
        )
        
        parser.add_argument(
            '--retry-pending',
            action='store_true',
            help='Retry Matrix registration for agents with pending registration'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of Matrix profiles even if they already exist'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of agents to process in each batch (default: 10)'
        )
    
    def handle(self, *args, **options):
        agent_uid = options.get('agent_uid')
        dry_run = options.get('dry_run', False)
        retry_pending = options.get('retry_pending', False)
        force = options.get('force', False)
        batch_size = options.get('batch_size', 10)
        
        self.stdout.write(
            self.style.SUCCESS('Starting Matrix profile creation for agents...')
        )
        
        try:
            if agent_uid:
                # Process specific agent
                self._process_specific_agent(agent_uid, dry_run, force, retry_pending)
            else:
                # Process all agents
                self._process_all_agents(dry_run, force, retry_pending, batch_size)
                
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise CommandError(f"Failed to create Matrix profiles: {str(e)}")
    
    def _process_specific_agent(self, agent_uid, dry_run, force, retry_pending):
        """Process a specific agent by UID."""
        try:
            agent = Agent.nodes.get(uid=agent_uid)
            
            if dry_run:
                self._show_agent_status(agent)
                return
            
            success = self._create_matrix_profile_for_agent(agent, force, retry_pending)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully created Matrix profile for agent {agent.name} ({agent.uid})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to create Matrix profile for agent {agent.name} ({agent.uid})"
                    )
                )
                
        except Agent.DoesNotExist:
            raise CommandError(f"Agent with UID {agent_uid} not found")
    
    def _process_all_agents(self, dry_run, force, retry_pending, batch_size):
        """Process all agents in batches."""
        # Get agents that need Matrix profiles
        if retry_pending:
            agents = Agent.nodes.filter(pending_matrix_registration=True)
            self.stdout.write(f"Found {len(agents)} agents with pending Matrix registration")
        elif force:
            agents = Agent.nodes.all()
            self.stdout.write(f"Found {len(agents)} agents (force mode - will recreate all profiles)")
        else:
            # Get agents without Matrix profiles
            agents_without_matrix = []
            for agent in Agent.nodes.all():
                if not agent.matrix_user_id or not agent.access_token:
                    agents_without_matrix.append(agent)
            agents = agents_without_matrix
            self.stdout.write(f"Found {len(agents)} agents without Matrix profiles")
        
        if not agents:
            self.stdout.write(
                self.style.SUCCESS("No agents need Matrix profile creation")
            )
            return
        
        if dry_run:
            self.stdout.write("\nDry run - showing agents that would be processed:")
            for agent in agents:
                self._show_agent_status(agent)
            return
        
        # Process agents in batches
        total_processed = 0
        total_success = 0
        total_failed = 0
        
        for i in range(0, len(agents), batch_size):
            batch = agents[i:i + batch_size]
            
            self.stdout.write(
                f"\nProcessing batch {i//batch_size + 1} ({len(batch)} agents)..."
            )
            
            for agent in batch:
                try:
                    success = self._create_matrix_profile_for_agent(agent, force, retry_pending)
                    
                    if success:
                        total_success += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ {agent.name} ({agent.uid})"
                            )
                        )
                    else:
                        total_failed += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ✗ {agent.name} ({agent.uid}) - Failed"
                            )
                        )
                    
                    total_processed += 1
                    
                except Exception as e:
                    total_failed += 1
                    total_processed += 1
                    logger.error(f"Error processing agent {agent.uid}: {str(e)}")
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ {agent.name} ({agent.uid}) - Error: {str(e)}"
                        )
                    )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Processed {total_processed} agents: "
                f"{total_success} successful, {total_failed} failed"
            )
        )
    
    def _create_matrix_profile_for_agent(self, agent, force, retry_pending):
        """Create Matrix profile for a single agent."""
        # Check if agent already has Matrix profile and force is not enabled
        if not force and agent.matrix_user_id and agent.access_token and not agent.pending_matrix_registration:
            logger.info(f"Agent {agent.uid} already has Matrix profile, skipping")
            return True
        
        # Handle retry pending case
        if retry_pending and agent.pending_matrix_registration:
            return retry_agent_matrix_registration(agent)
        
        # Create new Matrix profile
        return create_agent_matrix_profile(agent)
    
    def _show_agent_status(self, agent):
        """Show the current Matrix status of an agent."""
        status_parts = []
        
        if agent.matrix_user_id:
            status_parts.append(f"Matrix ID: {agent.matrix_user_id}")
        else:
            status_parts.append("No Matrix ID")
        
        if agent.access_token:
            status_parts.append("Has access token")
        else:
            status_parts.append("No access token")
        
        if agent.pending_matrix_registration:
            status_parts.append("Pending registration")
        
        status = " | ".join(status_parts)
        
        self.stdout.write(
            f"  {agent.name} ({agent.uid}): {status}"
        )