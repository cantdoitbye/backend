# truststream/deployment/health_checks.py

"""
Health Check Manager for TrustStream v4.4

This module provides comprehensive health checking capabilities for all
TrustStream services, databases, and external dependencies.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import aiohttp
import asyncpg
import redis.asyncio as redis
from neo4j import AsyncGraphDatabase
import psutil

from .production_config import ProductionConfig, get_config


@dataclass
class HealthCheckResult:
    """Individual health check result."""
    
    service: str
    status: str  # healthy, unhealthy, degraded, unknown
    response_time_ms: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class SystemHealthStatus:
    """Overall system health status."""
    
    overall_health: str  # healthy, degraded, unhealthy
    timestamp: datetime
    service_health: Dict[str, HealthCheckResult] = field(default_factory=dict)
    system_metrics: Dict[str, float] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)


class HealthCheckManager:
    """Comprehensive health check manager for TrustStream."""
    
    def __init__(self, config: Optional[ProductionConfig] = None):
        """Initialize health check manager."""
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)
        
        # Health check intervals (seconds)
        self.check_intervals = {
            'critical': 30,    # Database, Redis, Core API
            'important': 60,   # AI Providers, Matrix Integration
            'monitoring': 120  # Prometheus, Grafana
        }
        
        # Health thresholds
        self.thresholds = {
            'response_time_ms': 1000,
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'error_rate': 0.05
        }
        
        # Connection pools
        self._postgres_pool: Optional[asyncpg.Pool] = None
        self._redis_client: Optional[redis.Redis] = None
        self._neo4j_driver = None
    
    async def initialize(self):
        """Initialize database connections for health checks."""
        try:
            # Initialize PostgreSQL connection pool
            self._postgres_pool = await asyncpg.create_pool(
                host=self.config.database.postgres_host,
                port=self.config.database.postgres_port,
                user=self.config.database.postgres_user,
                password=self.config.database.postgres_password,
                database=self.config.database.postgres_db,
                min_size=1,
                max_size=3
            )
            
            # Initialize Redis client
            self._redis_client = redis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password,
                db=self.config.redis.db,
                decode_responses=True
            )
            
            # Initialize Neo4j driver
            self._neo4j_driver = AsyncGraphDatabase.driver(
                self.config.database.neo4j_uri,
                auth=(
                    self.config.database.neo4j_user,
                    self.config.database.neo4j_password
                )
            )
            
            self.logger.info("Health check manager initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize health check manager: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup database connections."""
        try:
            if self._postgres_pool:
                await self._postgres_pool.close()
            
            if self._redis_client:
                await self._redis_client.close()
            
            if self._neo4j_driver:
                await self._neo4j_driver.close()
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def run_all_health_checks(self) -> SystemHealthStatus:
        """Run all health checks and return system status."""
        start_time = time.time()
        
        # Initialize if not already done
        if not self._postgres_pool:
            await self.initialize()
        
        health_results = {}
        system_metrics = {}
        alerts = []
        
        # Run all health checks concurrently
        health_check_tasks = [
            self._check_postgres_health(),
            self._check_neo4j_health(),
            self._check_redis_health(),
            self._check_api_health(),
            self._check_ai_providers_health(),
            self._check_matrix_integration_health(),
            self._check_monitoring_health(),
            self._check_system_resources()
        ]
        
        try:
            results = await asyncio.gather(*health_check_tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Health check failed: {result}")
                    continue
                
                if isinstance(result, HealthCheckResult):
                    health_results[result.service] = result
                elif isinstance(result, dict):
                    # System metrics
                    system_metrics.update(result)
        
        except Exception as e:
            self.logger.error(f"Health check execution failed: {e}")
        
        # Determine overall health status
        overall_health = self._determine_overall_health(health_results)
        
        # Generate alerts
        alerts = self._generate_alerts(health_results, system_metrics)
        
        total_time = (time.time() - start_time) * 1000
        system_metrics['health_check_duration_ms'] = total_time
        
        return SystemHealthStatus(
            overall_health=overall_health,
            timestamp=datetime.now(),
            service_health=health_results,
            system_metrics=system_metrics,
            alerts=alerts
        )
    
    async def _check_postgres_health(self) -> HealthCheckResult:
        """Check PostgreSQL database health."""
        start_time = time.time()
        
        try:
            async with self._postgres_pool.acquire() as conn:
                # Test basic connectivity
                await conn.fetchval("SELECT 1")
                
                # Check database size
                db_size = await conn.fetchval("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                
                # Check active connections
                active_connections = await conn.fetchval("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                
                # Check for long-running queries
                long_queries = await conn.fetchval("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND query_start < now() - interval '5 minutes'
                """)
                
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    service="postgres",
                    status="healthy",
                    response_time_ms=response_time,
                    timestamp=datetime.now(),
                    details={
                        "database_size": db_size,
                        "active_connections": active_connections,
                        "long_running_queries": long_queries
                    },
                    metrics={
                        "response_time_ms": response_time,
                        "active_connections": active_connections,
                        "long_running_queries": long_queries
                    }
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="postgres",
                status="unhealthy",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_neo4j_health(self) -> HealthCheckResult:
        """Check Neo4j database health."""
        start_time = time.time()
        
        try:
            async with self._neo4j_driver.session() as session:
                # Test basic connectivity
                result = await session.run("RETURN 1 as test")
                await result.single()
                
                # Check database info
                db_info = await session.run("CALL dbms.components()")
                components = await db_info.data()
                
                # Check node count
                node_count_result = await session.run("MATCH (n) RETURN count(n) as count")
                node_count = (await node_count_result.single())["count"]
                
                # Check relationship count
                rel_count_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = (await rel_count_result.single())["count"]
                
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    service="neo4j",
                    status="healthy",
                    response_time_ms=response_time,
                    timestamp=datetime.now(),
                    details={
                        "components": components,
                        "node_count": node_count,
                        "relationship_count": rel_count
                    },
                    metrics={
                        "response_time_ms": response_time,
                        "node_count": node_count,
                        "relationship_count": rel_count
                    }
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="neo4j",
                status="unhealthy",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_redis_health(self) -> HealthCheckResult:
        """Check Redis health."""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            await self._redis_client.ping()
            
            # Get Redis info
            info = await self._redis_client.info()
            
            # Test set/get operation
            test_key = "health_check_test"
            await self._redis_client.set(test_key, "test_value", ex=60)
            test_value = await self._redis_client.get(test_key)
            await self._redis_client.delete(test_key)
            
            if test_value != "test_value":
                raise Exception("Redis set/get test failed")
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service="redis",
                status="healthy",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory": info.get("used_memory_human"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses")
                },
                metrics={
                    "response_time_ms": response_time,
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_bytes": info.get("used_memory", 0)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="redis",
                status="unhealthy",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_api_health(self) -> HealthCheckResult:
        """Check main API health."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check main health endpoint
                async with session.get(
                    "http://localhost:8000/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status != 200:
                        raise Exception(f"API health check returned status {response.status}")
                    
                    health_data = await response.json()
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    return HealthCheckResult(
                        service="api",
                        status="healthy",
                        response_time_ms=response_time,
                        timestamp=datetime.now(),
                        details=health_data,
                        metrics={
                            "response_time_ms": response_time
                        }
                    )
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="api",
                status="unhealthy",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_ai_providers_health(self) -> HealthCheckResult:
        """Check AI providers health."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check TrustStream AI endpoint
                async with session.get(
                    "http://localhost:8000/api/v1/trust/ai/health",
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status != 200:
                        raise Exception(f"AI providers health check returned status {response.status}")
                    
                    ai_health_data = await response.json()
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    # Determine status based on provider availability
                    healthy_providers = sum(1 for p in ai_health_data.get('providers', {}).values() 
                                          if p.get('status') == 'healthy')
                    total_providers = len(ai_health_data.get('providers', {}))
                    
                    if healthy_providers == 0:
                        status = "unhealthy"
                    elif healthy_providers < total_providers:
                        status = "degraded"
                    else:
                        status = "healthy"
                    
                    return HealthCheckResult(
                        service="ai_providers",
                        status=status,
                        response_time_ms=response_time,
                        timestamp=datetime.now(),
                        details=ai_health_data,
                        metrics={
                            "response_time_ms": response_time,
                            "healthy_providers": healthy_providers,
                            "total_providers": total_providers
                        }
                    )
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="ai_providers",
                status="unhealthy",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_matrix_integration_health(self) -> HealthCheckResult:
        """Check Matrix integration health."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check Matrix integration endpoint
                async with session.get(
                    "http://localhost:8000/api/v1/trust/matrix/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status != 200:
                        raise Exception(f"Matrix integration health check returned status {response.status}")
                    
                    matrix_health_data = await response.json()
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    return HealthCheckResult(
                        service="matrix_integration",
                        status="healthy",
                        response_time_ms=response_time,
                        timestamp=datetime.now(),
                        details=matrix_health_data,
                        metrics={
                            "response_time_ms": response_time
                        }
                    )
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="matrix_integration",
                status="unhealthy",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_monitoring_health(self) -> HealthCheckResult:
        """Check monitoring services health."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check Prometheus
                prometheus_healthy = False
                try:
                    async with session.get(
                        "http://localhost:9090/-/healthy",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        prometheus_healthy = response.status == 200
                except:
                    pass
                
                # Check Grafana
                grafana_healthy = False
                try:
                    async with session.get(
                        "http://localhost:3000/api/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        grafana_healthy = response.status == 200
                except:
                    pass
                
                response_time = (time.time() - start_time) * 1000
                
                # Determine overall monitoring health
                if prometheus_healthy and grafana_healthy:
                    status = "healthy"
                elif prometheus_healthy or grafana_healthy:
                    status = "degraded"
                else:
                    status = "unhealthy"
                
                return HealthCheckResult(
                    service="monitoring",
                    status=status,
                    response_time_ms=response_time,
                    timestamp=datetime.now(),
                    details={
                        "prometheus_healthy": prometheus_healthy,
                        "grafana_healthy": grafana_healthy
                    },
                    metrics={
                        "response_time_ms": response_time
                    }
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="monitoring",
                status="unhealthy",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_system_resources(self) -> Dict[str, float]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                load_1min = load_avg[0]
            except:
                load_1min = 0.0
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "load_1min": load_1min,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system resources: {e}")
            return {}
    
    def _determine_overall_health(self, health_results: Dict[str, HealthCheckResult]) -> str:
        """Determine overall system health based on individual service health."""
        if not health_results:
            return "unknown"
        
        # Critical services that must be healthy
        critical_services = ["postgres", "neo4j", "redis", "api"]
        
        # Check critical services
        critical_unhealthy = []
        critical_degraded = []
        
        for service in critical_services:
            if service in health_results:
                status = health_results[service].status
                if status == "unhealthy":
                    critical_unhealthy.append(service)
                elif status == "degraded":
                    critical_degraded.append(service)
        
        # If any critical service is unhealthy, system is unhealthy
        if critical_unhealthy:
            return "unhealthy"
        
        # Count all service statuses
        total_services = len(health_results)
        healthy_count = sum(1 for r in health_results.values() if r.status == "healthy")
        degraded_count = sum(1 for r in health_results.values() if r.status == "degraded")
        unhealthy_count = sum(1 for r in health_results.values() if r.status == "unhealthy")
        
        # Determine overall status
        if unhealthy_count > 0 or critical_degraded:
            return "degraded"
        elif degraded_count > 0:
            return "degraded"
        elif healthy_count == total_services:
            return "healthy"
        else:
            return "degraded"
    
    def _generate_alerts(self, 
                        health_results: Dict[str, HealthCheckResult],
                        system_metrics: Dict[str, float]) -> List[str]:
        """Generate alerts based on health check results and system metrics."""
        alerts = []
        
        # Service health alerts
        for service, result in health_results.items():
            if result.status == "unhealthy":
                alerts.append(f"CRITICAL: Service {service} is unhealthy - {result.error_message}")
            elif result.status == "degraded":
                alerts.append(f"WARNING: Service {service} is degraded")
            
            # Response time alerts
            if result.response_time_ms > self.thresholds['response_time_ms']:
                alerts.append(f"WARNING: Service {service} response time is high: {result.response_time_ms:.1f}ms")
        
        # System resource alerts
        if system_metrics.get('cpu_percent', 0) > self.thresholds['cpu_percent']:
            alerts.append(f"WARNING: High CPU usage: {system_metrics['cpu_percent']:.1f}%")
        
        if system_metrics.get('memory_percent', 0) > self.thresholds['memory_percent']:
            alerts.append(f"WARNING: High memory usage: {system_metrics['memory_percent']:.1f}%")
        
        if system_metrics.get('disk_percent', 0) > self.thresholds['disk_percent']:
            alerts.append(f"CRITICAL: High disk usage: {system_metrics['disk_percent']:.1f}%")
        
        return alerts
    
    async def run_single_health_check(self, service: str) -> HealthCheckResult:
        """Run health check for a single service."""
        check_methods = {
            'postgres': self._check_postgres_health,
            'neo4j': self._check_neo4j_health,
            'redis': self._check_redis_health,
            'api': self._check_api_health,
            'ai_providers': self._check_ai_providers_health,
            'matrix_integration': self._check_matrix_integration_health,
            'monitoring': self._check_monitoring_health
        }
        
        if service not in check_methods:
            return HealthCheckResult(
                service=service,
                status="unknown",
                response_time_ms=0,
                timestamp=datetime.now(),
                error_message=f"Unknown service: {service}"
            )
        
        # Initialize if not already done
        if not self._postgres_pool:
            await self.initialize()
        
        return await check_methods[service]()


# Global health check manager instance
health_check_manager = HealthCheckManager()


def get_health_check_manager() -> HealthCheckManager:
    """Get the global health check manager instance."""
    return health_check_manager