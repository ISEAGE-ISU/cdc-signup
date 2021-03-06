import ldap
import os
import re
import datetime

from django.conf import settings
from django.contrib.auth.models import User


class ActiveDirectoryAuthenticationBackend:

    """
    This authentication backend authenticates against Active directory.
    It updates the user objects according to the settings in the AD and is
    able to map specific groups to give users admin rights.
    """

    def __init__(self):
        """ initialise a debuging if enabled """
        self.debug = settings.AD_DEBUG
        if len(settings.AD_DEBUG_FILE) > 0 and self.debug:
            self.debugFile = settings.AD_DEBUG_FILE
            # is the debug file accessible?
            if not os.path.exists(self.debugFile):
                open(self.debugFile,'w').close()
            elif not os.access(self.debugFile, os.W_OK):
                raise IOError("Debug File is not writable")
        else:
            self.debugFile = None

    def authenticate(self,username=None,password=None):
        if not settings.AD_DNS_NAME:
            return None
        try:
            if len(password) == 0:
                return None
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            if settings.AD_CERT_FILE:
                ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.AD_CERT_FILE)
            l = ldap.initialize(settings.AD_LDAP_URL)
            l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
            l.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
            l.set_option(ldap.OPT_X_TLS_DEMAND, True)
            binddn = "{user}@{domain}".format(user=username, domain=settings.AD_NT4_DOMAIN)
            l.simple_bind_s(binddn, password)
            l.unbind_s()
            return self.get_or_create_user(username,password)

        except ImportError:
            self.debug_write('import error in authenticate')
        except ldap.INVALID_CREDENTIALS:
            self.debug_write(username + ': Invalid Credentials')
        except Exception as e:
            self.debug_write('Error connecting to LDAP. Message: {msg}'.format(msg=e))

    def get_or_create_user(self, username, password):
        """ create or update the User object """
        # get user info from AD
        user_info = self.get_user_info(username, password)

        # is there already a user?
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            if user_info is not None:
                user = User(username=username, password=password)
                self.debug_write('create new user ' + username)

        ## update the user objects
        # group mapping for the access rights
        if user_info['is_admin']:
            user.is_staff = True
            user.is_superuser = True
        elif user_info:
            user.is_staff = False
            user.is_superuser = False
        else:
            user.is_active = False

        # personal data
        user.first_name = user_info['first_name']
        user.last_name = user_info['last_name']
        user.email = user_info['mail']

        # cache the AD password
        user.set_password(password)
        user.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def debug_write(self,message):
        """ handle debug messages """
        if self.debugFile is not None:
            fObj = open(self.debugFile, 'a')
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            fObj.write("{now}\t{msg}\n".format(now=now, msg=message))
            fObj.close()

    def check_group(self,membership):
        """ evaluate ADS group memberships """
        self.debug_write("Evaluating group membership")
        group_dict = {
            'is_admin': False,
            'is_valid': False,
            'team_number': 0
        }
        pattern = re.compile(r'(CN|OU)=(?P<groupName>[\w\s|\d\s]+),')
        for group in membership:
            self.debug_write('checking group: ' + str(group))
            group_matches = pattern.finditer(str(group))
            for groupMatch in group_matches:
                if groupMatch:
                    this_group = groupMatch.group('groupName')
                    self.debug_write('checking match: ' + this_group)
                    if this_group in settings.AD_MEMBERSHIP_ADMIN:
                        group_dict['is_admin'] = True
                    if this_group in settings.AD_MEMBERSHIP_REQ:
                        group_dict['is_valid'] = True
                    self.debug_write("Comparing {prefix} to {group}".format(
                        prefix=str(settings.AD_BLUE_TEAM_PREFIX), group=str(this_group)))
                    if str(settings.AD_BLUE_TEAM_PREFIX) in str(this_group):
                        num_match = re.search('(\d+)$', this_group)
                        if num_match:
                            group_dict['team_number'] = num_match.group(0)

        if group_dict['is_admin']:
            self.debug_write('is admin user')
        elif group_dict['is_valid']:
            self.debug_write('is normal user (not admin)')
        else:
            self.debug_write('does not have the AD group membership needed')
        if group_dict['team_number'] > 0:
            self.debug_write('is blue user on team ' + group_dict['team_number'])

        return group_dict

    def get_user_info(self, username, password):
        """ get user info from ADS to a dictionary """
        try:
            userInfo = {
                    'username' : username,
                    'password' : password,
            }
            # prepare LDAP connection
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            if settings.AD_CERT_FILE:
                ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.AD_CERT_FILE)
            ldap.set_option(ldap.OPT_REFERRALS, 0)  # DO NOT TURN THIS OFF OR SEARCH WON'T WORK!

            # initialize
            self.debug_write('ldap.initialize...')
            l = ldap.initialize(settings.AD_LDAP_URL)
            l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
            l.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
            l.set_option(ldap.OPT_X_TLS_DEMAND, True)

            # bind
            binddn = "{user}@{domain}".format(user=username, domain=settings.AD_NT4_DOMAIN)
            self.debug_write('ldap.bind ' + binddn)
            l.bind_s(binddn,password)

            # search
            self.debug_write('searching for {dn}...'.format(dn=binddn))
            result = l.search_ext_s(settings.AD_BASE_DN, ldap.SCOPE_SUBTREE,
                                    "sAMAccountName={user}".format(user=username), settings.AD_SEARCH_FIELDS)

            self.debug_write("Full results: {0}".format(result))
            result = result[0][1]
            self.debug_write("results in {0}".format(result))

            # Validate that they are a member of review board group
            if 'memberOf' in result:
                membership = result['memberOf']
            else:
                self.debug_write('AD user has no group memberships')
                return None

            # user ADS Groups
            group_dict = self.check_group(membership)

            if not group_dict['is_valid']:
                return None

            userInfo.update(group_dict)

            # get user info from ADS
            # get email
            if 'mail' in result:
                mail = result['mail'][0]
            else:
                mail = ""

            userInfo['mail'] = str(mail)
            self.debug_write("mail=" + str(mail))

            # get surname
            if 'sn' in result:
                last_name = str(result['sn'][0])
            else:
                last_name = ""

            userInfo['last_name'] = last_name
            self.debug_write("sn=" + last_name)

            # get display name
            if 'givenName' in result:
                first_name = str(result['givenName'][0])
            else:
                first_name = None
            #Need a first name
            if first_name is None:
                first_name = str(userInfo['username'])

            userInfo['first_name'] = first_name
            self.debug_write("first_name=" + first_name)

            # LDAP unbind
            l.unbind_s()
            return userInfo

        except Exception as e:
            self.debug_write("exception caught!")
            self.debug_write(e)
            return None
