import ldap
from ldap import modlist
from signup import settings
import base
import datetime
import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
import re

# For checking that generated passwords meet AD complexity requirements
UPPER = re.compile('.*[A-Z].*')
LOWER = re.compile('.*[a-z].*')
NUMERIC = re.compile('.*[0-9].*')
PASSWORD_LENGTH = 12

##########
# LDAP functions
##########
def initialize_ldap():
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

    if settings.AD_CERT_FILE:
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.AD_CERT_FILE)

    try:
        f = open(settings.AD_DEBUG_FILE, 'a')
        l = ldap.initialize(settings.AD_LDAP_URL,
                            trace_level=settings.AD_LDAP_DEBUG_LEVEL,
                            trace_file=f)
    except:
        l = ldap.initialize(settings.AD_LDAP_URL)

    l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
    l.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
    l.set_option(ldap.OPT_X_TLS_DEMAND, True)

    return l

def admin_bind():
    l = initialize_ldap()
    try:
        admin_dn = base.get_global_setting('administrator_bind_dn')
        admin_pw = base.get_global_setting('administrator_bind_pw')
        l.simple_bind_s(admin_dn, admin_pw)

    except ldap.LDAPError as e:
        ldap_debug_write("Couldn't bind as admin to LDAP server: " + str(e))
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

def get_user_dn(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    fname = participant.user.first_name
    lname = participant.user.last_name
    user_dn = 'CN={first} {last},OU={ou},{base_dn}'.format(first=fname, last=lname,
                                                      ou=settings.AD_CDCUSER_OU,
                                                      base_dn=settings.AD_BASE_DN)
    return user_dn

def get_group_dn(team_id):
    team = models.Team.objects.get(pk=team_id)
    group = settings.AD_BLUE_TEAM_FORMAT.format(number=team.number)
    group_dn = 'CN={group},OU={ou},{base_dn}'.format(group=group,
                                                     ou=settings.AD_CDCUSER_OU,
                                                     base_dn=settings.AD_BASE_DN)
    return group_dn

##########
# User accounts
##########
def generate_password():
    # Generate a password that AD will like
    password = None
    while True:
        password = User.objects.make_random_password(length=PASSWORD_LENGTH)
        if UPPER.match(password) and LOWER.match(password) and NUMERIC.match(password):
            return password

def make_password_modlist(password):
    if password:
        # Prep the password
        unicode_pass = ('\"' + password + '\"').encode('iso-8859-1')
        password_value = unicode_pass.encode('utf-16-le')
        add_pass = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]
        return add_pass
    return None

def create_user_account(username, fname, lname, email):
    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    base_dn = settings.AD_BASE_DN
    cdcuser_ou = settings.AD_CDCUSER_OU

    # This is needed for searches to work
    ldap.set_option(ldap.OPT_REFERRALS, 0)

    ldap_debug_write("Attempting to create user {user} ({email})".format(user=username, email=email))

    # Check and see if user exists
    search_filter = '(&(sAMAccountName=' + username + ')(objectClass=person))'
    try:
        user_results = ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, ['distinguishedName'])
    except ldap.LDAPError as e:
        ldap_debug_write("Couldn't search for existing username: " + str(e))
        return False

    # Check the results
    if len(user_results) != 0 and user_results[0][0] is not None:
        ldap_debug_write("User " + username + " already exists in AD: " + user_results[0][1]['distinguishedName'][0])
        raise base.UsernameAlreadyExistsError()

    user_dn = 'CN={first} {last},OU={ou},{search}'.format(first=fname, last=lname,
                                                      ou=cdcuser_ou,
                                                      search=base_dn)
    user_attrs = {}
    user_attrs['objectClass'] = ['top', 'person', 'organizationalPerson', 'user']
    user_attrs['cn'] = str(fname + ' ' + lname)
    user_attrs['userPrincipalName'] = str(username + '@' + settings.AD_DOMAIN)
    user_attrs['sAMAccountName'] = str(username)
    user_attrs['givenName'] = str(fname)
    user_attrs['sn'] = str(lname)
    user_attrs['displayName'] = str(fname + ' ' + lname)
    user_attrs['userAccountControl'] = '514'
    user_attrs['mail'] = str(email)
    user_ldif = modlist.addModlist(user_attrs)

    password = generate_password()
    add_pass = make_password_modlist(password)

    # New group membership
    add_member = [(ldap.MOD_ADD, 'member', user_dn)]
    cdcuser_group_dn = 'CN={group},OU={ou},{search}'.format(group=settings.AD_CDCUSER_GROUP,
                                                      ou=cdcuser_ou,
                                                      search=base_dn)

    # 512 will set user account to enabled
    mod_acct = [(ldap.MOD_REPLACE, 'userAccountControl', '512')]

    # Add the new user account
    try:
        ldap_connection.add_s(user_dn, user_ldif)
    except ldap.LDAPError as e:
        ldap_debug_write("Error adding new user: " + str(e))
        return False

    # Add user to CDCUsers group
    try:
        ldap_connection.modify_s(cdcuser_group_dn, add_member)
    except ldap.LDAPError as e:
        ldap_debug_write("Error adding user to CDCUsers group: " + str(e))
        return False

    # Add the password
    try:
        ldap_connection.modify_s(user_dn, add_pass)
    except ldap.LDAPError as e:
        ldap_debug_write("Error setting password: " + str(e))
        return False

    # Change the account back to enabled
    try:
        ldap_connection.modify_s(user_dn, mod_acct)
    except ldap.LDAPError as e:
        ldap_debug_write("Error enabling user: " + str(e))
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
              If you have questions, email CDC support at {support}
              """

    send_mail('Your ISEAGE CDC account',
              email_body.format(fname=fname, lname=lname,username=username, password=password,
                                support=settings.SUPPORT_EMAIL),
              settings.EMAIL_FROM_ADDR,
              [email])

    # All is good
    return True

def update_password(participant_id, old_password, new_password):
    # Check that the current password is correct
    user_dn = get_user_dn(participant_id)
    l = initialize_ldap()
    ldap_debug_write("Attempting to reset password for " + user_dn)
    try:
        l.simple_bind_s(user_dn, old_password)
    except ldap.INVALID_CREDENTIALS:
        ldap_debug_write("Failed to authenticate current password for " + user_dn)
        raise base.PasswordMismatchError()
    except ldap.LDAPError as e:
        ldap_debug_write("Couldn't bind as user {dn} - ".format(dn=user_dn) + str(e))
        return False

    # If we got this far, auth was successful
    l.unbind_s()

    # Prep the password
    ml = make_password_modlist(new_password)

    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    # Change the password
    try:
        ldap_connection.modify_s(user_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error setting password: " + str(e))
        return False

    # If we're here, the password change succeeded
    ldap_connection.unbind_s()

    # Send email
    participant = models.Participant.objects.get(pk=participant_id)

    email_body = """Hi there {fname} {lname},

              Your password has been successfully updated.

              If you didn't change your password, please contact CDC support at {support} immediately.
              """

    send_mail('ISEAGE CDC Support: Password successfully updated',
              email_body.format(fname=participant.user.first_name, lname=participant.user.last_name,
                                support=settings.SUPPORT_EMAIL),
              settings.EMAIL_FROM_ADDR,
              [participant.user.email])

    # All done
    return True

def forgot_password(email):
    user = User.objects.get(email=email)

    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    user_dn = get_user_dn(user.participant.id)

    password = generate_password()
    ml = make_password_modlist(password)

    # Change the password
    ldap_debug_write("Resetting password for " + user_dn)
    try:
        ldap_connection.modify_s(user_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error resetting password: " + str(e))
        return False

    # If we're here, the password change succeeded
    ldap_connection.unbind_s()

    # Send email
    email_body = """Hi there {fname} {lname},

              Your password has been reset to {password}
              You should change it right away at https://signup.iseage.org/dashboard/

              If you didn't request a password reset, please contact CDC support at {support} immediately.
              """

    send_mail('ISEAGE CDC Support: Your password has been reset',
              email_body.format(fname=user.first_name, lname=user.last_name, password=password,
                                support=settings.SUPPORT_EMAIL),
              settings.EMAIL_FROM_ADDR,
              [user.email])

    # All done
    return True



##########
# Teams
##########
def assign_team_number(team_id):
    num_teams = base.get_global_setting('number_of_teams')
    assigned_numbers = models.Team.objects.values_list('number', flat=True)
    number = None

    for i in range(1, num_teams + 1):
        if not i in assigned_numbers:
            number = i
            break

    if not number:
        raise base.OutOfTeamNumbersError()

    team = models.Team.objects.get(pk=team_id)
    team.number = number
    team.save()

    return True

def create_team(name, captain_id):
    team, created = models.Team.objects.get_or_create(name=name)
    if not created:
        raise base.TeamAlreadyExistsError()

    assign_team_number(team.id)

    captain = models.Participant.objects.get(pk=captain_id)
    captain.team = team
    captain.captain = True
    captain.save()

    email_body = """Hi there {fname} {lname},

              Your team has been successfully created.
              Your team name is: {team}
              Your team number is: {number}

              You can manage your team by visiting https://signup.iseage.org/manage_team/

              Your team members should create an account and submit a request to join your team.

              If you have questions, email CDC support at {support}
              """

    send_mail('ISEAGE CDC Support: You have been added to a team',
              email_body.format(fname=captain.user.first_name, lname=captain.user.last_name,
                                team=team.name, number=team.number, support=settings.SUPPORT_EMAIL),
              settings.EMAIL_FROM_ADDR,
              [captain.user.email])

    return True

def add_user_to_team(team_id, participant_id):
    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    user_dn = get_user_dn(participant_id)
    group_dn = get_group_dn(team_id)

    ml = [(ldap.MOD_ADD, 'member', user_dn)]
    try:
        ldap_connection.modify_s(group_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error adding user to group: " + str(e))
        return False

    ldap_connection.unbind_s()

    # Send email
    participant = models.Participant.objects.get(pk=participant_id)
    team = models.Team.objects.get(pk=team_id)
    captain_list = models.Participant.objects.filter(team_id=team_id).filter(captain=True)
    captains = ""
    for captain in captain_list:
        captains = captains + "{fname} {lname}  \t{email}\n".format(fname=captain.user.first_name,
                                                                  lname=captain.user.last_name,
                                                                  email=captain.user.email)

    email_body = """Hi there {fname} {lname},

              Your request to join a team has been approved.
              You have been added to Team {number}: {team}

              Be sure to get in contact with your team captain(s) if you haven't already:

              {captains}

              If you have questions, email CDC support at {support}
              """

    send_mail('ISEAGE CDC Support: You have been added to a team',
              email_body.format(fname=participant.user.first_name, lname=participant.user.last_name,
                                number=team.number, team=team.name, captains=captains,
                                support=settings.SUPPORT_EMAIL),
              settings.EMAIL_FROM_ADDR,
              [participant.user.email])

    return True

def remove_user_from_team(team_id, participant_id):
    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    user_dn = get_user_dn(participant_id)
    group_dn = get_group_dn(team_id)

    ml = [(ldap.MOD_DELETE, 'member', user_dn)]
    try:
        ldap_connection.modify_s(group_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error removing user from group: " + str(e))
        return False

    ldap_connection.unbind_s()
    return True

def promote_to_captain(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    participant.captain = True
    participant.save()

def demote_captain(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    participant.captain = False
    participant.save()

def submit_join_request(participant_id, team_id):
    participant = models.Participant.objects.get(pk=participant_id)
    team = models.Team.objects.get(pk=team_id)
    captains = models.Participant.objects.filter(team_id=team_id).filter(captain=True)
    participant.requested_team = team
    participant.save()

    email_body = """Hi there captains,

              {fname} {lname} ({email}) has requested to join your team, {team}.

              Visit https://signup.iseage.org/manage_team/ to confirm or deny this request.

              If you have questions, email CDC support at {support}
              """

    send_mail('ISEAGE CDC Support: Someone has requested to join your team',
              email_body.format(fname=participant.user.first_name, lname=participant.user.last_name,
                                email=participant.user.email,team=team.name,
                                support=settings.SUPPORT_EMAIL),
              settings.EMAIL_FROM_ADDR,
              captains.values_list('email', flat=True))

def sumbit_captain_request(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    captains = models.Participant.objects.filter(team=participant.team).filter(captain=True)

    email_body = """Hi there captains,

              {fname} {lname} ({email}) has requested to become a captain of your team, {team}.

              Visit https://signup.iseage.org/manage_team/ to confirm or deny this request.

              If you have questions, email CDC support at {support}
              """

    send_mail('ISEAGE CDC Support: Someone has requested to become a captain of your team',
              email_body.format(fname=participant.user.first_name, lname=participant.user.last_name,
                                email=participant.user.email,team=participant.team.name,
                                support=settings.SUPPORT_EMAIL),
              settings.EMAIL_FROM_ADDR,
              captains.values_list('email', flat=True))