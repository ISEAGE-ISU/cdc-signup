from django.contrib.auth import models as auth_models
from django.db import models
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

import actions
from base.utils import AUDIENCE_CHOICES


class GlobalSettings(models.Model):
    number_of_teams = models.IntegerField(default=40)
    administrator_bind_dn = models.CharField(max_length=100)
    administrator_bind_pw = models.CharField(max_length=100)
    check_in_date = models.DateTimeField(null=True)
    documentation_url = models.CharField(max_length=200, blank=True, null=True)
    max_team_size = models.PositiveIntegerField(default=8)

    competition_name = models.CharField(max_length=100, blank=True, null=True)
    competition_date = models.DateTimeField(null=True)

    enable_account_creation = models.BooleanField(default=True)
    enable_red = models.BooleanField(default=True)
    enable_green = models.BooleanField(default=True)


class Team(models.Model):
    number = models.PositiveIntegerField(default=0)
    name = models.CharField(unique=True, max_length=50)
    looking_for_members = models.BooleanField(default=True, help_text="Allow anyone to join your team; uncheck if your team is full.")

    def members(self):
        return Participant.objects.filter(team=self)

    def captains(self):
        return self.members().filter(captain=True)

    def requested_members(self):
        return Participant.objects.filter(requested_team=self)

    def requested_captains(self):
        return self.members().filter(requests_captain=True)

    def member_email_list(self):
        member_emails = []
        for member in self.members():
            member_emails.append(member.user.email)
        return member_emails

    def captain_names(self):
        names = []
        for captain in self.captains():
            name = captain.user.get_full_name()
            names.append(name)
        formatted = ', '.join(names)
        return formatted

    def captain_emails(self):
        emails = ''
        for captain in self.captains():
            if len(emails):
                emails = emails + ', '
            emails = emails + captain.user.email
        return emails

    def is_full(self):
        return len(self.members()) >= actions.get_global_setting('max_team_size')

    def __unicode__(self):
        return "Team {number}: {name}".format(number=self.number, name=self.name)

    class Meta:
        ordering = ['number']


class Participant(models.Model):
    user = models.OneToOneField(auth_models.User)
    team = models.ForeignKey('Team', blank=True, null=True)
    captain = models.BooleanField(default=False)
    requested_team = models.ForeignKey('Team', related_name='requested_team', blank=True, null=True)
    requests_captain = models.BooleanField(default=False)
    checked_in = models.BooleanField(default=False)
    looking_for_team = models.BooleanField(default=False, help_text='ISEAGE will put you on a team')

    # Only used for Red/Green
    is_red = models.BooleanField(default=False)
    is_green = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)

    @property
    def is_redgreen(self):
        return self.is_red or self.is_green

    def check_in(self):
        self.checked_in = True
        self.save(update_fields=['checked_in'])

    def undo_check_in(self):
        self.checked_in = False
        self.save(update_fields=['checked_in'])

    def user_is_captain(self):
        return self.captain or self.user.is_superuser

    def request_team(self, team):
        if not self.team and not self.is_redgreen:
            self.requested_team = team
            self.save(update_fields=['requested_team'])

    def request_promotion(self):
        if not self.requests_captain and not self.is_redgreen:
            self.requests_captain = True
            self.save(update_fields=['requests_captain'])

    def promote(self):
        if not self.captain and not self.is_redgreen:
            self.captain = True
            self.requests_captain = False
            self.save(update_fields=['captain', 'requests_captain'])

    def demote(self):
        if self.captain and not self.is_redgreen:
            self.captain = False
            self.save(update_fields=['captain'])

    def approve(self):
        """
        Approve a Red/Green Member

        Only applies to Red/Green
        """
        if self.is_redgreen:
            self.approved = True
            self.save(update_fields=['approved'])
            actions.approve_user(self)

    def unapprove(self):
        """
        Unapprove a Red/Green Member

        Only applies to Red/Green
        """
        if self.is_redgreen:
            self.approved = False
            self.save(update_fields=['approved'])
            actions.unapprove_user(self)

    def __unicode__(self):
        return "{username} ({name})".format(username=self.user.get_username(), name=self.user.get_full_name())

    class Meta:
        ordering = ['team']


class ArchivedEmail(models.Model):
    subject = models.CharField(max_length=200)
    content = models.TextField()
    audience = models.CharField(max_length=30, choices=AUDIENCE_CHOICES)
    send_time = models.DateTimeField(auto_now_add=True)

    sender = models.ForeignKey(auth_models.User)


########
# Signals
########
@receiver(post_save, sender=GlobalSettings)
def update_settings(sender, instance, **kwargs):
    actions.reset_global_settings_object()


@receiver(post_save, sender=auth_models.User)
def create_participant(sender, instance, **kwargs):
    Participant.objects.get_or_create(user=instance)


@receiver(pre_save, sender=Participant)
def remove_old_ad_group(sender, instance, **kwargs):
    fields = kwargs.get('update_fields', None)
    if fields:
        if not 'team' in fields:
            return

    try:
        current = Participant.objects.get(pk=instance.id)
    except Participant.DoesNotExist:
        return
    team = current.team
    if team:
        user_dn = actions.get_user_dn(instance.id)
        group_dn = actions.get_group_dn(team.id)
        actions.remove_user_from_group(user_dn, group_dn)


@receiver(post_save, sender=Participant)
def add_new_ad_group(sender, instance, **kwargs):
    fields = kwargs.get('update_fields', None)
    if fields:
        if not 'team' in fields:
            return

    team = instance.team
    if team:
        user_dn = actions.get_user_dn(instance.id)
        group_dn = actions.get_group_dn(team.id)
        actions.add_user_to_group(user_dn, group_dn)


@receiver(pre_delete, sender=Team)
def remove_members(sender, instance, **kwargs):
    rc = instance.requested_captains()
    for member in rc:
        member.requests_captain = False
        member.save(update_fields=['requests_captain'])
    r = instance.requested_members()
    for participant in r:
        participant.requested_team = None
        participant.save(update_fields=['requested_team'])
    m = instance.members()
    for member in m:
        member.team = None
        member.captain = False
        member.save()
