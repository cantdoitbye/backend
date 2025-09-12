# Generated manually for feed_algorithm

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Interest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(blank=True, max_length=50)),
                ('is_trending', models.BooleanField(default=False)),
                ('popularity_score', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'interests',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feed_enabled', models.BooleanField(default=True)),
                ('content_language', models.CharField(default='en', max_length=10)),
                ('total_engagement_score', models.FloatField(default=0.0)),
                ('last_active', models.DateTimeField(auto_now=True)),
                ('privacy_level', models.CharField(choices=[('public', 'Public'), ('friends', 'Friends Only'), ('private', 'Private')], default='public', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_profiles',
            },
        ),
        migrations.CreateModel(
            name='TrendingMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(max_length=50)),
                ('content_id', models.PositiveIntegerField()),
                ('velocity_score', models.FloatField(default=0.0)),
                ('viral_coefficient', models.FloatField(default=0.0)),
                ('engagement_rate', models.FloatField(default=0.0)),
                ('trending_window', models.CharField(choices=[('1h', '1 Hour'), ('6h', '6 Hours'), ('24h', '24 Hours'), ('7d', '7 Days')], default='24h', max_length=10)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
            ],
            options={
                'db_table': 'trending_metrics',
            },
        ),
        migrations.CreateModel(
            name='InterestCollection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strength', models.FloatField(default=0.5, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('source', models.CharField(choices=[('explicit', 'User Selected'), ('inferred', 'AI Inferred'), ('behavioral', 'Behavioral Analysis')], default='explicit', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('interest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feed_algorithm.interest')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_interests',
            },
        ),
        migrations.CreateModel(
            name='FeedDebugEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('feed_generated', 'Feed Generated'), ('composition_changed', 'Composition Changed'), ('ab_test_assigned', 'A/B Test Assigned'), ('cache_hit', 'Cache Hit'), ('cache_miss', 'Cache Miss')], max_length=30)),
                ('event_data', models.JSONField(default=dict)),
                ('generation_time_ms', models.PositiveIntegerField(blank=True, null=True)),
                ('request_id', models.CharField(blank=True, max_length=100)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debug_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'feed_debug_events',
            },
        ),
        migrations.CreateModel(
            name='FeedComposition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('personal_connections', models.FloatField(default=0.4, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('interest_based', models.FloatField(default=0.25, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('trending_content', models.FloatField(default=0.15, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('discovery_content', models.FloatField(default=0.1, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('community_content', models.FloatField(default=0.05, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('product_content', models.FloatField(default=0.05, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('experiment_group', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='feed_composition', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'feed_compositions',
            },
        ),
        migrations.CreateModel(
            name='CreatorMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('overall_reputation', models.FloatField(default=0.0)),
                ('content_quality_score', models.FloatField(default=0.0)),
                ('engagement_rate', models.FloatField(default=0.0)),
                ('follower_growth_rate', models.FloatField(default=0.0)),
                ('total_posts', models.PositiveIntegerField(default=0)),
                ('total_engagements', models.PositiveIntegerField(default=0)),
                ('total_shares', models.PositiveIntegerField(default=0)),
                ('last_calculated', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='creator_metrics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'creator_metrics',
            },
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('circle_type', models.CharField(choices=[('inner', 'Inner Circle'), ('outer', 'Outer Circle'), ('universe', 'Universe')], default='universe', max_length=10)),
                ('interaction_count', models.PositiveIntegerField(default=0)),
                ('last_interaction', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connections_from', to=settings.AUTH_USER_MODEL)),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connections_to', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'connections',
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='interest',
            index=models.Index(fields=['category'], name='interests_categor_9c889e_idx'),
        ),
        migrations.AddIndex(
            model_name='interest',
            index=models.Index(fields=['popularity_score'], name='interests_popular_3dc5ec_idx'),
        ),
        migrations.AddIndex(
            model_name='interest',
            index=models.Index(fields=['is_trending'], name='interests_is_tren_ebb416_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['last_active'], name='user_profil_last_ac_f0c215_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['total_engagement_score'], name='user_profil_total_e_e2a3db_idx'),
        ),
        migrations.AddIndex(
            model_name='connection',
            index=models.Index(fields=['from_user', 'circle_type'], name='connection_from_us_ab1234_idx'),
        ),
        migrations.AddIndex(
            model_name='connection',
            index=models.Index(fields=['to_user', 'circle_type'], name='connection_to_user_cd5678_idx'),
        ),
        # Add unique constraints
        migrations.AddConstraint(
            model_name='connection',
            constraint=models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_connection'),
        ),
        migrations.AddConstraint(
            model_name='interestcollection',
            constraint=models.UniqueConstraint(fields=['user', 'interest'], name='unique_user_interest'),
        ),
        migrations.AddConstraint(
            model_name='trendingmetric',
            constraint=models.UniqueConstraint(fields=['content_type', 'content_id', 'trending_window'], name='unique_trending_metric'),
        ),
    ]
