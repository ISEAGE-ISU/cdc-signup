# Example local setting overrides for production

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'signup',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'signup',
        'PASSWORD': 'some-long-random-string',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

SECRET_KEY = 'another-long-random-string'

