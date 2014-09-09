from django.shortcuts import redirect
from django.views.generic.base import View, TemplateResponseMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404

from signup import settings
import base
from base import breadcrumbs
import forms as base_forms
import actions
import models

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
        return base.get_context(request)

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
        if '_method' in request.REQUEST:
            handler = getattr(self, request.REQUEST.get('_method'), self.http_method_not_allowed)
        elif request.method.lower() in self.http_method_names:
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
# Member views
##########
def login(request):
    this_breadcrumb = '<a href="%s" class="current">%s</a>' % ('/login', "Login")
    crumbs = mark_safe(breadcrumbs.render_breadcrumbs("/login/", {}) + this_breadcrumb)
    context={
        'page_title':"Login",
        'breadcrumbs':crumbs,
    }
    return auth_views.login(request, template_name='login.html', extra_context=context)


class IndexView(BaseTemplateView):
    template_name = 'index.html'
    page_title = "Welcome!"
    breadcrumb = 'Home'

    def get(self, request, context, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('dashboard')

        return self.render_to_response(context)


class SignupView(BaseTemplateView):
    template_name = 'signup.html'
    page_title = "Signup"
    breadcrumb = 'Signup'

    def get(self, request, context, *args, **kwargs):
        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.SignupForm()
        context['form'] = form
        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        form = base_forms.SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            first = form.cleaned_data['first_name']
            last = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            success = False
            try:
                success = actions.create_user_account(username,first,last,email)
            except base.DuplicateName:
                form.add_error('first_name', """It looks like there's already an account with the same first and last names as you provided.
                Try including your middle initial or middle name.""")
            except base.UsernameAlreadyExistsError:
                form.add_error('username', "That username already exists. Please choose another one.")
                return self.get(request, context, form=form)

            if success:
                messages.success(request, 'Account successfully created. Please check your email for further instructions.')
                return redirect('site-login')
            else:
                form.add_error(None, """Whoops! Something went wrong on our end.
                Please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL))

        return self.get(request, context, form=form)


class DashboardView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'dashboard.html'
    page_title = "Dashboard"
    breadcrumb = 'Dashboard'

    def get(self, request, context, *args, **kwargs):
        if request.user.participant:
            team = request.user.participant.team
            if team:
                context['team'] = team
            if request.user.participant.captain:
                context['is_captain'] = True

        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.ChangePasswordForm()
        context['form'] = form
        context['widget_data'] = {
            'title': 'Dashboard',
            'icon': 'fa-dashboard',
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
                form.add_error(None, """Whoops! Something went wrong on our end.
                Please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL))

        return self.get(request, context, form=form)


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

            if success:
                messages.success(request, 'Password successfully reset. Please check your email for further instructions.')
                return redirect('site-login')

        return self.get(request, context, form=form)


class TeamListView(LoginRequiredMixin, BaseTemplateView):
    template_name = 'team_list.html'
    page_title = "Join Team"
    breadcrumb = 'Team list'

    def get(self, request, context, *args, **kwargs):
        context['teams'] = actions.get_current_teams()
        context['widget_data'] = {
            'title': 'Team Members',
            'icon': 'fa-users',
        }
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
        team_id = kwargs.get('team_id')
        try:
            team = models.Team.objects.get(pk=team_id)
        except:
            raise Http404

        pt = context['participant']
        success = False
        success = actions.submit_join_request(pt.id, team.id)
        if success:
            messages.success(request, 'Request to join {team} has been successfully submitted.'.format(team=team.name))
            return redirect('dashboard')
        else:
            messages.error(request, """Whoops! Something went wrong on our end.
            Please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL))
            return redirect('dashboard')


class LeaveTeamView(LoginRequiredMixin, BaseTemplateView):
    pass


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
            except base.OutOfTeamNumbersError:
                form.add_error(None, """There are currently no slots available for new teams.
                Please email {support} and tell us this so we can fix it.""".format(support=settings.SUPPORT_EMAIL))

            if success:
                messages.success(request, 'Team {name} successfully created.'.format(name=name))
                return redirect('manage-team')
            else:
                form.add_error(None, """Whoops! Something went wrong on our end.
                Please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL))

        return self.get(request, context, form=form)


class CaptainHomeView(LoginRequiredMixin, UserIsCaptainMixin, BaseTemplateView):
    template_name = 'team_dash.html'
    page_title = 'Manage Team'
    breadcrumb = 'Manage team'

    def get(self, request, context, *args, **kwargs):
        if 'form' in kwargs:
            form = kwargs.pop('form')
        else:
            form = base_forms.UpdateTeamNameForm()
        context['form'] = form
        context['widget_data'] = {
            'title': 'Team Members',
            'icon': 'fa-users',
        }

        team = context['participant'].team
        context['current_members'] = team.members()
        context['member_requests'] = team.requested_members()
        context['captain_requests'] = team.requested_captains()

        return self.render_to_response(context)

    def post(self, request, context, *args, **kwargs):
        form = base_forms.UpdateTeamNameForm(request.POST)
        if form.is_valid():
            pt = context['participant']
            name = form.cleaned_data['name']
            success = False
            try:
                success = actions.rename_team(pt.team.id, name)
            except base.TeamAlreadyExistsError:
                form.add_error('name', "A team with that name already exists. Please choose another name.")

            if success:
                messages.success(request, 'Team name successfully updated.')
                return redirect('manage-team')

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
            if actions.add_user_to_team(team.id, participant_id):
                messages.success(request, '{first} {last} has been successfully added to your team.'.format(
                    first=participant.user.first_name,last=participant.user.last_name))
                return redirect('manage-team')
            else:
                messages.error(request, """Whoops! Something went wrong on our end.
                Please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL))
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
            if actions.add_user_to_team(team.id, participant_id):
                messages.success('{first} {last} has been successfully promoted to captain.'.format(
                    first=participant.user.first_name,last=participant.user.last_name))
                return redirect('manage-team')
            else:
                messages.error(request, """Whoops! Something went wrong on our end.
                Please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL))
                return self.render_to_response(context)
        else:
            raise Http404