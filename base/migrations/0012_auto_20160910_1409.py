# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_auto_20160908_1707'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='max_team_size',
            field=models.PositiveIntegerField(default=8),
        ),
        migrations.AlterField(
            model_name='participant',
            name='looking_for_team',
            field=models.BooleanField(default=True, help_text=b'ISEAGE will put you on a team'),
        ),
    ]
