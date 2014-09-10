# Don't actually send emails, just dump them to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SESSION_COOKIE_SECURE = False

AD_DEBUG = True
AD_LDAP_DEBUG_LEVEL = 2

DEBUG = True
TEMPLATE_DEBUG = True

AD_CDCUSER_OU = 'SignupTest'
AD_CDCUSER_GROUP = 'Test CDC Users'

AD_BLUE_TEAM_PREFIX = "Test Team "
AD_BLUE_TEAM_FORMAT = AD_BLUE_TEAM_PREFIX + "{number}"
