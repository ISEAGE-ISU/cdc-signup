import csv
from io import StringIO

from django.contrib import admin
from django.http import HttpResponse

import base.models as base_models


class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        '__unicode__', 'participant_email', 'team', 'checked_in', 'captain', 'requested_team', 'requests_captain',
        'looking_for_team', 'is_red', 'is_green', 'approved')
    list_filter = (
        'team', 'looking_for_team', 'checked_in', 'captain', 'requested_team', 'is_red', 'is_green', 'approved')
    actions = [
        'get_participant_emails',
        'check_in',
        'undo_check_in',
        'export_csv',
        'mark_lft',
        'unmark_lft',
    ]

    def unmark_lft(self, request, queryset):
        for participant in queryset:
            participant.looking_for_team = False
            participant.save()

    unmark_lft.short_description = "Unmark LFT"

    def mark_lft(self, request, queryset):
        for participant in queryset:
            participant.looking_for_team = True
            participant.save()

    mark_lft.short_description = "Mark LFT"

    def participant_email(self, obj):
        return obj.user.email

    participant_email.short_description = "Email"

    def export_csv(self, request, queryset):
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["Full Name", "Username", "Email", "Team Name", "Captain", "Checked In", "Red", "Green",
                     "R/G Approved"])

        for participant in queryset:
            user = participant.user
            # if not user.is_superuser and participant.team:
            cw.writerow([user.get_full_name(), user.username, user.email, participant.team, participant.captain,
                         participant.checked_in, participant.is_red, participant.is_green, participant.approved])

        return HttpResponse(content=si.getvalue(), content_type="text/plain")

    export_csv.short_name = "Export CSV of Participants"

    def get_participant_emails(self, request, queryset):
        emails = []
        for participant in queryset:
            user = participant.user
            if not user.is_superuser:
                emails.append(user.email + ', ')
        return HttpResponse(content=emails)

    get_participant_emails.short_description = "Get email list"

    def check_in(self, request, queryset):
        for participant in queryset:
            participant.check_in()

    check_in.short_description = "Check in"

    def undo_check_in(self, request, queryset):
        for participant in queryset:
            participant.undo_check_in()

    undo_check_in.short_description = "Undo check in"


class ParticipantInline(admin.TabularInline):
    model = base_models.Participant
    fk_name = 'team'


class TeamAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'looking_for_members', 'team_size', 'disbanded')
    list_filter = ('looking_for_members', 'disbanded')
    inlines = [
        ParticipantInline,
    ]

    def team_size(self, obj):
        return len(obj.members())


class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('subject', 'audience')
    list_filter = ('audience',)
    search_fields = ('subject', 'content')


# Register your models here.
admin.site.register(base_models.Participant, ParticipantAdmin)
admin.site.register(base_models.Team, TeamAdmin)
admin.site.register(base_models.ArchivedEmail, ArchiveAdmin)
