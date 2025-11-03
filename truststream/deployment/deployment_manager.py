# truststream/deployment/deployment_manager.py

"""
Deployment Manager for TrustStream v4.4

This module provides comprehensive deployment management capabilities including
health checks, database migrations, service orchestration, and monitoring setup.
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import asyncio
import aiohttp
import psutil
import docker
import yaml

from .production_config import ProductionConfig, get_config
from .docker_config import DockerConfig, get_docker_config
from .health_checks import HealthCheckManager
from .migration_runner import MigrationRunner


@dataclass
class DeploymentStatus:
    """Deployment status tracking."""
    
    deployment_id: str
    status: str  # pending, in_progress, completed, failed, rolled_back
    start_time: datetime
    end_time: Optional[datetime] = None
    services_deployed: List[str] = field(default_factory=list)
    services_failed: List[str] = field(default_factory=list)
    health_checks_passed: bool = False
    migrations_completed: bool = False
    rollback_available: bool = False
    error_message: Optional[str] = None
    deployment_logs: List[str] = field(default_factory=list)


@dataclass
class ServiceStatus:
    """Individual service status."""
    
    name: str
    status: str  # starting, running, healthy, unhealthy, stopped, failed
    container_id: Optional[str] = None
    health_check_status: Optional[str] = None
    last_health_check: Optional[datetime] = None
    resource_usage: Optional[Dict[str, Any]] = None
    logs: List[str] = field(default_factory=list)


class DeploymentManager:
    """Main deployment manager for TrustStream v4.4."""
    
    def __init__(self, config: Optional[ProductionConfig] = None):
        """Initialize deployment manager."""
        self.config = config or get_config()
        self.docker_config = get_docker_config()
        self.health_checker = HealthCheckManager(self.config)
        self.migration_runner = MigrationRunner(self.config)
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logging.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
        
        # Deployment tracking
        self.current_deployment: Optional[DeploymentStatus] = None
        self.service_statuses: Dict[str, ServiceStatus] = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    async def deploy(self, 
                    deployment_type: str = "full",
                    force_rebuild: bool = False,
                    skip_migrations: bool = False,
                    skip_health_checks: bool = False) -> DeploymentStatus:
        """
        Deploy TrustStream v4.4 to production.
        
        Args:
            deployment_type: Type of deployment (full, update, rollback)
            force_rebuild: Force rebuild of Docker images
            skip_migrations: Skip database migrations
            skip_health_checks: Skip health checks
            
        Returns:
            DeploymentStatus: Deployment status and results
        """
        deployment_id = f"truststream_deploy_{int(time.time())}"
        
        self.current_deployment = DeploymentStatus(
            deployment_id=deployment_id,
            status="pending",
            start_time=datetime.now()
        )
        
        try:
            self.logger.info(f"Starting TrustStream v4.4 deployment: {deployment_id}")
            self.current_deployment.status = "in_progress"
            
            # Step 1: Pre-deployment validation
            await self._validate_deployment_environment()
            
            # Step 2: Backup current deployment (if exists)
            if deployment_type != "rollback":
                await self._backup_current_deployment()
            
            # Step 3: Build and prepare Docker images
            if force_rebuild or deployment_type == "full":
                await self._build_docker_images()
            
            # Step 4: Run database migrations
            if not skip_migrations:
                await self._run_migrations()
                self.current_deployment.migrations_completed = True
            
            # Step 5: Deploy services
            await self._deploy_services(deployment_type)
            
            # Step 6: Run health checks
            if not skip_health_checks:
                await self._run_health_checks()
                self.current_deployment.health_checks_passed = True
            
            # Step 7: Configure monitoring and alerting
            await self._setup_monitoring()
            
            # Step 8: Final validation
            await self._validate_deployment()
            
            # Mark deployment as completed
            self.current_deployment.status = "completed"
            self.current_deployment.end_time = datetime.now()
            
            self.logger.info(f"Deployment {deployment_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Deployment {deployment_id} failed: {e}")
            self.current_deployment.status = "failed"
            self.current_deployment.error_message = str(e)
            self.current_deployment.end_time = datetime.now()
            
            # Attempt rollback on failure
            if deployment_type != "rollback":
                await self._rollback_deployment()
            
            raise
        
        return self.current_deployment
    
    async def _validate_deployment_environment(self):
        """Validate deployment environment and prerequisites."""
        self.logger.info("Validating deployment environment...")
        
        # Check Docker availability
        if not self.docker_client:
            raise RuntimeError("Docker client not available")
        
        # Check system resources
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 8:
            self.logger.warning(f"Low memory detected: {memory_gb:.1f}GB (recommended: 8GB+)")
        
        disk_usage = psutil.disk_usage('/')
        free_gb = disk_usage.free / (1024**3)
        if free_gb < 10:
            raise RuntimeError(f"Insufficient disk space: {free_gb:.1f}GB (required: 10GB+)")
        
        # Check required environment variables
        required_vars = [
            'POSTGRES_PASSWORD',
            'NEO4J_PASSWORD',
            'REDIS_PASSWORD',
            'JWT_SECRET_KEY',
            'ENCRYPTION_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise RuntimeError(f"Missing required environment variables: {missing_vars}")
        
        # Check network connectivity
        await self._check_network_connectivity()
        
        self.logger.info("Environment validation completed")
    
    async def _check_network_connectivity(self):
        """Check network connectivity to external services."""
        test_urls = [
            'https://api.openai.com',
            'https://api.anthropic.com',
            'https://hub.docker.com'
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in test_urls:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status != 200:
                            self.logger.warning(f"Network connectivity issue with {url}: {response.status}")
                except Exception as e:
                    self.logger.warning(f"Network connectivity test failed for {url}: {e}")
    
    async def _backup_current_deployment(self):
        """Backup current deployment for rollback capability."""
        self.logger.info("Creating deployment backup...")
        
        backup_dir = f"/tmp/truststream_backup_{int(time.time())}"
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            # Backup database
            await self._backup_databases(backup_dir)
            
            # Backup configuration
            await self._backup_configuration(backup_dir)
            
            # Mark rollback as available
            self.current_deployment.rollback_available = True
            
            self.logger.info(f"Backup created at {backup_dir}")
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            # Continue deployment without backup
    
    async def _backup_databases(self, backup_dir: str):
        """Backup PostgreSQL and Neo4j databases."""
        # PostgreSQL backup
        postgres_backup_file = os.path.join(backup_dir, "postgres_backup.sql")
        postgres_cmd = [
            "pg_dump",
            "-h", self.config.database.postgres_host,
            "-p", str(self.config.database.postgres_port),
            "-U", self.config.database.postgres_user,
            "-d", self.config.database.postgres_db,
            "-f", postgres_backup_file
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = self.config.database.postgres_password
        
        result = subprocess.run(postgres_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"PostgreSQL backup failed: {result.stderr}")
        
        # Neo4j backup (using neo4j-admin dump)
        neo4j_backup_file = os.path.join(backup_dir, "neo4j_backup.dump")
        neo4j_cmd = [
            "docker", "exec", "truststream-neo4j",
            "neo4j-admin", "database", "dump",
            "--to-path=/tmp",
            self.config.database.neo4j_database
        ]
        
        result = subprocess.run(neo4j_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.warning(f"Neo4j backup failed: {result.stderr}")
    
    async def _backup_configuration(self, backup_dir: str):
        """Backup current configuration files."""
        config_files = [
            "docker-compose.yml",
            ".env",
            "config/nginx.conf",
            "config/prometheus.yml"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                backup_path = os.path.join(backup_dir, os.path.basename(config_file))
                subprocess.run(["cp", config_file, backup_path])
    
    async def _build_docker_images(self):
        """Build Docker images for TrustStream services."""
        self.logger.info("Building Docker images...")
        
        # Generate Dockerfile if not exists
        if not os.path.exists("Dockerfile"):
            self.docker_config.save_dockerfile()
        
        # Build main application image
        try:
            image, build_logs = self.docker_client.images.build(
                path=".",
                tag="truststream/app:4.4.0",
                rm=True,
                forcerm=True
            )
            
            self.logger.info("Docker image built successfully")
            
        except Exception as e:
            raise RuntimeError(f"Docker image build failed: {e}")
    
    async def _run_migrations(self):
        """Run database migrations."""
        self.logger.info("Running database migrations...")
        
        try:
            # Run PostgreSQL migrations
            postgres_result = await self.migration_runner.run_postgres_migrations()
            if not postgres_result['success']:
                raise RuntimeError(f"PostgreSQL migrations failed: {postgres_result['error']}")
            
            # Run Neo4j migrations
            neo4j_result = await self.migration_runner.run_neo4j_migrations()
            if not neo4j_result['success']:
                raise RuntimeError(f"Neo4j migrations failed: {neo4j_result['error']}")
            
            self.logger.info("Database migrations completed successfully")
            
        except Exception as e:
            raise RuntimeError(f"Migration execution failed: {e}")
    
    async def _deploy_services(self, deployment_type: str):
        """Deploy Docker services using docker-compose."""
        self.logger.info("Deploying services...")
        
        # Generate docker-compose.yml if not exists
        if not os.path.exists("docker-compose.yml"):
            self.docker_config.save_docker_compose()
        
        # Deploy services based on deployment type
        if deployment_type == "full":
            await self._deploy_all_services()
        elif deployment_type == "update":
            await self._update_services()
        elif deployment_type == "rollback":
            await self._rollback_services()
    
    async def _deploy_all_services(self):
        """Deploy all services from scratch."""
        # Stop existing services
        subprocess.run(["docker-compose", "down"], capture_output=True)
        
        # Start all services
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Service deployment failed: {result.stderr}")
        
        # Track service status
        await self._update_service_statuses()
        
        self.current_deployment.services_deployed = list(self.service_statuses.keys())
    
    async def _update_services(self):
        """Update existing services."""
        services_to_update = ["truststream-app"]
        
        for service in services_to_update:
            result = subprocess.run(
                ["docker-compose", "up", "-d", "--no-deps", service],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.current_deployment.services_failed.append(service)
                self.logger.error(f"Failed to update service {service}: {result.stderr}")
            else:
                self.current_deployment.services_deployed.append(service)
        
        await self._update_service_statuses()
    
    async def _rollback_services(self):
        """Rollback services to previous version."""
        # This would typically involve deploying from backup or previous image tags
        self.logger.info("Rolling back services...")
        
        # For now, restart services with previous configuration
        result = subprocess.run(
            ["docker-compose", "restart"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Service rollback failed: {result.stderr}")
    
    async def _update_service_statuses(self):
        """Update status of all services."""
        try:
            containers = self.docker_client.containers.list(
                filters={"label": "com.docker.compose.project=truststream"}
            )
            
            for container in containers:
                service_name = container.labels.get("com.docker.compose.service", "unknown")
                
                self.service_statuses[service_name] = ServiceStatus(
                    name=service_name,
                    status=container.status,
                    container_id=container.id,
                    resource_usage=self._get_container_stats(container)
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update service statuses: {e}")
    
    def _get_container_stats(self, container) -> Dict[str, Any]:
        """Get container resource usage statistics."""
        try:
            stats = container.stats(stream=False)
            
            # Calculate CPU usage percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage / (1024**2), 2),
                'memory_percent': round(memory_percent, 2),
                'network_rx_bytes': stats['networks']['eth0']['rx_bytes'],
                'network_tx_bytes': stats['networks']['eth0']['tx_bytes']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get container stats: {e}")
            return {}
    
    async def _run_health_checks(self):
        """Run comprehensive health checks on deployed services."""
        self.logger.info("Running health checks...")
        
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                health_results = await self.health_checker.run_all_health_checks()
                
                if health_results['overall_health'] == 'healthy':
                    self.logger.info("All health checks passed")
                    return
                
                # Update service health status
                for service, status in health_results['service_health'].items():
                    if service in self.service_statuses:
                        self.service_statuses[service].health_check_status = status['status']
                        self.service_statuses[service].last_health_check = datetime.now()
                
                attempt += 1
                if attempt < max_attempts:
                    self.logger.info(f"Health check attempt {attempt}/{max_attempts} - waiting 10s...")
                    await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                attempt += 1
                await asyncio.sleep(10)
        
        raise RuntimeError("Health checks failed after maximum attempts")
    
    async def _setup_monitoring(self):
        """Setup monitoring and alerting."""
        self.logger.info("Setting up monitoring...")
        
        # Ensure Prometheus and Grafana are running
        monitoring_services = ["truststream-prometheus", "truststream-grafana"]
        
        for service in monitoring_services:
            if service not in self.service_statuses:
                self.logger.warning(f"Monitoring service {service} not found")
                continue
            
            if self.service_statuses[service].status != "running":
                self.logger.warning(f"Monitoring service {service} not running")
        
        # Configure alerting rules
        await self._configure_alerting()
    
    async def _configure_alerting(self):
        """Configure monitoring alerts."""
        # This would typically configure Prometheus alerting rules
        # and Grafana dashboards
        pass
    
    async def _validate_deployment(self):
        """Final deployment validation."""
        self.logger.info("Running final deployment validation...")
        
        # Check all critical services are running
        critical_services = [
            "truststream-app",
            "truststream-postgres", 
            "truststream-neo4j",
            "truststream-redis"
        ]
        
        for service in critical_services:
            if service not in self.service_statuses:
                raise RuntimeError(f"Critical service {service} not found")
            
            if self.service_statuses[service].status != "running":
                raise RuntimeError(f"Critical service {service} not running")
        
        # Test API endpoints
        await self._test_api_endpoints()
        
        self.logger.info("Deployment validation completed")
    
    async def _test_api_endpoints(self):
        """Test critical API endpoints."""
        test_endpoints = [
            "http://localhost:8000/health",
            "http://localhost:8000/api/v1/trust/health"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in test_endpoints:
                try:
                    async with session.get(endpoint, timeout=10) as response:
                        if response.status != 200:
                            raise RuntimeError(f"API endpoint {endpoint} returned {response.status}")
                except Exception as e:
                    raise RuntimeError(f"API endpoint test failed for {endpoint}: {e}")
    
    async def _rollback_deployment(self):
        """Rollback deployment to previous state."""
        if not self.current_deployment.rollback_available:
            self.logger.error("No rollback available")
            return
        
        self.logger.info("Rolling back deployment...")
        
        try:
            # Stop current services
            subprocess.run(["docker-compose", "down"], capture_output=True)
            
            # Restore from backup (simplified)
            # In a real implementation, this would restore databases and configuration
            
            # Restart services
            subprocess.run(["docker-compose", "up", "-d"], capture_output=True)
            
            self.current_deployment.status = "rolled_back"
            self.logger.info("Deployment rollback completed")
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
    
    def get_deployment_status(self) -> Optional[DeploymentStatus]:
        """Get current deployment status."""
        return self.current_deployment
    
    def get_service_statuses(self) -> Dict[str, ServiceStatus]:
        """Get status of all services."""
        return self.service_statuses
    
    async def stop_deployment(self):
        """Stop all deployed services."""
        self.logger.info("Stopping deployment...")
        
        result = subprocess.run(
            ["docker-compose", "down"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to stop services: {result.stderr}")
        
        self.service_statuses.clear()
        self.logger.info("All services stopped")
    
    async def restart_service(self, service_name: str):
        """Restart a specific service."""
        self.logger.info(f"Restarting service: {service_name}")
        
        result = subprocess.run(
            ["docker-compose", "restart", service_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to restart service {service_name}: {result.stderr}")
        
        await self._update_service_statuses()
        self.logger.info(f"Service {service_name} restarted")


# Global deployment manager instance
deployment_manager = DeploymentManager()


def get_deployment_manager() -> DeploymentManager:
    """Get the global deployment manager instance."""
    return deployment_manager