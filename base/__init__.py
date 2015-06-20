import actions
from django.conf import settings
from django import template as dt
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
    reset_global_settings_object()
    return True


def reset_global_settings_object():
    gs = actions.get_global_settings_object()
    cache.set(GLOBAL_SETTINGS_OBJECT, gs)
    return gs

def render_template(request, template, context=None):
    if not context: context = {}
    if request is not None:
        ctx = dt.RequestContext(request, context)
    else:
        ctx = dt.Context(context)
    return dt.loader.get_template(template).render(ctx)


def fetch_objects(objects):
    list = []
    for object in objects:
        list.append(object)
    return list

##########
# Exceptions
##########
class DuplicateName(Exception):
    pass


class UsernameAlreadyExistsError(Exception):
    pass


class OutOfTeamNumbersError(Exception):
    pass


class TeamAlreadyExistsError(Exception):
    pass


class PasswordMismatchError(Exception):
    pass


class OnlyRemainingCaptainError(Exception):
    pass
