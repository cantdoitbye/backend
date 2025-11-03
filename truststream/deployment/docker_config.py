# truststream/deployment/docker_config.py

"""
Docker Configuration for TrustStream v4.4

This module provides Docker containerization configuration for deploying
TrustStream with proper service orchestration, networking, and scaling.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import yaml
import json


@dataclass
class DockerServiceConfig:
    """Configuration for individual Docker services."""
    
    image: str
    container_name: str
    ports: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    restart_policy: str = "unless-stopped"
    healthcheck: Optional[Dict[str, Any]] = None
    deploy: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert service config to dictionary for docker-compose."""
        config = {
            'image': self.image,
            'container_name': self.container_name,
            'restart': self.restart_policy
        }
        
        if self.ports:
            config['ports'] = self.ports
        
        if self.environment:
            config['environment'] = self.environment
        
        if self.volumes:
            config['volumes'] = self.volumes
        
        if self.depends_on:
            config['depends_on'] = self.depends_on
        
        if self.networks:
            config['networks'] = self.networks
        
        if self.healthcheck:
            config['healthcheck'] = self.healthcheck
        
        if self.deploy:
            config['deploy'] = self.deploy
        
        return config


@dataclass
class DockerNetworkConfig:
    """Configuration for Docker networks."""
    
    name: str
    driver: str = "bridge"
    external: bool = False
    attachable: bool = True
    ipam: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert network config to dictionary."""
        config = {
            'driver': self.driver,
            'attachable': self.attachable
        }
        
        if self.external:
            config['external'] = True
        
        if self.ipam:
            config['ipam'] = self.ipam
        
        return config


@dataclass
class DockerVolumeConfig:
    """Configuration for Docker volumes."""
    
    name: str
    driver: str = "local"
    external: bool = False
    driver_opts: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert volume config to dictionary."""
        config = {
            'driver': self.driver
        }
        
        if self.external:
            config['external'] = True
        
        if self.driver_opts:
            config['driver_opts'] = self.driver_opts
        
        return config


class DockerConfig:
    """Main Docker configuration class for TrustStream deployment."""
    
    def __init__(self):
        """Initialize Docker configuration."""
        self.version = "3.8"
        self.project_name = "truststream"
        
        # Initialize services
        self.services = self._create_services()
        self.networks = self._create_networks()
        self.volumes = self._create_volumes()
    
    def _create_services(self) -> Dict[str, DockerServiceConfig]:
        """Create Docker service configurations."""
        services = {}
        
        # TrustStream Application Service
        services['truststream-app'] = DockerServiceConfig(
            image="truststream/app:4.4.0",
            container_name="truststream-app",
            ports=["8000:8000"],
            environment={
                'ENVIRONMENT': 'production',
                'POSTGRES_HOST': 'truststream-postgres',
                'NEO4J_URI': 'bolt://truststream-neo4j:7687',
                'REDIS_HOST': 'truststream-redis',
                'LOG_LEVEL': 'INFO'
            },
            volumes=[
                "./logs:/var/log/truststream",
                "./config:/app/config:ro"
            ],
            depends_on=[
                'truststream-postgres',
                'truststream-neo4j',
                'truststream-redis'
            ],
            networks=['truststream-network'],
            healthcheck={
                'test': ['CMD', 'curl', '-f', 'http://localhost:8000/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3,
                'start_period': '40s'
            },
            deploy={
                'replicas': 2,
                'resources': {
                    'limits': {
                        'cpus': '1.0',
                        'memory': '2G'
                    },
                    'reservations': {
                        'cpus': '0.5',
                        'memory': '1G'
                    }
                },
                'restart_policy': {
                    'condition': 'on-failure',
                    'delay': '5s',
                    'max_attempts': 3
                }
            }
        )
        
        # PostgreSQL Database Service
        services['truststream-postgres'] = DockerServiceConfig(
            image="postgres:15-alpine",
            container_name="truststream-postgres",
            ports=["5432:5432"],
            environment={
                'POSTGRES_DB': 'truststream_prod',
                'POSTGRES_USER': 'truststream',
                'POSTGRES_PASSWORD': '${POSTGRES_PASSWORD}',
                'POSTGRES_INITDB_ARGS': '--auth-host=scram-sha-256',
                'PGDATA': '/var/lib/postgresql/data/pgdata'
            },
            volumes=[
                "truststream-postgres-data:/var/lib/postgresql/data",
                "./init-scripts/postgres:/docker-entrypoint-initdb.d:ro"
            ],
            networks=['truststream-network'],
            healthcheck={
                'test': ['CMD-SHELL', 'pg_isready -U truststream -d truststream_prod'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            },
            deploy={
                'resources': {
                    'limits': {
                        'cpus': '2.0',
                        'memory': '4G'
                    },
                    'reservations': {
                        'cpus': '1.0',
                        'memory': '2G'
                    }
                }
            }
        )
        
        # Neo4j Graph Database Service
        services['truststream-neo4j'] = DockerServiceConfig(
            image="neo4j:5.15-community",
            container_name="truststream-neo4j",
            ports=["7474:7474", "7687:7687"],
            environment={
                'NEO4J_AUTH': 'neo4j/${NEO4J_PASSWORD}',
                'NEO4J_dbms_default__database': 'truststream',
                'NEO4J_dbms_security_procedures_unrestricted': 'gds.*,apoc.*',
                'NEO4J_dbms_security_procedures_allowlist': 'gds.*,apoc.*',
                'NEO4J_dbms_memory_heap_initial__size': '1G',
                'NEO4J_dbms_memory_heap_max__size': '2G',
                'NEO4J_dbms_memory_pagecache_size': '1G'
            },
            volumes=[
                "truststream-neo4j-data:/data",
                "truststream-neo4j-logs:/logs",
                "./init-scripts/neo4j:/var/lib/neo4j/import:ro"
            ],
            networks=['truststream-network'],
            healthcheck={
                'test': ['CMD', 'cypher-shell', '-u', 'neo4j', '-p', '${NEO4J_PASSWORD}', 'RETURN 1'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 5,
                'start_period': '60s'
            },
            deploy={
                'resources': {
                    'limits': {
                        'cpus': '2.0',
                        'memory': '4G'
                    },
                    'reservations': {
                        'cpus': '1.0',
                        'memory': '2G'
                    }
                }
            }
        )
        
        # Redis Cache Service
        services['truststream-redis'] = DockerServiceConfig(
            image="redis:7-alpine",
            container_name="truststream-redis",
            ports=["6379:6379"],
            environment={
                'REDIS_PASSWORD': '${REDIS_PASSWORD}'
            },
            volumes=[
                "truststream-redis-data:/data",
                "./config/redis.conf:/usr/local/etc/redis/redis.conf:ro"
            ],
            networks=['truststream-network'],
            healthcheck={
                'test': ['CMD', 'redis-cli', '--raw', 'incr', 'ping'],
                'interval': '10s',
                'timeout': '3s',
                'retries': 5
            },
            deploy={
                'resources': {
                    'limits': {
                        'cpus': '0.5',
                        'memory': '1G'
                    },
                    'reservations': {
                        'cpus': '0.25',
                        'memory': '512M'
                    }
                }
            }
        )
        
        # Nginx Load Balancer Service
        services['truststream-nginx'] = DockerServiceConfig(
            image="nginx:alpine",
            container_name="truststream-nginx",
            ports=["80:80", "443:443"],
            volumes=[
                "./config/nginx.conf:/etc/nginx/nginx.conf:ro",
                "./ssl:/etc/nginx/ssl:ro",
                "./logs/nginx:/var/log/nginx"
            ],
            depends_on=['truststream-app'],
            networks=['truststream-network'],
            healthcheck={
                'test': ['CMD', 'wget', '--quiet', '--tries=1', '--spider', 'http://localhost/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            },
            deploy={
                'resources': {
                    'limits': {
                        'cpus': '0.5',
                        'memory': '512M'
                    },
                    'reservations': {
                        'cpus': '0.25',
                        'memory': '256M'
                    }
                }
            }
        )
        
        # Prometheus Monitoring Service
        services['truststream-prometheus'] = DockerServiceConfig(
            image="prom/prometheus:latest",
            container_name="truststream-prometheus",
            ports=["9090:9090"],
            volumes=[
                "./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro",
                "truststream-prometheus-data:/prometheus"
            ],
            networks=['truststream-network'],
            healthcheck={
                'test': ['CMD', 'wget', '--quiet', '--tries=1', '--spider', 'http://localhost:9090/-/healthy'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        )
        
        # Grafana Dashboard Service
        services['truststream-grafana'] = DockerServiceConfig(
            image="grafana/grafana:latest",
            container_name="truststream-grafana",
            ports=["3000:3000"],
            environment={
                'GF_SECURITY_ADMIN_PASSWORD': '${GRAFANA_PASSWORD}',
                'GF_USERS_ALLOW_SIGN_UP': 'false'
            },
            volumes=[
                "truststream-grafana-data:/var/lib/grafana",
                "./config/grafana:/etc/grafana/provisioning:ro"
            ],
            depends_on=['truststream-prometheus'],
            networks=['truststream-network'],
            healthcheck={
                'test': ['CMD-SHELL', 'wget --quiet --tries=1 --spider http://localhost:3000/api/health || exit 1'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        )
        
        return services
    
    def _create_networks(self) -> Dict[str, DockerNetworkConfig]:
        """Create Docker network configurations."""
        return {
            'truststream-network': DockerNetworkConfig(
                name='truststream-network',
                driver='bridge',
                ipam={
                    'config': [
                        {
                            'subnet': '172.20.0.0/16',
                            'gateway': '172.20.0.1'
                        }
                    ]
                }
            )
        }
    
    def _create_volumes(self) -> Dict[str, DockerVolumeConfig]:
        """Create Docker volume configurations."""
        return {
            'truststream-postgres-data': DockerVolumeConfig(
                name='truststream-postgres-data'
            ),
            'truststream-neo4j-data': DockerVolumeConfig(
                name='truststream-neo4j-data'
            ),
            'truststream-neo4j-logs': DockerVolumeConfig(
                name='truststream-neo4j-logs'
            ),
            'truststream-redis-data': DockerVolumeConfig(
                name='truststream-redis-data'
            ),
            'truststream-prometheus-data': DockerVolumeConfig(
                name='truststream-prometheus-data'
            ),
            'truststream-grafana-data': DockerVolumeConfig(
                name='truststream-grafana-data'
            )
        }
    
    def generate_docker_compose(self) -> Dict[str, Any]:
        """Generate docker-compose.yml configuration."""
        compose_config = {
            'version': self.version,
            'services': {},
            'networks': {},
            'volumes': {}
        }
        
        # Add services
        for name, service in self.services.items():
            compose_config['services'][name] = service.to_dict()
        
        # Add Nginx service
        compose_config['services']['nginx'] = {
            'image': 'nginx:alpine',
            'container_name': 'truststream-nginx',
            'ports': ['80:80', '443:443', '8080:8080'],
            'volumes': [
                './config/nginx/nginx.conf:/etc/nginx/nginx.conf',
                './config/nginx/truststream.conf:/etc/nginx/conf.d/truststream.conf',
                './config/nginx/monitoring.conf:/etc/nginx/conf.d/monitoring.conf',
                './static:/var/www/truststream/static',
                './media:/var/www/truststream/media',
                './ssl:/etc/ssl/certs'
            ],
            'depends_on': ['truststream-app'],
            'networks': ['truststream-network'],
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'nginx', '-t'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        }
        
        # Add networks
        for name, network in self.networks.items():
            compose_config['networks'][name] = network.to_dict()
        
        # Add volumes
        for name, volume in self.volumes.items():
            compose_config['volumes'][name] = volume.to_dict()
        
        return compose_config
    
    def save_docker_compose(self, file_path: str = "docker-compose.yml"):
        """Save docker-compose configuration to file."""
        compose_config = self.generate_docker_compose()
        
        with open(file_path, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, indent=2)
    
    def generate_dockerfile(self) -> str:
        """Generate Dockerfile for TrustStream application."""
        dockerfile_content = """
# TrustStream v4.4 Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    git \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \\
    chown -R appuser:appuser /app
USER appuser

# Create necessary directories
RUN mkdir -p /var/log/truststream && \\
    mkdir -p /app/static && \\
    mkdir -p /app/media

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "30", "truststream.wsgi:application"]
"""
        return dockerfile_content.strip()
    
    def save_dockerfile(self, file_path: str = "Dockerfile"):
        """Save Dockerfile to file."""
        dockerfile_content = self.generate_dockerfile()
        
        with open(file_path, 'w') as f:
            f.write(dockerfile_content)
    
    def generate_docker_ignore(self) -> str:
        """Generate .dockerignore file content."""
        dockerignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Logs
*.log
logs/

# Environment files
.env
.env.local
.env.production

# Test files
.pytest_cache/
.coverage
htmlcov/

# Documentation
docs/
*.md

# Temporary files
tmp/
temp/
"""
        return dockerignore_content.strip()
    
    def save_docker_ignore(self, file_path: str = ".dockerignore"):
        """Save .dockerignore to file."""
        dockerignore_content = self.generate_docker_ignore()
        
        with open(file_path, 'w') as f:
            f.write(dockerignore_content)
    
    def generate_env_template(self) -> str:
        """Generate environment variables template."""
        env_template = """
# TrustStream v4.4 Environment Configuration Template

# Application Configuration
ENVIRONMENT=production
DEBUG=false
APP_NAME=TrustStream
APP_VERSION=4.4.0
APP_HOST=0.0.0.0
APP_PORT=8000

# Database Configuration
POSTGRES_HOST=truststream-postgres
POSTGRES_PORT=5432
POSTGRES_DB=truststream_prod
POSTGRES_USER=truststream
POSTGRES_PASSWORD=your_secure_postgres_password_here
POSTGRES_SSL_MODE=require

# Neo4j Configuration
NEO4J_URI=bolt://truststream-neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_neo4j_password_here
NEO4J_DATABASE=truststream

# Redis Configuration
REDIS_HOST=truststream-redis
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_redis_password_here
REDIS_DB=0

# Security Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
PASSWORD_SALT=your_password_salt_here

# AI Provider Configuration
OPENAI_API_KEY=your_openai_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here

# Monitoring Configuration
SENTRY_DSN=your_sentry_dsn_here
GRAFANA_PASSWORD=your_grafana_password_here

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://truststream.app,https://www.truststream.app

# Feature Flags
ENABLE_TRUST_PYRAMID=true
ENABLE_AI_PROVIDERS=true
ENABLE_AGENT_ECOSYSTEM=true
ENABLE_MATRIX_INTEGRATION=true
ENABLE_ADMIN_INTERFACE=true
ENABLE_EXPLAINABILITY=true

# Compliance Configuration
GDPR_COMPLIANCE=true
CCPA_COMPLIANCE=true
DATA_RETENTION_DAYS=365
"""
        return env_template.strip()
    
    def save_env_template(self, file_path: str = ".env.template"):
        """Save environment template to file."""
        env_template = self.generate_env_template()
        
        with open(file_path, 'w') as f:
            f.write(env_template)


# Global Docker configuration instance
docker_config = DockerConfig()


def get_docker_config() -> DockerConfig:
    """Get the global Docker configuration instance."""
    return docker_config