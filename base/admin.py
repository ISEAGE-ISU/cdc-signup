from django.contrib import admin
import base.models as base_models
from django.http import HttpResponse


class ParticipantAdmin(admin.ModelAdmin):
    actions = ['get_participant_emails']

    def get_participant_emails(self, request, queryset):
        emails = []
        for participant in queryset:
            user = participant.user
            if not user.is_superuser:
                emails.append(user.email + ', ')
        return HttpResponse(content=emails)

    get_participant_emails.short_description = "Get email list"


class ParticipantInline(admin.TabularInline):
    model = base_models.Participant
    fk_name = 'team'


class TeamAdmin(admin.ModelAdmin):
    inlines = [
        ParticipantInline,
    ]


# Register your models here.
admin.site.register(base_models.Participant, ParticipantAdmin)
admin.site.register(base_models.Team, TeamAdmin)
admin.site.register(base_models.GlobalSettings)