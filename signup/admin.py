from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from base import models as base_models


class ParticipantInline(admin.StackedInline):
    model = base_models.Participant
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    list_select_related = True
    list_display = ('username', 'email', 'first_name', 'last_name', 'participant_object', 'is_superuser')
    inlines = [
        ParticipantInline,
    ]

    def participant_object(self, user):
        return user.participant

    participant_object.admin_order_field = 'participant__id'
