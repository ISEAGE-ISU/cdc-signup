# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0014_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='competition_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='competition_name',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
