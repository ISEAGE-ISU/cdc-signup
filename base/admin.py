from django.contrib import admin
import base.models as base_models
from django.http import HttpResponse


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'team', 'checked_in', 'captain', 'requested_team', 'requests_captain')
    actions = [
        'get_participant_emails',
        'check_in',
        'undo_check_in'
    ]

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
    list_display = ('number', 'name')
    inlines = [
        ParticipantInline,
    ]


# Register your models here.
admin.site.register(base_models.Participant, ParticipantAdmin)
admin.site.register(base_models.Team, TeamAdmin)
