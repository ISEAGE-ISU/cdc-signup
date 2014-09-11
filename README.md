cdc-signup
==========

Web app for automating creation and management of CDC accounts.

Designed for Ubuntu 14.04 and Python 2.7

#Installation#

##Install dependencies##

```bash
apt-get install nginx mysql-server memcached supervisor python-pip python-dev libmysqlclient-dev libldap2-dev libxml2-dev libsasl2-dev libssl-dev
```

Note: for development purposes you may omit nginx, memcached, and supervisor and just use python manage.py runserver instead

##Install requirements##

```bash
pip install -r requirements.txt
```

##Local settings##

###Production###
Copy signup/local_settings_prod.py to signup/local_settings.py and set a random database password and secret key

###Development###
Copy signup/local_settings_dev.py to signup/local_settings.py

##Sync Database##

```bash
python manage.py syncdb
```

##Setup supervisor##

Copy signup.conf.supervisor to /etc/supervisor/conf.d/signup.conf

Reload and start:

```bash
supervisorctl reload
supervisorctl start signup
```

##Setup nginx##

Copy signup.conf.nginx to /etc/nginx/conf.d/signup.conf

Unlink default site and reload:

```bash
unlink /etc/nginx/sites-enabled/default
service nginx reload
```

