import ldap
from ldap import modlist
from signup import settings
import base
import datetime
import models
from django.contrib.auth.models import User
from django.db.models import Count
from django.core.mail import send_mail
import re
import email_templates
import smtplib
import logging

# For checking that generated passwords meet AD complexity requirements
UPPER = re.compile('.*[A-Z].*')
LOWER = re.compile('.*[a-z].*')
NUMERIC = re.compile('.*[0-9].*')
PASSWORD_LENGTH = 12

def get_current_teams():
    return models.Team.objects.annotate(member_count=Count('participant'))

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
    # As long as the password didn't fail, attempt this many times to do the bind
    num_retries = 2

    for i in range(num_retries + 1):
        l = initialize_ldap()
        try:
            admin_dn = base.get_global_setting('administrator_bind_dn')
            admin_pw = base.get_global_setting('administrator_bind_pw')
            l.simple_bind_s(admin_dn, admin_pw)
        except ldap.INVALID_CREDENTIALS:
            ldap_debug_write("Failed to authenticate current password for admin account specified in settings")
            l.unbind_s()
            return None
        except ldap.LDAPError as e:
            ldap_debug_write("[Attempt " + str(i + 1) + "] Couldn't bind as admin to LDAP server: " + str(e))
            l.unbind_s()
            if i < num_retries:
                continue
            else:
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
        l.unbind_s()
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
    except ldap.ALREADY_EXISTS as e:
        ldap_debug_write("That DN already exists: " + str(e))
        ldap_connection.unbind_s()
        raise base.DuplicateName()

    except ldap.LDAPError as e:
        ldap_debug_write("Error adding new user: " + str(e))
        l.unbind_s()
        return False

    # Add user to CDCUsers group
    try:
        ldap_connection.modify_s(cdcuser_group_dn, add_member)
    except ldap.LDAPError as e:
        ldap_debug_write("Error adding user to CDCUsers group: " + str(e))
        ldap_connection.unbind_s()
        return False

    # Add the password
    try:
        ldap_connection.modify_s(user_dn, add_pass)
    except ldap.LDAPError as e:
        ldap_debug_write("Error setting password: " + str(e))
        ldap_connection.unbind_s()
        return False

    # Change the account back to enabled
    try:
        ldap_connection.modify_s(user_dn, mod_acct)
    except ldap.LDAPError as e:
        ldap_debug_write("Error enabling user: " + str(e))
        ldap_connection.unbind_s()
        return False

    # LDAP unbind
    ldap_connection.unbind_s()

    # Send email
    email_body = email_templates.ACCOUNT_CREATED.format(fname=fname, lname=lname,username=username, password=password,
                                support=settings.SUPPORT_EMAIL)

    try:
        send_mail('Your ISEAGE CDC account', email_body, settings.EMAIL_FROM_ADDR, [email])
    except smtplib.SMTPException:
        logging.warning("Failed to send email to {email}:\n{body}".format(email=email, body=email_body))

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
        l.unbind_s()
        raise base.PasswordMismatchError()
    except ldap.LDAPError as e:
        ldap_debug_write("Couldn't bind as user {dn} - ".format(dn=user_dn) + str(e))
        l.unbind_s()
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
        ldap_connection.unbind_s()
        return False

    # If we're here, the password change succeeded
    ldap_connection.unbind_s()

    # Send email
    participant = models.Participant.objects.get(pk=participant_id)

    email = participant.user.email
    email_body = email_templates.PASSWORD_UPDATED.format(fname=participant.user.first_name,
                                                         lname=participant.user.last_name,
                                                         support=settings.SUPPORT_EMAIL)
    try:
        send_mail('ISEAGE CDC Support: Password successfully updated', email_body, settings.EMAIL_FROM_ADDR, [email])
    except smtplib.SMTPException:
        logging.warning("Failed to send email to {email}:\n{body}".format(email=email, body=email_body))

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
        ldap_connection.unbind_s()
        return False

    # If we're here, the password change succeeded
    ldap_connection.unbind_s()

    # Send email
    email = user.email
    email_body = email_templates.PASSWORD_RESET.format(fname=user.first_name, lname=user.last_name, password=password,
                                support=settings.SUPPORT_EMAIL)
    try:
        send_mail('ISEAGE CDC Support: Your password has been reset', email_body, settings.EMAIL_FROM_ADDR, [email])
    except smtplib.SMTPException:
        logging.warning("Failed to send email to {email}:\n{body}".format(email=email, body=email_body))

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

    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    user_dn = get_user_dn(captain_id)
    group_dn = get_group_dn(team.id)

    ml = [(ldap.MOD_ADD, 'member', user_dn)]
    try:
        ldap_connection.modify_s(group_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error adding user to group: " + str(e))
        ldap_connection.unbind_s()
        return False

    ldap_connection.unbind_s()

    # Reload so we get the correct number
    team = models.Team.objects.get(pk=team.id)

    captain = models.Participant.objects.get(pk=captain_id)
    captain.team = team
    captain.captain = True
    captain.save()

    email = captain.user.email
    email_body = email_templates.TEAM_CREATED.format(fname=captain.user.first_name, lname=captain.user.last_name,
                                team=team.name, number=team.number, support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: Team Created', email_body, settings.EMAIL_FROM_ADDR, [email])
    except smtplib.SMTPException:
        logging.warning("Failed to send email to {email}:\n{body}".format(email=email, body=email_body))

    return True

def rename_team(team_id, new_name):
    exists = True
    try:
        models.Team.objects.get(name=new_name)
    except models.Team.DoesNotExist:
        exists = False

    if exists:
        raise base.TeamAlreadyExistsError()

    team = models.Team.objects.get(pk=team_id)
    team.name = new_name
    team.save()
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
        ldap_connection.unbind_s()
        return False

    ldap_connection.unbind_s()


    participant = models.Participant.objects.get(pk=participant_id)
    team = models.Team.objects.get(pk=team_id)
    participant.team = team
    participant.requested_team = None
    participant.save()

    # Send email
    captain_list = team.captains()
    captains = ""
    for captain in captain_list:
        captains = captains + "{fname} {lname}  \t{email}\n".format(fname=captain.user.first_name,
                                                                    lname=captain.user.last_name,
                                                                    email=captain.user.email)

    email = participant.user.email
    email_body = email_templates.JOIN_REQUEST_APPROVED.format(fname=participant.user.first_name,
                                                              lname=participant.user.last_name,
                                                              number=team.number,
                                                              team=team.name,
                                                              captains=captains,
                                                              support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: You have been added to a team', email_body, settings.EMAIL_FROM_ADDR, [email])
    except smtplib.SMTPException:
        logging.warning("Failed to send email to {email}:\n{body}".format(email=email, body=email_body))

    return True

def leave_team(participant_id):
    ldap_connection = admin_bind()
    if not ldap_connection:
        return False

    participant = models.Participant.objects.get(pk=participant_id)
    team = participant.team
    user_dn = get_user_dn(participant_id)
    group_dn = get_group_dn(team.id)

    ml = [(ldap.MOD_DELETE, 'member', user_dn)]
    try:
        ldap_connection.modify_s(group_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error removing user from group: " + str(e))
        ldap_connection.unbind_s()
        return False

    ldap_connection.unbind_s()

    participant.team = None
    participant.requested_team = None
    participant.captain = False
    participant.requests_captain = False
    participant.save()

    captain_emails = []
    for captain in team.captains():
        captain_emails.append(captain.user.email)

    email_body = email_templates.LEFT_TEAM.format(fname=participant.user.first_name,
                                                  lname=participant.user.last_name,
                                                  email=participant.user.email,
                                                  team=team.name,
                                                  support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: A member has left your team', email_body, settings.EMAIL_FROM_ADDR, captain_emails)
    except smtplib.SMTPException:
        logging.warning("Failed to send email to captains of {team}:\n{body}".format(team=team.name, body=email_body))

    return True

def promote_to_captain(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    participant.captain = True
    participant.requests_captain = False
    participant.save()

    email = participant.user.email
    email_body = email_templates.CAPTAIN_REQUEST_APPROVED.format(fname=participant.user.first_name,
                                                                 lname=participant.user.last_name,
                                                                 support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: You have been promoted to captain', email_body, settings.EMAIL_FROM_ADDR, [email])
    except smtplib.SMTPException:
        logging.warning("Failed to send email to {email}:\n{body}".format(email=email, body=email_body))

    return True

def demote_captain(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    team = participant.team

    if len(team.captains()) < 2:
        raise base.OnlyRemainingCaptainError()

    participant.captain = False
    participant.save()

    captain_emails = []
    for captain in team.captains():
        captain_emails.append(captain.user.email)

    email_body = email_templates.STEPPED_DOWN.format(fname=participant.user.first_name,
                                                     lname=participant.user.last_name,
                                                     team=team.name,
                                                     support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: A member has stepped down as captain', email_body, settings.EMAIL_FROM_ADDR, captain_emails)
    except smtplib.SMTPException:
        logging.warning("Failed to send email to captains of {team}:\n{body}".format(team=team.name, body=email_body))

    return True

def submit_join_request(participant_id, team_id):
    participant = models.Participant.objects.get(pk=participant_id)
    team = models.Team.objects.get(pk=team_id)
    participant.requested_team = team
    participant.save()
    captain_emails = []
    for captain in team.captains():
        captain_emails.append(captain.user.email)

    email_body = email_templates.JOIN_REQUEST_SUBMITTED.format(fname=participant.user.first_name,
                                                               lname=participant.user.last_name,
                                                               email=participant.user.email,
                                                               team=team.name,
                                                               support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: Someone has requested to join your team', email_body, settings.EMAIL_FROM_ADDR,
                  captain_emails)
    except smtplib.SMTPException:
        logging.warning("Failed to send email to captains of {team}:\n{body}".format(team=team.name, body=email_body))


    return True

def sumbit_captain_request(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    participant.requests_captain = True
    participant.save()
    captain_emails = []
    for captain in participant.team.captains():
        captain_emails.append(captain.user.email)

    email_body = email_templates.CAPTAIN_REQUEST_SUBMITTED.format(fname=participant.user.first_name,
                                                                  lname=participant.user.last_name,
                                                                  email=participant.user.email,
                                                                  team=participant.team.name,
                                                                  support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: Someone has requested to become a captain of your team', email_body,
                  settings.EMAIL_FROM_ADDR, captain_emails)
    except smtplib.SMTPException:
        logging.warning("Failed to send email to captains of {team}:\n{body}".format(team=participant.team.name, body=email_body))

    return True

def disband_team(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    team = participant.team
    member_emails = []
    ldap_connection = admin_bind()

    group_dn = get_group_dn(team.id)

    for member in team.members():
        user_dn = get_user_dn(member.id)
        ml = [(ldap.MOD_DELETE, 'member', user_dn)]
        try:
            ldap_connection.modify_s(group_dn, ml)
        except ldap.LDAPError as e:
            ldap_debug_write("Error removing user from group: " + str(e))
            ldap_connection.unbind_s()
            return False

        member_emails.append(member.user.email)

    ldap_connection.unbind_s()

    name = team.name
    team.delete_and_members()

    email_body = email_templates.TEAM_DISBANDED.format(team=name, support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: Your team has been disbanded', email_body,
                  settings.EMAIL_FROM_ADDR, member_emails)
    except smtplib.SMTPException:
        logging.warning("Failed to send email to members of {team}:\n{body}".format(team=name, body=email_body))

    return True