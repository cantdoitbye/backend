import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import RealTimeMetric, ABTestExperiment
from .services import AnalyticsService


class AnalyticsDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time analytics dashboard updates
    """
    
    async def connect(self):
        self.room_group_name = 'analytics_dashboard'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial dashboard data
        await self.send_dashboard_data()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Handle messages from WebSocket
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'request_dashboard_data':
                await self.send_dashboard_data()
            elif message_type == 'request_experiment_data':
                experiment_id = text_data_json.get('experiment_id')
                await self.send_experiment_data(experiment_id)
            elif message_type == 'subscribe_metric':
                metric_name = text_data_json.get('metric_name')
                await self.subscribe_to_metric(metric_name)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON data'
            }))
    
    async def send_dashboard_data(self):
        """
        Send current dashboard data to client
        """
        try:
            # Get recent metrics
            metrics = await self.get_recent_metrics()
            
            # Get system health
            system_health = await self.get_system_health()
            
            # Get active experiments
            active_experiments = await self.get_active_experiments()
            
            await self.send(text_data=json.dumps({
                'type': 'dashboard_data',
                'data': {
                    'metrics': metrics,
                    'system_health': system_health,
                    'active_experiments': active_experiments,
                    'timestamp': timezone.now().isoformat()
                }
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error fetching dashboard data: {str(e)}'
            }))
    
    async def send_experiment_data(self, experiment_id):
        """
        Send specific experiment data
        """
        try:
            experiment_data = await self.get_experiment_data(experiment_id)
            
            await self.send(text_data=json.dumps({
                'type': 'experiment_data',
                'experiment_id': experiment_id,
                'data': experiment_data
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error fetching experiment data: {str(e)}'
            }))
    
    async def subscribe_to_metric(self, metric_name):
        """
        Subscribe to specific metric updates
        """
        # Add to metric-specific group
        metric_group_name = f'metric_{metric_name}'
        await self.channel_layer.group_add(
            metric_group_name,
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'metric_name': metric_name
        }))
    
    # Real-time update handlers
    async def metric_update(self, event):
        """
        Handle metric updates from group
        """
        await self.send(text_data=json.dumps({
            'type': 'metric_update',
            'metric_name': event['metric_name'],
            'value': event['value'],
            'timestamp': event['timestamp']
        }))
    
    async def experiment_update(self, event):
        """
        Handle experiment updates
        """
        await self.send(text_data=json.dumps({
            'type': 'experiment_update',
            'experiment_id': event['experiment_id'],
            'status': event['status'],
            'data': event['data']
        }))
    
    async def system_alert(self, event):
        """
        Handle system alerts
        """
        await self.send(text_data=json.dumps({
            'type': 'system_alert',
            'level': event['level'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))
    
    # Database queries (sync to async)
    @database_sync_to_async
    def get_recent_metrics(self):
        """
        Get recent metrics for dashboard
        """
        recent_metrics = RealTimeMetric.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(hours=1)
        ).order_by('-timestamp')[:50]
        
        return [
            {
                'name': metric.metric_name,
                'category': metric.metric_category,
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat()
            }
            for metric in recent_metrics
        ]
    
    @database_sync_to_async
    def get_system_health(self):
        """
        Get current system health status
        """
        # This would integrate with your health check system
        return {
            'status': 'healthy',
            'services': {
                'database': 'healthy',
                'redis': 'healthy',
                'celery': 'healthy'
            },
            'response_time': 45.2,  # ms
            'error_rate': 0.1  # %
        }
    
    @database_sync_to_async
    def get_active_experiments(self):
        """
        Get active A/B test experiments
        """
        active_experiments = ABTestExperiment.objects.filter(
            status='running'
        ).select_related('created_by')
        
        return [
            {
                'id': str(experiment.id),
                'name': experiment.name,
                'status': experiment.status,
                'traffic_allocation': experiment.traffic_allocation,
                'days_running': experiment.days_running,
                'participants_count': experiment.participants.count()
            }
            for experiment in active_experiments
        ]
    
    @database_sync_to_async
    def get_experiment_data(self, experiment_id):
        """
        Get detailed experiment data
        """
        try:
            experiment = ABTestExperiment.objects.get(id=experiment_id)
            service = AnalyticsService()
            
            return {
                'name': experiment.name,
                'status': experiment.status,
                'results': service.get_experiment_results(experiment_id),
                'participants': experiment.participants.count(),
                'statistical_significance': experiment.is_statistically_significant
            }
        except ABTestExperiment.DoesNotExist:
            return None


class MetricsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for specific metric streaming
    """
    
    async def connect(self):
        self.metric_name = self.scope['url_route']['kwargs']['metric_name']
        self.room_group_name = f'metric_{self.metric_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send recent data for this metric
        await self.send_metric_history()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Handle metric-specific requests
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'request_history':
                timerange = text_data_json.get('timerange', '1h')
                await self.send_metric_history(timerange)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON data'
            }))
    
    async def send_metric_history(self, timerange='1h'):
        """
        Send historical data for the metric
        """
        try:
            # Convert timerange to timedelta
            timerange_map = {
                '1h': timezone.timedelta(hours=1),
                '6h': timezone.timedelta(hours=6),
                '24h': timezone.timedelta(hours=24),
                '7d': timezone.timedelta(days=7)
            }
            
            delta = timerange_map.get(timerange, timezone.timedelta(hours=1))
            since = timezone.now() - delta
            
            history = await self.get_metric_history(since)
            
            await self.send(text_data=json.dumps({
                'type': 'metric_history',
                'metric_name': self.metric_name,
                'timerange': timerange,
                'data': history
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error fetching metric history: {str(e)}'
            }))
    
    async def metric_update(self, event):
        """
        Handle real-time metric updates
        """
        await self.send(text_data=json.dumps({
            'type': 'metric_update',
            'metric_name': event['metric_name'],
            'value': event['value'],
            'unit': event['unit'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def get_metric_history(self, since):
        """
        Get historical data for the specific metric
        """
        metrics = RealTimeMetric.objects.filter(
            metric_name=self.metric_name,
            timestamp__gte=since
        ).order_by('timestamp')
        
        return [
            {
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat(),
                'metadata': metric.metadata
            }
            for metric in metrics
        ]
