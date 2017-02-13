# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0018_globalsettings_certificate_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='rules_version',
            field=models.CharField(max_length=40, null=True, blank=True),
        ),
    ]
