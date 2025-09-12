import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings.production')

app = Celery('ooumph_feed')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Task configuration
app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'analytics_dashboard.tasks.*': {'queue': 'analytics'},
        'caching.tasks.*': {'queue': 'caching'},
        'scoring_engines.tasks.*': {'queue': 'scoring'},
        'feed_algorithm.tasks.*': {'queue': 'feeds'},
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Task retry configuration
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Result backend configuration
    result_backend_transport_options={
        'master_name': 'mymaster',
        'retry_on_timeout': True,
    },
    
    # Beat scheduler configuration
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Task error handling
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Task monitoring
@app.task
def health_check():
    """Simple health check task for monitoring"""
    return {'status': 'healthy', 'timestamp': timezone.now().isoformat()}

# Celery signals for monitoring
from celery.signals import task_prerun, task_postrun, task_failure

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Record task start metrics"""
    try:
        from analytics_dashboard.services import RealtimeMetricsCollector
        collector = RealtimeMetricsCollector()
        collector.collect_system_metrics(
            'celery_task_started',
            1,
            'count'
        )
    except ImportError:
        # Analytics not available yet
        pass

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Record task completion metrics"""
    try:
        from analytics_dashboard.services import RealtimeMetricsCollector
        collector = RealtimeMetricsCollector()
        collector.collect_system_metrics(
            f'celery_task_{state.lower()}',
            1,
            'count'
        )
    except ImportError:
        # Analytics not available yet
        pass

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Record task failure metrics"""
    try:
        from analytics_dashboard.services import RealtimeMetricsCollector
        collector = RealtimeMetricsCollector()
        collector.collect_system_metrics(
            'celery_task_failed',
            1,
            'count'
        )
    except ImportError:
        # Analytics not available yet
        pass
