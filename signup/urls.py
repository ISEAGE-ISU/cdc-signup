from django.conf.urls import patterns, include, url
from base import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'signup.views.home', name='home'),
    # url(r'^signup/', include('signup.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', views.IndexView.as_view(), name='site-index'),
    url(r'^login/$', 'base.views.login', name='site-login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name='site-logout'),

    url(r'^signup/$', views.SignupView.as_view(), name='signup'),
    url(r'^dashboard/$', views.DashboardView.as_view(), name='dashboard'),
    url(r'^forgot/$', views.ForgotPasswordView.as_view(), name='forgot-password'),

    # url(r'^join_team/$', '', name='team-list'),
    # url(r'^join_team/(?P<team_id>[0-9-_:]+)/$', '', name='join-team'),
    # url(r'^create_team/$', '', name='create-team'),
    # url(r'^leave_team/$', '', name='leave-team'),
    #
    # url(r'^manage_team/$', '', name='manage-team'),
    # url(r'^approve/(?P<participant_id>[0-9-_:]+)/$', '', name='approve-member'),
    # url(r'^approve_captain/(?P<participant_id>[0-9-_:]+)/$', '', name='approve-captain'),

)
