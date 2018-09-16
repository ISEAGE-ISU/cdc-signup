# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0009_auto_20150620_1849'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='enable_green',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='enable_red',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='participant',
            name='is_green',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='participant',
            name='is_red',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='globalsettings',
            name='documentation_url',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
