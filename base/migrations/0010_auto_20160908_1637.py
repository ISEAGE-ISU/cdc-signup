# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0009_auto_20150620_1849'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='looking_for_team',
            field=models.BooleanField(default=True, help_text=b'ISEAGE will put you on a team'),
        ),
        migrations.AlterField(
            model_name='globalsettings',
            name='documentation_url',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
