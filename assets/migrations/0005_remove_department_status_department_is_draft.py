# Generated by Django 5.0.5 on 2024-09-21 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0004_asset_is_draft_alter_asset_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='department',
            name='status',
        ),
        migrations.AddField(
            model_name='department',
            name='is_draft',
            field=models.BooleanField(default=False),
        ),
    ]
