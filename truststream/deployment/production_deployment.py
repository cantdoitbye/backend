# truststream/deployment/production_deployment.py

"""
Production Deployment Orchestrator for TrustStream v4.4

This module orchestrates the complete production deployment of TrustStream,
including infrastructure setup, service deployment, monitoring, and health checks.
"""

import os
import sys
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from .production_config import ProductionConfig, get_config
from .docker_config import DockerConfig
from .nginx_config import NginxConfigGenerator
from .monitoring_config import MonitoringConfigGenerator
from .deployment_manager import DeploymentManager, DeploymentStatus
from .health_checks import HealthCheckManager
from .migration_runner import MigrationRunner


@dataclass
class DeploymentPlan:
    """Production deployment plan."""
    
    environment: str
    domain: str
    ssl_mode: str  # 'dev' or 'prod'
    enable_monitoring: bool = True
    enable_ssl: bool = True
    backup_before_deploy: bool = True
    run_migrations: bool = True
    validate_deployment: bool = True


class ProductionDeploymentOrchestrator:
    """Orchestrates complete TrustStream production deployment."""
    
    def __init__(self, config: Optional[ProductionConfig] = None):
        """Initialize production deployment orchestrator."""
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.docker_config = DockerConfig()
        self.nginx_config = NginxConfigGenerator(self.config)
        self.monitoring_config = MonitoringConfigGenerator(self.config)
        self.deployment_manager = DeploymentManager(self.config)
        self.health_checker = HealthCheckManager(self.config)
        self.migration_runner = MigrationRunner(self.config)
        
        # Deployment state
        self.deployment_status = DeploymentStatus.PENDING
        self.deployment_logs = []
    
    def log_step(self, message: str, level: str = "INFO"):
        """Log deployment step."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}"
        self.deployment_logs.append(log_message)
        
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        print(log_message)
    
    async def deploy_production(self, plan: DeploymentPlan) -> bool:
        """Deploy TrustStream to production."""
        try:
            self.log_step("Starting TrustStream v4.4 production deployment")
            self.deployment_status = DeploymentStatus.IN_PROGRESS
            
            # Step 1: Validate environment
            if not await self._validate_environment(plan):
                return False
            
            # Step 2: Generate configurations
            if not await self._generate_configurations(plan):
                return False
            
            # Step 3: Backup existing deployment (if requested)
            if plan.backup_before_deploy:
                if not await self._backup_deployment():
                    return False
            
            # Step 4: Build and deploy services
            if not await self._deploy_services(plan):
                return False
            
            # Step 5: Run database migrations
            if plan.run_migrations:
                if not await self._run_migrations():
                    return False
            
            # Step 6: Setup SSL certificates
            if plan.enable_ssl:
                if not await self._setup_ssl(plan):
                    return False
            
            # Step 7: Deploy monitoring stack
            if plan.enable_monitoring:
                if not await self._deploy_monitoring():
                    return False
            
            # Step 8: Validate deployment
            if plan.validate_deployment:
                if not await self._validate_deployment():
                    return False
            
            # Step 9: Final health checks
            if not await self._final_health_checks():
                return False
            
            self.deployment_status = DeploymentStatus.COMPLETED
            self.log_step("TrustStream v4.4 production deployment completed successfully!")
            
            # Print deployment summary
            self._print_deployment_summary(plan)
            
            return True
            
        except Exception as e:
            self.deployment_status = DeploymentStatus.FAILED
            self.log_step(f"Deployment failed: {str(e)}", "ERROR")
            return False
    
    async def _validate_environment(self, plan: DeploymentPlan) -> bool:
        """Validate deployment environment."""
        self.log_step("Validating deployment environment")
        
        try:
            # Check Docker
            result = await asyncio.create_subprocess_exec(
                'docker', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            if result.returncode != 0:
                self.log_step("Docker is not installed or not running", "ERROR")
                return False
            
            # Check Docker Compose
            result = await asyncio.create_subprocess_exec(
                'docker-compose', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            if result.returncode != 0:
                self.log_step("Docker Compose is not installed", "ERROR")
                return False
            
            # Check required environment variables
            required_vars = [
                'TRUSTSTREAM_SECRET_KEY',
                'POSTGRES_PASSWORD',
                'NEO4J_PASSWORD',
                'OPENAI_API_KEY'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.log_step(f"Missing required environment variables: {', '.join(missing_vars)}", "ERROR")
                return False
            
            # Check disk space (minimum 10GB)
            import shutil
            free_space = shutil.disk_usage('.').free / (1024**3)  # GB
            if free_space < 10:
                self.log_step(f"Insufficient disk space: {free_space:.1f}GB available, 10GB required", "ERROR")
                return False
            
            self.log_step("Environment validation completed successfully")
            return True
            
        except Exception as e:
            self.log_step(f"Environment validation failed: {str(e)}", "ERROR")
            return False
    
    async def _generate_configurations(self, plan: DeploymentPlan) -> bool:
        """Generate all configuration files."""
        self.log_step("Generating configuration files")
        
        try:
            # Create config directories
            config_dirs = ['config/docker', 'config/nginx', 'config/monitoring']
            for dir_path in config_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            
            # Generate Docker configurations
            self.docker_config.save_configurations('config/docker')
            self.log_step("Docker configurations generated")
            
            # Generate Nginx configurations
            self.nginx_config.save_configurations('config/nginx')
            self.log_step("Nginx configurations generated")
            
            # Generate monitoring configurations
            self.monitoring_config.save_configurations('config/monitoring')
            self.log_step("Monitoring configurations generated")
            
            # Generate environment file
            self._generate_env_file(plan)
            self.log_step("Environment file generated")
            
            return True
            
        except Exception as e:
            self.log_step(f"Configuration generation failed: {str(e)}", "ERROR")
            return False
    
    def _generate_env_file(self, plan: DeploymentPlan):
        """Generate .env file for deployment."""
        env_content = f"""# TrustStream v4.4 Production Environment
# Generated automatically - do not edit manually

# Environment
ENVIRONMENT={plan.environment}
DOMAIN={plan.domain}
DEBUG=false

# Security
SECRET_KEY={os.getenv('TRUSTSTREAM_SECRET_KEY')}
ALLOWED_HOSTS={plan.domain},localhost,127.0.0.1

# Database
POSTGRES_DB=truststream
POSTGRES_USER=truststream
POSTGRES_PASSWORD={os.getenv('POSTGRES_PASSWORD')}
POSTGRES_HOST=truststream-postgres
POSTGRES_PORT=5432

# Neo4j
NEO4J_URI=bolt://truststream-neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD={os.getenv('NEO4J_PASSWORD')}

# Redis
REDIS_URL=redis://truststream-redis:6379/0

# AI Providers
OPENAI_API_KEY={os.getenv('OPENAI_API_KEY')}
CLAUDE_API_KEY={os.getenv('CLAUDE_API_KEY', '')}

# Matrix Integration
MATRIX_HOMESERVER_URL={os.getenv('MATRIX_HOMESERVER_URL', '')}
MATRIX_ACCESS_TOKEN={os.getenv('MATRIX_ACCESS_TOKEN', '')}

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# Performance
WORKERS=4
MAX_CONNECTIONS=1000
CACHE_TTL=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
    
    async def _backup_deployment(self) -> bool:
        """Backup existing deployment."""
        self.log_step("Creating deployment backup")
        
        try:
            backup_result = await self.deployment_manager.backup_deployment()
            if backup_result:
                self.log_step(f"Backup created successfully: {backup_result}")
                return True
            else:
                self.log_step("Backup creation failed", "WARNING")
                return True  # Continue deployment even if backup fails
                
        except Exception as e:
            self.log_step(f"Backup failed: {str(e)}", "WARNING")
            return True  # Continue deployment even if backup fails
    
    async def _deploy_services(self, plan: DeploymentPlan) -> bool:
        """Deploy all services."""
        self.log_step("Deploying services")
        
        try:
            # Build Docker images
            self.log_step("Building Docker images")
            result = await asyncio.create_subprocess_exec(
                'docker-compose', '-f', 'config/docker/docker-compose.yml', 'build',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            if result.returncode != 0:
                self.log_step("Docker image build failed", "ERROR")
                return False
            
            # Deploy services
            self.log_step("Starting services")
            result = await asyncio.create_subprocess_exec(
                'docker-compose', '-f', 'config/docker/docker-compose.yml', 'up', '-d',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            if result.returncode != 0:
                self.log_step("Service deployment failed", "ERROR")
                return False
            
            # Wait for services to be ready
            self.log_step("Waiting for services to be ready")
            await asyncio.sleep(30)  # Give services time to start
            
            return True
            
        except Exception as e:
            self.log_step(f"Service deployment failed: {str(e)}", "ERROR")
            return False
    
    async def _run_migrations(self) -> bool:
        """Run database migrations."""
        self.log_step("Running database migrations")
        
        try:
            # Wait for databases to be ready
            await asyncio.sleep(10)
            
            # Run migrations
            migration_result = await self.migration_runner.run_all_migrations()
            
            if migration_result.success:
                self.log_step("Database migrations completed successfully")
                return True
            else:
                self.log_step(f"Database migrations failed: {migration_result.error}", "ERROR")
                return False
                
        except Exception as e:
            self.log_step(f"Migration execution failed: {str(e)}", "ERROR")
            return False
    
    async def _setup_ssl(self, plan: DeploymentPlan) -> bool:
        """Setup SSL certificates."""
        self.log_step(f"Setting up SSL certificates ({plan.ssl_mode} mode)")
        
        try:
            # Run SSL setup script
            result = await asyncio.create_subprocess_exec(
                'bash', 'config/nginx/ssl_setup.sh', plan.ssl_mode,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            
            if result.returncode == 0:
                self.log_step("SSL certificates setup completed")
                return True
            else:
                self.log_step("SSL setup failed", "ERROR")
                return False
                
        except Exception as e:
            self.log_step(f"SSL setup failed: {str(e)}", "ERROR")
            return False
    
    async def _deploy_monitoring(self) -> bool:
        """Deploy monitoring stack."""
        self.log_step("Deploying monitoring stack")
        
        try:
            # Deploy monitoring services
            result = await asyncio.create_subprocess_exec(
                'docker-compose', '-f', 'config/monitoring/docker-compose.monitoring.yml', 'up', '-d',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            
            if result.returncode == 0:
                self.log_step("Monitoring stack deployed successfully")
                return True
            else:
                self.log_step("Monitoring deployment failed", "ERROR")
                return False
                
        except Exception as e:
            self.log_step(f"Monitoring deployment failed: {str(e)}", "ERROR")
            return False
    
    async def _validate_deployment(self) -> bool:
        """Validate deployment."""
        self.log_step("Validating deployment")
        
        try:
            # Validate migrations
            validation_result = await self.migration_runner.validate_migrations()
            
            if not validation_result.success:
                self.log_step(f"Migration validation failed: {validation_result.error}", "ERROR")
                return False
            
            self.log_step("Deployment validation completed successfully")
            return True
            
        except Exception as e:
            self.log_step(f"Deployment validation failed: {str(e)}", "ERROR")
            return False
    
    async def _final_health_checks(self) -> bool:
        """Perform final health checks."""
        self.log_step("Performing final health checks")
        
        try:
            # Wait for all services to be fully ready
            await asyncio.sleep(30)
            
            # Run comprehensive health checks
            health_status = await self.health_checker.check_system_health()
            
            if health_status.overall_health == "healthy":
                self.log_step("All health checks passed")
                return True
            else:
                self.log_step(f"Health checks failed: {health_status.overall_health}", "ERROR")
                for service, result in health_status.service_results.items():
                    if not result.healthy:
                        self.log_step(f"  - {service}: {result.error}", "ERROR")
                return False
                
        except Exception as e:
            self.log_step(f"Health checks failed: {str(e)}", "ERROR")
            return False
    
    def _print_deployment_summary(self, plan: DeploymentPlan):
        """Print deployment summary."""
        print("\n" + "="*60)
        print("TrustStream v4.4 Production Deployment Summary")
        print("="*60)
        print(f"Environment: {plan.environment}")
        print(f"Domain: {plan.domain}")
        print(f"SSL Mode: {plan.ssl_mode}")
        print(f"Monitoring: {'Enabled' if plan.enable_monitoring else 'Disabled'}")
        print(f"Status: {self.deployment_status.value}")
        print("\nServices:")
        print("  - TrustStream Application: http://localhost:8000")
        print("  - Nginx Reverse Proxy: http://localhost:80")
        if plan.enable_ssl:
            print("  - HTTPS: https://localhost:443")
        if plan.enable_monitoring:
            print("  - Prometheus: http://localhost:9090")
            print("  - Grafana: http://localhost:3000")
            print("  - Alertmanager: http://localhost:9093")
        print("\nDatabases:")
        print("  - PostgreSQL: localhost:5432")
        print("  - Neo4j: localhost:7474 (HTTP), localhost:7687 (Bolt)")
        print("  - Redis: localhost:6379")
        print("\nNext Steps:")
        print("  1. Access the application at your configured domain")
        print("  2. Monitor system health via Grafana dashboards")
        print("  3. Check logs: docker-compose logs -f")
        print("  4. Scale services: docker-compose up --scale app=3")
        print("="*60)


async def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy TrustStream v4.4 to production')
    parser.add_argument('--environment', default='production', help='Deployment environment')
    parser.add_argument('--domain', default='truststream.local', help='Domain name')
    parser.add_argument('--ssl-mode', choices=['dev', 'prod'], default='dev', help='SSL certificate mode')
    parser.add_argument('--no-monitoring', action='store_true', help='Disable monitoring stack')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL setup')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    parser.add_argument('--no-migrations', action='store_true', help='Skip database migrations')
    parser.add_argument('--no-validation', action='store_true', help='Skip deployment validation')
    
    args = parser.parse_args()
    
    # Create deployment plan
    plan = DeploymentPlan(
        environment=args.environment,
        domain=args.domain,
        ssl_mode=args.ssl_mode,
        enable_monitoring=not args.no_monitoring,
        enable_ssl=not args.no_ssl,
        backup_before_deploy=not args.no_backup,
        run_migrations=not args.no_migrations,
        validate_deployment=not args.no_validation
    )
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Deploy
    orchestrator = ProductionDeploymentOrchestrator()
    success = await orchestrator.deploy_production(plan)
    
    if success:
        print("\n✅ Deployment completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())