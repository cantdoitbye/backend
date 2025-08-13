# Management command for validating the complete agentic system
# This command performs comprehensive validation of all system components.

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import connection
import logging
import json
from datetime import datetime, timedelta

from community.models import Community, Membership
from auth_manager.models import Users
from agentic.models import Agent, AgentCommunityAssignment, AgentActionLog, AgentMemory
from agentic.services.agent_service import AgentService
from agentic.services.auth_service import AgentAuthService
from agentic.services.memory_service import AgentMemoryService
from agentic.services.audit_service import audit_service


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to validate the complete agentic system.
    
    This command performs comprehensive validation including:
    - Database integrity checks
    - Service functionality tests
    - Permission system validation
    - Memory system validation
    - Integration tests
    """
    
    help = 'Validate the complete agentic community management system'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Run only quick validation checks'
        )
        
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Attempt to fix issues found during validation'
        )
        
        parser.add_argument(
            '--output-format',
            choices=['text', 'json'],
            default='text',
            help='Output format for validation results'
        )
        
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file for validation results'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(
            self.style.SUCCESS('Starting agentic system validation...')
        )
        
        try:
            # Initialize validation results
            validation_results = {
                'timestamp': timezone.now().isoformat(),
                'validation_type': 'quick' if options['quick'] else 'comprehensive',
                'checks': [],
                'summary': {
                    'total_checks': 0,
                    'passed': 0,
                    'failed': 0,
                    'warnings': 0,
                    'fixed': 0
                },
                'issues_found': [],
                'recommendations': []
            }
            
            # Run validation checks
            if options['quick']:
                self._run_quick_validation(validation_results, options['fix_issues'])
            else:
                self._run_comprehensive_validation(validation_results, options['fix_issues'])
            
            # Output results
            self._output_results(validation_results, options)
            
            # Exit with appropriate code
            if validation_results['summary']['failed'] > 0:
                raise CommandError(f"Validation failed with {validation_results['summary']['failed']} errors")
            
            self.stdout.write(
                self.style.SUCCESS('✅ System validation completed successfully!')
            )
            
        except Exception as e:
            logger.error(f'System validation failed: {str(e)}')
            raise CommandError(f'Validation failed: {str(e)}')
    
    def _run_quick_validation(self, results, fix_issues):
        """Run quick validation checks."""
        self.stdout.write('Running quick validation checks...')
        
        checks = [
            ('Database Connectivity', self._check_database_connectivity),
            ('Agent Models', self._check_agent_models),
            ('Basic Services', self._check_basic_services),
            ('Critical Permissions', self._check_critical_permissions)
        ]
        
        self._execute_checks(checks, results, fix_issues)
    
    def _run_comprehensive_validation(self, results, fix_issues):
        """Run comprehensive validation checks."""
        self.stdout.write('Running comprehensive validation checks...')
        
        checks = [
            # Database checks
            ('Database Connectivity', self._check_database_connectivity),
            ('Database Integrity', self._check_database_integrity),
            ('Model Relationships', self._check_model_relationships),
            
            # Service checks
            ('Agent Service', self._check_agent_service),
            ('Auth Service', self._check_auth_service),
            ('Memory Service', self._check_memory_service),
            ('Audit Service', self._check_audit_service),
            
            # Data validation
            ('Agent Data Integrity', self._check_agent_data_integrity),
            ('Assignment Consistency', self._check_assignment_consistency),
            ('Permission System', self._check_permission_system),
            ('Memory System', self._check_memory_system),
            
            # Integration tests
            ('GraphQL Integration', self._check_graphql_integration),
            ('Notification Integration', self._check_notification_integration),
            ('Webhook Integration', self._check_webhook_integration),
            
            # Performance checks
            ('Performance Metrics', self._check_performance_metrics),
            ('Resource Usage', self._check_resource_usage)
        ]
        
        self._execute_checks(checks, results, fix_issues)
    
    def _execute_checks(self, checks, results, fix_issues):
        """Execute a list of validation checks."""
        for check_name, check_function in checks:
            self.stdout.write(f'  Checking {check_name}...')
            
            try:
                check_result = check_function()
                
                # Process check result
                if check_result['status'] == 'pass':
                    results['summary']['passed'] += 1
                    self.stdout.write(f'    ✅ {check_name}: PASSED')
                elif check_result['status'] == 'warning':
                    results['summary']['warnings'] += 1
                    self.stdout.write(f'    ⚠️ {check_name}: WARNING - {check_result.get("message", "")}')
                else:
                    results['summary']['failed'] += 1
                    self.stdout.write(f'    ❌ {check_name}: FAILED - {check_result.get("message", "")}')
                    
                    # Attempt to fix if requested
                    if fix_issues and 'fix_function' in check_result:
                        try:
                            fix_result = check_result['fix_function']()
                            if fix_result:
                                results['summary']['fixed'] += 1
                                self.stdout.write(f'    🔧 {check_name}: FIXED')
                        except Exception as e:
                            self.stdout.write(f'    ❌ {check_name}: FIX FAILED - {str(e)}')
                
                # Add to results
                results['checks'].append({
                    'name': check_name,
                    'status': check_result['status'],
                    'message': check_result.get('message', ''),
                    'details': check_result.get('details', {}),
                    'timestamp': timezone.now().isoformat()
                })
                
                # Add issues and recommendations
                if 'issues' in check_result:
                    results['issues_found'].extend(check_result['issues'])
                if 'recommendations' in check_result:
                    results['recommendations'].extend(check_result['recommendations'])
                
                results['summary']['total_checks'] += 1
                
            except Exception as e:
                results['summary']['failed'] += 1
                results['summary']['total_checks'] += 1
                
                error_result = {
                    'name': check_name,
                    'status': 'error',
                    'message': f'Check execution failed: {str(e)}',
                    'details': {'exception': str(e)},
                    'timestamp': timezone.now().isoformat()
                }
                
                results['checks'].append(error_result)
                self.stdout.write(f'    💥 {check_name}: ERROR - {str(e)}')
    
    def _check_database_connectivity(self):
        """Check database connectivity."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            if result and result[0] == 1:
                return {'status': 'pass', 'message': 'Database connection successful'}
            else:
                return {'status': 'fail', 'message': 'Database query returned unexpected result'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Database connection failed: {str(e)}'}
    
    def _check_database_integrity(self):
        """Check database integrity."""
        try:
            issues = []
            
            # Check for orphaned records
            orphaned_assignments = AgentCommunityAssignment.objects.filter(
                agent_uid__isnull=True
            ).count()
            
            if orphaned_assignments > 0:
                issues.append(f'{orphaned_assignments} orphaned agent assignments found')
            
            # Check for duplicate active assignments
            from django.db.models import Count
            duplicate_assignments = AgentCommunityAssignment.objects.values(
                'agent_uid', 'community_uid'
            ).annotate(
                count=Count('id')
            ).filter(count__gt=1, status='ACTIVE')
            
            if duplicate_assignments.exists():
                issues.append(f'{duplicate_assignments.count()} duplicate active assignments found')
            
            if issues:
                return {
                    'status': 'warning',
                    'message': 'Database integrity issues found',
                    'issues': issues,
                    'recommendations': ['Run database cleanup commands']
                }
            else:
                return {'status': 'pass', 'message': 'Database integrity check passed'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Database integrity check failed: {str(e)}'}
    
    def _check_model_relationships(self):
        """Check model relationships."""
        try:
            issues = []
            
            # Check agent-assignment relationships
            agents_with_assignments = Agent.nodes.all()
            for agent in agents_with_assignments:
                try:
                    assignments = list(agent.assigned_communities.all())
                    # This will fail if relationships are broken
                except Exception as e:
                    issues.append(f'Agent {agent.uid} has broken assignment relationships: {str(e)}')
            
            # Check community-assignment relationships
            communities = Community.nodes.all()
            for community in communities:
                try:
                    # Check if community has valid members
                    members = list(community.members.all())
                except Exception as e:
                    issues.append(f'Community {community.uid} has broken member relationships: {str(e)}')
            
            if issues:
                return {
                    'status': 'fail',
                    'message': 'Model relationship issues found',
                    'issues': issues
                }
            else:
                return {'status': 'pass', 'message': 'Model relationships are valid'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Model relationship check failed: {str(e)}'}
    
    def _check_agent_service(self):
        """Check agent service functionality."""
        try:
            agent_service = AgentService()
            
            # Test basic operations
            test_results = []
            
            # Test agent retrieval
            try:
                agents = list(Agent.nodes.all()[:1])
                if agents:
                    agent = agent_service.get_agent_by_uid(agents[0].uid)
                    test_results.append('Agent retrieval: PASS')
                else:
                    test_results.append('Agent retrieval: SKIP (no agents found)')
            except Exception as e:
                test_results.append(f'Agent retrieval: FAIL - {str(e)}')
            
            # Test assignment retrieval
            try:
                assignments = list(AgentCommunityAssignment.objects.all()[:1])
                if assignments:
                    assignment = agent_service.get_assignment_by_uid(assignments[0].uid)
                    test_results.append('Assignment retrieval: PASS')
                else:
                    test_results.append('Assignment retrieval: SKIP (no assignments found)')
            except Exception as e:
                test_results.append(f'Assignment retrieval: FAIL - {str(e)}')
            
            # Check for any failures
            failures = [result for result in test_results if 'FAIL' in result]
            
            if failures:
                return {
                    'status': 'fail',
                    'message': 'Agent service tests failed',
                    'details': {'test_results': test_results},
                    'issues': failures
                }
            else:
                return {
                    'status': 'pass',
                    'message': 'Agent service is functional',
                    'details': {'test_results': test_results}
                }
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Agent service check failed: {str(e)}'}
    
    def _check_auth_service(self):
        """Check authentication service functionality."""
        try:
            auth_service = AgentAuthService()
            
            # Test permission checking
            test_results = []
            
            # Get a test agent and community
            agents = list(Agent.nodes.all()[:1])
            communities = list(Community.nodes.all()[:1])
            
            if agents and communities:
                agent = agents[0]
                community = communities[0]
                
                # Test authentication
                try:
                    is_authenticated = auth_service.authenticate_agent(agent.uid, community.uid)
                    test_results.append(f'Authentication test: {"PASS" if isinstance(is_authenticated, bool) else "FAIL"}')
                except Exception as e:
                    test_results.append(f'Authentication test: FAIL - {str(e)}')
                
                # Test permission checking
                try:
                    has_permission = auth_service.check_permission(agent.uid, community.uid, 'send_messages')
                    test_results.append(f'Permission check: {"PASS" if isinstance(has_permission, bool) else "FAIL"}')
                except Exception as e:
                    test_results.append(f'Permission check: FAIL - {str(e)}')
            else:
                test_results.append('Auth tests: SKIP (no test data available)')
            
            failures = [result for result in test_results if 'FAIL' in result]
            
            if failures:
                return {
                    'status': 'fail',
                    'message': 'Auth service tests failed',
                    'details': {'test_results': test_results},
                    'issues': failures
                }
            else:
                return {
                    'status': 'pass',
                    'message': 'Auth service is functional',
                    'details': {'test_results': test_results}
                }
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Auth service check failed: {str(e)}'}
    
    def _check_memory_service(self):
        """Check memory service functionality."""
        try:
            memory_service = AgentMemoryService()
            
            # Test memory operations
            test_results = []
            
            # Get test data
            agents = list(Agent.nodes.all()[:1])
            communities = list(Community.nodes.all()[:1])
            
            if agents and communities:
                agent = agents[0]
                community = communities[0]
                
                # Test context storage and retrieval
                try:
                    test_context = {'test': 'validation_data', 'timestamp': timezone.now().isoformat()}
                    
                    # Store context
                    memory_service.store_context(agent.uid, community.uid, test_context, expires_in_hours=1)
                    
                    # Retrieve context
                    retrieved_context = memory_service.retrieve_context(agent.uid, community.uid)
                    
                    if retrieved_context.get('test') == 'validation_data':
                        test_results.append('Context storage/retrieval: PASS')
                    else:
                        test_results.append('Context storage/retrieval: FAIL - Data mismatch')
                        
                except Exception as e:
                    test_results.append(f'Context storage/retrieval: FAIL - {str(e)}')
                
                # Test memory stats
                try:
                    stats = memory_service.get_memory_stats(agent.uid, community.uid)
                    if isinstance(stats, dict):
                        test_results.append('Memory stats: PASS')
                    else:
                        test_results.append('Memory stats: FAIL - Invalid response')
                except Exception as e:
                    test_results.append(f'Memory stats: FAIL - {str(e)}')
            else:
                test_results.append('Memory tests: SKIP (no test data available)')
            
            failures = [result for result in test_results if 'FAIL' in result]
            
            if failures:
                return {
                    'status': 'fail',
                    'message': 'Memory service tests failed',
                    'details': {'test_results': test_results},
                    'issues': failures
                }
            else:
                return {
                    'status': 'pass',
                    'message': 'Memory service is functional',
                    'details': {'test_results': test_results}
                }
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Memory service check failed: {str(e)}'}
    
    def _check_audit_service(self):
        """Check audit service functionality."""
        try:
            # Test audit report generation
            try:
                report = audit_service.generate_audit_report(
                    start_date=timezone.now() - timedelta(days=1),
                    end_date=timezone.now(),
                    include_details=False
                )
                
                if isinstance(report, dict) and 'summary' in report:
                    return {'status': 'pass', 'message': 'Audit service is functional'}
                else:
                    return {'status': 'fail', 'message': 'Audit service returned invalid report format'}
                    
            except Exception as e:
                return {'status': 'fail', 'message': f'Audit service test failed: {str(e)}'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Audit service check failed: {str(e)}'}
    
    def _check_agent_data_integrity(self):
        """Check agent data integrity."""
        try:
            issues = []
            
            # Check for agents with invalid data
            agents = Agent.nodes.all()
            for agent in agents:
                if not agent.name or len(agent.name.strip()) == 0:
                    issues.append(f'Agent {agent.uid} has empty name')
                
                if not agent.agent_type or agent.agent_type not in ['COMMUNITY_LEADER', 'MODERATOR', 'ASSISTANT']:
                    issues.append(f'Agent {agent.uid} has invalid agent_type: {agent.agent_type}')
                
                if not agent.capabilities or len(agent.capabilities) == 0:
                    issues.append(f'Agent {agent.uid} has no capabilities')
            
            if issues:
                return {
                    'status': 'warning',
                    'message': 'Agent data integrity issues found',
                    'issues': issues,
                    'recommendations': ['Review and fix agent data']
                }
            else:
                return {'status': 'pass', 'message': 'Agent data integrity check passed'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Agent data integrity check failed: {str(e)}'}
    
    def _check_assignment_consistency(self):
        """Check assignment consistency."""
        try:
            issues = []
            
            # Check for inconsistent assignments
            assignments = AgentCommunityAssignment.objects.all()
            
            for assignment in assignments:
                # Check if referenced agent exists
                try:
                    agent = Agent.nodes.get(uid=assignment.agent_uid)
                except Agent.DoesNotExist:
                    issues.append(f'Assignment {assignment.uid} references non-existent agent {assignment.agent_uid}')
                
                # Check if referenced community exists
                try:
                    community = Community.nodes.get(uid=assignment.community_uid)
                except Community.DoesNotExist:
                    issues.append(f'Assignment {assignment.uid} references non-existent community {assignment.community_uid}')
            
            if issues:
                return {
                    'status': 'fail',
                    'message': 'Assignment consistency issues found',
                    'issues': issues,
                    'recommendations': ['Clean up orphaned assignments']
                }
            else:
                return {'status': 'pass', 'message': 'Assignment consistency check passed'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Assignment consistency check failed: {str(e)}'}
    
    def _check_permission_system(self):
        """Check permission system."""
        try:
            auth_service = AgentAuthService()
            
            # Test standard capabilities
            standard_capabilities = auth_service.STANDARD_CAPABILITIES
            
            if not standard_capabilities or len(standard_capabilities) == 0:
                return {'status': 'fail', 'message': 'No standard capabilities defined'}
            
            # Test permission validation
            test_permissions = ['edit_community', 'moderate_users', 'send_messages']
            invalid_permissions = []
            
            for permission in test_permissions:
                if permission not in standard_capabilities:
                    invalid_permissions.append(permission)
            
            if invalid_permissions:
                return {
                    'status': 'warning',
                    'message': 'Some test permissions are not in standard capabilities',
                    'details': {'invalid_permissions': invalid_permissions}
                }
            else:
                return {'status': 'pass', 'message': 'Permission system is properly configured'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Permission system check failed: {str(e)}'}
    
    def _check_memory_system(self):
        """Check memory system."""
        try:
            # Check for expired memory that should be cleaned up
            expired_memory = AgentMemory.objects.filter(
                expires_at__lt=timezone.now()
            ).count()
            
            if expired_memory > 1000:  # Arbitrary threshold
                return {
                    'status': 'warning',
                    'message': f'{expired_memory} expired memory records found',
                    'recommendations': ['Run memory cleanup command']
                }
            else:
                return {'status': 'pass', 'message': 'Memory system is healthy'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Memory system check failed: {str(e)}'}
    
    def _check_graphql_integration(self):
        """Check GraphQL integration."""
        try:
            # This would test GraphQL schema and resolvers
            # For now, just check if the modules can be imported
            from agentic.graphql.types import AgentType
            from agentic.graphql.mutations import AgentMutations
            from agentic.graphql.queries import AgentQueries
            
            return {'status': 'pass', 'message': 'GraphQL integration modules loaded successfully'}
            
        except ImportError as e:
            return {'status': 'fail', 'message': f'GraphQL integration check failed: {str(e)}'}
        except Exception as e:
            return {'status': 'fail', 'message': f'GraphQL integration check failed: {str(e)}'}
    
    def _check_notification_integration(self):
        """Check notification integration."""
        try:
            from agentic.services.notification_integration import agent_notification_service
            
            # Basic service availability check
            if agent_notification_service:
                return {'status': 'pass', 'message': 'Notification integration is available'}
            else:
                return {'status': 'fail', 'message': 'Notification integration service not available'}
                
        except ImportError as e:
            return {'status': 'fail', 'message': f'Notification integration check failed: {str(e)}'}
        except Exception as e:
            return {'status': 'fail', 'message': f'Notification integration check failed: {str(e)}'}
    
    def _check_webhook_integration(self):
        """Check webhook integration."""
        try:
            from agentic.services.webhook_service import webhook_service
            
            # Basic service availability check
            if webhook_service:
                return {'status': 'pass', 'message': 'Webhook integration is available'}
            else:
                return {'status': 'fail', 'message': 'Webhook integration service not available'}
                
        except ImportError as e:
            return {'status': 'fail', 'message': f'Webhook integration check failed: {str(e)}'}
        except Exception as e:
            return {'status': 'fail', 'message': f'Webhook integration check failed: {str(e)}'}
    
    def _check_performance_metrics(self):
        """Check performance metrics."""
        try:
            # Check database query performance
            start_time = timezone.now()
            
            # Run some typical queries
            agent_count = Agent.nodes.count()
            assignment_count = AgentCommunityAssignment.objects.count()
            memory_count = AgentMemory.objects.count()
            
            end_time = timezone.now()
            query_time = (end_time - start_time).total_seconds()
            
            if query_time > 5.0:  # 5 seconds threshold
                return {
                    'status': 'warning',
                    'message': f'Database queries are slow ({query_time:.2f}s)',
                    'recommendations': ['Consider database optimization']
                }
            else:
                return {
                    'status': 'pass',
                    'message': f'Performance metrics are acceptable ({query_time:.2f}s)',
                    'details': {
                        'agent_count': agent_count,
                        'assignment_count': assignment_count,
                        'memory_count': memory_count,
                        'query_time': query_time
                    }
                }
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Performance metrics check failed: {str(e)}'}
    
    def _check_resource_usage(self):
        """Check resource usage."""
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            
            if memory.percent > 90:
                issues.append(f'High memory usage: {memory.percent}%')
            
            if disk.percent > 90:
                issues.append(f'High disk usage: {disk.percent}%')
            
            if issues:
                return {
                    'status': 'warning',
                    'message': 'Resource usage issues detected',
                    'issues': issues,
                    'details': {
                        'memory_percent': memory.percent,
                        'disk_percent': disk.percent
                    }
                }
            else:
                return {
                    'status': 'pass',
                    'message': 'Resource usage is normal',
                    'details': {
                        'memory_percent': memory.percent,
                        'disk_percent': disk.percent
                    }
                }
                
        except ImportError:
            return {'status': 'warning', 'message': 'psutil not available for resource monitoring'}
        except Exception as e:
            return {'status': 'fail', 'message': f'Resource usage check failed: {str(e)}'}
    
    def _output_results(self, results, options):
        """Output validation results."""
        if options['output_format'] == 'json':
            output = json.dumps(results, indent=2, default=str)
        else:
            output = self._format_text_results(results)
        
        if options['output_file']:
            with open(options['output_file'], 'w') as f:
                f.write(output)
            self.stdout.write(f'Results saved to: {options["output_file"]}')
        else:
            self.stdout.write(output)
    
    def _format_text_results(self, results):
        """Format results as text."""
        lines = []
        
        lines.append('=' * 60)
        lines.append('AGENTIC SYSTEM VALIDATION RESULTS')
        lines.append('=' * 60)
        lines.append('')
        
        # Summary
        summary = results['summary']
        lines.append('SUMMARY:')
        lines.append(f'  Total Checks: {summary["total_checks"]}')
        lines.append(f'  Passed: {summary["passed"]}')
        lines.append(f'  Failed: {summary["failed"]}')
        lines.append(f'  Warnings: {summary["warnings"]}')
        if summary['fixed'] > 0:
            lines.append(f'  Fixed: {summary["fixed"]}')
        lines.append('')
        
        # Overall status
        if summary['failed'] == 0:
            lines.append('✅ OVERALL STATUS: HEALTHY')
        elif summary['failed'] < summary['passed']:
            lines.append('⚠️ OVERALL STATUS: ISSUES DETECTED')
        else:
            lines.append('❌ OVERALL STATUS: CRITICAL ISSUES')
        lines.append('')
        
        # Issues found
        if results['issues_found']:
            lines.append('ISSUES FOUND:')
            for issue in results['issues_found']:
                lines.append(f'  • {issue}')
            lines.append('')
        
        # Recommendations
        if results['recommendations']:
            lines.append('RECOMMENDATIONS:')
            for rec in results['recommendations']:
                lines.append(f'  • {rec}')
            lines.append('')
        
        # Detailed results
        lines.append('DETAILED RESULTS:')
        for check in results['checks']:
            status_icon = {
                'pass': '✅',
                'fail': '❌',
                'warning': '⚠️',
                'error': '💥'
            }.get(check['status'], '❓')
            
            lines.append(f'{status_icon} {check["name"]}: {check["status"].upper()}')
            if check['message']:
                lines.append(f'    {check["message"]}')
        
        lines.append('')
        lines.append('=' * 60)
        
        return '\\n'.join(lines)