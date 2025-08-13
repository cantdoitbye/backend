# Management command for generating audit reports
# This command generates comprehensive audit reports for agent activities.

import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import logging

from agentic.services.audit_service import audit_service, AuditCategory


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to generate agent audit reports.
    
    This command generates comprehensive audit reports for agent activities
    with various filtering and output options.
    """
    
    help = 'Generate comprehensive audit reports for agent activities'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--agent-uid',
            type=str,
            help='Filter by specific agent UID'
        )
        
        parser.add_argument(
            '--community-uid',
            type=str,
            help='Filter by specific community UID'
        )
        
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for report (YYYY-MM-DD format)'
        )
        
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for report (YYYY-MM-DD format)'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            help='Number of days back from today to include in report'
        )
        
        parser.add_argument(
            '--categories',
            nargs='+',
            choices=[
                AuditCategory.AUTHENTICATION,
                AuditCategory.AUTHORIZATION,
                AuditCategory.AGENT_MANAGEMENT,
                AuditCategory.COMMUNITY_MANAGEMENT,
                AuditCategory.USER_MODERATION,
                AuditCategory.MEMORY_OPERATIONS,
                AuditCategory.SYSTEM_OPERATIONS,
                AuditCategory.DATA_ACCESS,
                AuditCategory.CONFIGURATION,
                AuditCategory.INTEGRATION
            ],
            help='Filter by specific audit categories'
        )
        
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path for the report (JSON format)'
        )
        
        parser.add_argument(
            '--include-details',
            action='store_true',
            default=True,
            help='Include detailed log entries in the report'
        )
        
        parser.add_argument(
            '--summary-only',
            action='store_true',
            help='Generate summary report only (no detailed logs)'
        )
        
        parser.add_argument(
            '--format',
            choices=['json', 'text'],
            default='text',
            help='Output format for the report'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Generating audit report...'))\n        \n        try:\n            # Parse date arguments\n            start_date = self._parse_date_argument(options.get('start_date'))\n            end_date = self._parse_date_argument(options.get('end_date'))\n            \n            # Handle days argument\n            if options.get('days'):\n                if start_date or end_date:\n                    raise CommandError('Cannot use --days with --start-date or --end-date')\n                start_date = timezone.now() - timedelta(days=options['days'])\n                end_date = timezone.now()\n            \n            # Set default date range if none specified (last 30 days)\n            if not start_date and not end_date:\n                start_date = timezone.now() - timedelta(days=30)\n                end_date = timezone.now()\n            \n            # Generate report\n            report = audit_service.generate_audit_report(\n                agent_uid=options.get('agent_uid'),\n                community_uid=options.get('community_uid'),\n                start_date=start_date,\n                end_date=end_date,\n                categories=options.get('categories'),\n                include_details=not options.get('summary_only', False)\n            )\n            \n            # Output report\n            if options.get('format') == 'json':\n                self._output_json_report(report, options.get('output_file'))\n            else:\n                self._output_text_report(report, options.get('output_file'))\n            \n            self.stdout.write(\n                self.style.SUCCESS('Audit report generated successfully')\n            )\n            \n        except Exception as e:\n            logger.error(f'Audit report generation failed: {str(e)}')\n            raise CommandError(f'Audit report generation failed: {str(e)}')\n    \n    def _parse_date_argument(self, date_str):\n        \"\"\"Parse date string argument.\"\"\"\n        if not date_str:\n            return None\n        \n        try:\n            return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.get_current_timezone())\n        except ValueError:\n            raise CommandError(f'Invalid date format: {date_str}. Use YYYY-MM-DD format.')\n    \n    def _output_json_report(self, report, output_file):\n        \"\"\"Output report in JSON format.\"\"\"\n        json_output = json.dumps(report, indent=2, default=str)\n        \n        if output_file:\n            with open(output_file, 'w') as f:\n                f.write(json_output)\n            self.stdout.write(f'Report saved to: {output_file}')\n        else:\n            self.stdout.write(json_output)\n    \n    def _output_text_report(self, report, output_file):\n        \"\"\"Output report in human-readable text format.\"\"\"\n        lines = []\n        \n        # Header\n        lines.append('=' * 60)\n        lines.append('AGENT AUDIT REPORT')\n        lines.append('=' * 60)\n        lines.append('')\n        \n        # Report metadata\n        lines.append(f\"Generated at: {report['report_generated_at']}\")\n        lines.append('')\n        \n        # Filters\n        filters = report['filters']\n        lines.append('FILTERS:')\n        if filters['agent_uid']:\n            lines.append(f\"  Agent UID: {filters['agent_uid']}\")\n        if filters['community_uid']:\n            lines.append(f\"  Community UID: {filters['community_uid']}\")\n        if filters['start_date']:\n            lines.append(f\"  Start Date: {filters['start_date']}\")\n        if filters['end_date']:\n            lines.append(f\"  End Date: {filters['end_date']}\")\n        if filters['categories']:\n            lines.append(f\"  Categories: {', '.join(filters['categories'])}\")\n        lines.append('')\n        \n        # Summary\n        summary = report['summary']\n        lines.append('SUMMARY:')\n        lines.append(f\"  Total Logs: {summary['total_logs']}\")\n        lines.append(f\"  Successful Operations: {summary['success_count']}\")\n        lines.append(f\"  Failed Operations: {summary['failure_count']}\")\n        lines.append(f\"  Success Rate: {summary['success_rate']:.2f}%\")\n        lines.append('')\n        \n        # Category breakdown\n        if report['category_breakdown']:\n            lines.append('CATEGORY BREAKDOWN:')\n            for category, count in sorted(report['category_breakdown'].items()):\n                lines.append(f\"  {category}: {count}\")\n            lines.append('')\n        \n        # Action breakdown\n        if report['action_breakdown']:\n            lines.append('ACTION BREAKDOWN:')\n            for action, count in sorted(report['action_breakdown'].items(), key=lambda x: x[1], reverse=True):\n                lines.append(f\"  {action}: {count}\")\n            lines.append('')\n        \n        # Detailed logs\n        if 'detailed_logs' in report and report['detailed_logs']:\n            lines.append('DETAILED LOGS (Most Recent 100):')\n            lines.append('-' * 60)\n            \n            for log in report['detailed_logs']:\n                lines.append(f\"Timestamp: {log['timestamp']}\")\n                lines.append(f\"Agent: {log['agent_uid']}\")\n                lines.append(f\"Community: {log['community_uid']}\")\n                lines.append(f\"Action: {log['action_type']}\")\n                lines.append(f\"Success: {log['success']}\")\n                \n                if log['execution_time_ms']:\n                    lines.append(f\"Execution Time: {log['execution_time_ms']}ms\")\n                \n                if log['error_message']:\n                    lines.append(f\"Error: {log['error_message']}\")\n                \n                if log['details']:\n                    lines.append(f\"Details: {json.dumps(log['details'], indent=2)}\")\n                \n                lines.append('-' * 40)\n        \n        # Output\n        text_output = '\\n'.join(lines)\n        \n        if output_file:\n            with open(output_file, 'w') as f:\n                f.write(text_output)\n            self.stdout.write(f'Report saved to: {output_file}')\n        else:\n            self.stdout.write(text_output)