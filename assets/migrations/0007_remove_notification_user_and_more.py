# Generated by Django 5.0.5 on 2025-01-14 14:12

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0006_notification_maintenanceschedule'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='user',
        ),
        migrations.AddField(
            model_name='maintenanceschedule',
            name='next_occurrence',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='maintenanceschedule',
            name='frequency',
            field=models.CharField(choices=[('once', 'Once'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly'), ('quarterly', 'Quarterly')], default='once', max_length=10),
        ),
        migrations.AddIndex(
            model_name='assetactivity',
            index=models.Index(fields=['asset', 'date_time'], name='assets_asse_asset_i_20f934_idx'),
        ),
        migrations.AddIndex(
            model_name='maintenanceschedule',
            index=models.Index(fields=['asset'], name='assets_main_asset_i_51efb5_idx'),
        ),
        migrations.AddIndex(
            model_name='maintenanceschedule',
            index=models.Index(fields=['next_occurrence'], name='assets_main_next_oc_dbd0c8_idx'),
        ),
        migrations.DeleteModel(
            name='Notification',
        ),
    ]
