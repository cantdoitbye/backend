# Generated manually for scoring_engines

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScoringAlgorithm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('algorithm_type', models.CharField(choices=[('personal_connections', 'Personal Connections'), ('interest_based', 'Interest Based'), ('trending', 'Trending Content'), ('discovery', 'Discovery'), ('community', 'Community Based'), ('product', 'Product Recommendation')], max_length=30)),
                ('config', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('last_executed', models.DateTimeField(blank=True, null=True)),
                ('execution_count', models.PositiveIntegerField(default=0)),
                ('average_execution_time_ms', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'scoring_algorithms',
            },
        ),
        migrations.CreateModel(
            name='PersonalConnectionsScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_object_id', models.PositiveIntegerField()),
                ('inner_circle_score', models.FloatField(default=0.0)),
                ('outer_circle_score', models.FloatField(default=0.0)),
                ('universe_score', models.FloatField(default=0.0)),
                ('total_score', models.FloatField(default=0.0)),
                ('connection_count', models.PositiveIntegerField(default=0)),
                ('calculation_method', models.CharField(blank=True, max_length=50)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('target_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connection_scores', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'personal_connections_scores',
            },
        ),
        migrations.CreateModel(
            name='InterestBasedScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_object_id', models.PositiveIntegerField()),
                ('explicit_interests_score', models.FloatField(default=0.0)),
                ('inferred_interests_score', models.FloatField(default=0.0)),
                ('behavioral_interests_score', models.FloatField(default=0.0)),
                ('total_score', models.FloatField(default=0.0)),
                ('matched_interests', models.JSONField(default=list)),
                ('interest_strength_avg', models.FloatField(default=0.0)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('target_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interest_scores', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'interest_based_scores',
            },
        ),
        migrations.CreateModel(
            name='TrendingScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('velocity_score', models.FloatField(default=0.0)),
                ('viral_coefficient', models.FloatField(default=0.0)),
                ('engagement_velocity', models.FloatField(default=0.0)),
                ('time_decay_factor', models.FloatField(default=1.0)),
                ('total_score', models.FloatField(default=0.0)),
                ('window_hours', models.PositiveIntegerField(default=24)),
                ('engagement_count', models.PositiveIntegerField(default=0)),
                ('unique_users', models.PositiveIntegerField(default=0)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'db_table': 'trending_scores',
            },
        ),
        migrations.CreateModel(
            name='DiscoveryScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_object_id', models.PositiveIntegerField()),
                ('collaborative_filtering_score', models.FloatField(default=0.0)),
                ('serendipity_score', models.FloatField(default=0.0)),
                ('diversity_score', models.FloatField(default=0.0)),
                ('novelty_score', models.FloatField(default=0.0)),
                ('total_score', models.FloatField(default=0.0)),
                ('similar_users', models.JSONField(default=list)),
                ('recommendation_reason', models.CharField(blank=True, max_length=100)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('target_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discovery_scores', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'discovery_scores',
            },
        ),
        migrations.CreateModel(
            name='ScoringWeight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('weight_value', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)])),
                ('scope', models.CharField(choices=[('global', 'Global'), ('content_type', 'Content Type Specific'), ('user_segment', 'User Segment Specific'), ('experimental', 'A/B Testing')], default='global', max_length=20)),
                ('config', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('version', models.CharField(default='1.0', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'scoring_weights',
            },
        ),
        migrations.CreateModel(
            name='ScoreAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('event_type', models.CharField(choices=[('score_calculated', 'Score Calculated'), ('weight_changed', 'Weight Changed'), ('algorithm_updated', 'Algorithm Updated'), ('cache_cleared', 'Cache Cleared'), ('performance_issue', 'Performance Issue')], max_length=30)),
                ('event_data', models.JSONField(default=dict)),
                ('execution_time_ms', models.FloatField(blank=True, null=True)),
                ('session_id', models.CharField(blank=True, max_length=100)),
                ('request_id', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'score_audit_logs',
            },
        ),
        # Add constraints
        migrations.AddConstraint(
            model_name='personalconnectionsscore',
            constraint=models.UniqueConstraint(fields=['user', 'target_content_type', 'target_object_id'], name='unique_personal_connections_score'),
        ),
        migrations.AddConstraint(
            model_name='interestbasedscore',
            constraint=models.UniqueConstraint(fields=['user', 'target_content_type', 'target_object_id'], name='unique_interest_based_score'),
        ),
        migrations.AddConstraint(
            model_name='trendingscore',
            constraint=models.UniqueConstraint(fields=['content_type', 'object_id', 'window_hours'], name='unique_trending_score'),
        ),
        migrations.AddConstraint(
            model_name='discoveryscore',
            constraint=models.UniqueConstraint(fields=['user', 'target_content_type', 'target_object_id'], name='unique_discovery_score'),
        ),
    ]
