# Generated by Django 5.0.5 on 2025-01-14 18:25

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0008_alter_department_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, max_length=255, populate_from='name', unique=True),
        ),
    ]