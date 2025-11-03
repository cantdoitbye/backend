# TrustStream Admin Interface v4.4
# Comprehensive Dashboard for AI Moderation Monitoring and Community Health Management

import logging
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sqlite3
import psycopg2
from neo4j import GraphDatabase

from .agents.manager import AgentManager
from .ai_providers import AIProviderManager
from .trust_pyramid import TrustPyramidCalculator
from .matrix_integration import MatrixModerationBot

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(Enum):
    """Types of metrics to track"""
    MODERATION = "moderation"
    TRUST = "trust"
    COMMUNITY = "community"
    PERFORMANCE = "performance"
    AI_PROVIDER = "ai_provider"
    AGENT = "agent"


@dataclass
class SystemAlert:
    """System alert for admin attention"""
    id: str
    level: AlertLevel
    title: str
    description: str
    timestamp: datetime
    source: str
    resolved: bool
    metadata: Dict[str, Any]


@dataclass
class ModerationSummary:
    """Summary of moderation activities"""
    total_actions: int
    actions_by_type: Dict[str, int]
    avg_confidence: float
    escalation_rate: float
    false_positive_rate: float
    response_time_avg: float
    top_violation_types: List[Tuple[str, int]]
    agent_performance: Dict[str, Dict[str, Any]]


@dataclass
class CommunityHealthMetrics:
    """Community health and engagement metrics"""
    active_users: int
    new_users: int
    user_retention_rate: float
    avg_trust_score: float
    trust_distribution: Dict[str, int]
    engagement_metrics: Dict[str, float]
    content_quality_score: float
    toxicity_trend: List[Tuple[datetime, float]]
    diversity_index: float


class TrustStreamAdminInterface:
    """
    TrustStream Admin Interface v4.4
    
    Comprehensive web-based dashboard for monitoring and managing TrustStream:
    - Real-time AI moderation monitoring and analytics
    - Community health metrics and trend analysis
    - Trust score distribution and user behavior insights
    - Agent performance monitoring and optimization
    - AI provider usage statistics and cost tracking
    - System alerts and automated incident response
    - Configuration management and policy updates
    - Audit logs and compliance reporting
    - User appeal management and decision review
    - Performance optimization and scaling insights
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize TrustStream components
        self.agent_manager = AgentManager(config.get('agents', {}))
        self.ai_manager = AIProviderManager(config.get('ai_providers', {}))
        self.trust_calculator = TrustPyramidCalculator(config.get('trust_pyramid', {}))
        self.matrix_bot = None  # Will be initialized if Matrix is enabled
        
        # Database connections
        self.db_config = config.get('database', {})
        self.postgres_conn = None
        self.neo4j_driver = None
        self.sqlite_conn = None
        
        # Admin state
        self.alerts: List[SystemAlert] = []
        self.metrics_cache: Dict[str, Any] = {}
        self.last_refresh = datetime.utcnow()
        
        # Streamlit configuration
        self.setup_streamlit_config()
        
        logger.info("TrustStream Admin Interface initialized")
    
    def setup_streamlit_config(self):
        """Configure Streamlit interface."""
        st.set_page_config(
            page_title="TrustStream Admin Dashboard",
            page_icon="🛡️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        .alert-critical {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .alert-warning {
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .alert-info {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    async def initialize_connections(self):
        """Initialize database connections."""
        try:
            # PostgreSQL connection
            if self.db_config.get('postgres'):
                self.postgres_conn = psycopg2.connect(**self.db_config['postgres'])
                logger.info("PostgreSQL connection established")
            
            # Neo4j connection
            if self.db_config.get('neo4j'):
                self.neo4j_driver = GraphDatabase.driver(
                    self.db_config['neo4j']['uri'],
                    auth=(self.db_config['neo4j']['user'], self.db_config['neo4j']['password'])
                )
                logger.info("Neo4j connection established")
            
            # SQLite for local metrics
            self.sqlite_conn = sqlite3.connect(':memory:')
            self._setup_metrics_tables()
            
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            self._add_alert(AlertLevel.CRITICAL, "Database Connection Failed", str(e))
    
    def run_dashboard(self):
        """Run the main Streamlit dashboard."""
        try:
            # Auto-refresh every 30 seconds
            st_autorefresh(interval=30000, key="dashboard_refresh")
            
            # Header
            st.markdown('<h1 class="main-header">🛡️ TrustStream Admin Dashboard</h1>', 
                       unsafe_allow_html=True)
            
            # Sidebar navigation
            page = self._render_sidebar()
            
            # Main content based on selected page
            if page == "Overview":
                self._render_overview_page()
            elif page == "Moderation":
                self._render_moderation_page()
            elif page == "Community Health":
                self._render_community_health_page()
            elif page == "Trust Analytics":
                self._render_trust_analytics_page()
            elif page == "Agent Performance":
                self._render_agent_performance_page()
            elif page == "AI Providers":
                self._render_ai_providers_page()
            elif page == "System Alerts":
                self._render_alerts_page()
            elif page == "Configuration":
                self._render_configuration_page()
            elif page == "Audit Logs":
                self._render_audit_logs_page()
            elif page == "User Appeals":
                self._render_appeals_page()
            
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            st.error(f"Dashboard error: {str(e)}")
    
    def _render_sidebar(self) -> str:
        """Render sidebar navigation."""
        st.sidebar.title("Navigation")
        
        # System status indicator
        status = self._get_system_status()
        status_color = "🟢" if status == "healthy" else "🟡" if status == "warning" else "🔴"
        st.sidebar.markdown(f"**System Status:** {status_color} {status.title()}")
        
        # Navigation menu
        pages = [
            "Overview",
            "Moderation",
            "Community Health", 
            "Trust Analytics",
            "Agent Performance",
            "AI Providers",
            "System Alerts",
            "Configuration",
            "Audit Logs",
            "User Appeals"
        ]
        
        selected_page = st.sidebar.selectbox("Select Page", pages)
        
        # Quick stats
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Quick Stats**")
        
        try:
            quick_stats = self._get_quick_stats()
            st.sidebar.metric("Active Users", quick_stats.get('active_users', 0))
            st.sidebar.metric("Moderations Today", quick_stats.get('moderations_today', 0))
            st.sidebar.metric("Avg Trust Score", f"{quick_stats.get('avg_trust_score', 0.5):.2f}")
            st.sidebar.metric("System Load", f"{quick_stats.get('system_load', 0):.1f}%")
        except Exception as e:
            st.sidebar.error("Failed to load quick stats")
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            self._refresh_all_data()
            st.experimental_rerun()
        
        return selected_page
    
    def _render_overview_page(self):
        """Render main overview dashboard."""
        st.header("System Overview")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            overview_data = self._get_overview_data()
            
            with col1:
                st.metric(
                    "Total Users",
                    overview_data['total_users'],
                    delta=overview_data['users_change']
                )
            
            with col2:
                st.metric(
                    "Moderations (24h)",
                    overview_data['moderations_24h'],
                    delta=overview_data['moderations_change']
                )
            
            with col3:
                st.metric(
                    "Avg Response Time",
                    f"{overview_data['avg_response_time']:.2f}s",
                    delta=f"{overview_data['response_time_change']:.2f}s"
                )
            
            with col4:
                st.metric(
                    "System Uptime",
                    overview_data['uptime'],
                    delta=None
                )
            
            # Charts row
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Moderation Activity (Last 7 Days)")
                moderation_chart = self._create_moderation_timeline_chart()
                st.plotly_chart(moderation_chart, use_container_width=True)
            
            with col2:
                st.subheader("Trust Score Distribution")
                trust_chart = self._create_trust_distribution_chart()
                st.plotly_chart(trust_chart, use_container_width=True)
            
            # Recent alerts
            st.subheader("Recent System Alerts")
            recent_alerts = self._get_recent_alerts(limit=5)
            if recent_alerts:
                for alert in recent_alerts:
                    self._render_alert_card(alert)
            else:
                st.info("No recent alerts")
            
            # Agent status
            st.subheader("Agent Status Overview")
            agent_status = self._get_agent_status_overview()
            
            agent_cols = st.columns(len(agent_status))
            for i, (agent_name, status) in enumerate(agent_status.items()):
                with agent_cols[i]:
                    status_icon = "✅" if status['healthy'] else "❌"
                    st.markdown(f"**{agent_name}** {status_icon}")
                    st.caption(f"Processed: {status['processed']}")
                    st.caption(f"Accuracy: {status['accuracy']:.1%}")
            
        except Exception as e:
            st.error(f"Failed to load overview data: {str(e)}")
    
    def _render_moderation_page(self):
        """Render moderation monitoring page."""
        st.header("Moderation Monitoring")
        
        # Time range selector
        col1, col2 = st.columns([3, 1])
        with col1:
            time_range = st.selectbox(
                "Time Range",
                ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"]
            )
        with col2:
            auto_refresh = st.checkbox("Auto Refresh", value=True)
        
        try:
            moderation_data = self._get_moderation_data(time_range)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Actions", moderation_data['total_actions'])
            with col2:
                st.metric("Avg Confidence", f"{moderation_data['avg_confidence']:.2f}")
            with col3:
                st.metric("Escalation Rate", f"{moderation_data['escalation_rate']:.1%}")
            with col4:
                st.metric("False Positive Rate", f"{moderation_data['false_positive_rate']:.1%}")
            
            # Action breakdown chart
            st.subheader("Moderation Actions Breakdown")
            action_chart = self._create_action_breakdown_chart(moderation_data['actions_by_type'])
            st.plotly_chart(action_chart, use_container_width=True)
            
            # Recent moderations table
            st.subheader("Recent Moderation Actions")
            recent_moderations = self._get_recent_moderations(limit=20)
            
            if recent_moderations:
                df = pd.DataFrame(recent_moderations)
                st.dataframe(
                    df,
                    column_config={
                        "timestamp": st.column_config.DatetimeColumn("Time"),
                        "action": st.column_config.TextColumn("Action"),
                        "confidence": st.column_config.NumberColumn("Confidence", format="%.2f"),
                        "user_id": st.column_config.TextColumn("User"),
                        "reason": st.column_config.TextColumn("Reason")
                    },
                    use_container_width=True
                )
            else:
                st.info("No recent moderation actions")
            
            # Performance trends
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Response Time Trend")
                response_chart = self._create_response_time_chart(time_range)
                st.plotly_chart(response_chart, use_container_width=True)
            
            with col2:
                st.subheader("Confidence Distribution")
                confidence_chart = self._create_confidence_distribution_chart(time_range)
                st.plotly_chart(confidence_chart, use_container_width=True)
            
        except Exception as e:
            st.error(f"Failed to load moderation data: {str(e)}")
    
    def _render_community_health_page(self):
        """Render community health analytics page."""
        st.header("Community Health Analytics")
        
        try:
            health_metrics = self._get_community_health_metrics()
            
            # Health score overview
            col1, col2, col3 = st.columns(3)
            
            with col1:
                health_score = self._calculate_overall_health_score(health_metrics)
                st.metric("Overall Health Score", f"{health_score:.1f}/10")
                
                # Health indicator
                if health_score >= 8:
                    st.success("🟢 Excellent Community Health")
                elif health_score >= 6:
                    st.warning("🟡 Good Community Health")
                else:
                    st.error("🔴 Community Health Needs Attention")
            
            with col2:
                st.metric("Active Users", health_metrics.active_users)
                st.metric("New Users", health_metrics.new_users)
            
            with col3:
                st.metric("Retention Rate", f"{health_metrics.user_retention_rate:.1%}")
                st.metric("Avg Trust Score", f"{health_metrics.avg_trust_score:.2f}")
            
            # Engagement metrics
            st.subheader("User Engagement Metrics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                engagement_chart = self._create_engagement_chart(health_metrics.engagement_metrics)
                st.plotly_chart(engagement_chart, use_container_width=True)
            
            with col2:
                trust_dist_chart = self._create_detailed_trust_distribution_chart(
                    health_metrics.trust_distribution
                )
                st.plotly_chart(trust_dist_chart, use_container_width=True)
            
            # Toxicity trend
            st.subheader("Community Toxicity Trend")
            toxicity_chart = self._create_toxicity_trend_chart(health_metrics.toxicity_trend)
            st.plotly_chart(toxicity_chart, use_container_width=True)
            
            # Diversity metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Content Quality Metrics")
                quality_metrics = {
                    "Overall Quality": health_metrics.content_quality_score,
                    "Diversity Index": health_metrics.diversity_index,
                    "Engagement Rate": health_metrics.engagement_metrics.get('engagement_rate', 0)
                }
                
                for metric, value in quality_metrics.items():
                    st.metric(metric, f"{value:.2f}")
            
            with col2:
                st.subheader("Community Insights")
                insights = self._generate_community_insights(health_metrics)
                for insight in insights:
                    st.info(insight)
            
        except Exception as e:
            st.error(f"Failed to load community health data: {str(e)}")
    
    def _render_trust_analytics_page(self):
        """Render trust score analytics page."""
        st.header("Trust Score Analytics")
        
        try:
            # Trust overview
            trust_data = self._get_trust_analytics_data()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Avg Trust Score", f"{trust_data['avg_score']:.2f}")
            with col2:
                st.metric("High Trust Users", trust_data['high_trust_count'])
            with col3:
                st.metric("Low Trust Users", trust_data['low_trust_count'])
            with col4:
                st.metric("Trust Volatility", f"{trust_data['volatility']:.2f}")
            
            # Trust layer breakdown
            st.subheader("Trust Layer Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                layer_chart = self._create_trust_layer_chart(trust_data['layer_averages'])
                st.plotly_chart(layer_chart, use_container_width=True)
            
            with col2:
                correlation_chart = self._create_trust_correlation_chart(trust_data['correlations'])
                st.plotly_chart(correlation_chart, use_container_width=True)
            
            # Trust evolution over time
            st.subheader("Trust Score Evolution")
            evolution_chart = self._create_trust_evolution_chart(trust_data['evolution'])
            st.plotly_chart(evolution_chart, use_container_width=True)
            
            # User segments
            st.subheader("User Trust Segments")
            
            segments = trust_data['segments']
            segment_cols = st.columns(len(segments))
            
            for i, (segment_name, segment_data) in enumerate(segments.items()):
                with segment_cols[i]:
                    st.markdown(f"**{segment_name}**")
                    st.metric("Users", segment_data['count'])
                    st.metric("Avg Score", f"{segment_data['avg_score']:.2f}")
                    st.metric("Behavior", segment_data['behavior_trend'])
            
            # Trust prediction model
            st.subheader("Trust Prediction Insights")
            predictions = self._get_trust_predictions()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Predicted Trust Changes (Next 7 Days)**")
                for user_id, prediction in predictions['user_predictions'][:10]:
                    direction = "📈" if prediction > 0 else "📉"
                    st.write(f"{direction} {user_id}: {prediction:+.2f}")
            
            with col2:
                st.markdown("**Trust Factors Impact**")
                for factor, impact in predictions['factor_impacts'].items():
                    st.write(f"• {factor}: {impact:.2f}")
            
        except Exception as e:
            st.error(f"Failed to load trust analytics: {str(e)}")
    
    def _render_agent_performance_page(self):
        """Render agent performance monitoring page."""
        st.header("Agent Performance Monitoring")
        
        try:
            agent_data = self._get_agent_performance_data()
            
            # Agent overview
            st.subheader("Agent Performance Overview")
            
            agent_names = list(agent_data.keys())
            selected_agents = st.multiselect(
                "Select Agents to Monitor",
                agent_names,
                default=agent_names[:3]  # Show first 3 by default
            )
            
            if selected_agents:
                # Performance metrics table
                performance_df = pd.DataFrame([
                    {
                        'Agent': name,
                        'Accuracy': data['accuracy'],
                        'Precision': data['precision'],
                        'Recall': data['recall'],
                        'F1 Score': data['f1_score'],
                        'Avg Response Time': data['avg_response_time'],
                        'Total Processed': data['total_processed']
                    }
                    for name, data in agent_data.items()
                    if name in selected_agents
                ])
                
                st.dataframe(
                    performance_df,
                    column_config={
                        "Accuracy": st.column_config.ProgressColumn("Accuracy", min_value=0, max_value=1),
                        "Precision": st.column_config.ProgressColumn("Precision", min_value=0, max_value=1),
                        "Recall": st.column_config.ProgressColumn("Recall", min_value=0, max_value=1),
                        "F1 Score": st.column_config.ProgressColumn("F1 Score", min_value=0, max_value=1),
                        "Avg Response Time": st.column_config.NumberColumn("Avg Response Time", format="%.3fs")
                    },
                    use_container_width=True
                )
                
                # Performance trends
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Accuracy Trends")
                    accuracy_chart = self._create_agent_accuracy_chart(selected_agents, agent_data)
                    st.plotly_chart(accuracy_chart, use_container_width=True)
                
                with col2:
                    st.subheader("Response Time Trends")
                    response_chart = self._create_agent_response_chart(selected_agents, agent_data)
                    st.plotly_chart(response_chart, use_container_width=True)
                
                # Agent-specific insights
                st.subheader("Agent Insights and Recommendations")
                
                for agent_name in selected_agents:
                    with st.expander(f"{agent_name} Details"):
                        agent_info = agent_data[agent_name]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Performance Metrics**")
                            st.write(f"• Accuracy: {agent_info['accuracy']:.2%}")
                            st.write(f"• Precision: {agent_info['precision']:.2%}")
                            st.write(f"• Recall: {agent_info['recall']:.2%}")
                            st.write(f"• F1 Score: {agent_info['f1_score']:.2%}")
                        
                        with col2:
                            st.markdown("**Operational Metrics**")
                            st.write(f"• Avg Response Time: {agent_info['avg_response_time']:.3f}s")
                            st.write(f"• Total Processed: {agent_info['total_processed']:,}")
                            st.write(f"• Error Rate: {agent_info['error_rate']:.2%}")
                            st.write(f"• Last Updated: {agent_info['last_updated']}")
                        
                        # Recommendations
                        recommendations = self._get_agent_recommendations(agent_name, agent_info)
                        if recommendations:
                            st.markdown("**Recommendations**")
                            for rec in recommendations:
                                st.info(rec)
            
        except Exception as e:
            st.error(f"Failed to load agent performance data: {str(e)}")
    
    def _render_ai_providers_page(self):
        """Render AI providers monitoring page."""
        st.header("AI Providers Monitoring")
        
        try:
            provider_data = self._get_ai_provider_data()
            
            # Provider overview
            st.subheader("Provider Status Overview")
            
            provider_cols = st.columns(len(provider_data))
            
            for i, (provider_name, data) in enumerate(provider_data.items()):
                with provider_cols[i]:
                    status_icon = "🟢" if data['status'] == 'healthy' else "🔴"
                    st.markdown(f"**{provider_name}** {status_icon}")
                    st.metric("Requests Today", data['requests_today'])
                    st.metric("Avg Latency", f"{data['avg_latency']:.0f}ms")
                    st.metric("Success Rate", f"{data['success_rate']:.1%}")
            
            # Usage and cost analytics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Usage Distribution")
                usage_chart = self._create_provider_usage_chart(provider_data)
                st.plotly_chart(usage_chart, use_container_width=True)
            
            with col2:
                st.subheader("Cost Analysis")
                cost_chart = self._create_provider_cost_chart(provider_data)
                st.plotly_chart(cost_chart, use_container_width=True)
            
            # Performance comparison
            st.subheader("Provider Performance Comparison")
            
            comparison_df = pd.DataFrame([
                {
                    'Provider': name,
                    'Latency (ms)': data['avg_latency'],
                    'Success Rate': data['success_rate'],
                    'Cost per 1K': data['cost_per_1k'],
                    'Quality Score': data['quality_score'],
                    'Requests/Day': data['requests_today']
                }
                for name, data in provider_data.items()
            ])
            
            st.dataframe(
                comparison_df,
                column_config={
                    "Success Rate": st.column_config.ProgressColumn("Success Rate", min_value=0, max_value=1),
                    "Quality Score": st.column_config.ProgressColumn("Quality Score", min_value=0, max_value=1),
                    "Cost per 1K": st.column_config.NumberColumn("Cost per 1K", format="$%.4f")
                },
                use_container_width=True
            )
            
            # Provider-specific details
            st.subheader("Provider Details")
            
            selected_provider = st.selectbox("Select Provider for Details", list(provider_data.keys()))
            
            if selected_provider:
                provider_info = provider_data[selected_provider]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Performance Metrics**")
                    st.write(f"• Average Latency: {provider_info['avg_latency']:.0f}ms")
                    st.write(f"• Success Rate: {provider_info['success_rate']:.2%}")
                    st.write(f"• Error Rate: {provider_info['error_rate']:.2%}")
                    st.write(f"• Quality Score: {provider_info['quality_score']:.2f}")
                
                with col2:
                    st.markdown("**Usage Statistics**")
                    st.write(f"• Requests Today: {provider_info['requests_today']:,}")
                    st.write(f"• Total Requests: {provider_info['total_requests']:,}")
                    st.write(f"• Peak RPS: {provider_info['peak_rps']}")
                    st.write(f"• Current Load: {provider_info['current_load']:.1%}")
                
                with col3:
                    st.markdown("**Cost Information**")
                    st.write(f"• Cost per 1K: ${provider_info['cost_per_1k']:.4f}")
                    st.write(f"• Daily Cost: ${provider_info['daily_cost']:.2f}")
                    st.write(f"• Monthly Estimate: ${provider_info['monthly_estimate']:.2f}")
                    st.write(f"• Rate Limit: {provider_info['rate_limit']}/min")
                
                # Recent errors
                if provider_info.get('recent_errors'):
                    st.markdown("**Recent Errors**")
                    for error in provider_info['recent_errors'][-5:]:
                        st.error(f"{error['timestamp']}: {error['message']}")
            
        except Exception as e:
            st.error(f"Failed to load AI provider data: {str(e)}")
    
    def _render_alerts_page(self):
        """Render system alerts page."""
        st.header("System Alerts")
        
        # Alert controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            alert_level_filter = st.selectbox(
                "Filter by Level",
                ["All", "Critical", "Warning", "Info"]
            )
        
        with col2:
            resolved_filter = st.selectbox(
                "Show Alerts",
                ["All", "Unresolved", "Resolved"]
            )
        
        with col3:
            if st.button("🔄 Refresh Alerts"):
                self._refresh_alerts()
                st.experimental_rerun()
        
        # Alert summary
        alert_summary = self._get_alert_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Alerts", alert_summary['total'])
        with col2:
            st.metric("Critical", alert_summary['critical'], delta=alert_summary['critical_change'])
        with col3:
            st.metric("Warnings", alert_summary['warnings'], delta=alert_summary['warnings_change'])
        with col4:
            st.metric("Unresolved", alert_summary['unresolved'])
        
        # Alerts list
        filtered_alerts = self._filter_alerts(alert_level_filter, resolved_filter)
        
        if filtered_alerts:
            for alert in filtered_alerts:
                self._render_detailed_alert_card(alert)
        else:
            st.info("No alerts match the current filters")
        
        # Alert trends
        st.subheader("Alert Trends")
        alert_trend_chart = self._create_alert_trend_chart()
        st.plotly_chart(alert_trend_chart, use_container_width=True)
    
    def _render_configuration_page(self):
        """Render system configuration page."""
        st.header("System Configuration")
        
        # Configuration sections
        config_section = st.selectbox(
            "Configuration Section",
            ["Moderation Settings", "Trust Parameters", "AI Providers", "Agent Settings", "Alerts"]
        )
        
        if config_section == "Moderation Settings":
            self._render_moderation_config()
        elif config_section == "Trust Parameters":
            self._render_trust_config()
        elif config_section == "AI Providers":
            self._render_ai_provider_config()
        elif config_section == "Agent Settings":
            self._render_agent_config()
        elif config_section == "Alerts":
            self._render_alert_config()
    
    def _render_audit_logs_page(self):
        """Render audit logs page."""
        st.header("Audit Logs")
        
        # Log filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_type = st.selectbox(
                "Log Type",
                ["All", "Moderation", "Trust Changes", "System Events", "User Actions"]
            )
        
        with col2:
            time_range = st.selectbox(
                "Time Range",
                ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"]
            )
        
        with col3:
            user_filter = st.text_input("Filter by User ID")
        
        # Load and display logs
        try:
            logs = self._get_audit_logs(log_type, time_range, user_filter)
            
            if logs:
                df = pd.DataFrame(logs)
                st.dataframe(
                    df,
                    column_config={
                        "timestamp": st.column_config.DatetimeColumn("Timestamp"),
                        "event_type": st.column_config.TextColumn("Event Type"),
                        "user_id": st.column_config.TextColumn("User ID"),
                        "details": st.column_config.TextColumn("Details")
                    },
                    use_container_width=True
                )
                
                # Export logs
                if st.button("📥 Export Logs"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No logs found for the selected criteria")
                
        except Exception as e:
            st.error(f"Failed to load audit logs: {str(e)}")
    
    def _render_appeals_page(self):
        """Render user appeals management page."""
        st.header("User Appeals Management")
        
        # Appeals overview
        appeals_data = self._get_appeals_data()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Pending Appeals", appeals_data['pending'])
        with col2:
            st.metric("Approved Today", appeals_data['approved_today'])
        with col3:
            st.metric("Rejected Today", appeals_data['rejected_today'])
        with col4:
            st.metric("Avg Resolution Time", f"{appeals_data['avg_resolution_hours']:.1f}h")
        
        # Appeals queue
        st.subheader("Appeals Queue")
        
        pending_appeals = self._get_pending_appeals()
        
        if pending_appeals:
            for appeal in pending_appeals:
                with st.expander(f"Appeal #{appeal['id']} - {appeal['user_id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Original Decision**")
                        st.write(f"Action: {appeal['original_action']}")
                        st.write(f"Reason: {appeal['original_reason']}")
                        st.write(f"Confidence: {appeal['original_confidence']:.2f}")
                        st.write(f"Date: {appeal['decision_date']}")
                    
                    with col2:
                        st.markdown("**Appeal Details**")
                        st.write(f"Submitted: {appeal['appeal_date']}")
                        st.write(f"User Reason: {appeal['user_reason']}")
                        
                        # Appeal decision
                        col_approve, col_reject = st.columns(2)
                        
                        with col_approve:
                            if st.button(f"✅ Approve #{appeal['id']}", key=f"approve_{appeal['id']}"):
                                self._process_appeal(appeal['id'], 'approved')
                                st.success("Appeal approved")
                                st.experimental_rerun()
                        
                        with col_reject:
                            if st.button(f"❌ Reject #{appeal['id']}", key=f"reject_{appeal['id']}"):
                                self._process_appeal(appeal['id'], 'rejected')
                                st.success("Appeal rejected")
                                st.experimental_rerun()
        else:
            st.info("No pending appeals")
    
    # Helper methods for data retrieval and processing
    
    def _get_system_status(self) -> str:
        """Get overall system status."""
        try:
            # Check critical alerts
            critical_alerts = len([a for a in self.alerts if a.level == AlertLevel.CRITICAL and not a.resolved])
            
            if critical_alerts > 0:
                return "critical"
            
            # Check warning alerts
            warning_alerts = len([a for a in self.alerts if a.level == AlertLevel.WARNING and not a.resolved])
            
            if warning_alerts > 3:
                return "warning"
            
            return "healthy"
            
        except Exception:
            return "unknown"
    
    def _get_quick_stats(self) -> Dict[str, Any]:
        """Get quick statistics for sidebar."""
        # Placeholder implementation
        return {
            'active_users': 1250,
            'moderations_today': 45,
            'avg_trust_score': 0.72,
            'system_load': 23.5
        }
    
    def _refresh_all_data(self):
        """Refresh all cached data."""
        self.metrics_cache.clear()
        self.last_refresh = datetime.utcnow()
        logger.info("All data refreshed")
    
    def _add_alert(self, level: AlertLevel, title: str, description: str, source: str = "system"):
        """Add new system alert."""
        alert = SystemAlert(
            id=f"alert_{int(time.time())}",
            level=level,
            title=title,
            description=description,
            timestamp=datetime.utcnow(),
            source=source,
            resolved=False,
            metadata={}
        )
        
        self.alerts.append(alert)
        logger.info(f"Alert added: {level.value} - {title}")
    
    def _setup_metrics_tables(self):
        """Setup SQLite tables for metrics storage."""
        cursor = self.sqlite_conn.cursor()
        
        # Moderation metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moderation_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                action_type TEXT,
                confidence REAL,
                response_time REAL,
                user_id TEXT,
                agent_name TEXT
            )
        """)
        
        # Trust metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trust_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                user_id TEXT,
                trust_score REAL,
                iq_layer REAL,
                appeal_layer REAL,
                social_layer REAL,
                humanity_layer REAL
            )
        """)
        
        self.sqlite_conn.commit()
    
    # Chart creation methods (placeholder implementations)
    
    def _create_moderation_timeline_chart(self):
        """Create moderation activity timeline chart."""
        # Placeholder data
        dates = pd.date_range(start='2024-01-01', periods=7, freq='D')
        moderations = [12, 8, 15, 22, 18, 9, 14]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=moderations,
            mode='lines+markers',
            name='Moderations',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.update_layout(
            title="Moderation Activity Timeline",
            xaxis_title="Date",
            yaxis_title="Number of Moderations",
            height=400
        )
        
        return fig
    
    def _create_trust_distribution_chart(self):
        """Create trust score distribution chart."""
        # Placeholder data
        trust_ranges = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
        user_counts = [45, 120, 380, 520, 235]
        
        fig = go.Figure(data=[
            go.Bar(x=trust_ranges, y=user_counts, marker_color='#2ca02c')
        ])
        
        fig.update_layout(
            title="Trust Score Distribution",
            xaxis_title="Trust Score Range",
            yaxis_title="Number of Users",
            height=400
        )
        
        return fig
    
    # Additional placeholder methods for data retrieval
    
    def _get_overview_data(self) -> Dict[str, Any]:
        """Get overview dashboard data."""
        return {
            'total_users': 1250,
            'users_change': 25,
            'moderations_24h': 45,
            'moderations_change': -3,
            'avg_response_time': 0.245,
            'response_time_change': -0.012,
            'uptime': "99.8%"
        }
    
    def _get_recent_alerts(self, limit: int = 5) -> List[SystemAlert]:
        """Get recent system alerts."""
        return sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def _get_agent_status_overview(self) -> Dict[str, Dict[str, Any]]:
        """Get agent status overview."""
        return {
            'Content Quality': {'healthy': True, 'processed': 1250, 'accuracy': 0.94},
            'Harassment Detector': {'healthy': True, 'processed': 890, 'accuracy': 0.91},
            'Bias Prevention': {'healthy': True, 'processed': 670, 'accuracy': 0.88},
            'Mental Health': {'healthy': True, 'processed': 340, 'accuracy': 0.96}
        }
    
    def _render_alert_card(self, alert: SystemAlert):
        """Render alert card."""
        alert_class = f"alert-{alert.level.value}"
        level_icon = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(alert.level.value, "📢")
        
        st.markdown(f"""
        <div class="{alert_class}">
            <strong>{level_icon} {alert.title}</strong><br>
            {alert.description}<br>
            <small>Source: {alert.source} | {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</small>
        </div>
        """, unsafe_allow_html=True)


# Streamlit app entry point
def main():
    """Main entry point for Streamlit app."""
    try:
        # Load configuration
        config = {
            'agents': {},
            'ai_providers': {},
            'trust_pyramid': {},
            'database': {},
            'monitored_rooms': []
        }
        
        # Initialize admin interface
        admin = TrustStreamAdminInterface(config)
        
        # Run dashboard
        admin.run_dashboard()
        
    except Exception as e:
        st.error(f"Failed to initialize TrustStream Admin Interface: {str(e)}")
        logger.error(f"Admin interface error: {str(e)}")


if __name__ == "__main__":
    main()