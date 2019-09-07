# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-08-28 21:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0025_auto_20190828_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalsettings',
            name='documentation_url',
            field=models.URLField(blank=True, help_text=b'Where blue teams can go to see their documentation. Usually a Google Drive folder.', null=True),
        ),
    ]