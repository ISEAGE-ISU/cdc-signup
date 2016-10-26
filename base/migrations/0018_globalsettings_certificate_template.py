# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0017_archivedemail_sender'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='certificate_template',
            field=models.FileField(null=True, upload_to=b'', blank=True),
        ),
    ]
