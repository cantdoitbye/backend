# truststream/deployment/production_config.py

"""
Production Configuration for TrustStream v4.4

This module contains production-ready configuration settings for deploying
TrustStream with optimal security, performance, and monitoring capabilities.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import timedelta
import logging


@dataclass
class DatabaseConfig:
    """Database configuration for production deployment."""
    
    # PostgreSQL Configuration
    postgres_host: str = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port: int = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_db: str = os.getenv('POSTGRES_DB', 'truststream_prod')
    postgres_user: str = os.getenv('POSTGRES_USER', 'truststream')
    postgres_password: str = os.getenv('POSTGRES_PASSWORD', '')
    postgres_ssl_mode: str = os.getenv('POSTGRES_SSL_MODE', 'require')
    
    # Neo4j Configuration
    neo4j_uri: str = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user: str = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password: str = os.getenv('NEO4J_PASSWORD', '')
    neo4j_database: str = os.getenv('NEO4J_DATABASE', 'truststream')
    neo4j_encrypted: bool = os.getenv('NEO4J_ENCRYPTED', 'true').lower() == 'true'
    
    # Connection Pool Settings
    postgres_max_connections: int = int(os.getenv('POSTGRES_MAX_CONNECTIONS', '100'))
    postgres_min_connections: int = int(os.getenv('POSTGRES_MIN_CONNECTIONS', '10'))
    neo4j_max_connection_pool_size: int = int(os.getenv('NEO4J_MAX_POOL_SIZE', '50'))
    
    # Performance Settings
    postgres_connection_timeout: int = int(os.getenv('POSTGRES_TIMEOUT', '30'))
    neo4j_connection_timeout: int = int(os.getenv('NEO4J_TIMEOUT', '30'))
    query_timeout: int = int(os.getenv('QUERY_TIMEOUT', '60'))
    
    def get_postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            f"?sslmode={self.postgres_ssl_mode}"
        )
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j connection configuration."""
        return {
            'uri': self.neo4j_uri,
            'auth': (self.neo4j_user, self.neo4j_password),
            'database': self.neo4j_database,
            'encrypted': self.neo4j_encrypted,
            'max_connection_pool_size': self.neo4j_max_connection_pool_size,
            'connection_timeout': self.neo4j_connection_timeout
        }


@dataclass
class RedisConfig:
    """Redis configuration for caching and session management."""
    
    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    password: str = os.getenv('REDIS_PASSWORD', '')
    db: int = int(os.getenv('REDIS_DB', '0'))
    ssl: bool = os.getenv('REDIS_SSL', 'false').lower() == 'true'
    
    # Connection Pool Settings
    max_connections: int = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
    connection_timeout: int = int(os.getenv('REDIS_TIMEOUT', '5'))
    
    # Cache Settings
    default_ttl: int = int(os.getenv('REDIS_DEFAULT_TTL', '3600'))  # 1 hour
    trust_score_ttl: int = int(os.getenv('REDIS_TRUST_SCORE_TTL', '1800'))  # 30 minutes
    session_ttl: int = int(os.getenv('REDIS_SESSION_TTL', '28800'))  # 8 hours
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        protocol = 'rediss' if self.ssl else 'redis'
        auth_part = f":{self.password}@" if self.password else ""
        return f"{protocol}://{auth_part}{self.host}:{self.port}/{self.db}"


@dataclass
class AIProviderConfig:
    """AI provider configuration for production."""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    openai_model: str = os.getenv('OPENAI_MODEL', 'gpt-4')
    openai_max_tokens: int = int(os.getenv('OPENAI_MAX_TOKENS', '2048'))
    openai_temperature: float = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    # Claude Configuration
    claude_api_key: str = os.getenv('CLAUDE_API_KEY', '')
    claude_model: str = os.getenv('CLAUDE_MODEL', 'claude-3-sonnet-20240229')
    claude_max_tokens: int = int(os.getenv('CLAUDE_MAX_TOKENS', '2048'))
    
    # Rate Limiting
    requests_per_minute: int = int(os.getenv('AI_REQUESTS_PER_MINUTE', '100'))
    requests_per_hour: int = int(os.getenv('AI_REQUESTS_PER_HOUR', '1000'))
    
    # Fallback Configuration
    enable_fallback: bool = os.getenv('AI_ENABLE_FALLBACK', 'true').lower() == 'true'
    fallback_timeout: int = int(os.getenv('AI_FALLBACK_TIMEOUT', '10'))
    
    # Cost Optimization
    cost_optimization_enabled: bool = os.getenv('AI_COST_OPTIMIZATION', 'true').lower() == 'true'
    max_daily_cost: float = float(os.getenv('AI_MAX_DAILY_COST', '100.0'))


@dataclass
class SecurityConfig:
    """Security configuration for production deployment."""
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv('JWT_SECRET_KEY', '')
    jwt_algorithm: str = os.getenv('JWT_ALGORITHM', 'HS256')
    jwt_expiration_hours: int = int(os.getenv('JWT_EXPIRATION_HOURS', '8'))
    
    # Encryption Configuration
    encryption_key: str = os.getenv('ENCRYPTION_KEY', '')
    password_salt: str = os.getenv('PASSWORD_SALT', '')
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = int(os.getenv('RATE_LIMIT_RPM', '60'))
    rate_limit_requests_per_hour: int = int(os.getenv('RATE_LIMIT_RPH', '1000'))
    
    # CORS Configuration
    cors_allowed_origins: List[str] = field(default_factory=lambda: 
        os.getenv('CORS_ALLOWED_ORIGINS', 'https://truststream.app').split(','))
    cors_allow_credentials: bool = os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true'
    
    # Security Headers
    enable_security_headers: bool = True
    hsts_max_age: int = int(os.getenv('HSTS_MAX_AGE', '31536000'))  # 1 year
    
    # Content Security Policy
    csp_policy: str = os.getenv('CSP_POLICY', 
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
    
    # Session Security
    session_cookie_secure: bool = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = os.getenv('SESSION_COOKIE_SAMESITE', 'Strict')


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    
    # Logging Configuration
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_format: str = os.getenv('LOG_FORMAT', 'json')
    log_file_path: str = os.getenv('LOG_FILE_PATH', '/var/log/truststream/app.log')
    
    # Metrics Configuration
    enable_metrics: bool = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    metrics_port: int = int(os.getenv('METRICS_PORT', '9090'))
    metrics_path: str = os.getenv('METRICS_PATH', '/metrics')
    
    # Health Check Configuration
    health_check_interval: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
    health_check_timeout: int = int(os.getenv('HEALTH_CHECK_TIMEOUT', '10'))
    
    # Performance Monitoring
    enable_performance_monitoring: bool = os.getenv('ENABLE_PERF_MONITORING', 'true').lower() == 'true'
    performance_sample_rate: float = float(os.getenv('PERF_SAMPLE_RATE', '0.1'))
    
    # Error Tracking
    sentry_dsn: str = os.getenv('SENTRY_DSN', '')
    sentry_environment: str = os.getenv('SENTRY_ENVIRONMENT', 'production')
    sentry_sample_rate: float = float(os.getenv('SENTRY_SAMPLE_RATE', '1.0'))
    
    # Alerting Configuration
    enable_alerting: bool = os.getenv('ENABLE_ALERTING', 'true').lower() == 'true'
    alert_webhook_url: str = os.getenv('ALERT_WEBHOOK_URL', '')
    alert_email_recipients: List[str] = field(default_factory=lambda:
        os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',') if os.getenv('ALERT_EMAIL_RECIPIENTS') else [])


@dataclass
class PerformanceConfig:
    """Performance optimization configuration."""
    
    # Worker Configuration
    worker_processes: int = int(os.getenv('WORKER_PROCESSES', '4'))
    worker_threads: int = int(os.getenv('WORKER_THREADS', '8'))
    worker_timeout: int = int(os.getenv('WORKER_TIMEOUT', '30'))
    
    # Async Configuration
    async_pool_size: int = int(os.getenv('ASYNC_POOL_SIZE', '100'))
    async_timeout: int = int(os.getenv('ASYNC_TIMEOUT', '60'))
    
    # Batch Processing
    batch_size: int = int(os.getenv('BATCH_SIZE', '100'))
    batch_timeout: int = int(os.getenv('BATCH_TIMEOUT', '30'))
    
    # Memory Management
    max_memory_usage_mb: int = int(os.getenv('MAX_MEMORY_USAGE_MB', '2048'))
    gc_threshold: int = int(os.getenv('GC_THRESHOLD', '1000'))
    
    # Request Processing
    max_request_size_mb: int = int(os.getenv('MAX_REQUEST_SIZE_MB', '10'))
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '30'))


@dataclass
class ProductionConfig:
    """Main production configuration class."""
    
    # Environment
    environment: str = os.getenv('ENVIRONMENT', 'production')
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    testing: bool = os.getenv('TESTING', 'false').lower() == 'true'
    
    # Application Configuration
    app_name: str = os.getenv('APP_NAME', 'TrustStream')
    app_version: str = os.getenv('APP_VERSION', '4.4.0')
    app_host: str = os.getenv('APP_HOST', '0.0.0.0')
    app_port: int = int(os.getenv('APP_PORT', '8000'))
    
    # Component Configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    ai_providers: AIProviderConfig = field(default_factory=AIProviderConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Feature Flags
    enable_trust_pyramid: bool = os.getenv('ENABLE_TRUST_PYRAMID', 'true').lower() == 'true'
    enable_ai_providers: bool = os.getenv('ENABLE_AI_PROVIDERS', 'true').lower() == 'true'
    enable_agent_ecosystem: bool = os.getenv('ENABLE_AGENT_ECOSYSTEM', 'true').lower() == 'true'
    enable_matrix_integration: bool = os.getenv('ENABLE_MATRIX_INTEGRATION', 'true').lower() == 'true'
    enable_admin_interface: bool = os.getenv('ENABLE_ADMIN_INTERFACE', 'true').lower() == 'true'
    enable_explainability: bool = os.getenv('ENABLE_EXPLAINABILITY', 'true').lower() == 'true'
    
    # Compliance Configuration
    gdpr_compliance: bool = os.getenv('GDPR_COMPLIANCE', 'true').lower() == 'true'
    ccpa_compliance: bool = os.getenv('CCPA_COMPLIANCE', 'true').lower() == 'true'
    data_retention_days: int = int(os.getenv('DATA_RETENTION_DAYS', '365'))
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_configuration()
        self._setup_logging()
    
    def _validate_configuration(self):
        """Validate critical configuration settings."""
        errors = []
        
        # Validate required secrets
        if not self.security.jwt_secret_key:
            errors.append("JWT_SECRET_KEY is required")
        
        if not self.security.encryption_key:
            errors.append("ENCRYPTION_KEY is required")
        
        if not self.database.postgres_password:
            errors.append("POSTGRES_PASSWORD is required")
        
        if not self.database.neo4j_password:
            errors.append("NEO4J_PASSWORD is required")
        
        # Validate AI provider keys
        if self.enable_ai_providers:
            if not self.ai_providers.openai_api_key and not self.ai_providers.claude_api_key:
                errors.append("At least one AI provider API key is required")
        
        # Validate monitoring configuration
        if self.monitoring.enable_alerting and not self.monitoring.alert_webhook_url:
            errors.append("ALERT_WEBHOOK_URL is required when alerting is enabled")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.monitoring.log_level.upper())
        
        if self.monitoring.log_format == 'json':
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.monitoring.log_file_path)
            ]
        )
    
    def get_database_urls(self) -> Dict[str, str]:
        """Get database connection URLs."""
        return {
            'postgres': self.database.get_postgres_url(),
            'redis': self.redis.get_redis_url()
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flag configuration."""
        return {
            'trust_pyramid': self.enable_trust_pyramid,
            'ai_providers': self.enable_ai_providers,
            'agent_ecosystem': self.enable_agent_ecosystem,
            'matrix_integration': self.enable_matrix_integration,
            'admin_interface': self.enable_admin_interface,
            'explainability': self.enable_explainability
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == 'production'
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration."""
        return {
            'allow_origins': self.security.cors_allowed_origins,
            'allow_credentials': self.security.cors_allow_credentials,
            'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['*']
        }


# Global production configuration instance
production_config = ProductionConfig()


def get_config() -> ProductionConfig:
    """Get the global production configuration instance."""
    return production_config


def reload_config() -> ProductionConfig:
    """Reload configuration from environment variables."""
    global production_config
    production_config = ProductionConfig()
    return production_config