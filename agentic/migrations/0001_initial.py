# Generated Django migration for agentic models

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AgentActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_uid', models.CharField(db_index=True, max_length=255)),
                ('community_uid', models.CharField(db_index=True, max_length=255)),
                ('action_type', models.CharField(db_index=True, max_length=100)),
                ('action_details', models.JSONField()),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('success', models.BooleanField()),
                ('error_message', models.TextField(blank=True, null=True)),
                ('execution_time_ms', models.IntegerField(blank=True, null=True)),
                ('user_context', models.JSONField(blank=True, null=True)),
            ],
            options={
                'db_table': 'agentic_agentactionlog',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='AgentMemory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_uid', models.CharField(db_index=True, max_length=255)),
                ('community_uid', models.CharField(db_index=True, max_length=255)),
                ('memory_type', models.CharField(choices=[('context', 'Context'), ('conversation', 'Conversation'), ('knowledge', 'Knowledge'), ('preferences', 'Preferences')], db_index=True, max_length=50)),
                ('content', models.JSONField()),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('priority', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'agentic_agentmemory',
                'ordering': ['-updated_date'],
            },
        ),
        migrations.AddIndex(
            model_name='agentactionlog',
            index=models.Index(fields=['agent_uid', 'timestamp'], name='agentic_age_agent_u_b8e5a4_idx'),
        ),
        migrations.AddIndex(
            model_name='agentactionlog',
            index=models.Index(fields=['community_uid', 'timestamp'], name='agentic_age_communi_4c8b9a_idx'),
        ),
        migrations.AddIndex(
            model_name='agentactionlog',
            index=models.Index(fields=['action_type', 'timestamp'], name='agentic_age_action__7f2c1d_idx'),
        ),
        migrations.AddIndex(
            model_name='agentactionlog',
            index=models.Index(fields=['success', 'timestamp'], name='agentic_age_success_8a9e2f_idx'),
        ),
        migrations.AddIndex(
            model_name='agentmemory',
            index=models.Index(fields=['agent_uid', 'community_uid'], name='agentic_age_agent_u_c5d7e8_idx'),
        ),
        migrations.AddIndex(
            model_name='agentmemory',
            index=models.Index(fields=['memory_type', 'updated_date'], name='agentic_age_memory__9f3a1b_idx'),
        ),
        migrations.AddIndex(
            model_name='agentmemory',
            index=models.Index(fields=['expires_at'], name='agentic_age_expires_2e4b6c_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='agentmemory',
            unique_together={('agent_uid', 'community_uid', 'memory_type')},
        ),
    ]