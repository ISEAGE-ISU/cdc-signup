import os

# Django settings for signup project.
SITE_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
URL_ROOT = '/'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'signup',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'signup',
        'PASSWORD': 'signuppass',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'static/upload/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = URL_ROOT + 'static/upload/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT,"static/"),
    os.path.join(SITE_ROOT,"static/media/"),
    os.path.join(SITE_ROOT,"static/font/"),
    os.path.join(SITE_ROOT,"static/img/"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'mfhb+)!0n$wx8^5!)d!w-^i10pbwh)$kt3u7n3&5+w0epd&(9o'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.core.context_processors.csrf",
    "django.contrib.messages.context_processors.messages",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'signup.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'signup.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'base',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
)

LOGIN_URL = URL_ROOT + 'login/'
LOGOUT_URL = URL_ROOT + 'logout/'
LOGIN_REDIRECT_URL = URL_ROOT
SESSION_SAVE_EVERY_REQUEST = True  # http://stackoverflow.com/questions/1366146/django-session-expiry
SESSION_COOKIE_AGE = 60 * 60  # age in seconds
#SESSION_COOKIE_SECURE = True
DEFAULT_NEXT_URL = "/"

##############
# Email
##############
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'mailhub.iastate.edu'
EMAIL_PORT = 25

# Where people should ask for help
SUPPORT_EMAIL = 'cdc_support@iastate.edu'
# What will appear in the From field of emails
EMAIL_FROM_ADDR = SUPPORT_EMAIL


##############
# Caching
##############
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}


##############
# Active Directory Settings
##############
AD_DNS_NAME = "dc1.iseage.org"  # FQDN of your DC
AD_LDAP_PORT=636
AD_LDAP_URL='ldaps://%s:%s' % (AD_DNS_NAME,AD_LDAP_PORT)

AD_CDCUSER_OU = 'CDCUsers'
AD_CDCUSER_GROUP = 'CDCUsers'

AD_BLUE_TEAM_PREFIX = "CDC Team "
AD_BLUE_TEAM_FORMAT = AD_BLUE_TEAM_PREFIX + "{number}"

AD_BASE_DN = 'DC=iseage,DC=org'
AD_DOMAIN = 'iseage.org'
AD_NT4_DOMAIN = 'ISEAGE'
AD_SEARCH_FIELDS = ['mail','givenName','sn','sAMAccountName','memberOf']
AD_MEMBERSHIP_ADMIN = ['Domain Admins']  # this ad group gets superuser status in django
AD_MEMBERSHIP_REQ = AD_MEMBERSHIP_ADMIN + [AD_CDCUSER_GROUP]  # only members of these groups can access
AD_CERT_FILE = False  # this is the certificate of the Certificate Authority issuing your DCs certificate
AD_DEBUG = False
AD_LDAP_DEBUG_LEVEL = 2
AD_DEBUG_FILE = '/var/log/signup/ldap.debug'

AUTHENTICATION_BACKENDS = (
    'signup.auth.ActiveDirectoryAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend'
)


SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# Logging
# Log everything to console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level':'INFO',
            'class':'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

try:
    from local_settings import *
except ImportError:
    pass
