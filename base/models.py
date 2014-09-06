from django.db import models
from django.contrib.auth import models as auth_models


class GlobalSettings(models.Model):
    number_of_teams = models.IntegerField(default=40)
    administrator_bind_dn = models.CharField(max_length=100)
    administrator_bind_pw = models.CharField(max_length=100)


class Team(models.Model):
    number = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "Team {number}: {name}".format(number=self.number, name=self.name)


class Participant(models.Model):
    user = models.OneToOneField(auth_models.User)
    team = models.ForeignKey('Team', blank=True)
    captain = models.BooleanField(default=False)
    requested_team = models.ForeignKey('Team', related_name='requested_team',blank=True)

    def __unicode__(self):
        return "{username} ({name})".format(username=self.user.get_username(), name=self.user.get_full_name())