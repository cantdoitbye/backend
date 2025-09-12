from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import (
    ABTestExperiment, ExperimentParticipant, RealTimeMetric
)
from .services import AnalyticsService

channel_layer = get_channel_layer()


@receiver(post_save, sender=ABTestExperiment)
def experiment_updated(sender, instance, created, **kwargs):
    """
    Send real-time updates when experiments are created or updated
    """
    if channel_layer:
        # Broadcast experiment update to dashboard clients
        async_to_sync(channel_layer.group_send)(
            'analytics_dashboard',
            {
                'type': 'experiment_update',
                'experiment_id': str(instance.id),
                'status': instance.status,
                'data': {
                    'name': instance.name,
                    'status': instance.status,
                    'created': created,
                    'participants_count': instance.participants.count()
                }
            }
        )


@receiver(post_save, sender=ExperimentParticipant)
def participant_added(sender, instance, created, **kwargs):
    """
    Send updates when new participants are added to experiments
    """
    if created and channel_layer:
        # Update participant count for the experiment
        async_to_sync(channel_layer.group_send)(
            'analytics_dashboard',
            {
                'type': 'experiment_update',
                'experiment_id': str(instance.experiment.id),
                'status': instance.experiment.status,
                'data': {
                    'participants_count': instance.experiment.participants.count(),
                    'new_participant': {
                        'user': instance.user.username,
                        'group': instance.group
                    }
                }
            }
        )


@receiver(post_save, sender=RealTimeMetric)
def metric_recorded(sender, instance, created, **kwargs):
    """
    Broadcast real-time metric updates to connected clients
    """
    if created and channel_layer:
        # Send to metric-specific channel
        async_to_sync(channel_layer.group_send)(
            f'metric_{instance.metric_name}',
            {
                'type': 'metric_update',
                'metric_name': instance.metric_name,
                'value': instance.value,
                'unit': instance.unit,
                'timestamp': instance.timestamp.isoformat()
            }
        )
        
        # Also send to general dashboard channel
        async_to_sync(channel_layer.group_send)(
            'analytics_dashboard',
            {
                'type': 'metric_update',
                'metric_name': instance.metric_name,
                'value': instance.value,
                'category': instance.metric_category,
                'timestamp': instance.timestamp.isoformat()
            }
        )
