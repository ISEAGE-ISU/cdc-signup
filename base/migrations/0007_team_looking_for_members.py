# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_globalsettings_documentation_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='looking_for_members',
            field=models.BooleanField(default=True),
        ),
    ]
