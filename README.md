cdc-signup
==========

Web app for automating creation and management of CDC accounts.

Designed for Ubuntu 14.04 and Python 2.7

#Installation

##Install dependencies

`apt-get install nginx mysql-server memcached supervisor python-pip python-dev libmysqlclient-dev libldap2-dev libxml2-dev libsasl2-dev libssl-dev`

##Install requirements

`pip install -r requirements.txt`

##Setup supervisor

Copy signup.conf.supervisor to /etc/supervisor/conf.d/signup.conf

Reload and start:

`supervisorctl reload
supervisorctl start signup`

##Setup nginx

Copy signup.conf.nginx to /etc/nginx/conf.d/signup.conf

Unlink default site and reload:

`unlink /etc/nginx/sites-enabled/default
service nginx reload`

