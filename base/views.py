from django.shortcuts import redirect
from django.views.generic.base import View, TemplateResponseMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from signup import settings
import base
import forms as base_forms
import actions

def login(request):
    context={
        'page_title':"Login",
    }
    return auth_views.login(request, template_name='login.html', extra_context=context)


class LoginRequiredMixin(object):
    """
    Including this mixin with your view will ensure the user is authenticated.
    """
    @method_decorator(login_required(login_url='/login/'))
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class BaseView(View):
    """
    Override Django's default dispatch method to include the context in handler calls.
    """
    page_title = "ISEAGE CDC Signup"

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
        return {
            'page_title': self.get_page_title(request, context),
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


class IndexView(BaseTemplateView):
    template_name = 'index.html'


class SignupView(BaseTemplateView):
    template_name = 'signup.html'

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
            except base.UsernameAlreadyExistsError:
                form.add_error('username', "That username already exists. Please choose another one.")
                return self.get(request, context, form=form)

            if success:
                messages.success(request, 'Account successfully created. Please check your email for further instructions.')
                return redirect('site-login')
            else:
                messages.error(request, """Whoops! Something went wrong.
                Please email us at {support} so we can fix it.""".format(support=settings.SUPPORT_EMAIL))

        return self.get(request, context, form=form)


class DashboardView(BaseTemplateView, LoginRequiredMixin):
    template_name = 'dashboard.html'
    page_title = "Dashboard"


class CaptainHome(BaseTemplateView, LoginRequiredMixin):
    pass


class ForgotPasswordView(BaseTemplateView):
    template_name = 'forgot.html'

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
                messages.success(request, 'Password successfully reset. Please check your email for further instructions')
                return redirect('site-login')

        return self.get(request, context, form=form)


class TeamCreationView(BaseTemplateView, LoginRequiredMixin):
    template_name = 'create_team.html'

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

        return self.get(request, context, form=form)
