# Generated migration for adding deep_link and web_link fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0002_rename_notificatio_created_log_idx_notificatio_created_8b707a_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usernotification',
            name='deep_link',
            field=models.CharField(blank=True, help_text='Deep link for mobile app (e.g., ooumph://post/123)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='web_link',
            field=models.URLField(blank=True, help_text='Web link for browser (e.g., https://app.ooumph.com/post/123)', max_length=500, null=True),
        ),
    ]
