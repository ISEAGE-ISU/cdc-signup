from django.db.models.query_utils import Q
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import View, TemplateResponseMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404
from django.core.urlresolvers import reverse

from django.conf import settings
from base import breadcrumbs, utils
import forms as base_forms
import base
import actions
import models
from django.utils import timezone

from base.models import ArchivedEmail

TRY_AGAIN = """Whoops! Something went wrong on our end. You can try submitting the form again in a few seconds. \
If that still didn't work, please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL)

WHOOPS = """Whoops! Something went wrong on our end. \
Please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL)

CREATION_DISABLED = """Account Creation is currently disabled. \
Email us at {support} if you need to make an account.""".format(support=settings.SUPPORT_EMAIL)


##########
# Base Classes
##########
class LoginRequiredMixin(object):
    """
    Including this mixin with your view will ensure the user is authenticated.
    """
    @method_decorator(login_required(login_url='/login/'))
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class UserIsCaptainMixin(object):
    """
    Verify that the user is a captain.
    """
    test_pass = lambda u: u.participant.user_is_captain()

    @method_decorator(user_passes_test(test_pass))
    def dispatch(self, *args, **kwargs):
        return super(UserIsCaptainMixin, self).dispatch(*args, **kwargs)


class UserIsAdminMixin(object):
    """
    Verify that the user is a superuser.
    """
    test_pass = lambda u: u.participant.user.is_superuser

    @method_decorator(user_passes_test(test_pass))
    def dispatch(self, *args, **kwargs):
        return super(UserIsAdminMixin, self).dispatch(*args, **kwargs)


class BaseView(View):
    """
    Override Django's default dispatch method to include the context in handler calls.
    """
    page_title = "ISEAGE CDC Signup"
    breadcrumb = "Breadcrumb"

    # Override this method in a subclass if the page title cannot be a simple string.
    # E.g. contains some kind of variable.
    def get_page_title(self, request, context):
        return self.page_title

    # This function is used to get the context for the current app. e.g. base has a different
    # default context than blue or green.
    def app_context(self, request):
        return actions.get_context(request)

    # This function is used to add class properties to the context, such as page_title.
    def _view_context(self, request, context, *args, **kwargs):
        crumbs = breadcrumbs.render_breadcrumbs(request.get_full_path(), context)
        return {
            'page_title': self.get_page_title(request, context),
            'breadcrumbs': mark_safe(crumbs),
        }

    def modify_context(self, request, context, *args, **kwargs):
        pass

    def dispatch(self, request, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        self.request = request
        self.args = args
        self.kwargs = kwargs

        # Setup the app context for the particular area
        context = self.app_context(request)

        # Let the subclasses add/edit items in the context before calling the method handler.
        self.modify_context(request, context, *args, **kwargs)

        # _view_context is used by other superclass views to add class properties to the context,
        # such as the page title.
        view_context = getattr(self, '_view_context', {})
        if callable(view_context):
            view_context = view_context(request, context, *args, **kwargs)
        context.update(view_context)

        return handler(request, context, *args, **kwargs)

    def get(self, request, context, *args, **kwargs):
        raise NotImplementedError("GET method not implemented on the view.")

    def post(self, request, context, *args, **kwargs):
        raise NotImplementedError("POST method not implemented on the view.")

    def put(self, request, context, *args, **kwargs):
        raise NotImplementedError("PUT method not implemented on the view.")

    def delete(self, request, context, *args, **kwargs):
        raise NotImplementedError("DELETE method not implemented on the view.")

    def head(self, request, context, *args, **kwargs):
        raise NotImplementedError("HEAD method not implemented on the view.")


class BaseTemplateView(BaseView, TemplateResponseMixin):

    def get(self, request, context, *args, **kwargs):
        return self.render_to_response(context)


##########
# Admin views
##########
class AdminDashboard(LoginRequiredMixin, UserIsAdminMixin, BaseTemplateView):
    template_name = 'admin_dash.html'
    page_title = "Admin Dashboard"
    breadcrumb = "Admin"

    def modify_context(self, request, context, *args, **kwargs):
        context['g_setting'] = actions.get_global_settings_object()

    def get(self, request, context, *args, **kwargs):
        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.GlobalSettingsForm(instance=context['g_setting'])
        context['form'] = form
        context['enable_red'] = context['g_setting'].enable_red
        context['enable_green'] = context['g_setting'].enable_green
        if request.GET.get('email_list'):
            context['emails'] = User.objects.filter(is_superuser=False).values_list('email', flat=True)

        context['archive'] = models.ArchivedEmail.objects.all()
        context['participant_approvals'] = {
            'title': 'Red/Green Approvals',
            'icon': 'fa-check',
        }
        context['email_list'] = {
            'title': 'Participant Email Addresses',
            'icon': 'fa-paper-plane-o',
        }
        context['email_archive'] = {
            'title': 'Email Archive',
            'icon': 'fa-book'
        }
        context['danger_zone'] = {
            'title': 'Danger Zone',
            'icon': 'fa-exclamation-triangle',
        }
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        initial_pass = actions.get_global_setting('administrator_bind_pw')
        form = base_forms.GlobalSettingsForm(request.POST, request.FILES, instance=context['g_setting'])
        if form.is_valid():
            gs = form.save(commit=False)
            if not gs.administrator_bind_pw:
                gs.administrator_bind_pw = initial_pass
            gs.save()
            messages.success(request, 'Global settings successfully updated.')
        return self.get(request, context, form=form)


class RedGreenApprovals(LoginRequiredMixin, UserIsAdminMixin, BaseTemplateView):
    template_name = 'admin/approvals.html'
    page_title = "Red/Green Approvals"
    breadcrumb = "Approvals"

    def get(self, request, context, *args, **kwargs):
        redgreen = models.Participant.objects.filter(Q(is_red=True) | Q(is_green=True))

        context['pending'] = redgreen.filter(approved=False)
        context['approved'] = redgreen.filter(approved=True)

        context['pending_widget'] = {
            'title': 'Participants Pending Approval',
            'icon': 'fa-adjust',
        }
        context['approved_widget'] = {
            'title': "Approved Participants",
            'icon': 'fa-check',
        }

        return self.render_to_response(context)


class RedGreenApprove(LoginRequiredMixin, UserIsAdminMixin, BaseTemplateView):
    def get(self, request, context, *args, **kwargs):
        participant = models.Participant.objects.get(pk=kwargs['participant_id'])
        participant.approve()
        return redirect(reverse('admin-approvals'))


class RedGreenUnapprove(LoginRequiredMixin, UserIsAdminMixin, BaseTemplateView):
    def get(self, request, context, *args, **kwargs):
        participant = models.Participant.objects.get(pk=kwargs['participant_id'])
        participant.unapprove()
        return redirect(reverse('admin-approvals'))


class AdminCompetitionResetView(LoginRequiredMixin, UserIsAdminMixin, BaseTemplateView):
    template_name = 'competition_reset.html'
    page_title = "Competition Reset"
    breadcrumb = "Reset"

    def get(self, request, context, *args, **kwargs):
        context['team_count'] = models.Team.objects.count()
        context['participant_count'] = models.Participant.objects.exclude(user__is_superuser=True).count()
        context['reset'] = {
            'title': 'Competition Reset',
            'icon': 'fa-exclamation-triangle',
        }
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        models.Team.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        ArchivedEmail.objects.all().delete()
        messages.success(request, 'Competition successfully reset.')
        return redirect('admin-dash')


class AdminSendEmailView(LoginRequiredMixin, UserIsAdminMixin, BaseTemplateView):
    template_name = 'admin_email.html'
    page_title = "Send Email"
    breadcrumb = "Email"

    def get(self, request, context, *args, **kwargs):
        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.AdminEmailForm()
        context['form'] = form

        context['email_form'] = {
            'title': 'Send Email to Participants',
            'icon': 'fa-paper-plane-o',
        }
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        form = base_forms.AdminEmailForm(data=request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            content = form.cleaned_data['content']
            audience = form.cleaned_data['send_to']

            content += "\n\n" + request.user.get_full_name()
            actions.email_participants(subject, content, audience, request.user)
            messages.success(request, 'Sent Email to Participants')
            return redirect(reverse('admin-dash'))
        return self.get(request, context, form=form)


##########
# Member views
##########
def login(request):
    this_breadcrumb = u'<a href="{link}" class="current">{text}</a>'.format(link='/login', text="Login")
    crumbs = mark_safe(breadcrumbs.render_breadcrumbs("/login/", {}) + this_breadcrumb)
    context= {
        'page_title': "Login",
        'breadcrumbs': crumbs,
    }
    return auth_views.login(request, template_name='login.html', extra_context=context)

def logout(request):
    messages.success(request, "You have been successfully logged out.")
    return auth_views.logout(request, next_page='site-index')

class IndexView(BaseTemplateView):
    template_name = 'index.html'
    page_title = "Welcome!"
    breadcrumb = 'Home'

    def get(self, request, context, *args, **kwargs):
        admin_bind_dn = actions.get_global_setting('administrator_bind_dn')
        context['enable_creation'] = actions.get_global_setting('enable_account_creation')
        context['enable_green'] = actions.get_global_setting('enable_green')
        context['enable_red'] = actions.get_global_setting('enable_red')
        if not admin_bind_dn:
            if request.user.is_authenticated():
                messages.success(request, 'Setup your CDC here.')
            else:
                messages.success(request, 'Login to setup your CDC.')
            return redirect('admin-dash')

        if request.user.is_authenticated():
            if request.user.is_superuser:
                return redirect('admin-dash')
            else:
                return redirect('dashboard')

        return self.render_to_response(context)


class SignupView(BaseTemplateView):
    template_name = 'signup.html'
    page_title = "Signup"
    breadcrumb = 'Signup'

    def get(self, request, context, *args, **kwargs):
        enabled = actions.get_global_setting('enable_account_creation')
        if not enabled:
            messages.error(request, CREATION_DISABLED)
            return redirect('site-index')

        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.SignupForm()
        context['form'] = form
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        enabled = actions.get_global_setting('enable_account_creation')
        if not enabled:
            messages.error(request, CREATION_DISABLED)
            return redirect('site-index')

        form = base_forms.SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            first = form.cleaned_data['first_name']
            last = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            success = False
            try:
                success = actions.create_user_account(username, first, last, email)
            except base.DuplicateName:
                form.add_error('first_name', """It looks like there's already an account with the same first and last names as you provided. \
                Try including your middle initial or middle name.""")
            except base.UsernameAlreadyExistsError:
                form.add_error('username', "That username already exists. Please choose another one.")
                return self.get(request, context, form=form)
            if success:
                messages.success(request, 'Account successfully created. Please check your email for further instructions.')
                return redirect('site-login')
            else:
                messages.error(request, TRY_AGAIN)

        return self.get(request, context, form=form)


class RedGreenSignupView(BaseTemplateView):
    template_name = 'signup.html'
    page_title = "Red/Green Signup"
    breadcrumb = "Red/Green"

    def get(self, request, context, *args, **kwargs):
        enabled_red = actions.get_global_setting('enable_red')
        enabled_green = actions.get_global_setting('enable_green')
        enabled = enabled_red or enabled_green

        if not enabled:
            messages.error(request, CREATION_DISABLED)
            return redirect('site-index')

        start_value = request.GET.get('type')
        initial_data = {'acct_type': start_value}

        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.RedGreenSignupForm(initial=initial_data)
        context['form'] = form
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        enabled = actions.get_global_setting('enable_red') or actions.get_global_setting('enable_green')
        if not enabled:
            messages.error(request, CREATION_DISABLED)
            return redirect('site-index')

        form = base_forms.RedGreenSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            first = form.cleaned_data['first_name']
            last = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            acct_type = form.cleaned_data['acct_type']
            success = False
            try:
                success = actions.create_account(username, first,
                        last, email, acct_type)
            except base.DuplicateName:
                form.add_error('first_name', """It looks like there's already an account with the same first and last names as your provided. \
                Try including your middle initial or middle name.""")
            except base.UsernameAlreadyExistsError:
                form.add_error('username', "That username already exists. Please choose another one.")
                return self.get(request, context, form=form)
            if success:
                # Update the participant object since it is created throught
                # a signal rather than directly
                user = User.objects.get(username=username)
                if acct_type == 'red':
                    user.participant.is_red = True
                elif acct_type == 'green':
                    user.participant.is_green = True
                user.participant.save()
                messages.success(request, 'Account successfully created. Please check your email for further instructions.')
                return redirect('site-login')
            else:
                messages.error(request, TRY_AGAIN)

        return self.get(request, context, form=form)


class DashboardView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'dashboard.html'
    page_title = "Dashboard"
    breadcrumb = 'Dashboard'

    def get(self, request, context, *args, **kwargs):
        participant = request.user.participant
        if participant:
            if not participant.checked_in:
                now = timezone.now()
                check_in_date = actions.get_global_setting('check_in_date')
                if check_in_date:
                    if now > check_in_date:
                        context['check_in'] = True
            requested_team = participant.requested_team
            if requested_team:
                context['requested_team'] = requested_team
            team = participant.team
            if team:
                context['team'] = team
                context['current_members'] = team.members()
                context['captain_requested'] = participant.requests_captain
            else:
                context['looking_for_team'] = participant.looking_for_team
            if participant.captain:
                context['is_captain'] = True
            if participant.is_redgreen:
                context['is_redgreen'] = True
                context['is_green'] = participant.is_green
                context['is_red'] = participant.is_red

        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.ChangePasswordForm()
        context['form'] = form
        context['widget_data'] = {
            'title': 'Dashboard',
            'icon': 'fa-dashboard',
        }
        context['docs_url'] = actions.get_global_setting('documentation_url')
        context['download_docs'] = {
            'title': 'Scenario Documents',
            'icon': 'fa-file',
        }

        context['competition_name'] = actions.get_global_setting('competition_name')
        context['competition_date'] = actions.get_global_setting('competition_date')
        context['rules_version'] = actions.get_global_setting('rules_version')

        context['archived_emails'] = models.ArchivedEmail.objects.filter(audience__in=utils.get_user_audience(request.user))

        context['important_info'] = {
            'title': 'Important Information',
            'icon': 'fa-book',
        }

        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        form = base_forms.ChangePasswordForm(request.POST)
        if form.is_valid():
            pt = request.user.participant
            old = form.cleaned_data['old_password']
            new = form.cleaned_data['new_password']
            success = False
            try:
                success = actions.update_password(pt.id, old, new)
            except base.PasswordMismatchError:
                form.add_error('old_password', "The password you entered does not match the one found in our records.")

            if success:
                messages.success(request, 'Password successfully updated.')
                return redirect('site-login')
            else:
                messages.error(request, WHOOPS)
        return self.get(request, context, form=form)


class ArchiveEmailView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'email_view.html'
    page_title = 'Archived Email'
    breadcrumb = 'Archived Email'

    def modify_context(self, request, context, *args, **kwargs):
        context['archived'] = get_object_or_404(models.ArchivedEmail, pk=kwargs['email_id'])

    def get_page_title(self, request, context):
        return "Archive: " + context['archived'].subject

    def get(self, request, context, *args, **kwargs):
        if not utils.user_in_audience(request.user, context['archived'].audience):
            messages.warning(request, "You are not in the audience for this email")
            return redirect(reverse('site-index'))

        # If this is not here, the context entry will
        # not exist after rendering. WTF.
        context['archived'] = context['archived']
        return self.render_to_response(context)


class ToggleLFTView(BaseView):
    def get(self, request, context, *args, **kwargs):
        participant = request.user.participant

        if participant.team:
            messages.error(request, "You are already on a team")
            participant.looking_for_team = False
            participant.save()
            return redirect(reverse('dashboard'))

        participant.looking_for_team = not participant.looking_for_team
        participant.save()

        if participant.looking_for_team:
            messages.success(request, 'You are "Looking For Team", ISEAGE will place you on a team if you cannot find one')
        else:
            messages.success(request, 'You are no longer "Looking for Team"')

        return redirect(reverse('dashboard'))


class ForgotPasswordView(BaseTemplateView):
    template_name = 'forgot.html'
    page_title = "Forgot your password?"
    breadcrumb = 'Reset password'

    def get(self, request, context, *args, **kwargs):
        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.ForgotPasswordForm()
        context['form'] = form
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        form = base_forms.ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            success = False
            try:
                success = actions.forgot_password(email)
            except User.DoesNotExist:
                form.add_error('email', "No account with that email exists.")
                return self.get(request, context, form=form)

            if success:
                messages.success(request, 'Password successfully reset. Please check your email for further instructions.')
                return redirect('site-login')
            else:
                messages.error(request, WHOOPS)

        return self.get(request, context, form=form)


class TeamListView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'team_list.html'
    page_title = "Join Team"
    breadcrumb = 'Team list'

    def get(self, request, context, *args, **kwargs):
        teams = actions.get_current_teams()
        if len(teams):
            context['teams'] = actions.get_current_teams()
        return self.render_to_response(context)


class JoinTeamView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'join_team.html'
    page_title = "Team Join Request"
    breadcrumb = 'Join Team'

    def get(self, request, context, *args, **kwargs):
        team_id = kwargs.get('team_id')
        try:
            team = models.Team.objects.get(pk=team_id)
            context['team'] = team
        except:
            raise Http404

        context['widget_data'] = {
            'title': 'Join Team',
            'icon': 'fa-question-circle',
        }
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        if request.user.is_superuser:
            messages.warning(request, "Joining Teams as a super user is disabled for your safety")
            return redirect('dashboard')
        team_id = kwargs.get('team_id')
        try:
            team = models.Team.objects.get(pk=team_id)
        except:
            raise Http404

        pt = context['participant']
        success = False
        if team.is_full():
            messages.error(request, u"Request to join team {} failed; this team is already full".format(team.name))
            return redirect('dashboard')
        if team.looking_for_members:
            if actions.join_team(pt.id, team.id):
                messages.success(request, u'You have successfully joined Team {team}.'.format(team=team.name))
            return redirect('dashboard')
        elif actions.submit_join_request(pt.id, team.id):
            messages.success(request, u'Request to join {team} has been successfully submitted.'.format(team=team.name))
            return redirect('dashboard')
        else:
            messages.error(request, TRY_AGAIN)
            return redirect('dashboard')


class RequestCaptainView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'request_captain.html'
    page_title = "Request Captain"
    breadcrumb = 'Request Captain'

    def get(self, request, context, *args, **kwargs):
        team = request.user.participant.team
        if team:
            context['team'] = team
            context['widget_data'] = {
                'title': 'Confirm request',
                'icon': 'fa-question',
            }
            return self.render_to_response(context)
        else:
            messages.error(request, "You must join a team before requesting to become a captain.")
            return redirect('dashboard')

    def post(self, request, context, *args, **kwargs):
        team = request.user.participant.team
        if team:
            success = actions.sumbit_captain_request(request.user.participant.id)
            if success:
                messages.success(request, "Captain request successfully submitted.")
            else:
                messages.error(request, TRY_AGAIN)
                return self.render_to_response(context)
        else:
            messages.error(request, "You must join a team before requesting to become a captain.")
        return redirect('dashboard')


class LeaveTeamView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'leave_team.html'
    page_title = "Leave Team"
    breadcrumb = 'Leave Team'

    def get(self, request, context, *args, **kwargs):
        team = request.user.participant.team
        if team:
            context['team'] = team
            context['widget_data'] = {
                'title': 'Confirm request',
                'icon': 'fa-question',
            }
            return self.render_to_response(context)
        else:
            messages.error(request, "You aren't currently a member of a team.")
            return redirect('dashboard')

    def post(self, request, context, *args, **kwargs):
        team = request.user.participant.team
        if team:
            success = actions.leave_team(request.user.participant.id)
            if success:
                messages.success(request, u"You have successfully left {name}.".format(name=team.name))
            else:
                messages.error(request, TRY_AGAIN)
                return self.render_to_response(context)
        else:
            messages.error(request, "You aren't currently a member of a team.")
        return redirect('dashboard')


class CheckInView(LoginRequiredMixin, BaseTemplateView):
    template_name = "check_in.html"
    page_title = "Check In"
    breadcrumb = "Check in"

    def get(self, request, context, *args, **kwargs):
        try:
            participant = request.user.participant
        except:
            raise Http404

        if not participant.checked_in:
            context['widget_data'] = {
                'title': 'Check In',
                'icon': 'fa-check',
            }
            return self.render_to_response(context)
        else:
            messages.warning(request, 'You have already checked in.')
            return redirect('dashboard')

    def post(self, request, context, *args, **kwargs):
        try:
            participant = request.user.participant
        except:
            raise Http404
        if not participant.checked_in:
            participant.check_in()
            messages.success(request, 'You have successfully checked in.')
            return redirect('dashboard')
        else:
            raise Http404


##########
# Captain views
##########
class TeamCreationView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'create_team.html'
    page_title = "Create Team"
    breadcrumb = 'Create team'

    def get(self, request, context, *args, **kwargs):
        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.CreateTeamForm()
        context['form'] = form
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        form = base_forms.CreateTeamForm(request.POST)
        if form.is_valid():
            if request.user.is_superuser:
                messages.warning(request, 'Team creation by Superusers is disabled for your safety.')
                return self.get(request, context, form=form)

            pt = context['participant']
            name = form.cleaned_data['name']
            success = False
            try:
                success = actions.create_team(name, pt.id)
            except base.TeamAlreadyExistsError:
                form.add_error('name', "A team with that name already exists. Please choose another name.")
                return self.get(request, context, form=form)
            except base.OutOfTeamNumbersError:
                form.add_error(None, """There are currently no slots available for new teams. \
                Please email {support} and tell us this so we can fix it.""".format(support=settings.SUPPORT_EMAIL))
                return self.get(request, context, form=form)

            if success:
                messages.success(request, u'Team {name} successfully created.'.format(name=name))
                return redirect('manage-team')
            else:
                messages.error(request, WHOOPS)

        return self.get(request, context, form=form)


class CaptainHomeView(LoginRequiredMixin, UserIsCaptainMixin, BaseTemplateView):
    template_name = 'team_dash.html'
    page_title = 'Manage Team'
    breadcrumb = 'Manage team'

    def get(self, request, context, *args, **kwargs):
        team = context['participant'].team
        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.ModifyTeamForm(instance=team)
        context['form'] = form
        context['widget_data'] = {
            'title': 'Team Members',
            'icon': 'fa-users',
        }
        context['danger_widget_data'] = {
            'title': 'Danger area',
            'icon': 'fa-warning',
        }

        context['current_members'] = team.members()
        context['member_requests'] = team.requested_members()
        context['captain_requests'] = team.requested_captains()

        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        team = context['participant'].team
        form = base_forms.ModifyTeamForm(data=request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team successfully updated.')
            return redirect('manage-team')
        #If the form was invalid, get the old participant object back
        context['participant'] = request.user.participant
        return self.get(request, context, form=form)


class ApproveMemberView(LoginRequiredMixin, UserIsCaptainMixin, BaseTemplateView):
    template_name = 'approve_member.html'
    page_title = 'Confirm Member Approval'
    breadcrumb = 'Approve Member'

    def get(self, request, context, *args, **kwargs):
        participant_id = kwargs.get('participant_id')
        try:
            team = request.user.participant.team
            participant = models.Participant.objects.get(pk=participant_id)
        except:
            raise Http404

        if participant.requested_team == team:
            context['member'] = participant
            context['widget_data'] = {
                'title': 'Confirm approval',
                'icon': 'fa-question',
            }
            return self.render_to_response(context)
        else:
            raise Http404

    def post(self, request, context, *args, **kwargs):
        participant_id = kwargs.get('participant_id')
        try:
            team = request.user.participant.team
            participant = models.Participant.objects.get(pk=participant_id)
        except:
            raise Http404

        if participant.requested_team == team:
            if team.is_full():
                messages.error(request, 'Your team is already full.')
                return redirect('manage-team')
            if actions.add_user_to_team(team.id, participant_id):
                messages.success(request, u'{first} {last} has been successfully added to your team.'.format(
                    first=participant.user.first_name,last=participant.user.last_name))
                return redirect('manage-team')
            else:
                messages.error(request, WHOOPS)
                return self.render_to_response(context)
        else:
            messages.error(request, 'No such join request.')
            return redirect('manage-team')


class ApproveCaptainView(LoginRequiredMixin, UserIsCaptainMixin, BaseTemplateView):
    template_name = 'approve_captain.html'
    page_title = 'Confirm Captain Approval'
    breadcrumb = 'Approve Captain'

    def get(self, request, context, *args, **kwargs):
        participant_id = kwargs.get('participant_id')
        try:
            team = request.user.participant.team
            participant = models.Participant.objects.get(pk=participant_id)
        except:
            raise Http404

        if participant.team.id == team.id and participant.requests_captain:
            context['member'] = participant
            context['widget_data'] = {
                'title': 'Confirm approval',
                'icon': 'fa-question',
            }
            return self.render_to_response(context)
        else:
            raise Http404

    def post(self, request, context, *args, **kwargs):
        participant_id = kwargs.get('participant_id')
        try:
            team = request.user.participant.team
            participant = models.Participant.objects.get(pk=participant_id)
        except:
            raise Http404
        if participant.team.id == team.id and participant.requests_captain:
            if actions.promote_to_captain(participant.id):
                messages.success(request, u'{first} {last} has been successfully promoted to captain.'.format(
                    first=participant.user.first_name,last=participant.user.last_name))
                return redirect('manage-team')
            else:
                messages.error(request, WHOOPS)
                context['widget_data'] = {
                    'title': 'Confirm approval',
                    'icon': 'fa-question',
                }
                return self.render_to_response(context)
        else:
            raise Http404


class StepDownView(LoginRequiredMixin, UserIsCaptainMixin, BaseTemplateView):
    template_name = 'step_down.html'
    page_title = "Step Down as Captain"
    breadcrumb = 'Step down'

    def get(self, request, context, *args, **kwargs):
        team = request.user.participant.team
        if team:
            context['team'] = team
            context['widget_data'] = {
                'title': 'Confirm action',
                'icon': 'fa-question',
            }
            return self.render_to_response(context)
        else:
            messages.error(request, "You aren't currently a member of a team.")
            return redirect('dashboard')

    def post(self, request, context, *args, **kwargs):
        team = request.user.participant.team
        context['widget_data'] = {
                'title': 'Confirm action',
                'icon': 'fa-question',
        }
        if team:
            try:
                success = actions.demote_captain(request.user.participant.id)
            except base.OnlyRemainingCaptainError:
                messages.error(request, "You are the only remaining captain of this team. You must promote someone else to captain before stepping down.")
                return redirect('dashboard')
            if success:
                messages.success(request, u"You have successfully stepped down as a captain of {name}.".format(name=team.name))
            else:
                messages.error(request, TRY_AGAIN)
                return self.render_to_response(context)
        else:
            messages.error(request, "You aren't currently a member of a team.")
        return redirect('dashboard')


class DisbandTeamView(LoginRequiredMixin, UserIsCaptainMixin, BaseTemplateView):
    template_name = 'disband.html'
    page_title = "Disband Team"
    breadcrumb = 'Disband team'

    def get(self, request, context, *args, **kwargs):
        team = request.user.participant.team
        if team:
            context['team'] = team
            context['widget_data'] = {
                'title': 'Disband team',
                'icon': 'fa-warning',
            }
            return self.render_to_response(context)
        else:
            messages.error(request, "You aren't currently a member of a team.")
            return redirect('dashboard')

    def post(self, request, context, *args, **kwargs):
        team = request.user.participant.team
        if team:
            name = team.name
            success = actions.disband_team(request.user.participant.id)
            if success:
                messages.success(request, "{name} has been successfully disbanded.".format(name=name))
            else:
                messages.error(request, TRY_AGAIN)
                return self.render_to_response(context)
        else:
            messages.error(request, "You aren't currently a member of a team.")
        return redirect('dashboard')
