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



# Register your models here.
admin.site.register(base_models.Participant, ParticipantAdmin)
admin.site.register(base_models.Team)
admin.site.register(base_models.GlobalSettings)