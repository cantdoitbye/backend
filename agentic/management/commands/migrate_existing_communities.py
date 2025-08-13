# Management command for migrating existing communities to support agent assignment
# This command adds agent support to existing communities without agents.

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
import logging

from community.models import Community, Membership
from auth_manager.models import Users
from agentic.models import Agent, AgentCommunityAssignment
from agentic.services.agent_service import AgentService
from agentic.services.audit_service import audit_service


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to migrate existing communities to support agent assignment.
    
    This command:
    1. Identifies communities without AI agents
    2. Creates appropriate agents for each community type
    3. Assigns agents to communities
    4. Initializes agent memory and context
    """
    
    help = 'Migrate existing communities to support AI agent assignment'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--community-uid',
            type=str,
            help='Migrate specific community by UID'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of communities to process in each batch'
        )
        
        parser.add_argument(
            '--agent-type',
            choices=['COMMUNITY_LEADER', 'MODERATOR', 'ASSISTANT'],
            default='COMMUNITY_LEADER',
            help='Type of agent to create for communities'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually migrating'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts'
        )
        
        parser.add_argument(
            '--creator-uid',
            type=str,
            help='UID of user to set as agent creator (defaults to community creator)'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(
            self.style.SUCCESS('Starting community migration for agent support...')
        )
        
        try:
            # Get communities to migrate
            communities_to_migrate = self._get_communities_to_migrate(
                community_uid=options.get('community_uid'),
                batch_size=options['batch_size']
            )
            
            if not communities_to_migrate:
                self.stdout.write(
                    self.style.SUCCESS('No communities found that need migration')
                )
                return
            
            self.stdout.write(
                f'Found {len(communities_to_migrate)} communities to migrate'
            )
            
            # Show preview
            self._show_migration_preview(communities_to_migrate)
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING('DRY RUN: No changes will be made')
                )
                return
            
            # Confirm migration unless force is used
            if not options['force']:
                confirm = input(f'Proceed with migrating {len(communities_to_migrate)} communities? (yes/no): ')
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.ERROR('Migration cancelled'))
                    return
            
            # Perform migration
            results = self._migrate_communities(
                communities_to_migrate,
                agent_type=options['agent_type'],
                creator_uid=options.get('creator_uid')
            )
            
            # Show results
            self._show_migration_results(results)
            
        except Exception as e:
            logger.error(f'Community migration failed: {str(e)}')
            raise CommandError(f'Migration failed: {str(e)}')
    
    def _get_communities_to_migrate(self, community_uid=None, batch_size=10):
        """Get communities that need migration."""
        try:
            if community_uid:
                # Migrate specific community
                community = Community.nodes.get(uid=community_uid)
                return [community]
            else:
                # Get communities without agents
                all_communities = list(Community.nodes.all())
                communities_without_agents = []
                
                for community in all_communities:
                    # Check if community already has an agent
                    existing_assignments = AgentCommunityAssignment.nodes.filter(
                        community_uid=community.uid,
                        status='ACTIVE'
                    )
                    
                    if not existing_assignments:
                        communities_without_agents.append(community)
                
                # Return batch
                return communities_without_agents[:batch_size]
                
        except Exception as e:
            logger.error(f'Error getting communities to migrate: {str(e)}')
            raise CommandError(f'Failed to get communities: {str(e)}')
    
    def _show_migration_preview(self, communities):
        """Show preview of what will be migrated."""
        self.stdout.write('\\nMigration Preview:')
        self.stdout.write('-' * 50)
        
        for community in communities:
            # Get community info
            member_count = len(list(community.members.all()))
            creator = self._get_community_creator(community)
            
            self.stdout.write(f'Community: {community.name}')
            self.stdout.write(f'  UID: {community.uid}')
            self.stdout.write(f'  Members: {member_count}')
            self.stdout.write(f'  Creator: {creator.username if creator else \"Unknown\"}')
            self.stdout.write(f'  Private: {community.is_private}')
            self.stdout.write('')
    
    def _migrate_communities(self, communities, agent_type='COMMUNITY_LEADER', creator_uid=None):
        """Perform the actual migration."""
        results = {
            'successful': [],
            'failed': [],
            'agents_created': [],
            'assignments_created': []
        }
        
        agent_service = AgentService()
        
        for community in communities:
            try:
                self.stdout.write(f'Migrating community: {community.name}')
                
                with transaction.atomic():
                    # Step 1: Determine agent creator
                    if creator_uid:
                        agent_creator_uid = creator_uid
                    else:
                        creator = self._get_community_creator(community)
                        agent_creator_uid = creator.uid if creator else None
                    
                    if not agent_creator_uid:
                        results['failed'].append({
                            'community': community,
                            'error': 'No creator found for agent'
                        })
                        continue
                    
                    # Step 2: Create agent
                    agent_name = f'{community.name} AI {agent_type.replace(\"_\", \" \").title()}'
                    agent_capabilities = self._get_default_capabilities(agent_type)
                    
                    agent = agent_service.create_agent(
                        name=agent_name,
                        agent_type=agent_type,
                        capabilities=agent_capabilities,
                        description=f'AI {agent_type.lower().replace(\"_\", \" \")} for {community.name} community',
                        created_by_uid=agent_creator_uid
                    )
                    
                    if not agent:
                        results['failed'].append({
                            'community': community,
                            'error': 'Failed to create agent'
                        })
                        continue
                    
                    results['agents_created'].append(agent)
                    
                    # Step 3: Assign agent to community
                    assignment = agent_service.assign_agent_to_community(
                        agent_uid=agent.uid,
                        community_uid=community.uid,
                        assigned_by_uid=agent_creator_uid,
                        permissions=self._get_default_permissions(agent_type)
                    )
                    
                    if not assignment:
                        results['failed'].append({
                            'community': community,
                            'error': 'Failed to assign agent'
                        })
                        continue
                    
                    results['assignments_created'].append(assignment)
                    
                    # Step 4: Initialize agent context
                    self._initialize_agent_context(agent, community)
                    
                    # Step 5: Log migration
                    audit_service.log_system_event(
                        event_type='community_migration',\n                        event_details={\n                            'community_uid': community.uid,\n                            'community_name': community.name,\n                            'agent_uid': agent.uid,\n                            'agent_name': agent.name,\n                            'assignment_uid': assignment.uid,\n                            'migration_type': 'existing_community_agent_support'\n                        },\n                        agent_uid=agent.uid,\n                        community_uid=community.uid\n                    )\n                    \n                    results['successful'].append({\n                        'community': community,\n                        'agent': agent,\n                        'assignment': assignment\n                    })\n                    \n                    self.stdout.write(\n                        self.style.SUCCESS(f'  ✅ Successfully migrated {community.name}')\n                    )\n                    \n            except Exception as e:\n                logger.error(f'Failed to migrate community {community.uid}: {str(e)}')\n                results['failed'].append({\n                    'community': community,\n                    'error': str(e)\n                })\n                self.stdout.write(\n                    self.style.ERROR(f'  ❌ Failed to migrate {community.name}: {str(e)}')\n                )\n        \n        return results\n    \n    def _get_community_creator(self, community):\n        \"\"\"Get the creator of a community.\"\"\"\n        try:\n            # Find admin member who created the community\n            members = community.members.all()\n            for membership in members:\n                if membership.is_admin:\n                    user = membership.user.single()\n                    if user:\n                        return user\n            \n            # If no admin found, return first member\n            if members:\n                first_membership = members[0]\n                return first_membership.user.single()\n            \n            return None\n            \n        except Exception as e:\n            logger.warning(f'Error getting community creator: {str(e)}')\n            return None\n    \n    def _get_default_capabilities(self, agent_type):\n        \"\"\"Get default capabilities for agent type.\"\"\"\n        capability_map = {\n            'COMMUNITY_LEADER': [\n                'edit_community',\n                'moderate_users',\n                'manage_events',\n                'send_messages',\n                'view_reports'\n            ],\n            'MODERATOR': [\n                'moderate_users',\n                'delete_content',\n                'send_messages',\n                'view_reports'\n            ],\n            'ASSISTANT': [\n                'send_messages',\n                'fetch_metrics'\n            ]\n        }\n        \n        return capability_map.get(agent_type, ['send_messages'])\n    \n    def _get_default_permissions(self, agent_type):\n        \"\"\"Get default assignment permissions for agent type.\"\"\"\n        permission_map = {\n            'COMMUNITY_LEADER': ['manage_events', 'access_analytics'],\n            'MODERATOR': ['access_reports'],\n            'ASSISTANT': []\n        }\n        \n        return permission_map.get(agent_type, [])\n    \n    def _initialize_agent_context(self, agent, community):\n        \"\"\"Initialize agent context for the community.\"\"\"\n        try:\n            from agentic.services.memory_service import AgentMemoryService\n            \n            memory_service = AgentMemoryService()\n            \n            # Get community statistics\n            member_count = len(list(community.members.all()))\n            \n            # Create initial context\n            initial_context = {\n                'initialization_date': timezone.now().isoformat(),\n                'migration_source': 'existing_community',\n                'community_info': {\n                    'name': community.name,\n                    'description': community.description,\n                    'member_count': member_count,\n                    'is_private': community.is_private\n                },\n                'setup_tasks': [\n                    'learn_community_culture',\n                    'establish_communication_patterns',\n                    'understand_member_preferences',\n                    'create_engagement_strategy'\n                ],\n                'status': 'newly_assigned',\n                'learning_phase': True\n            }\n            \n            # Store context\n            memory_service.store_context(\n                agent_uid=agent.uid,\n                community_uid=community.uid,\n                context=initial_context,\n                expires_in_hours=24 * 30  # 30 days\n            )\n            \n            # Store initial preferences\n            initial_preferences = {\n                'communication_style': 'friendly_professional',\n                'moderation_approach': 'community_guidelines_based',\n                'engagement_frequency': 'moderate',\n                'learning_mode': True,\n                'auto_responses': False  # Start with manual oversight\n            }\n            \n            memory_service.store_preferences(\n                agent_uid=agent.uid,\n                community_uid=community.uid,\n                preferences=initial_preferences\n            )\n            \n            logger.info(f'Initialized context for agent {agent.uid} in community {community.uid}')\n            \n        except Exception as e:\n            logger.warning(f'Failed to initialize agent context: {str(e)}')\n            # Don't fail the migration for context initialization issues\n    \n    def _show_migration_results(self, results):\n        \"\"\"Show migration results summary.\"\"\"\n        self.stdout.write('\\n' + '=' * 60)\n        self.stdout.write('MIGRATION RESULTS')\n        self.stdout.write('=' * 60)\n        \n        # Summary\n        total_processed = len(results['successful']) + len(results['failed'])\n        self.stdout.write(f'Total communities processed: {total_processed}')\n        self.stdout.write(f'Successful migrations: {len(results[\"successful\"])}')\n        self.stdout.write(f'Failed migrations: {len(results[\"failed\"])}')\n        self.stdout.write(f'Agents created: {len(results[\"agents_created\"])}')\n        self.stdout.write(f'Assignments created: {len(results[\"assignments_created\"])}')\n        \n        # Successful migrations\n        if results['successful']:\n            self.stdout.write('\\n✅ SUCCESSFUL MIGRATIONS:')\n            for result in results['successful']:\n                community = result['community']\n                agent = result['agent']\n                self.stdout.write(f'  • {community.name} → {agent.name} ({agent.uid})')\n        \n        # Failed migrations\n        if results['failed']:\n            self.stdout.write('\\n❌ FAILED MIGRATIONS:')\n            for result in results['failed']:\n                community = result['community']\n                error = result['error']\n                self.stdout.write(f'  • {community.name}: {error}')\n        \n        # Next steps\n        if results['successful']:\n            self.stdout.write('\\n📋 NEXT STEPS:')\n            self.stdout.write('  1. Review agent assignments in the admin panel')\n            self.stdout.write('  2. Configure agent preferences as needed')\n            self.stdout.write('  3. Test agent functionality in migrated communities')\n            self.stdout.write('  4. Monitor agent performance and adjust as needed')\n            self.stdout.write('  5. Consider enabling auto-responses after observation period')\n        \n        self.stdout.write('\\n' + '=' * 60)\n        \n        if results['successful']:\n            self.stdout.write(\n                self.style.SUCCESS(\n                    f'Migration completed successfully! {len(results[\"successful\"])} communities now have AI agents.'\n                )\n            )\n        else:\n            self.stdout.write(\n                self.style.ERROR('Migration completed with errors. Check the logs for details.')\n            )