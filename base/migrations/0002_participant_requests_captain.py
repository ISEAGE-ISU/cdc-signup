# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='requests_captain',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
