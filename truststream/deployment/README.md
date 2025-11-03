# TrustStream v4.4 Production Deployment Guide

This guide provides comprehensive instructions for deploying TrustStream v4.4 to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [Monitoring](#monitoring)
6. [Security](#security)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB minimum, SSD recommended
- **Network**: Stable internet connection

### Software Dependencies

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.9+
- **Git**: 2.30+

### Installation Commands

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose python3 python3-pip git

# CentOS/RHEL
sudo yum install -y docker docker-compose python3 python3-pip git

# macOS (with Homebrew)
brew install docker docker-compose python git
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/truststream.git
cd truststream
```

### 2. Set Environment Variables

```bash
# Copy environment template
cp .env.template .env

# Edit environment variables
nano .env
```

Required environment variables:
```bash
TRUSTSTREAM_SECRET_KEY=your-secret-key-here
POSTGRES_PASSWORD=secure-postgres-password
NEO4J_PASSWORD=secure-neo4j-password
OPENAI_API_KEY=your-openai-api-key
CLAUDE_API_KEY=your-claude-api-key  # Optional
MATRIX_HOMESERVER_URL=https://matrix.org  # Optional
MATRIX_ACCESS_TOKEN=your-matrix-token  # Optional
```

### 3. Deploy to Production

```bash
# Basic deployment
python -m truststream.deployment.production_deployment

# Custom deployment
python -m truststream.deployment.production_deployment \
    --environment production \
    --domain your-domain.com \
    --ssl-mode prod
```

### 4. Verify Deployment

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Health check
curl http://localhost/health
```

## Configuration

### Environment Configuration

The deployment system uses several configuration files:

- **`.env`**: Environment variables
- **`config/docker/`**: Docker configurations
- **`config/nginx/`**: Nginx configurations
- **`config/monitoring/`**: Monitoring configurations

### Database Configuration

#### PostgreSQL
- **Host**: `truststream-postgres`
- **Port**: `5432`
- **Database**: `truststream`
- **User**: `truststream`

#### Neo4j
- **Host**: `truststream-neo4j`
- **HTTP Port**: `7474`
- **Bolt Port**: `7687`
- **User**: `neo4j`

#### Redis
- **Host**: `truststream-redis`
- **Port**: `6379`
- **Database**: `0`

### AI Provider Configuration

#### OpenAI
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
```

#### Claude (Optional)
```bash
CLAUDE_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-sonnet-20240229
CLAUDE_MAX_TOKENS=2000
```

## Deployment Options

### Development Deployment

```bash
python -m truststream.deployment.production_deployment \
    --environment development \
    --domain localhost \
    --ssl-mode dev \
    --no-backup
```

### Staging Deployment

```bash
python -m truststream.deployment.production_deployment \
    --environment staging \
    --domain staging.truststream.com \
    --ssl-mode prod
```

### Production Deployment

```bash
python -m truststream.deployment.production_deployment \
    --environment production \
    --domain truststream.com \
    --ssl-mode prod
```

### Custom Deployment Options

- `--no-monitoring`: Disable monitoring stack
- `--no-ssl`: Disable SSL setup
- `--no-backup`: Skip backup creation
- `--no-migrations`: Skip database migrations
- `--no-validation`: Skip deployment validation

## Monitoring

### Prometheus Metrics

Access Prometheus at `http://localhost:9090`

Key metrics:
- `http_requests_total`: HTTP request count
- `http_request_duration_seconds`: Request duration
- `truststream_trust_calculations_total`: Trust calculations
- `truststream_ai_requests_total`: AI provider requests

### Grafana Dashboards

Access Grafana at `http://localhost:3000`
- **Username**: `admin`
- **Password**: `admin123`

Available dashboards:
- TrustStream Overview
- Application Performance
- Database Monitoring
- Trust System Metrics
- AI Provider Usage
- Matrix Integration

### Alerting

Alertmanager is configured at `http://localhost:9093`

Alert channels:
- Email notifications
- Slack integration (configure webhook)
- PagerDuty integration (optional)

## Security

### SSL/TLS Configuration

#### Development (Self-signed)
```bash
# Generate self-signed certificate
bash config/nginx/ssl_setup.sh dev
```

#### Production (Let's Encrypt)
```bash
# Setup Let's Encrypt certificate
bash config/nginx/ssl_setup.sh prod
```

### Security Headers

Nginx is configured with security headers:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Content-Security-Policy`

### Rate Limiting

Configured rate limits:
- API endpoints: 100 requests/second
- Authentication: 5 requests/second
- File uploads: 2 requests/second

### Access Control

- Admin interface restricted to internal networks
- Monitoring endpoints require authentication
- Database access limited to application containers

## Maintenance

### Backup and Restore

#### Create Backup
```bash
# Manual backup
docker-compose exec postgres pg_dump -U truststream truststream > backup.sql
docker-compose exec neo4j cypher-shell -u neo4j -p password "CALL apoc.export.cypher.all('/backup.cypher', {})"

# Automated backup (included in deployment)
python -c "from truststream.deployment.deployment_manager import DeploymentManager; DeploymentManager().backup_deployment()"
```

#### Restore Backup
```bash
# PostgreSQL restore
docker-compose exec -T postgres psql -U truststream truststream < backup.sql

# Neo4j restore
docker-compose exec neo4j cypher-shell -u neo4j -p password -f /backup.cypher
```

### Updates and Migrations

#### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and redeploy
docker-compose build
docker-compose up -d

# Run migrations
python -c "from truststream.deployment.migration_runner import MigrationRunner; MigrationRunner().run_all_migrations()"
```

#### Database Migrations
```bash
# Run PostgreSQL migrations
python manage.py migrate

# Run Neo4j migrations
python -c "from truststream.neo4j_migrations import Neo4jMigrationManager; Neo4jMigrationManager().run_migrations()"
```

### Scaling

#### Horizontal Scaling
```bash
# Scale application instances
docker-compose up --scale app=3

# Scale with load balancer
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

#### Vertical Scaling
```yaml
# Update docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### Log Management

#### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app

# With timestamps
docker-compose logs -f -t app
```

#### Log Rotation
```bash
# Configure log rotation in docker-compose.yml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs service-name

# Restart service
docker-compose restart service-name
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready -U truststream
docker-compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1"
docker-compose exec redis redis-cli ping

# Reset database connections
docker-compose restart app
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in /etc/ssl/certs/truststream.crt -text -noout

# Regenerate certificate
bash config/nginx/ssl_setup.sh dev  # or prod
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services to free memory
docker-compose restart

# Scale down if necessary
docker-compose up --scale app=1
```

### Health Checks

#### Manual Health Check
```bash
# Application health
curl http://localhost/health

# Database health
python -c "from truststream.deployment.health_checks import HealthCheckManager; print(HealthCheckManager().check_system_health())"
```

#### Automated Health Monitoring
```bash
# Enable health check monitoring
docker-compose up -d healthcheck-monitor

# View health check logs
docker-compose logs healthcheck-monitor
```

### Performance Optimization

#### Database Optimization
```sql
-- PostgreSQL optimization
ANALYZE;
REINDEX DATABASE truststream;

-- Neo4j optimization
CALL db.indexes();
CALL apoc.cypher.runTimeboxed("MATCH (n) RETURN count(n)", {}, 30000);
```

#### Cache Optimization
```bash
# Redis cache statistics
docker-compose exec redis redis-cli info memory

# Clear cache if needed
docker-compose exec redis redis-cli flushall
```

### Support and Documentation

- **GitHub Issues**: https://github.com/your-org/truststream/issues
- **Documentation**: https://docs.truststream.com
- **Community**: https://community.truststream.com
- **Email Support**: support@truststream.com

### Emergency Procedures

#### Rollback Deployment
```bash
# Stop current deployment
docker-compose down

# Restore from backup
# (Follow backup restore procedures above)

# Start previous version
git checkout previous-tag
docker-compose up -d
```

#### Emergency Shutdown
```bash
# Graceful shutdown
docker-compose down

# Force shutdown
docker-compose kill
```

#### Data Recovery
```bash
# Check data integrity
python -c "from truststream.deployment.migration_runner import MigrationRunner; MigrationRunner().validate_migrations()"

# Repair data if needed
python manage.py check --deploy
```

---

For additional support or questions, please refer to the TrustStream documentation or contact the development team.