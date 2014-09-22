# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_auto_20140922_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='check_in_date',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
    ]
