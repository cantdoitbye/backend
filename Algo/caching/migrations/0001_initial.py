# Generated manually for caching

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.contrib.contenttypes.models import ContentType


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CacheConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('cache_type', models.CharField(choices=[('feed', 'User Feed Cache'), ('trending', 'Trending Content Cache'), ('connections', 'Connection Circle Cache'), ('interests', 'Interest-based Cache'), ('scores', 'Scoring Cache'), ('analytics', 'Analytics Cache')], max_length=30)),
                ('default_ttl_seconds', models.PositiveIntegerField(default=3600)),
                ('max_entries', models.PositiveIntegerField(default=10000)),
                ('strategy', models.CharField(choices=[('lru', 'Least Recently Used'), ('lfu', 'Least Frequently Used'), ('ttl', 'Time To Live'), ('write_through', 'Write Through'), ('write_back', 'Write Back')], default='ttl', max_length=20)),
                ('config', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'cache_configurations',
            },
        ),
        migrations.CreateModel(
            name='CacheEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cache_key', models.CharField(max_length=250, unique=True)),
                ('cache_type', models.CharField(max_length=30)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('hit_count', models.PositiveIntegerField(default=0)),
                ('miss_count', models.PositiveIntegerField(default=0)),
                ('size_bytes', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_accessed', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'cache_entries',
            },
        ),
        migrations.CreateModel(
            name='FeedCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feed_data', models.JSONField(default=list)),
                ('composition', models.JSONField(default=dict)),
                ('cache_key', models.CharField(max_length=200)),
                ('generation_time_ms', models.PositiveIntegerField(default=0)),
                ('content_count', models.PositiveIntegerField(default=0)),
                ('version', models.CharField(default='1.0', max_length=50)),
                ('checksum', models.CharField(blank=True, max_length=64)),
                ('is_valid', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feed_caches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'feed_caches',
            },
        ),
        migrations.CreateModel(
            name='TrendingCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_window', models.CharField(choices=[('1h', '1 Hour'), ('6h', '6 Hours'), ('24h', '24 Hours'), ('7d', '7 Days')], default='24h', max_length=10)),
                ('trending_items', models.JSONField(default=list)),
                ('total_items', models.PositiveIntegerField(default=0)),
                ('cache_key', models.CharField(max_length=200)),
                ('calculation_time_ms', models.PositiveIntegerField(default=0)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'db_table': 'trending_caches',
            },
        ),
        migrations.CreateModel(
            name='ConnectionCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inner_circle_users', models.JSONField(default=list)),
                ('outer_circle_users', models.JSONField(default=list)),
                ('universe_users', models.JSONField(default=list)),
                ('cache_key', models.CharField(max_length=200)),
                ('total_connections', models.PositiveIntegerField(default=0)),
                ('last_connection_update', models.DateTimeField(blank=True, null=True)),
                ('is_stale', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connection_caches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'connection_caches',
            },
        ),
        migrations.CreateModel(
            name='CacheInvalidationEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cache_type', models.CharField(max_length=30)),
                ('cache_key', models.CharField(blank=True, max_length=250)),
                ('event_type', models.CharField(choices=[('manual', 'Manual Invalidation'), ('expired', 'TTL Expiration'), ('dependency', 'Dependency Change'), ('capacity', 'Cache Capacity Limit'), ('error', 'Error Occurred')], max_length=30)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('reason', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'cache_invalidation_events',
            },
        ),
        # Add constraints
        migrations.AddConstraint(
            model_name='feedcache',
            constraint=models.UniqueConstraint(fields=['user', 'cache_key'], name='unique_feed_cache'),
        ),
        migrations.AddConstraint(
            model_name='trendingcache',
            constraint=models.UniqueConstraint(fields=['content_type', 'time_window'], name='unique_trending_cache'),
        ),
        migrations.AddConstraint(
            model_name='connectioncache',
            constraint=models.UniqueConstraint(fields=['user', 'cache_key'], name='unique_connection_cache'),
        ),
    ]
