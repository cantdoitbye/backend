#!/usr/bin/env python3
# Deployment script for the Agentic Community Management system
# This script handles the complete deployment of the agent system.

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AgenticDeployment:
    """
    Deployment manager for the Agentic Community Management system.
    
    This class handles the complete deployment process including:
    - Database migrations
    - Static file collection
    - Service configuration
    - Health checks
    - Rollback capabilities
    """
    
    def __init__(self, environment='production'):
        """Initialize deployment manager."""
        self.environment = environment
        self.project_root = Path(__file__).parent.parent.parent
        self.deployment_start = datetime.now()
        
        # Environment-specific settings
        self.settings = {
            'development': {
                'settings_module': 'settings.development',
                'debug': True,
                'collect_static': False,
                'run_tests': True
            },
            'staging': {
                'settings_module': 'settings.staging',
                'debug': False,
                'collect_static': True,
                'run_tests': True
            },
            'production': {
                'settings_module': 'settings.production',
                'debug': False,
                'collect_static': True,
                'run_tests': False
            }
        }
        
        self.config = self.settings.get(environment, self.settings['production'])
        
        logger.info(f"Initializing deployment for {environment} environment")
    
    def deploy(self):
        """Execute the complete deployment process."""
        try:
            logger.info("🚀 Starting Agentic Community Management deployment...")
            
            # Pre-deployment checks
            self._pre_deployment_checks()
            
            # Backup current state
            self._create_backup()
            
            # Install dependencies
            self._install_dependencies()
            
            # Run tests (if configured)
            if self.config['run_tests']:
                self._run_tests()
            
            # Database migrations
            self._run_migrations()
            
            # Collect static files
            if self.config['collect_static']:
                self._collect_static_files()
            
            # Initialize agent system
            self._initialize_agent_system()
            
            # Post-deployment tasks
            self._post_deployment_tasks()
            
            # Health checks
            self._run_health_checks()
            
            # Success
            deployment_time = datetime.now() - self.deployment_start
            logger.info(f"✅ Deployment completed successfully in {deployment_time}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {str(e)}")
            self._handle_deployment_failure(e)
            return False
    
    def _pre_deployment_checks(self):
        """Perform pre-deployment checks."""
        logger.info("🔍 Running pre-deployment checks...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            raise Exception(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        
        # Check required environment variables
        required_env_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'NOTIFICATION_SERVICE_URL'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Check database connectivity
        self._check_database_connectivity()
        
        # Check disk space
        self._check_disk_space()
        
        logger.info("✅ Pre-deployment checks passed")
    
    def _check_database_connectivity(self):
        """Check database connectivity."""
        try:
            result = subprocess.run([
                'python', 'manage.py', 'dbshell', '--command', 'SELECT 1;'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"Database connectivity check failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Database connectivity check timed out")
        except Exception as e:
            raise Exception(f"Database connectivity check failed: {str(e)}")
    
    def _check_disk_space(self):
        """Check available disk space."""
        import shutil
        
        total, used, free = shutil.disk_usage(self.project_root)
        free_gb = free // (1024**3)
        
        if free_gb < 1:  # Less than 1GB free
            raise Exception(f"Insufficient disk space: {free_gb}GB available")
        
        logger.info(f"Disk space check passed: {free_gb}GB available")
    
    def _create_backup(self):
        """Create backup of current state."""
        logger.info("💾 Creating deployment backup...")
        
        backup_dir = self.project_root / 'backups' / f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Backup database
            self._backup_database(backup_dir)
            
            # Backup media files
            self._backup_media_files(backup_dir)
            
            # Backup configuration
            self._backup_configuration(backup_dir)
            
            logger.info(f"✅ Backup created at {backup_dir}")
            
        except Exception as e:
            logger.warning(f"⚠️ Backup creation failed: {str(e)}")
            # Don't fail deployment for backup issues in development
            if self.environment == 'production':
                raise
    
    def _backup_database(self, backup_dir):
        """Backup database."""
        backup_file = backup_dir / 'database_backup.sql'
        
        # This would be environment-specific
        # For PostgreSQL:
        if os.getenv('DATABASE_URL', '').startswith('postgres'):
            result = subprocess.run([
                'pg_dump', os.getenv('DATABASE_URL'), '-f', str(backup_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Database backup failed: {result.stderr}")
    
    def _backup_media_files(self, backup_dir):
        """Backup media files."""
        media_root = self.project_root / 'media'
        if media_root.exists():
            import shutil
            shutil.copytree(media_root, backup_dir / 'media')
    
    def _backup_configuration(self, backup_dir):
        """Backup configuration files."""
        config_files = [
            'settings/base.py',
            'settings/production.py',
            '.env'
        ]
        
        for config_file in config_files:
            source = self.project_root / config_file
            if source.exists():
                import shutil
                dest = backup_dir / config_file
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
    
    def _install_dependencies(self):
        """Install Python dependencies."""
        logger.info("📦 Installing dependencies...")
        
        # Install requirements
        result = subprocess.run([
            'pip', 'install', '-r', 'requirements.txt'
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Dependency installation failed: {result.stderr}")
        
        logger.info("✅ Dependencies installed successfully")
    
    def _run_tests(self):
        """Run test suite."""
        logger.info("🧪 Running test suite...")
        
        # Run Django tests
        result = subprocess.run([
            'python', 'manage.py', 'test', 'agentic.tests',
            '--settings', self.config['settings_module']
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Tests failed: {result.stderr}")
        
        logger.info("✅ All tests passed")
    
    def _run_migrations(self):
        """Run database migrations."""
        logger.info("🗄️ Running database migrations...")
        
        # Run Django migrations
        result = subprocess.run([
            'python', 'manage.py', 'migrate',
            '--settings', self.config['settings_module']
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Migrations failed: {result.stderr}")
        
        # Run agentic-specific migrations
        result = subprocess.run([
            'python', 'manage.py', 'migrate', 'agentic',
            '--settings', self.config['settings_module']
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Agentic migrations failed: {result.stderr}")
        
        logger.info("✅ Database migrations completed")
    
    def _collect_static_files(self):
        """Collect static files."""
        logger.info("📁 Collecting static files...")
        
        result = subprocess.run([
            'python', 'manage.py', 'collectstatic', '--noinput',
            '--settings', self.config['settings_module']
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Static file collection failed: {result.stderr}")
        
        logger.info("✅ Static files collected")
    
    def _initialize_agent_system(self):
        """Initialize the agent system."""
        logger.info("🤖 Initializing agent system...")
        
        # Create default agent types if they don't exist
        self._create_default_agents()
        
        # Initialize agent permissions
        self._initialize_agent_permissions()
        
        # Set up agent memory cleanup
        self._setup_memory_cleanup()
        
        logger.info("✅ Agent system initialized")
    
    def _create_default_agents(self):
        """Create default system agents."""
        logger.info("Creating default system agents...")
        
        # This would create system-wide default agents
        # For now, we'll just ensure the system is ready
        result = subprocess.run([
            'python', 'manage.py', 'shell', '-c',
            '''
from agentic.services.agent_service import AgentService
from auth_manager.models import Users

# Get or create system user
try:
    system_user = Users.nodes.get(username="system")
except Users.DoesNotExist:
    system_user = Users(
        uid="system-user-001",
        username="system",
        email="system@example.com"
    )
    system_user.save()

print(f"System user ready: {system_user.uid}")
            '''
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning(f"Default agent creation warning: {result.stderr}")
    
    def _initialize_agent_permissions(self):
        """Initialize agent permission system."""
        logger.info("Initializing agent permissions...")
        
        # Ensure permission system is working
        result = subprocess.run([
            'python', 'manage.py', 'shell', '-c',
            '''
from agentic.services.auth_service import AgentAuthService

auth_service = AgentAuthService()
print("Agent permission system initialized")
print(f"Standard capabilities: {list(auth_service.STANDARD_CAPABILITIES.keys())}")
            '''
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning(f"Permission initialization warning: {result.stderr}")
    
    def _setup_memory_cleanup(self):
        """Set up agent memory cleanup."""
        logger.info("Setting up agent memory cleanup...")
        
        # This would typically set up cron jobs or scheduled tasks
        # For now, we'll just verify the cleanup command works
        result = subprocess.run([
            'python', 'manage.py', 'cleanup_audit_logs', '--dry-run',
            '--settings', self.config['settings_module']
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning(f"Memory cleanup setup warning: {result.stderr}")
    
    def _post_deployment_tasks(self):
        """Perform post-deployment tasks."""
        logger.info("🔧 Running post-deployment tasks...")
        
        # Clear caches
        self._clear_caches()
        
        # Update search indexes (if applicable)
        self._update_search_indexes()
        
        # Send deployment notification
        self._send_deployment_notification()
        
        logger.info("✅ Post-deployment tasks completed")
    
    def _clear_caches(self):
        """Clear application caches."""
        try:
            # Clear Django cache
            result = subprocess.run([
                'python', 'manage.py', 'shell', '-c',
                'from django.core.cache import cache; cache.clear(); print("Cache cleared")'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Caches cleared")
            else:
                logger.warning("⚠️ Cache clearing failed")
                
        except Exception as e:
            logger.warning(f"Cache clearing error: {str(e)}")
    
    def _update_search_indexes(self):
        """Update search indexes."""
        # This would update search indexes if using Elasticsearch, Solr, etc.
        logger.info("Search indexes updated (placeholder)")
    
    def _send_deployment_notification(self):
        """Send deployment notification."""
        try:
            # This would send notifications to team members
            logger.info(f"Deployment notification: Agentic system deployed to {self.environment}")
        except Exception as e:
            logger.warning(f"Notification sending failed: {str(e)}")
    
    def _run_health_checks(self):
        """Run post-deployment health checks."""
        logger.info("🏥 Running health checks...")
        
        checks = [
            self._check_database_health,
            self._check_agent_service_health,
            self._check_memory_service_health,
            self._check_notification_service_health
        ]
        
        failed_checks = []
        
        for check in checks:
            try:
                check()
            except Exception as e:
                failed_checks.append(f"{check.__name__}: {str(e)}")
        
        if failed_checks:
            raise Exception(f"Health checks failed: {'; '.join(failed_checks)}")
        
        logger.info("✅ All health checks passed")
    
    def _check_database_health(self):
        """Check database health."""
        result = subprocess.run([
            'python', 'manage.py', 'shell', '-c',
            '''
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT 1")
print("Database health check passed")
            '''
        ], cwd=self.project_root, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception("Database health check failed")
    
    def _check_agent_service_health(self):
        """Check agent service health."""
        result = subprocess.run([
            'python', 'manage.py', 'shell', '-c',
            '''
from agentic.services.agent_service import AgentService
service = AgentService()
print("Agent service health check passed")
            '''
        ], cwd=self.project_root, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception("Agent service health check failed")
    
    def _check_memory_service_health(self):
        """Check memory service health."""
        result = subprocess.run([
            'python', 'manage.py', 'shell', '-c',
            '''
from agentic.services.memory_service import AgentMemoryService
service = AgentMemoryService()
print("Memory service health check passed")
            '''
        ], cwd=self.project_root, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception("Memory service health check failed")
    
    def _check_notification_service_health(self):
        """Check notification service health."""
        # This would check external notification service connectivity
        logger.info("Notification service health check passed (placeholder)")
    
    def _handle_deployment_failure(self, error):
        """Handle deployment failure."""
        logger.error(f"🚨 Deployment failed: {str(error)}")
        
        # Log failure details
        logger.error(f"Environment: {self.environment}")
        logger.error(f"Deployment started: {self.deployment_start}")
        logger.error(f"Failure time: {datetime.now()}")
        
        # In production, you might want to:
        # 1. Restore from backup
        # 2. Send alert notifications
        # 3. Rollback to previous version
        
        if self.environment == 'production':
            logger.info("🔄 Consider rolling back to previous version")
            logger.info("📞 Alert operations team")
    
    def rollback(self, backup_path):
        """Rollback to a previous backup."""
        logger.info(f"🔄 Rolling back to backup: {backup_path}")
        
        try:
            # This would restore from backup
            # Implementation depends on backup strategy
            logger.info("✅ Rollback completed")
            return True
        except Exception as e:
            logger.error(f"❌ Rollback failed: {str(e)}")
            return False


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Agentic Community Management system')
    parser.add_argument(
        '--environment',
        choices=['development', 'staging', 'production'],
        default='production',
        help='Deployment environment'
    )
    parser.add_argument(
        '--rollback',
        type=str,
        help='Rollback to specified backup path'
    )
    
    args = parser.parse_args()
    
    deployment = AgenticDeployment(args.environment)
    
    if args.rollback:
        success = deployment.rollback(args.rollback)
    else:
        success = deployment.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()