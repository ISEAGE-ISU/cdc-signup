from django.contrib import admin
import base.models as base_models

# Register your models here.
admin.site.register(base_models.Participant)
admin.site.register(base_models.Team)
admin.site.register(base_models.GlobalSettings)