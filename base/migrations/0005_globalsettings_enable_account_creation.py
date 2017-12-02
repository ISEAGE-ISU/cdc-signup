# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_globalsettings_check_in_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='enable_account_creation',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
