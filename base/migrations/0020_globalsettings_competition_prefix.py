# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0019_globalsettings_rules_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='competition_prefix',
            field=models.CharField(max_length=6, null=True, blank=True),
        ),
    ]
