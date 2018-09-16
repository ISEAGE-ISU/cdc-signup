# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0010_auto_20160908_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='looking_for_team',
            field=models.BooleanField(default=False, help_text=b'ISEAGE will put you on a team'),
        ),
    ]
