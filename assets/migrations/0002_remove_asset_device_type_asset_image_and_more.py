# Generated by Django 5.0.5 on 2024-09-19 16:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='device_type',
        ),
        migrations.AddField(
            model_name='asset',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='assets/'),
        ),
        migrations.AddField(
            model_name='department',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('published', 'Published')], default='draft', max_length=20),
        ),
        migrations.AlterField(
            model_name='asset',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('repair', 'Under Maintenance'), ('decommissioned', 'Decommissioned'), ('draft', 'Draft')], default='draft', max_length=20),
        ),
        migrations.CreateModel(
            name='ActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(help_text='The type of action performed.', max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True, help_text='The time the action was logged.')),
                ('changes', models.TextField(help_text='A detailed description of what was changed.')),
                ('reason', models.TextField(blank=True, help_text='The reason for the change.')),
                ('asset', models.ForeignKey(help_text='The asset that the action was performed on.', on_delete=django.db.models.deletion.CASCADE, related_name='action_logs', to='assets.asset')),
                ('performed_by', models.ForeignKey(help_text='The user who performed the action.', on_delete=django.db.models.deletion.CASCADE, related_name='action_logs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='MaintenanceReport',
        ),
    ]