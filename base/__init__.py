import models
from signup import settings
from django.template import RequestContext
from django.core.cache import cache
from django.contrib.auth.models import User

GLOBAL_SETTINGS_OBJECT = 'GLOBAL_SETTINGS_OBJECT'

def get_context(request):
    context = {}
    context['current_url_full'] = request.get_full_path()
    request.session.__setitem__('ip_addr', request.META.get('HTTP_X_FORWARDED_FOR'))
    request.session.__setitem__('recent_path', request.META.get('PATH_INFO'))
    if request.user:
        context['user'] = request.user
        if isinstance(request.user, User):
            obj, created = models.Participant.objects.get_or_create(user=request.user)
            context['participant'] = obj

    r_ctx = RequestContext(request, context)
    return r_ctx


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
