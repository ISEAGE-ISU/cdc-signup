# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0012_auto_20160910_1409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='looking_for_team',
            field=models.BooleanField(default=False, help_text=b'ISEAGE will put you on a team'),
        ),
        migrations.AlterField(
            model_name='team',
            name='looking_for_members',
            field=models.BooleanField(default=True, help_text=b'Allow anyone to join your team; uncheck if your team is full.'),
        ),
    ]
