# truststream/deployment/monitoring_config.py

"""
Monitoring Configuration for TrustStream v4.4

This module generates Prometheus and Grafana configurations for comprehensive
system monitoring, alerting, and observability.
"""

import json
import yaml
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from .production_config import ProductionConfig, get_config


@dataclass
class PrometheusTarget:
    """Prometheus scrape target configuration."""
    
    job_name: str
    targets: List[str]
    scrape_interval: str = "15s"
    metrics_path: str = "/metrics"
    scheme: str = "http"
    params: Dict[str, List[str]] = field(default_factory=dict)
    static_configs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AlertRule:
    """Prometheus alert rule configuration."""
    
    alert: str
    expr: str
    for_duration: str
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class GrafanaDashboard:
    """Grafana dashboard configuration."""
    
    title: str
    uid: str
    tags: List[str] = field(default_factory=list)
    panels: List[Dict[str, Any]] = field(default_factory=list)
    time_range: Dict[str, str] = field(default_factory=lambda: {"from": "now-1h", "to": "now"})
    refresh: str = "30s"


class MonitoringConfigGenerator:
    """Monitoring configuration generator for TrustStream."""
    
    def __init__(self, config: Optional[ProductionConfig] = None):
        """Initialize monitoring configuration generator."""
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)
        
        # Prometheus configuration
        self.prometheus_targets = self._setup_prometheus_targets()
        self.alert_rules = self._setup_alert_rules()
        
        # Grafana configuration
        self.grafana_dashboards = self._setup_grafana_dashboards()
    
    def _setup_prometheus_targets(self) -> List[PrometheusTarget]:
        """Setup Prometheus scrape targets."""
        targets = [
            # TrustStream application metrics
            PrometheusTarget(
                job_name="truststream-app",
                targets=["truststream-app:8000"],
                scrape_interval="15s",
                metrics_path="/metrics"
            ),
            
            # PostgreSQL metrics
            PrometheusTarget(
                job_name="postgresql",
                targets=["postgres-exporter:9187"],
                scrape_interval="30s"
            ),
            
            # Neo4j metrics
            PrometheusTarget(
                job_name="neo4j",
                targets=["neo4j:2004"],
                scrape_interval="30s",
                metrics_path="/metrics"
            ),
            
            # Redis metrics
            PrometheusTarget(
                job_name="redis",
                targets=["redis-exporter:9121"],
                scrape_interval="30s"
            ),
            
            # Nginx metrics
            PrometheusTarget(
                job_name="nginx",
                targets=["nginx-exporter:9113"],
                scrape_interval="30s"
            ),
            
            # Node exporter (system metrics)
            PrometheusTarget(
                job_name="node-exporter",
                targets=["node-exporter:9100"],
                scrape_interval="15s"
            ),
            
            # cAdvisor (container metrics)
            PrometheusTarget(
                job_name="cadvisor",
                targets=["cadvisor:8080"],
                scrape_interval="30s",
                metrics_path="/metrics"
            )
        ]
        
        return targets
    
    def _setup_alert_rules(self) -> List[AlertRule]:
        """Setup Prometheus alert rules."""
        rules = [
            # Application health alerts
            AlertRule(
                alert="TrustStreamAppDown",
                expr='up{job="truststream-app"} == 0',
                for_duration="1m",
                labels={"severity": "critical"},
                annotations={
                    "summary": "TrustStream application is down",
                    "description": "TrustStream application has been down for more than 1 minute."
                }
            ),
            
            AlertRule(
                alert="HighResponseTime",
                expr='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="truststream-app"}[5m])) > 2',
                for_duration="5m",
                labels={"severity": "warning"},
                annotations={
                    "summary": "High response time detected",
                    "description": "95th percentile response time is above 2 seconds for 5 minutes."
                }
            ),
            
            AlertRule(
                alert="HighErrorRate",
                expr='rate(http_requests_total{job="truststream-app",status=~"5.."}[5m]) / rate(http_requests_total{job="truststream-app"}[5m]) > 0.05',
                for_duration="5m",
                labels={"severity": "critical"},
                annotations={
                    "summary": "High error rate detected",
                    "description": "Error rate is above 5% for 5 minutes."
                }
            ),
            
            # Database alerts
            AlertRule(
                alert="PostgreSQLDown",
                expr='up{job="postgresql"} == 0',
                for_duration="1m",
                labels={"severity": "critical"},
                annotations={
                    "summary": "PostgreSQL is down",
                    "description": "PostgreSQL database has been down for more than 1 minute."
                }
            ),
            
            AlertRule(
                alert="Neo4jDown",
                expr='up{job="neo4j"} == 0',
                for_duration="1m",
                labels={"severity": "critical"},
                annotations={
                    "summary": "Neo4j is down",
                    "description": "Neo4j database has been down for more than 1 minute."
                }
            ),
            
            AlertRule(
                alert="RedisDown",
                expr='up{job="redis"} == 0',
                for_duration="1m",
                labels={"severity": "critical"},
                annotations={
                    "summary": "Redis is down",
                    "description": "Redis cache has been down for more than 1 minute."
                }
            ),
            
            # System resource alerts
            AlertRule(
                alert="HighCPUUsage",
                expr='100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80',
                for_duration="10m",
                labels={"severity": "warning"},
                annotations={
                    "summary": "High CPU usage detected",
                    "description": "CPU usage is above 80% for 10 minutes on {{ $labels.instance }}."
                }
            ),
            
            AlertRule(
                alert="HighMemoryUsage",
                expr='(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85',
                for_duration="10m",
                labels={"severity": "warning"},
                annotations={
                    "summary": "High memory usage detected",
                    "description": "Memory usage is above 85% for 10 minutes on {{ $labels.instance }}."
                }
            ),
            
            AlertRule(
                alert="DiskSpaceLow",
                expr='(1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"})) * 100 > 85',
                for_duration="5m",
                labels={"severity": "warning"},
                annotations={
                    "summary": "Low disk space detected",
                    "description": "Disk usage is above 85% on {{ $labels.instance }} filesystem {{ $labels.mountpoint }}."
                }
            ),
            
            # TrustStream specific alerts
            AlertRule(
                alert="TrustCalculationFailures",
                expr='rate(truststream_trust_calculation_failures_total[5m]) > 0.1',
                for_duration="5m",
                labels={"severity": "warning"},
                annotations={
                    "summary": "High trust calculation failure rate",
                    "description": "Trust calculation failure rate is above 0.1 per second for 5 minutes."
                }
            ),
            
            AlertRule(
                alert="AIProviderFailures",
                expr='rate(truststream_ai_provider_failures_total[5m]) > 0.05',
                for_duration="5m",
                labels={"severity": "warning"},
                annotations={
                    "summary": "High AI provider failure rate",
                    "description": "AI provider failure rate is above 0.05 per second for 5 minutes."
                }
            ),
            
            AlertRule(
                alert="MatrixModerationBacklog",
                expr='truststream_matrix_moderation_queue_size > 100',
                for_duration="10m",
                labels={"severity": "warning"},
                annotations={
                    "summary": "Matrix moderation queue backlog",
                    "description": "Matrix moderation queue has more than 100 pending items for 10 minutes."
                }
            )
        ]
        
        return rules
    
    def _setup_grafana_dashboards(self) -> List[GrafanaDashboard]:
        """Setup Grafana dashboards."""
        dashboards = [
            # Main TrustStream dashboard
            GrafanaDashboard(
                title="TrustStream Overview",
                uid="truststream-overview",
                tags=["truststream", "overview"]
            ),
            
            # Application performance dashboard
            GrafanaDashboard(
                title="TrustStream Application Performance",
                uid="truststream-performance",
                tags=["truststream", "performance"]
            ),
            
            # Database monitoring dashboard
            GrafanaDashboard(
                title="TrustStream Database Monitoring",
                uid="truststream-database",
                tags=["truststream", "database"]
            ),
            
            # Trust system dashboard
            GrafanaDashboard(
                title="TrustStream Trust System",
                uid="truststream-trust",
                tags=["truststream", "trust"]
            ),
            
            # AI providers dashboard
            GrafanaDashboard(
                title="TrustStream AI Providers",
                uid="truststream-ai",
                tags=["truststream", "ai"]
            ),
            
            # Matrix integration dashboard
            GrafanaDashboard(
                title="TrustStream Matrix Integration",
                uid="truststream-matrix",
                tags=["truststream", "matrix"]
            )
        ]
        
        return dashboards
    
    def generate_prometheus_config(self) -> Dict[str, Any]:
        """Generate Prometheus configuration."""
        config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s",
                "external_labels": {
                    "cluster": "truststream-production"
                }
            },
            
            "rule_files": [
                "/etc/prometheus/rules/*.yml"
            ],
            
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {
                                "targets": ["alertmanager:9093"]
                            }
                        ]
                    }
                ]
            },
            
            "scrape_configs": []
        }
        
        # Add scrape configurations
        for target in self.prometheus_targets:
            scrape_config = {
                "job_name": target.job_name,
                "scrape_interval": target.scrape_interval,
                "metrics_path": target.metrics_path,
                "scheme": target.scheme,
                "static_configs": [
                    {
                        "targets": target.targets
                    }
                ]
            }
            
            if target.params:
                scrape_config["params"] = target.params
            
            config["scrape_configs"].append(scrape_config)
        
        return config
    
    def generate_alert_rules(self) -> Dict[str, Any]:
        """Generate Prometheus alert rules."""
        groups = [
            {
                "name": "truststream.rules",
                "rules": []
            }
        ]
        
        for rule in self.alert_rules:
            alert_rule = {
                "alert": rule.alert,
                "expr": rule.expr,
                "for": rule.for_duration,
                "labels": rule.labels,
                "annotations": rule.annotations
            }
            groups[0]["rules"].append(alert_rule)
        
        return {"groups": groups}
    
    def generate_alertmanager_config(self) -> Dict[str, Any]:
        """Generate Alertmanager configuration."""
        config = {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": "alerts@truststream.local"
            },
            
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "web.hook"
            },
            
            "receivers": [
                {
                    "name": "web.hook",
                    "email_configs": [
                        {
                            "to": "admin@truststream.local",
                            "subject": "TrustStream Alert: {{ .GroupLabels.alertname }}",
                            "body": """
{{ range .Alerts }}
Alert: {{ .Annotations.summary }}
Description: {{ .Annotations.description }}
Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
{{ end }}
                            """
                        }
                    ],
                    "slack_configs": [
                        {
                            "api_url": "YOUR_SLACK_WEBHOOK_URL",
                            "channel": "#truststream-alerts",
                            "title": "TrustStream Alert",
                            "text": "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}"
                        }
                    ]
                }
            ]
        }
        
        return config
    
    def generate_grafana_overview_dashboard(self) -> Dict[str, Any]:
        """Generate main TrustStream overview dashboard."""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "TrustStream Overview",
                "uid": "truststream-overview",
                "tags": ["truststream", "overview"],
                "timezone": "browser",
                "panels": [
                    # System health panel
                    {
                        "id": 1,
                        "title": "System Health",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": 'up{job="truststream-app"}',
                                "legendFormat": "App Status"
                            },
                            {
                                "expr": 'up{job="postgresql"}',
                                "legendFormat": "PostgreSQL"
                            },
                            {
                                "expr": 'up{job="neo4j"}',
                                "legendFormat": "Neo4j"
                            },
                            {
                                "expr": 'up{job="redis"}',
                                "legendFormat": "Redis"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    
                    # Request rate panel
                    {
                        "id": 2,
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": 'rate(http_requests_total{job="truststream-app"}[5m])',
                                "legendFormat": "Requests/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    
                    # Response time panel
                    {
                        "id": 3,
                        "title": "Response Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": 'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job="truststream-app"}[5m]))',
                                "legendFormat": "50th percentile"
                            },
                            {
                                "expr": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="truststream-app"}[5m]))',
                                "legendFormat": "95th percentile"
                            },
                            {
                                "expr": 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{job="truststream-app"}[5m]))',
                                "legendFormat": "99th percentile"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    },
                    
                    # Error rate panel
                    {
                        "id": 4,
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": 'rate(http_requests_total{job="truststream-app",status=~"4.."}[5m])',
                                "legendFormat": "4xx errors"
                            },
                            {
                                "expr": 'rate(http_requests_total{job="truststream-app",status=~"5.."}[5m])',
                                "legendFormat": "5xx errors"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                    },
                    
                    # Trust calculations panel
                    {
                        "id": 5,
                        "title": "Trust Calculations",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": 'rate(truststream_trust_calculations_total[5m])',
                                "legendFormat": "Calculations/sec"
                            },
                            {
                                "expr": 'rate(truststream_trust_calculation_failures_total[5m])',
                                "legendFormat": "Failures/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
                    },
                    
                    # AI provider usage panel
                    {
                        "id": 6,
                        "title": "AI Provider Usage",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": 'rate(truststream_ai_requests_total[5m])',
                                "legendFormat": "{{ provider }} requests/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "30s"
            }
        }
        
        return dashboard
    
    def save_configurations(self, output_dir: str = "config/monitoring"):
        """Save all monitoring configurations to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Prometheus configuration
        prometheus_config_path = output_path / "prometheus.yml"
        with open(prometheus_config_path, 'w') as f:
            yaml.dump(self.generate_prometheus_config(), f, default_flow_style=False)
        
        # Alert rules
        alert_rules_path = output_path / "alert_rules.yml"
        with open(alert_rules_path, 'w') as f:
            yaml.dump(self.generate_alert_rules(), f, default_flow_style=False)
        
        # Alertmanager configuration
        alertmanager_config_path = output_path / "alertmanager.yml"
        with open(alertmanager_config_path, 'w') as f:
            yaml.dump(self.generate_alertmanager_config(), f, default_flow_style=False)
        
        # Grafana dashboard
        grafana_dashboard_path = output_path / "grafana_dashboard.json"
        with open(grafana_dashboard_path, 'w') as f:
            json.dump(self.generate_grafana_overview_dashboard(), f, indent=2)
        
        # Docker compose for monitoring stack
        monitoring_compose_path = output_path / "docker-compose.monitoring.yml"
        with open(monitoring_compose_path, 'w') as f:
            f.write(self._generate_monitoring_docker_compose())
        
        self.logger.info(f"Monitoring configurations saved to {output_path}")
        
        return {
            'prometheus_config': str(prometheus_config_path),
            'alert_rules': str(alert_rules_path),
            'alertmanager_config': str(alertmanager_config_path),
            'grafana_dashboard': str(grafana_dashboard_path),
            'monitoring_compose': str(monitoring_compose_path)
        }
    
    def _generate_monitoring_docker_compose(self) -> str:
        """Generate Docker Compose for monitoring stack."""
        compose = """version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: truststream-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/rules/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - truststream_network
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: truststream-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    networks:
      - truststream_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: truststream-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana_dashboard.json:/etc/grafana/provisioning/dashboards/truststream.json
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - truststream_network
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: truststream-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - truststream_network
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: truststream-cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks:
      - truststream_network
    restart: unless-stopped

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: truststream-postgres-exporter
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://truststream:password@truststream-postgres:5432/truststream?sslmode=disable
    networks:
      - truststream_network
    restart: unless-stopped
    depends_on:
      - postgres

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: truststream-redis-exporter
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://truststream-redis:6379
    networks:
      - truststream_network
    restart: unless-stopped
    depends_on:
      - redis

  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:latest
    container_name: truststream-nginx-exporter
    ports:
      - "9113:9113"
    command:
      - '-nginx.scrape-uri=http://truststream-nginx:8080/nginx_status'
    networks:
      - truststream_network
    restart: unless-stopped
    depends_on:
      - nginx

volumes:
  prometheus_data:
  alertmanager_data:
  grafana_data:

networks:
  truststream_network:
    external: true
"""
        return compose


# Global monitoring configuration generator
monitoring_config_generator = MonitoringConfigGenerator()


def get_monitoring_config_generator() -> MonitoringConfigGenerator:
    """Get the global monitoring configuration generator instance."""
    return monitoring_config_generator