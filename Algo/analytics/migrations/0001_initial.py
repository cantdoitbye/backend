# Generated manually for analytics

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalyticsEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_name', models.CharField(max_length=100)),
                ('event_category', models.CharField(choices=[('feed', 'Feed Interaction'), ('content', 'Content Interaction'), ('user', 'User Action'), ('system', 'System Event'), ('performance', 'Performance Metric'), ('error', 'Error Event')], max_length=50)),
                ('session_id', models.CharField(blank=True, max_length=100)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('properties', models.JSONField(blank=True, default=dict)),
                ('value', models.FloatField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('referrer', models.URLField(blank=True)),
                ('device_type', models.CharField(choices=[('mobile', 'Mobile'), ('tablet', 'Tablet'), ('desktop', 'Desktop'), ('unknown', 'Unknown')], default='unknown', max_length=20)),
                ('platform', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'analytics_events',
            },
        ),
        migrations.CreateModel(
            name='FeedAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generation_time_ms', models.PositiveIntegerField()),
                ('content_count', models.PositiveIntegerField()),
                ('composition_used', models.JSONField(default=dict)),
                ('personal_connections_count', models.PositiveIntegerField(default=0)),
                ('interest_based_count', models.PositiveIntegerField(default=0)),
                ('trending_count', models.PositiveIntegerField(default=0)),
                ('discovery_count', models.PositiveIntegerField(default=0)),
                ('community_count', models.PositiveIntegerField(default=0)),
                ('product_count', models.PositiveIntegerField(default=0)),
                ('cache_hit', models.BooleanField(default=False)),
                ('cache_key', models.CharField(blank=True, max_length=200)),
                ('items_viewed', models.PositiveIntegerField(default=0)),
                ('items_engaged', models.PositiveIntegerField(default=0)),
                ('total_engagement_time_seconds', models.PositiveIntegerField(default=0)),
                ('experiment_group', models.CharField(blank=True, max_length=50)),
                ('request_id', models.CharField(blank=True, max_length=100)),
                ('device_type', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feed_analytics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'feed_analytics',
            },
        ),
        migrations.CreateModel(
            name='UserEngagementMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_type', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], max_length=10)),
                ('period_start', models.DateTimeField()),
                ('period_end', models.DateTimeField()),
                ('sessions_count', models.PositiveIntegerField(default=0)),
                ('total_session_duration_seconds', models.PositiveIntegerField(default=0)),
                ('feed_views', models.PositiveIntegerField(default=0)),
                ('content_views', models.PositiveIntegerField(default=0)),
                ('likes_given', models.PositiveIntegerField(default=0)),
                ('comments_made', models.PositiveIntegerField(default=0)),
                ('shares_made', models.PositiveIntegerField(default=0)),
                ('posts_created', models.PositiveIntegerField(default=0)),
                ('communities_joined', models.PositiveIntegerField(default=0)),
                ('connections_made', models.PositiveIntegerField(default=0)),
                ('engagement_score', models.FloatField(default=0.0)),
                ('activity_score', models.FloatField(default=0.0)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='engagement_metrics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_engagement_metrics',
            },
        ),
        migrations.CreateModel(
            name='ContentPerformanceMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('period_type', models.CharField(choices=[('hourly', 'Hourly'), ('daily', 'Daily'), ('weekly', 'Weekly')], max_length=10)),
                ('period_start', models.DateTimeField()),
                ('period_end', models.DateTimeField()),
                ('impressions', models.PositiveIntegerField(default=0)),
                ('unique_views', models.PositiveIntegerField(default=0)),
                ('total_view_time_seconds', models.PositiveIntegerField(default=0)),
                ('likes', models.PositiveIntegerField(default=0)),
                ('dislikes', models.PositiveIntegerField(default=0)),
                ('comments', models.PositiveIntegerField(default=0)),
                ('shares', models.PositiveIntegerField(default=0)),
                ('bookmarks', models.PositiveIntegerField(default=0)),
                ('engagement_rate', models.FloatField(default=0.0)),
                ('viral_coefficient', models.FloatField(default=0.0)),
                ('average_view_time_seconds', models.FloatField(default=0.0)),
                ('feed_appearances', models.PositiveIntegerField(default=0)),
                ('trending_appearances', models.PositiveIntegerField(default=0)),
                ('search_appearances', models.PositiveIntegerField(default=0)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'db_table': 'content_performance_metrics',
            },
        ),
        migrations.CreateModel(
            name='SystemPerformanceMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric_name', models.CharField(max_length=100)),
                ('metric_category', models.CharField(choices=[('database', 'Database'), ('cache', 'Cache'), ('api', 'API'), ('feed_generation', 'Feed Generation'), ('scoring', 'Scoring Engine'), ('memory', 'Memory Usage'), ('cpu', 'CPU Usage')], max_length=30)),
                ('value', models.FloatField()),
                ('unit', models.CharField(blank=True, max_length=20)),
                ('warning_threshold', models.FloatField(blank=True, null=True)),
                ('critical_threshold', models.FloatField(blank=True, null=True)),
                ('server_id', models.CharField(blank=True, max_length=50)),
                ('environment', models.CharField(choices=[('development', 'Development'), ('staging', 'Staging'), ('production', 'Production')], default='production', max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'system_performance_metrics',
            },
        ),
        migrations.CreateModel(
            name='ErrorLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error_type', models.CharField(max_length=100)),
                ('error_message', models.TextField()),
                ('stack_trace', models.TextField(blank=True)),
                ('session_id', models.CharField(blank=True, max_length=100)),
                ('request_id', models.CharField(blank=True, max_length=100)),
                ('url_path', models.TextField(blank=True)),
                ('http_method', models.CharField(blank=True, max_length=10)),
                ('user_agent', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('severity', models.CharField(choices=[('debug', 'Debug'), ('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')], default='error', max_length=20)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('resolution_notes', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'error_logs',
            },
        ),
        # Add constraints
        migrations.AddConstraint(
            model_name='userengagementmetrics',
            constraint=models.UniqueConstraint(fields=['user', 'period_type', 'period_start'], name='unique_user_engagement_metrics'),
        ),
        migrations.AddConstraint(
            model_name='contentperformancemetrics',
            constraint=models.UniqueConstraint(fields=['content_type', 'object_id', 'period_type', 'period_start'], name='unique_content_performance_metrics'),
        ),
    ]
