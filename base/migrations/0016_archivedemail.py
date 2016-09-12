# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0015_auto_20160912_1722'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivedEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('audience', models.CharField(max_length=30, choices=[(b'all', b'All (Blue) participants'), (b'with_team', b'Participants with a team'), (b'no_team', b'Participants without a team'), (b'red_team_all', b'Red Team Members (All)'), (b'red_team_approved', b'Red Team Members (Approved)'), (b'green_team_all', b'Green Team Members (All)'), (b'green_team_approved', b'Green Team Members (Approved)'), (b'everyone', b'Everyone')])),
                ('send_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
