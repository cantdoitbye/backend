# truststream/deployment/nginx_config.py

"""
Nginx Configuration Generator for TrustStream v4.4

This module generates Nginx configuration files for load balancing,
SSL termination, reverse proxy, and static file serving.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from .production_config import ProductionConfig, get_config


@dataclass
class UpstreamServer:
    """Upstream server configuration."""
    
    host: str
    port: int
    weight: int = 1
    max_fails: int = 3
    fail_timeout: str = "30s"
    backup: bool = False


@dataclass
class SSLConfig:
    """SSL configuration."""
    
    certificate_path: str
    private_key_path: str
    protocols: List[str] = field(default_factory=lambda: ["TLSv1.2", "TLSv1.3"])
    ciphers: str = "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
    prefer_server_ciphers: bool = True
    session_cache: str = "shared:SSL:10m"
    session_timeout: str = "10m"
    stapling: bool = True
    stapling_verify: bool = True


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    
    zone_name: str
    zone_size: str = "10m"
    rate: str = "10r/s"
    burst: int = 20
    nodelay: bool = True


@dataclass
class CacheConfig:
    """Caching configuration."""
    
    static_cache_time: str = "1y"
    api_cache_time: str = "5m"
    no_cache_paths: List[str] = field(default_factory=lambda: ["/api/v1/trust/admin", "/health"])


class NginxConfigGenerator:
    """Nginx configuration generator for TrustStream."""
    
    def __init__(self, config: Optional[ProductionConfig] = None):
        """Initialize Nginx configuration generator."""
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.worker_processes = "auto"
        self.worker_connections = 1024
        self.keepalive_timeout = 65
        self.client_max_body_size = "100M"
        
        # Upstream servers
        self.upstream_servers = [
            UpstreamServer(host="truststream-app", port=8000, weight=1),
            # Add more app servers for load balancing
        ]
        
        # SSL configuration
        self.ssl_config = SSLConfig(
            certificate_path="/etc/ssl/certs/truststream.crt",
            private_key_path="/etc/ssl/private/truststream.key"
        )
        
        # Rate limiting
        self.rate_limits = [
            RateLimitConfig(zone_name="api", rate="100r/s", burst=200),
            RateLimitConfig(zone_name="auth", rate="5r/s", burst=10),
            RateLimitConfig(zone_name="upload", rate="2r/s", burst=5)
        ]
        
        # Caching
        self.cache_config = CacheConfig()
    
    def generate_main_config(self) -> str:
        """Generate main nginx.conf configuration."""
        config = f"""# TrustStream v4.4 Nginx Configuration
# Generated automatically - do not edit manually

user nginx;
worker_processes {self.worker_processes};
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {{
    worker_connections {self.worker_connections};
    use epoll;
    multi_accept on;
}}

http {{
    # Basic settings
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    access_log /var/log/nginx/access.log main;
    
    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout {self.keepalive_timeout};
    types_hash_max_size 2048;
    client_max_body_size {self.client_max_body_size};
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https:;" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Rate limiting zones
{self._generate_rate_limit_zones()}
    
    # Upstream servers
{self._generate_upstream_config()}
    
    # SSL configuration
{self._generate_ssl_config()}
    
    # Cache configuration
{self._generate_cache_config()}
    
    # Include server configurations
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}}
"""
        return config
    
    def _generate_rate_limit_zones(self) -> str:
        """Generate rate limiting zones."""
        zones = []
        for rate_limit in self.rate_limits:
            zones.append(f"    limit_req_zone $binary_remote_addr zone={rate_limit.zone_name}:{rate_limit.zone_size} rate={rate_limit.rate};")
        return "\n".join(zones)
    
    def _generate_upstream_config(self) -> str:
        """Generate upstream server configuration."""
        config = "    upstream truststream_backend {\n"
        config += "        least_conn;\n"
        
        for server in self.upstream_servers:
            server_line = f"        server {server.host}:{server.port}"
            if server.weight != 1:
                server_line += f" weight={server.weight}"
            if server.max_fails != 3:
                server_line += f" max_fails={server.max_fails}"
            if server.fail_timeout != "30s":
                server_line += f" fail_timeout={server.fail_timeout}"
            if server.backup:
                server_line += " backup"
            server_line += ";\n"
            config += server_line
        
        config += "        keepalive 32;\n"
        config += "    }\n"
        
        return config
    
    def _generate_ssl_config(self) -> str:
        """Generate SSL configuration."""
        config = f"""    # SSL configuration
    ssl_protocols {' '.join(self.ssl_config.protocols)};
    ssl_ciphers {self.ssl_config.ciphers};
    ssl_prefer_server_ciphers {'on' if self.ssl_config.prefer_server_ciphers else 'off'};
    ssl_session_cache {self.ssl_config.session_cache};
    ssl_session_timeout {self.ssl_config.session_timeout};
    ssl_session_tickets off;
    
    # OCSP stapling
    ssl_stapling {'on' if self.ssl_config.stapling else 'off'};
    ssl_stapling_verify {'on' if self.ssl_config.stapling_verify else 'off'};
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
"""
        return config
    
    def _generate_cache_config(self) -> str:
        """Generate cache configuration."""
        config = """    # Cache configuration
    proxy_cache_path /var/cache/nginx/truststream levels=1:2 keys_zone=truststream_cache:10m max_size=1g inactive=60m use_temp_path=off;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    proxy_cache_valid 200 302 10m;
    proxy_cache_valid 404 1m;
"""
        return config
    
    def generate_server_config(self, domain: str = "truststream.local") -> str:
        """Generate server configuration."""
        config = f"""# TrustStream Server Configuration
server {{
    listen 80;
    server_name {domain} www.{domain};
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {domain} www.{domain};
    
    # SSL certificates
    ssl_certificate {self.ssl_config.certificate_path};
    ssl_certificate_key {self.ssl_config.private_key_path};
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Root directory for static files
    root /var/www/truststream;
    index index.html index.htm;
    
    # Rate limiting
    limit_req zone=api burst={self.rate_limits[0].burst} {'nodelay' if self.rate_limits[0].nodelay else ''};
    
    # Main application proxy
    location / {{
        # Try static files first, then proxy to app
        try_files $uri $uri/ @truststream_app;
    }}
    
    # API endpoints
    location /api/ {{
        limit_req zone=api burst={self.rate_limits[0].burst} {'nodelay' if self.rate_limits[0].nodelay else ''};
        
        proxy_pass http://truststream_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # Cache API responses (selective)
{self._generate_api_cache_rules()}
    }}
    
    # Authentication endpoints (stricter rate limiting)
    location /api/v1/auth/ {{
        limit_req zone=auth burst={self.rate_limits[1].burst} {'nodelay' if self.rate_limits[1].nodelay else ''};
        
        proxy_pass http://truststream_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # No caching for auth endpoints
        proxy_cache off;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }}
    
    # File upload endpoints
    location /api/v1/upload/ {{
        limit_req zone=upload burst={self.rate_limits[2].burst} {'nodelay' if self.rate_limits[2].nodelay else ''};
        
        client_max_body_size 100M;
        
        proxy_pass http://truststream_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Extended timeouts for uploads
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }}
    
    # WebSocket support for real-time features
    location /ws/ {{
        proxy_pass http://truststream_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }}
    
    # Static files
    location /static/ {{
        alias /var/www/truststream/static/;
        expires {self.cache_config.static_cache_time};
        add_header Cache-Control "public, immutable";
        
        # Gzip static files
        gzip_static on;
        
        # Security for static files
        location ~* \.(js|css)$ {{
            add_header Content-Security-Policy "default-src 'self'";
        }}
    }}
    
    # Media files
    location /media/ {{
        alias /var/www/truststream/media/;
        expires 30d;
        add_header Cache-Control "public";
        
        # Security for media files
        location ~* \.(jpg|jpeg|png|gif|ico|svg)$ {{
            add_header X-Content-Type-Options nosniff;
        }}
    }}
    
    # Health check endpoint (no rate limiting)
    location /health {{
        proxy_pass http://truststream_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        access_log off;
    }}
    
    # Monitoring endpoints (Prometheus metrics)
    location /metrics {{
        proxy_pass http://truststream_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Restrict access to monitoring
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }}
    
    # Fallback to application
    location @truststream_app {{
        proxy_pass http://truststream_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Default timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }}
    
    # Security: Block access to sensitive files
    location ~ /\. {{
        deny all;
        access_log off;
        log_not_found off;
    }}
    
    location ~ ~$ {{
        deny all;
        access_log off;
        log_not_found off;
    }}
    
    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    location = /404.html {{
        root /var/www/truststream/error_pages;
        internal;
    }}
    
    location = /50x.html {{
        root /var/www/truststream/error_pages;
        internal;
    }}
}}
"""
        return config
    
    def _generate_api_cache_rules(self) -> str:
        """Generate API caching rules."""
        rules = []
        
        # Cache GET requests for certain endpoints
        rules.append("        # Cache GET requests for read-only endpoints")
        rules.append("        proxy_cache truststream_cache;")
        rules.append("        proxy_cache_methods GET HEAD;")
        rules.append("        proxy_cache_valid 200 5m;")
        rules.append("        proxy_cache_valid 404 1m;")
        
        # Don't cache certain paths
        for path in self.cache_config.no_cache_paths:
            rules.append(f"        location {path} {{")
            rules.append("            proxy_cache off;")
            rules.append("            proxy_pass http://truststream_backend;")
            rules.append("        }")
        
        # Cache bypass for authenticated requests
        rules.append("        proxy_cache_bypass $http_authorization;")
        rules.append("        proxy_no_cache $http_authorization;")
        
        return "\n        ".join(rules)
    
    def generate_monitoring_config(self) -> str:
        """Generate monitoring server configuration."""
        config = """# TrustStream Monitoring Configuration
server {
    listen 8080;
    server_name monitoring.truststream.local;
    
    # Prometheus
    location /prometheus/ {
        proxy_pass http://truststream-prometheus:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Authentication (basic auth)
        auth_basic "Monitoring Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
    
    # Grafana
    location /grafana/ {
        proxy_pass http://truststream-grafana:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Grafana
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Restrict access to monitoring
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;
}
"""
        return config
    
    def save_configurations(self, output_dir: str = "config/nginx"):
        """Save all Nginx configurations to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Main nginx.conf
        main_config_path = output_path / "nginx.conf"
        with open(main_config_path, 'w') as f:
            f.write(self.generate_main_config())
        
        # Server configuration
        server_config_path = output_path / "truststream.conf"
        with open(server_config_path, 'w') as f:
            f.write(self.generate_server_config())
        
        # Monitoring configuration
        monitoring_config_path = output_path / "monitoring.conf"
        with open(monitoring_config_path, 'w') as f:
            f.write(self.generate_monitoring_config())
        
        # SSL configuration template
        ssl_template_path = output_path / "ssl_setup.sh"
        with open(ssl_template_path, 'w') as f:
            f.write(self._generate_ssl_setup_script())
        
        # Make SSL setup script executable
        os.chmod(ssl_template_path, 0o755)
        
        self.logger.info(f"Nginx configurations saved to {output_path}")
        
        return {
            'main_config': str(main_config_path),
            'server_config': str(server_config_path),
            'monitoring_config': str(monitoring_config_path),
            'ssl_setup_script': str(ssl_template_path)
        }
    
    def _generate_ssl_setup_script(self) -> str:
        """Generate SSL certificate setup script."""
        script = f"""#!/bin/bash
# TrustStream SSL Certificate Setup Script

set -e

echo "Setting up SSL certificates for TrustStream..."

# Create SSL directories
sudo mkdir -p /etc/ssl/certs
sudo mkdir -p /etc/ssl/private

# Generate self-signed certificate for development
if [ "$1" = "dev" ]; then
    echo "Generating self-signed certificate for development..."
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
        -keyout {self.ssl_config.private_key_path} \\
        -out {self.ssl_config.certificate_path} \\
        -subj "/C=US/ST=State/L=City/O=TrustStream/CN=truststream.local"
    
    echo "Self-signed certificate generated successfully!"
    echo "Certificate: {self.ssl_config.certificate_path}"
    echo "Private key: {self.ssl_config.private_key_path}"

# Setup Let's Encrypt certificate for production
elif [ "$1" = "prod" ]; then
    echo "Setting up Let's Encrypt certificate for production..."
    
    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot..."
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Get domain from user
    read -p "Enter your domain name: " DOMAIN
    
    # Obtain certificate
    sudo certbot --nginx -d $DOMAIN
    
    # Update nginx configuration with real certificate paths
    sudo sed -i "s|{self.ssl_config.certificate_path}|/etc/letsencrypt/live/$DOMAIN/fullchain.pem|g" /etc/nginx/sites-available/truststream.conf
    sudo sed -i "s|{self.ssl_config.private_key_path}|/etc/letsencrypt/live/$DOMAIN/privkey.pem|g" /etc/nginx/sites-available/truststream.conf
    
    echo "Let's Encrypt certificate setup completed!"

else
    echo "Usage: $0 [dev|prod]"
    echo "  dev  - Generate self-signed certificate for development"
    echo "  prod - Setup Let's Encrypt certificate for production"
    exit 1
fi

# Set proper permissions
sudo chmod 644 {self.ssl_config.certificate_path}
sudo chmod 600 {self.ssl_config.private_key_path}

# Test nginx configuration
sudo nginx -t

echo "SSL setup completed successfully!"
echo "Remember to reload nginx: sudo systemctl reload nginx"
"""
        return script
    
    def generate_docker_nginx_config(self) -> str:
        """Generate Nginx configuration for Docker deployment."""
        # Simplified configuration for Docker
        self.upstream_servers = [
            UpstreamServer(host="truststream-app", port=8000)
        ]
        
        return self.generate_server_config("localhost")


# Global Nginx configuration generator
nginx_config_generator = NginxConfigGenerator()


def get_nginx_config_generator() -> NginxConfigGenerator:
    """Get the global Nginx configuration generator instance."""
    return nginx_config_generator