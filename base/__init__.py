import models
from signup import settings
from django.core.cache import cache

GLOBAL_SETTINGS_OBJECT = 'GLOBAL_SETTINGS_OBJECT'


def get_global_settings_object():
    gs = cache.get(GLOBAL_SETTINGS_OBJECT)
    if not gs:
        gs = reset_global_settings_object()
    return gs


def get_global_setting(setting_name):
    gs = get_global_settings_object()
    gs_result = getattr(gs, setting_name)
    if gs_result:
        return gs_result
    elif hasattr(settings, setting_name):
        return getattr(settings, setting_name)
    else:
        return None


def set_global_setting(setting_name, value):
    gs = get_global_settings_object()
    try:
        setattr(gs, setting_name, value)
        gs.save()
    except Exception as e:
        return False
    #Reassign object in memcache
    cache.set(GLOBAL_SETTINGS_OBJECT, models.GlobalSettings.objects.get_or_create(id__exact=1)[0])
    return True


def reset_global_settings_object():
    gs = models.GlobalSettings.objects.get_or_create(id__exact=1)[0]
    cache.set(GLOBAL_SETTINGS_OBJECT, gs)
    return gs

##########
# Exceptions
##########
class UsernameAlreadyExistsError(Exception):
    pass


class OutOfTeamNumbersError(Exception):
    pass


class TeamAlreadyExistsError(Exception):
    pass

class PasswordMismatchError(Exception):
    pass