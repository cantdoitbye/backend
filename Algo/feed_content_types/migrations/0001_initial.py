# Generated manually for feed_content_types

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
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('share_count', models.PositiveIntegerField(default=0)),
                ('comment_count', models.PositiveIntegerField(default=0)),
                ('engagement_score', models.FloatField(default=0.0)),
                ('quality_score', models.FloatField(default=0.0)),
                ('trending_score', models.FloatField(default=0.0)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('content', models.TextField()),
                ('image_urls', models.JSONField(blank=True, default=list)),
                ('video_url', models.URLField(blank=True)),
                ('post_type', models.CharField(choices=[('text', 'Text Only'), ('image', 'Image Post'), ('video', 'Video Post'), ('link', 'Link Share'), ('poll', 'Poll')], default='text', max_length=20)),
                ('visibility', models.CharField(choices=[('public', 'Public'), ('friends', 'Friends'), ('private', 'Private')], default='public', max_length=10)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('coordinates', models.JSONField(blank=True, null=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'posts',
            },
        ),
        migrations.CreateModel(
            name='Community',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('share_count', models.PositiveIntegerField(default=0)),
                ('comment_count', models.PositiveIntegerField(default=0)),
                ('engagement_score', models.FloatField(default=0.0)),
                ('quality_score', models.FloatField(default=0.0)),
                ('trending_score', models.FloatField(default=0.0)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('category', models.CharField(choices=[('technology', 'Technology'), ('entertainment', 'Entertainment'), ('sports', 'Sports'), ('lifestyle', 'Lifestyle'), ('business', 'Business'), ('education', 'Education'), ('health', 'Health'), ('other', 'Other')], max_length=50)),
                ('is_private', models.BooleanField(default=False)),
                ('requires_approval', models.BooleanField(default=False)),
                ('member_count', models.PositiveIntegerField(default=0)),
                ('max_members', models.PositiveIntegerField(blank=True, null=True)),
                ('rules', models.TextField(blank=True)),
                ('welcome_message', models.TextField(blank=True)),
                ('avatar_url', models.URLField(blank=True)),
                ('banner_url', models.URLField(blank=True)),
                ('theme_color', models.CharField(blank=True, max_length=7)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'communities',
                'verbose_name_plural': 'Communities',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('share_count', models.PositiveIntegerField(default=0)),
                ('comment_count', models.PositiveIntegerField(default=0)),
                ('engagement_score', models.FloatField(default=0.0)),
                ('quality_score', models.FloatField(default=0.0)),
                ('trending_score', models.FloatField(default=0.0)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('brand', models.CharField(blank=True, max_length=100)),
                ('model', models.CharField(blank=True, max_length=100)),
                ('sku', models.CharField(blank=True, max_length=50)),
                ('stock_quantity', models.PositiveIntegerField(default=0)),
                ('is_in_stock', models.BooleanField(default=True)),
                ('primary_image_url', models.URLField(blank=True)),
                ('gallery_urls', models.JSONField(blank=True, default=list)),
                ('category', models.CharField(choices=[('electronics', 'Electronics'), ('clothing', 'Clothing'), ('home', 'Home & Garden'), ('sports', 'Sports & Outdoors'), ('books', 'Books'), ('health', 'Health & Beauty'), ('toys', 'Toys & Games'), ('automotive', 'Automotive'), ('other', 'Other')], max_length=50)),
                ('attributes', models.JSONField(blank=True, default=dict)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_created', to=settings.AUTH_USER_MODEL)),
                ('seller', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products_sold', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'products',
            },
        ),
        migrations.CreateModel(
            name='Engagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('engagement_type', models.CharField(choices=[('view', 'View'), ('like', 'Like'), ('dislike', 'Dislike'), ('share', 'Share'), ('comment', 'Comment'), ('bookmark', 'Bookmark'), ('report', 'Report')], max_length=20)),
                ('source', models.CharField(choices=[('feed', 'Feed'), ('search', 'Search'), ('profile', 'Profile'), ('trending', 'Trending'), ('notification', 'Notification'), ('direct', 'Direct Link')], default='feed', max_length=30)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('session_id', models.CharField(blank=True, max_length=100)),
                ('device_type', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='engagements', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'engagements',
            },
        ),
        migrations.CreateModel(
            name='CommunityMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('member', 'Member'), ('moderator', 'Moderator'), ('admin', 'Admin'), ('owner', 'Owner')], default='member', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('pending', 'Pending Approval'), ('suspended', 'Suspended'), ('banned', 'Banned')], default='active', max_length=15)),
                ('post_count', models.PositiveIntegerField(default=0)),
                ('last_active', models.DateTimeField(blank=True, null=True)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('community', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='feed_content_types.community')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'community_memberships',
            },
        ),
        # Add indexes and constraints
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['creator', 'created_at'], name='posts_creator_created_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['engagement_score'], name='posts_engagement_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['post_type', 'created_at'], name='posts_type_created_idx'),
        ),
        migrations.AddConstraint(
            model_name='engagement',
            constraint=models.UniqueConstraint(fields=['user', 'content_type', 'object_id', 'engagement_type'], name='unique_engagement'),
        ),
        migrations.AddConstraint(
            model_name='communitymembership',
            constraint=models.UniqueConstraint(fields=['community', 'user'], name='unique_community_membership'),
        ),
    ]
