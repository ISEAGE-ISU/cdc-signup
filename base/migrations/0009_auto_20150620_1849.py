# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_auto_20150620_1832'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='looking_for_members',
            field=models.BooleanField(default=True, help_text=b'Uncheck if your team is full.'),
        ),
    ]
