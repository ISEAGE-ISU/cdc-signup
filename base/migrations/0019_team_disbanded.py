# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0018_globalsettings_certificate_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='disbanded',
            field=models.BooleanField(default=False),
        ),
    ]
