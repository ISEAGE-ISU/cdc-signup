# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0020_globalsettings_competition_prefix'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalsettings',
            name='competition_prefix',
            field=models.CharField(max_length=15, null=True, blank=True),
        ),
    ]
