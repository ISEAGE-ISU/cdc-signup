# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0010_auto_20160503_2317'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='approved',
            field=models.BooleanField(default=False),
        ),
    ]
