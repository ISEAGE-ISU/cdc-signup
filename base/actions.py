import ldap
from ldap import modlist
from django.conf import settings
import auth as ad_auth
import base
import datetime
import models
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.core.mail import send_mail, EmailMessage
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.core.cache import cache
import re
import email_templates
import smtplib
import logging

GLOBAL_SETTINGS_OBJECT = 'GLOBAL_SETTINGS_OBJECT'

# For checking that generated passwords meet AD complexity requirements
UPPER = re.compile('.*[A-Z].*')
LOWER = re.compile('.*[a-z].*')
NUMERIC = re.compile('.*[0-9].*')
PASSWORD_LENGTH = 12

AD_AUTH = ad_auth.ActiveDirectoryAuthenticationBackend()


def email_participants(subject, content, audience):
    emails = User.objects.filter(is_superuser=False)
    if audience == 'all':
        # All Blue Team Members, no Red/Green
        emails = emails.exclude(Q(participant__is_red=True) |
                Q(participant__is_green=True))
    elif audience == 'with_team':
        # All Blue Team Members on a team, no Red/Green
        emails = emails.exclude(participant__team=None)
    elif audience == 'no_team':
        # All Blue Team Members NOT on a team, no Red/Green
        emails = emails.filter(Q(participant__team=None) &
                Q(participant__is_red=False) &
                Q(participant__is_green=False))
    elif audience == 'red_team_approved':
        # Approved Red Team Members, no Blue/Green
        emails = emails.filter(participant__is_red=True, participant__approved=True)
    elif audience == 'red_team_all':
        # All Red Team Members (Approved & Unapproved), no Blue/Green
        emails = emails.filter(participant__is_red=True)
    elif audience == 'green_team_approved':
        # Approved Green Team Members, no Blue/Red
        emails = emails.filter(participant__is_green=True, participant__approved=True)
    elif audience == 'green_team_all':
        # All Green Team Members (Approved & Unapproved), no Blue/Green
        emails = emails.filter(participant__is_green=True)
    emails = emails.values_list('email', flat=True)

    print(audience, emails)
    email = EmailMessage(subject=subject, body=content, bcc=emails, to=(settings.EMAIL_FROM_ADDR,), from_email=settings.EMAIL_FROM_ADDR)

    try:
        email.send()
    except smtplib.SMTPException:
        logging.warning("Failed to send email to {email}:\n{body}".format(email=email, body=content))


def get_current_teams():
    return models.Team.objects.annotate(member_count=Count('participant'))


def reset_global_settings_object():
    gs = models.GlobalSettings.objects.get_or_create(id__exact=1)[0]
    cache.set(GLOBAL_SETTINGS_OBJECT, gs)
    return gs


def get_global_settings_object():
    gs = cache.get(GLOBAL_SETTINGS_OBJECT)
    if not gs:
        gs = reset_global_settings_object()
    return gs


def get_global_setting(setting_name):
    gs = get_global_settings_object()
    gs_result = getattr(gs, setting_name)
    if gs_result:
        return gs_result
    elif hasattr(settings, setting_name):
        return getattr(settings, setting_name)
    else:
        return None


def set_global_setting(setting_name, value):
    gs = get_global_settings_object()
    try:
        setattr(gs, setting_name, value)
        gs.save()
    except Exception as e:
        return False
    #Reassign object in memcache
    reset_global_settings_object()
    return True


def render_template(request, template, context=None):
    if not context:
        context = {}
    if request is not None:
        ctx = RequestContext(request, context)
    else:
        ctx = Context(context)
    return get_template(template).render(ctx)


def get_context(request):
    context = {}
    context['current_url_full'] = request.get_full_path()
    request.session.__setitem__('ip_addr', request.META.get('HTTP_X_FORWARDED_FOR'))
    request.session.__setitem__('recent_path', request.META.get('PATH_INFO'))
    if request.user:
        context['user'] = request.user
        if isinstance(request.user, User):
            obj, created = models.Participant.objects.get_or_create(user=request.user)
            context['participant'] = obj

    r_ctx = RequestContext(request, context)
    return r_ctx


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
        ldap_debug_write("*****Initializing admin bind*****")
        try:
            admin_dn = get_global_setting('administrator_bind_dn')
            admin_pw = get_global_setting('administrator_bind_pw')
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


# Decorator to automatically handle setting up/tearing down an admin LDAP session if none is provided
def ldap_admin_bind(func):

    def session(*args, **kwargs):
        ldap_connection = admin_bind()
        if not ldap_connection:
            return False

        kwargs.update(ldap_connection=ldap_connection)

        try:
            ret = func(*args, **kwargs)
        except:
            raise
        finally:
            ldap_connection.unbind_s()
        return ret
    return session


def ldap_debug_write(message):
    """ handle debug messages """
    debug_file = settings.AD_DEBUG_FILE
    if debug_file is not None:
        fObj = open(debug_file, 'a')
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        fObj.write("{now}\t{msg}\n".format(now=now, msg=message))
        fObj.close()


def get_user_dn(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    fname = participant.user.first_name
    lname = participant.user.last_name
    if participant.is_red:
        ou = settings.AD_RED_OU
    elif participant.is_green:
        ou = settings.AD_GREEN_OU
    else:
        ou = settings.AD_CDCUSER_OU
    user_dn = 'CN={first} {last},OU={ou},{base_dn}'.format(first=fname, last=lname,
                                                      ou=ou, base_dn=settings.AD_BASE_DN)
    return user_dn


def get_group_dn(team_id):
    team = models.Team.objects.get(pk=team_id)
    group = settings.AD_BLUE_TEAM_FORMAT.format(number=team.number)
    group_dn = 'CN={group},OU={ou},{base_dn}'.format(group=group,
                                                     ou=settings.AD_CDCUSER_OU,
                                                     base_dn=settings.AD_BASE_DN)
    return group_dn


@ldap_admin_bind
def add_user_to_group(user_dn, group_dn, ldap_connection):
    ml = [(ldap.MOD_ADD, 'member', user_dn)]
    try:
        ldap_connection.modify_s(group_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error adding user to group: " + str(e))
        return False

    return True


@ldap_admin_bind
def remove_user_from_group(user_dn, group_dn, ldap_connection):
    ml = [(ldap.MOD_DELETE, 'member', user_dn)]
    try:
        ldap_connection.modify_s(group_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error removing user from group: " + str(e))
        return False
    return True


@ldap_admin_bind
def set_password(participant_id, password, ldap_connection):
    if not password:
        return False

    # Prep the password
    unicode_pass = ('\"' + password + '\"').encode('iso-8859-1')
    password_value = unicode_pass.encode('utf-16-le')
    ml = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]

    user_dn = get_user_dn(participant_id)

    # Change the password
    try:
        ldap_connection.modify_s(user_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error setting password: " + str(e))
        return False

    # If we're here, the password set succeeded
    username = models.Participant.objects.get(pk=participant_id).user.username

    # Ensure the password is updated locally
    AD_AUTH.get_or_create_user(username, password)

    return True


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


def create_user_account(username, fname, lname, email):
    return create_account(username, fname, lname, email, 'blue')


@ldap_admin_bind
def create_account(username, fname, lname, email, acct_type, ldap_connection):
    base_dn = settings.AD_BASE_DN

    if acct_type == 'blue':
        ou = settings.AD_CDCUSER_OU
        group = settings.AD_CDCUSER_GROUP
    elif acct_type == 'red':
        ou = settings.AD_RED_OU
        group = settings.AD_RED_PENDING
    elif acct_type == 'green':
        ou = settings.AD_GREEN_OU
        group = settings.AD_GREEN_PENDING

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
                                                      ou=ou,
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


    # 512 will set user account to enabled
    mod_acct = [(ldap.MOD_REPLACE, 'userAccountControl', '512')]

    # Add the new user account
    try:
        ldap_connection.add_s(user_dn, user_ldif)
    except ldap.ALREADY_EXISTS as e:
        ldap_debug_write("That DN already exists: " + str(e))
        raise base.DuplicateName()

    except ldap.LDAPError as e:
        ldap_debug_write("Error adding new user: " + str(e))
        return False

    # New group membership
    add_member = [(ldap.MOD_ADD, 'member', user_dn)]
    cdcuser_group_dn = 'CN={group},OU={ou},{search}'.format(group=group,
                                                            ou=ou,
                                                            search=base_dn)
    ldap_debug_write("Attempting to add user to group: " + cdcuser_group_dn)

    # Add user to appropriate group
    try:
        ldap_connection.modify_s(cdcuser_group_dn, add_member)
    except ldap.LDAPError as e:
        ldap_debug_write("Error adding user to {group} group: ".format(
            group=group) + str(e))
        return False

    # Prep the password
    unicode_pass = ('\"' + password + '\"').encode('iso-8859-1')
    password_value = unicode_pass.encode('utf-16-le')
    ml = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]

    # Set the password
    try:
        ldap_connection.modify_s(user_dn, ml)
    except ldap.LDAPError as e:
        ldap_debug_write("Error setting password: " + str(e))
        return False

    # Change the account back to enabled
    try:
        ldap_connection.modify_s(user_dn, mod_acct)
    except ldap.LDAPError as e:
        ldap_debug_write("Error enabling user: " + str(e))
        return False

    # Ensure the account exists locally
    AD_AUTH.get_or_create_user(username, password)

    # Send email
    if acct_type == 'blue':
        template = email_templates.ACCOUNT_CREATED
    elif acct_type == 'red':
        template = email_templates.ACCOUNT_CREATED_RED
    elif acct_type == 'green':
        template = email_templates.ACCOUNT_CREATED_GREEN
    email_body = template.format(fname=fname, lname=lname, username=username, password=password,
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

    success = set_password(participant_id, new_password)
    if not success:
        return False

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
    users = User.objects.filter(email=email)
    if len(users) < 1:
        raise User.DoesNotExist()
    for user in users:
        participant, created = models.Participant.objects.get_or_create(user=user)
        user_dn = get_user_dn(participant.id)
        password = generate_password()

        success = set_password(participant.id, password)
        if not success:
            return False

        # Send email
        username = user.get_username()
        email = user.email
        email_body = email_templates.PASSWORD_RESET.format(fname=user.first_name, lname=user.last_name,
                                                           username=username, password=password,
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
    num_teams = get_global_setting('number_of_teams')
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


def add_user_to_team(team_id, participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    team = models.Team.objects.get(pk=team_id)

    participant.team = team
    participant.requested_team = None
    participant.looking_for_team = False
    participant.save()

    if len(team.members()) >= get_global_setting('max_team_size'):
        team.looking_for_members = False
        team.save()

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


def join_team(participant_id, team_id):
    participant = models.Participant.objects.get(pk=participant_id)
    team = models.Team.objects.get(pk=team_id)

    participant.team = team
    participant.requested_team = None
    participant.looking_for_team = False
    participant.save()

    if len(team.members()) >= get_global_setting('max_team_size'):
        team.looking_for_members = False
        team.save()

    # Send email
    captains = ""
    for captain in team.captains():
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

    email_body2 = email_templates.MEMBER_JOINED.format(fname=participant.user.first_name,
                                                               lname=participant.user.last_name,
                                                               email=participant.user.email,
                                                               team=team.name,
                                                               support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: You have been added to a team', email_body, settings.EMAIL_FROM_ADDR, [email])
        send_mail('ISEAGE CDC Support: Someone has joined your team', email_body2, settings.EMAIL_FROM_ADDR, list(team.captain_emails()))
    except smtplib.SMTPException:
        logging.warning("Failed to send email to {email}:\n{body}".format(email=email, body=email_body))

    return True


def leave_team(participant_id):
    participant = models.Participant.objects.get(pk=participant_id)
    team = participant.team

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
    participant.promote()

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

    participant.demote()

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

    participant.request_team(team)

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

    participant.request_promotion()

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
    if not participant.captain:
        return False

    team = participant.team
    name = team.name
    member_emails = team.member_email_list()

    team.delete()

    email_body = email_templates.TEAM_DISBANDED.format(team=name, support=settings.SUPPORT_EMAIL)

    try:
        send_mail('ISEAGE CDC Support: Your team has been disbanded', email_body,
                  settings.EMAIL_FROM_ADDR, member_emails)
    except smtplib.SMTPException:
        logging.warning("Failed to send email to members of {team}:\n{body}".format(team=name, body=email_body))

    return True


def _get_group_dn(group, ou):
    return "CN={group},OU={ou},{dn}".format(group=group, ou=ou, dn=settings.AD_BASE_DN)


def approve_user(participant):
    user_dn = get_user_dn(participant.id)
    group_dn = None
    old_group_dn = None
    if participant.is_red:
        group_dn = _get_group_dn(settings.AD_RED_GROUP, settings.AD_RED_OU)
        old_group_dn = _get_group_dn(settings.AD_RED_PENDING, settings.AD_RED_OU)
    elif participant.is_green:
        group_dn = _get_group_dn(settings.AD_GREEN_GROUP, settings.AD_GREEN_OU)
        old_group_dn = _get_group_dn(settings.AD_GREEN_PENDING, settings.AD_GREEN_OU)
    remove_user_from_group(user_dn, old_group_dn)
    add_user_to_group(user_dn, group_dn)


def unapprove_user(participant):
    user_dn = get_user_dn(participant.id)
    group_dn = None
    new_group_dn = None
    if participant.is_red:
        group_dn = _get_group_dn(settings.AD_RED_GROUP, settings.AD_RED_OU)
        new_group_dn = _get_group_dn(settings.AD_RED_PENDING, settings.AD_RED_OU)
    elif participant.is_green:
        group_dn = _get_group_dn(settings.AD_GREEN_GROUP, settings.AD_GREEN_OU)
        new_group_dn = _get_group_dn(settings.AD_GREEN_PENDING, settings.AD_GREEN_OU)
    remove_user_from_group(user_dn, group_dn)
    add_user_to_group(user_dn, new_group_dn)


def get_type_choices():
    choices = []

    if get_global_setting('enable_green'):
        choices.append(('green', 'Green Team'))
    if get_global_setting('enable_red'):
        choices.append(('red', 'Red Team'))

    return choices
