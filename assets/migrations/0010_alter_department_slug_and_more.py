# Generated by Django 5.0.5 on 2025-01-14 22:12

import autoslug.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0009_alter_department_slug'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, max_length=255, populate_from='name'),
        ),
        migrations.AddConstraint(
            model_name='department',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 'published')), fields=('slug',), name='unique_department_slug_when_published'),
        ),
    ]
