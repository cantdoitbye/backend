# Agent Audit Logging Service
# This module provides comprehensive audit logging for all agent operations.

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from django.utils import timezone
from django.db import transaction

from ..models import AgentActionLog, AgentMemory
from ..exceptions import AgentError, AgentMemoryError
from .auth_service import AgentAuthService


logger = logging.getLogger(__name__)


class AuditLogLevel:
    """Constants for audit log levels."""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class AuditCategory:
    """Constants for audit categories."""
    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    AGENT_MANAGEMENT = 'agent_management'
    COMMUNITY_MANAGEMENT = 'community_management'
    USER_MODERATION = 'user_moderation'
    MEMORY_OPERATIONS = 'memory_operations'
    SYSTEM_OPERATIONS = 'system_operations'
    DATA_ACCESS = 'data_access'
    CONFIGURATION = 'configuration'
    INTEGRATION = 'integration'


class AgentAuditService:
    """
    Comprehensive audit logging service for agent operations.
    
    This service provides structured logging of all agent activities,
    including authentication, authorization, actions, and system events.
    """
    
    def __init__(self):
        """Initialize the audit service."""
        self.auth_service = AgentAuthService()
        self.logger = logging.getLogger('agentic.audit')
        
        # Configure structured logging
        self._configure_audit_logger()
    
    def _configure_audit_logger(self):
        """Configure the audit logger with structured formatting."""
        # This would typically be configured in Django settings
        # For now, we'll ensure the logger exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_agent_authentication(
        self,
        agent_uid: str,
        community_uid: str,
        success: bool,
        authentication_method: str = 'token',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log agent authentication attempts.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            success: Whether authentication succeeded
            authentication_method: Method used for authentication
            ip_address: IP address of the request
            user_agent: User agent string
            failure_reason: Reason for failure if applicable
            
        Returns:
            Dict containing the audit log entry
        """
        audit_data = {
            'agent_uid': agent_uid,
            'community_uid': community_uid,
            'category': AuditCategory.AUTHENTICATION,
            'action': 'authenticate',
            'success': success,
            'authentication_method': authentication_method,
            'timestamp': timezone.now().isoformat(),
            'metadata': {
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        }
        
        if not success and failure_reason:
            audit_data['failure_reason'] = failure_reason
            audit_data['level'] = AuditLogLevel.WARNING
        else:
            audit_data['level'] = AuditLogLevel.INFO
        
        # Store in database
        try:
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type='authentication',
                details=audit_data,
                success=success,
                error_message=failure_reason
            )
        except Exception as e:
            logger.error(f"Failed to store authentication audit log: {str(e)}")
        
        # Log to structured logger
        log_level = logging.WARNING if not success else logging.INFO
        self.logger.log(
            log_level,
            f"Agent authentication {'succeeded' if success else 'failed'}",
            extra=audit_data
        )
        
        return audit_data
    
    def log_permission_check(
        self,
        agent_uid: str,
        community_uid: str,
        permission: str,
        resource: Optional[str] = None,
        granted: bool = True,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log permission checks and authorization decisions.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            permission: Permission being checked
            resource: Resource being accessed
            granted: Whether permission was granted
            reason: Reason for denial if applicable
            
        Returns:
            Dict containing the audit log entry
        """
        audit_data = {
            'agent_uid': agent_uid,
            'community_uid': community_uid,
            'category': AuditCategory.AUTHORIZATION,
            'action': 'permission_check',
            'permission': permission,
            'resource': resource,
            'granted': granted,
            'timestamp': timezone.now().isoformat(),
            'level': AuditLogLevel.INFO if granted else AuditLogLevel.WARNING
        }
        
        if not granted and reason:
            audit_data['denial_reason'] = reason
        
        # Store in database
        try:
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type='permission_check',
                details=audit_data,
                success=granted,
                error_message=reason if not granted else None
            )
        except Exception as e:
            logger.error(f"Failed to store permission check audit log: {str(e)}")
        
        # Log to structured logger
        log_level = logging.WARNING if not granted else logging.DEBUG
        self.logger.log(
            log_level,
            f"Permission check: {permission} {'granted' if granted else 'denied'}",
            extra=audit_data
        )
        
        return audit_data
    
    def log_agent_action(
        self,
        agent_uid: str,
        community_uid: str,
        action_type: str,
        target_resource: Optional[str] = None,
        target_resource_id: Optional[str] = None,
        action_details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log agent actions and operations.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            action_type: Type of action performed
            target_resource: Type of resource being acted upon
            target_resource_id: ID of the specific resource
            action_details: Detailed information about the action
            success: Whether the action succeeded
            error_message: Error message if action failed
            execution_time_ms: Time taken to execute the action
            user_context: Additional user context information
            
        Returns:
            Dict containing the audit log entry
        """
        # Determine category based on action type
        category = self._categorize_action(action_type)
        
        audit_data = {
            'agent_uid': agent_uid,
            'community_uid': community_uid,
            'category': category,
            'action': action_type,
            'target_resource': target_resource,
            'target_resource_id': target_resource_id,
            'success': success,
            'timestamp': timezone.now().isoformat(),
            'level': AuditLogLevel.INFO if success else AuditLogLevel.ERROR,
            'execution_time_ms': execution_time_ms,
            'details': action_details or {},
            'user_context': user_context or {}
        }
        
        if not success and error_message:
            audit_data['error_message'] = error_message
        
        # Store in database
        try:
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type=action_type,
                details=audit_data,
                success=success,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
                user_context=user_context
            )
        except Exception as e:
            logger.error(f"Failed to store action audit log: {str(e)}")
        
        # Log to structured logger
        log_level = logging.ERROR if not success else logging.INFO
        self.logger.log(
            log_level,
            f"Agent action: {action_type} {'succeeded' if success else 'failed'}",
            extra=audit_data
        )
        
        return audit_data
    
    def log_data_access(
        self,
        agent_uid: str,
        community_uid: str,
        data_type: str,
        operation: str,
        record_count: Optional[int] = None,
        filters_applied: Optional[Dict[str, Any]] = None,
        sensitive_data: bool = False
    ) -> Dict[str, Any]:
        """
        Log data access operations.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            data_type: Type of data being accessed
            operation: Operation performed (read, write, delete, etc.)
            record_count: Number of records affected
            filters_applied: Filters applied to the data query
            sensitive_data: Whether sensitive data was accessed
            
        Returns:
            Dict containing the audit log entry
        """
        audit_data = {
            'agent_uid': agent_uid,
            'community_uid': community_uid,
            'category': AuditCategory.DATA_ACCESS,
            'action': f'data_{operation}',
            'data_type': data_type,
            'operation': operation,
            'record_count': record_count,
            'filters_applied': filters_applied or {},
            'sensitive_data': sensitive_data,
            'timestamp': timezone.now().isoformat(),
            'level': AuditLogLevel.WARNING if sensitive_data else AuditLogLevel.INFO
        }
        
        # Store in database
        try:
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type=f'data_{operation}',
                details=audit_data,
                success=True
            )
        except Exception as e:
            logger.error(f"Failed to store data access audit log: {str(e)}")
        
        # Log to structured logger
        log_level = logging.WARNING if sensitive_data else logging.INFO
        self.logger.log(
            log_level,
            f"Data access: {operation} {data_type}",
            extra=audit_data
        )
        
        return audit_data
    
    def log_system_event(
        self,
        event_type: str,
        event_details: Dict[str, Any],
        agent_uid: Optional[str] = None,
        community_uid: Optional[str] = None,
        severity: str = AuditLogLevel.INFO
    ) -> Dict[str, Any]:
        """
        Log system-level events.
        
        Args:
            event_type: Type of system event
            event_details: Details about the event
            agent_uid: UID of the agent if applicable
            community_uid: UID of the community if applicable
            severity: Severity level of the event
            
        Returns:
            Dict containing the audit log entry
        """
        audit_data = {
            'category': AuditCategory.SYSTEM_OPERATIONS,
            'action': event_type,
            'details': event_details,
            'timestamp': timezone.now().isoformat(),
            'level': severity
        }
        
        if agent_uid:
            audit_data['agent_uid'] = agent_uid
        if community_uid:
            audit_data['community_uid'] = community_uid
        
        # Store in database if agent/community context is available
        if agent_uid and community_uid:
            try:
                self.auth_service.log_agent_action(
                    agent_uid=agent_uid,
                    community_uid=community_uid,
                    action_type=event_type,
                    details=audit_data,
                    success=True
                )
            except Exception as e:
                logger.error(f"Failed to store system event audit log: {str(e)}")
        
        # Log to structured logger
        log_level = getattr(logging, severity, logging.INFO)
        self.logger.log(
            log_level,
            f"System event: {event_type}",
            extra=audit_data
        )
        
        return audit_data
    
    def log_configuration_change(
        self,
        agent_uid: str,
        community_uid: str,
        configuration_type: str,
        old_value: Any,
        new_value: Any,
        changed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log configuration changes.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            configuration_type: Type of configuration changed
            old_value: Previous value
            new_value: New value
            changed_by: Who made the change
            
        Returns:
            Dict containing the audit log entry
        """
        audit_data = {
            'agent_uid': agent_uid,
            'community_uid': community_uid,
            'category': AuditCategory.CONFIGURATION,
            'action': 'configuration_change',
            'configuration_type': configuration_type,
            'old_value': self._sanitize_value(old_value),
            'new_value': self._sanitize_value(new_value),
            'changed_by': changed_by,
            'timestamp': timezone.now().isoformat(),
            'level': AuditLogLevel.INFO
        }
        
        # Store in database
        try:
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type='configuration_change',
                details=audit_data,
                success=True
            )
        except Exception as e:
            logger.error(f"Failed to store configuration change audit log: {str(e)}")
        
        # Log to structured logger
        self.logger.info(
            f"Configuration change: {configuration_type}",
            extra=audit_data
        )
        
        return audit_data
    
    def generate_audit_report(
        self,
        agent_uid: Optional[str] = None,
        community_uid: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        categories: Optional[List[str]] = None,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report.
        
        Args:
            agent_uid: Filter by agent UID
            community_uid: Filter by community UID
            start_date: Start date for the report
            end_date: End date for the report
            categories: List of categories to include
            include_details: Whether to include detailed logs
            
        Returns:
            Dict containing the audit report
        """
        try:
            # Build query filters
            filters = {}
            if agent_uid:
                filters['agent_uid'] = agent_uid
            if community_uid:
                filters['community_uid'] = community_uid
            if start_date:
                filters['timestamp__gte'] = start_date
            if end_date:
                filters['timestamp__lte'] = end_date
            
            # Get audit logs from database
            logs = AgentActionLog.objects.filter(**filters).order_by('-timestamp')
            
            # Filter by categories if specified
            if categories:
                category_logs = []
                for log in logs:
                    try:
                        details = json.loads(log.action_details) if log.action_details else {}
                        if details.get('category') in categories:
                            category_logs.append(log)
                    except (json.JSONDecodeError, AttributeError):
                        continue
                logs = category_logs
            
            # Generate summary statistics
            total_logs = len(logs)
            success_count = sum(1 for log in logs if log.success)
            failure_count = total_logs - success_count
            
            # Category breakdown
            category_stats = {}
            action_stats = {}
            
            for log in logs:
                try:
                    details = json.loads(log.action_details) if log.action_details else {}
                    category = details.get('category', 'unknown')
                    action = log.action_type
                    
                    category_stats[category] = category_stats.get(category, 0) + 1
                    action_stats[action] = action_stats.get(action, 0) + 1
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # Build report
            report = {
                'report_generated_at': timezone.now().isoformat(),
                'filters': {
                    'agent_uid': agent_uid,
                    'community_uid': community_uid,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'categories': categories
                },
                'summary': {
                    'total_logs': total_logs,
                    'success_count': success_count,
                    'failure_count': failure_count,
                    'success_rate': (success_count / total_logs * 100) if total_logs > 0 else 0
                },
                'category_breakdown': category_stats,
                'action_breakdown': action_stats
            }
            
            # Include detailed logs if requested
            if include_details:
                detailed_logs = []
                for log in logs[:100]:  # Limit to 100 most recent logs
                    try:
                        details = json.loads(log.action_details) if log.action_details else {}
                        detailed_logs.append({
                            'timestamp': log.timestamp.isoformat(),
                            'agent_uid': log.agent_uid,
                            'community_uid': log.community_uid,
                            'action_type': log.action_type,
                            'success': log.success,
                            'execution_time_ms': log.execution_time_ms,
                            'details': details,
                            'error_message': log.error_message
                        })
                    except (json.JSONDecodeError, AttributeError):
                        continue
                
                report['detailed_logs'] = detailed_logs
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {str(e)}")
            raise AgentError(f"Failed to generate audit report: {str(e)}")
    
    def cleanup_old_logs(self, retention_days: int = 90) -> Dict[str, Any]:
        """
        Clean up old audit logs based on retention policy.
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Dict containing cleanup results
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=retention_days)
            
            # Count logs to be deleted
            logs_to_delete = AgentActionLog.objects.filter(timestamp__lt=cutoff_date)
            count_to_delete = logs_to_delete.count()
            
            # Delete old logs
            with transaction.atomic():
                deleted_count, _ = logs_to_delete.delete()
            
            # Log the cleanup operation
            cleanup_result = {
                'cleanup_date': timezone.now().isoformat(),
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat(),
                'logs_deleted': deleted_count
            }
            
            self.log_system_event(
                event_type='audit_log_cleanup',
                event_details=cleanup_result,
                severity=AuditLogLevel.INFO
            )
            
            logger.info(f"Cleaned up {deleted_count} old audit logs")
            
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {str(e)}")
            raise AgentError(f"Failed to cleanup audit logs: {str(e)}")
    
    def _categorize_action(self, action_type: str) -> str:
        """
        Categorize an action type into an audit category.
        
        Args:
            action_type: The action type to categorize
            
        Returns:
            str: The audit category
        """
        action_category_map = {
            'authenticate': AuditCategory.AUTHENTICATION,
            'permission_check': AuditCategory.AUTHORIZATION,
            'create_agent': AuditCategory.AGENT_MANAGEMENT,
            'update_agent': AuditCategory.AGENT_MANAGEMENT,
            'delete_agent': AuditCategory.AGENT_MANAGEMENT,
            'assign_agent': AuditCategory.AGENT_MANAGEMENT,
            'edit_community': AuditCategory.COMMUNITY_MANAGEMENT,
            'manage_events': AuditCategory.COMMUNITY_MANAGEMENT,
            'moderate_user': AuditCategory.USER_MODERATION,
            'ban_user': AuditCategory.USER_MODERATION,
            'store_memory': AuditCategory.MEMORY_OPERATIONS,
            'retrieve_memory': AuditCategory.MEMORY_OPERATIONS,
            'webhook_dispatch': AuditCategory.INTEGRATION,
            'notification_sent': AuditCategory.INTEGRATION
        }
        
        return action_category_map.get(action_type, AuditCategory.SYSTEM_OPERATIONS)
    
    def _sanitize_value(self, value: Any) -> Any:
        """
        Sanitize values for logging (remove sensitive information).
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized value
        """
        if isinstance(value, dict):
            sanitized = {}
            sensitive_keys = {'password', 'token', 'secret', 'key', 'credential'}
            
            for k, v in value.items():
                if any(sensitive in k.lower() for sensitive in sensitive_keys):
                    sanitized[k] = '[REDACTED]'
                else:
                    sanitized[k] = self._sanitize_value(v)
            
            return sanitized
        
        elif isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        
        elif isinstance(value, str) and len(value) > 1000:
            # Truncate very long strings
            return value[:1000] + '...[TRUNCATED]'
        
        return value


# Global audit service instance
audit_service = AgentAuditService()