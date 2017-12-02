# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_participant_requests_captain'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='participant',
            options={'ordering': ['team']},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ['number']},
        ),
        migrations.AddField(
            model_name='participant',
            name='checked_in',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
