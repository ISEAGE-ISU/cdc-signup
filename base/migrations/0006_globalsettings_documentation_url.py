# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_globalsettings_enable_account_creation'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='documentation_url',
            field=models.CharField(max_length=200, null=True),
            preserve_default=True,
        ),
    ]
