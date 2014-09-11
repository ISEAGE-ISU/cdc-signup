from django.db import models
from django.contrib.auth import models as auth_models
from django.db.models.signals import post_save
from django.dispatch import receiver


########
# Signal for automatically making Participant objects
########
@receiver(post_save, sender=auth_models.User)
def create_participant(sender, instance, **kwargs):
    Participant.objects.get_or_create(user=instance)


class GlobalSettings(models.Model):
    number_of_teams = models.IntegerField(default=40)
    administrator_bind_dn = models.CharField(max_length=100)
    administrator_bind_pw = models.CharField(max_length=100)


class Team(models.Model):
    number = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=50)

    def members(self):
        return Participant.objects.filter(team=self)

    def captains(self):
        return self.members().filter(captain=True)

    def requested_members(self):
        return Participant.objects.filter(requested_team=self)

    def requested_captains(self):
        return self.members().filter(requests_captain=True)

    def delete_and_members(self):
        rc = self.requested_captains()
        for member in rc:
            member.requests_captain = False
            member.save()
        r = self.requested_members()
        for participant in r:
            participant.requested_team = None
            participant.save()
        m = self.members()
        for member in m:
            member.team = None
            member.captain = False
            member.save()
        self.delete()

    def __unicode__(self):
        return "Team {number}: {name}".format(number=self.number, name=self.name)


class Participant(models.Model):
    user = models.OneToOneField(auth_models.User)
    team = models.ForeignKey('Team', blank=True, null=True)
    captain = models.BooleanField(default=False)
    requested_team = models.ForeignKey('Team', related_name='requested_team', blank=True, null=True)
    requests_captain = models.BooleanField(default=False)

    def user_is_captain(self):
        return self.captain or self.user.is_superuser

    def __unicode__(self):
        return "{username} ({name})".format(username=self.user.get_username(), name=self.user.get_full_name())
