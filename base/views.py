from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth import views as auth_views

def login(request):
    context={
        'page_title':"Login",
    }
    return auth_views.login(request, template_name='login.html', extra_context=context)


class BaseView(TemplateView):
    pass


class IndexView(BaseView):
    template_name = 'index.html'


class SignupView(BaseView):
    template_name = 'signup.html'


class HomeView(BaseView):
    template_name = 'home.html'


class CaptainHome(BaseView):
    pass


class ForgotPasswordView(BaseView):
    template_name = 'forgot.html'


class TeamCreationView(BaseView):
    pass