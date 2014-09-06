from django.shortcuts import render
from django.views.generic.base import View, TemplateResponseMixin
from django.contrib.auth import views as auth_views
import base
import json

def login(request):
    context={
        'page_title':"Login",
    }
    return auth_views.login(request, template_name='login.html', extra_context=context)


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


class HomeView(BaseTemplateView):
    template_name = 'home.html'


class CaptainHome(BaseTemplateView):
    pass


class ForgotPasswordView(BaseTemplateView):
    template_name = 'forgot.html'


class TeamCreationView(BaseTemplateView):
    pass