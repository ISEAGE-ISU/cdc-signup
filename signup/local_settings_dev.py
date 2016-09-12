# Don't actually send emails, just dump them to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SESSION_COOKIE_SECURE = False

AD_DEBUG = True
AD_LDAP_DEBUG_LEVEL = 2

DEBUG = True
TEMPLATE_DEBUG = True

AD_CDCUSER_OU = 'SignupTest'
AD_CDCUSER_GROUP = 'Test CDC Users'

AD_RED_OU = 'RedTest'
AD_RED_GROUP = 'RedTest'
AD_RED_PENDING = 'RedPendingTest'

AD_GREEN_OU = 'GreenTest'
AD_GREEN_GROUP = 'GreenTest'
AD_GREEN_PENDING = 'GreenPendingTest'

AD_BLUE_TEAM_PREFIX = "Test Team "
AD_BLUE_TEAM_FORMAT = AD_BLUE_TEAM_PREFIX + "{number}"
AD_MEMBERSHIP_ADMIN = ['Domain Admins']  # this ad group gets superuser status in django
AD_MEMBERSHIP_REQ = AD_MEMBERSHIP_ADMIN + [AD_CDCUSER_GROUP, AD_RED_GROUP, AD_RED_PENDING,
         AD_GREEN_GROUP, AD_GREEN_PENDING]  # only members of these groups can access
