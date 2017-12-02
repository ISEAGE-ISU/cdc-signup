# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0022_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archivedemail',
            name='audience',
            field=models.CharField(max_length=30, choices=[(b'with_team', b'Participants with a team'), (b'no_team', b'Participants without a team'), (b'all', b'Blue Team Participants (All)'), (b'red_team_all', b'Red Team Members (All)'), (b'red_team_approved', b'Red Team Members (Approved)'), (b'green_team_all', b'Green Team Members (All)'), (b'green_team_approved', b'Green Team Members (Approved)'), (b'everyone', b'Everyone')]),
        ),
    ]
