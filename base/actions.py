import ldap
from signup import settings
import base
import datetime
import models
from django.contrib.auth.models import BaseUserManager as usermgr
from django.core.mail import send_mail

def initialize_ldap():
    if settings.AD_CERT_FILE:
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.AD_CERT_FILE)

    l = ldap.initialize(settings.AD_LDAP_URL,
                        trace_level=settings.AD_LDAP_DEBUG_LEVEL,
                        trace_file=settings.AD_DEBUG_FILE)

    l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)

    return l

def admin_bind():
    l = initialize_ldap()
    try:
        admin_dn = base.get_global_setting('administrator_bind_dn')
        admin_pw = base.get_global_setting('administrator_bind_pw')
        l.simple_bind_s(admin_dn, admin_pw)

    except ldap.LDAPerror, e:
        ldap_debug_write("Couldn't bind as admin to LDAP server: " + e)
        return None

    return l

def ldap_debug_write(message):
    """ handle debug messages """
    debug_file = settings.AD_DEBUG_FILE
    if debug_file is not None:
        fObj = open(debug_file, 'a')
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        fObj.write("%s\t%s\n" % (now,message))
        fObj.close()

def create_user_account(username, fname, lname, email):
    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    base_dn = settings.AD_BASE_DN
    cdcuser_ou = settings.AD_CDCUSER_OU

    # Check and see if user exists
    search_filter = '(&(sAMAccountName=' + username + ')(objectClass=person))'
    try:
        user_results = ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, ['distinguishedName'])
    except ldap.LDAPError, e:
        ldap_debug_write("Couldn't search for existing username: " + e)
        return False

    # Check the results
    if len(user_results) != 0:
        ldap_debug_write("User ", username, " already exists in AD: " + user_results[0][1]['distinguishedName'][0])
        return False

    user_dn = 'CN={username},OU={ou},{search}'.format(username=username,
                                                      ou=cdcuser_ou,
                                                      search=base_dn)
    user_attrs = {}
    user_attrs['objectClass'] = ['top', 'person', 'organizationalPerson', 'user']
    user_attrs['cn'] = fname + ' ' + lname
    user_attrs['userPrincipalName'] = username + '@' + settings.AD_DOMAIN
    user_attrs['sAMAccountName'] = username
    user_attrs['givenName'] = fname
    user_attrs['sn'] = lname
    user_attrs['displayName'] = fname + ' ' + lname
    user_attrs['userAccountControl'] = '514'
    user_attrs['mail'] = email
    user_ldif = ldap.modlist.addModlist(user_attrs)

    password = usermgr.make_random_password(length=12)

    # Prep the password
    unicode_pass = unicode('\"' + password + '\"', 'iso-8859-1')
    password_value = unicode_pass.encode('utf-16-le')
    add_pass = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]

    # 512 will set user account to enabled
    mod_acct = [(ldap.MOD_REPLACE, 'userAccountControl', '512')]

    # Add the new user account
    try:
        ldap_connection.add_s(user_dn, user_ldif)
    except ldap.LDAPError, e:
        ldap_debug_write("Error adding new user: " + e)
        return False

    # Add the password
    try:
        ldap_connection.modify_s(user_dn, add_pass)
    except ldap.LDAPError, e:
        ldap_debug_write("Error setting password: " + e)
        return False

    # Change the account back to enabled
    try:
        ldap_connection.modify_s(user_dn, mod_acct)
    except ldap.LDAPError, e:
        ldap_debug_write("Error enabling user: " + e)
        return False

    # LDAP unbind
    ldap_connection.unbind_s()

    # Send email
    email_body = """Hi there {fname} {lname},

              Your ISEAGE CDC account has been successfully created!
              Please use the following credentials to log in at https://signup.iseage.org/login/

              Username: {username}
              Password: {password}

              Make sure you change your password right away.
              If you have questions, email CDC support at cdc_support@iastate.edu
              """

    send_mail('Your ISEAGE CDC account',
              email_body.format(fname=fname, lname=lname,username=username, password=password),
              'cdc_support@iastate.edu',
              email)

    # All is good
    return True

def get_available_team_numbers():
    pass

def get_user_dn(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    username = participant.user.get_username()
    user_dn = 'CN={username},OU={ou},{base_dn}'.format(username=username,
                                                      ou=settings.AD_CDCUSER_OU,
                                                      base_dn=settings.AD_BASE_DN)

def get_group_dn(team_id):
    team = models.Team.objects.get(pk=team_id)
    group = base.get_global_setting('ldap_group_format').format(number=team.number)
    group_dn = 'CN={group},OU={ou},{base_dn}'.format(group=group,
                                                     ou=settings.AD_CDCUSER_OU,
                                                     base_dn=settings.AD_BASE_DN)

def add_user_to_team(team_id, participant_id):
    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    user_dn = get_user_dn(participant_id)
    group_dn = get_group_dn(team_id)

    modlist = [(ldap.MOD_ADD, 'member', user_dn)]
    try:
        ldap_connection.modify_s(group_dn, modlist)
    except ldap.LDAPError, e:
        print "Error adding user to group: " + e
        return False

    ldap_connection.unbind_s()
    return True

def remove_user_from_team(team_id, participant_id):
    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    user_dn = get_user_dn(participant_id)
    group_dn = get_group_dn(team_id)

    modlist = [(ldap.MOD_DELETE, 'member', user_dn)]
    try:
        ldap_connection.modify_s(group_dn, modlist)
    except ldap.LDAPError, e:
        print "Error adding user to group: " + e
        return False

    ldap_connection.unbind_s()
    return True

def assign_team_number(team_id):
    num_teams = base.get_global_setting('number_of_teams')
    assigned_numbers = models.Team.objects.values_list('number', flat=True)
    number = None

    for i in range(1, num_teams + 1):
        if not i in assigned_numbers:
            number = i
            break

    if not number:
        return False

    team = models.Team.objects.get(pk=team_id)
    team.number = number
    team.save()

    return True

def update_password(user, old_password, new_password):
    pass
