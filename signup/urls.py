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

    url(r'^join_team/$', views.TeamListView.as_view(), name='team-list'),
    url(r'^join_team/(?P<team_id>[0-9-_:]+)/$', views.JoinTeamView.as_view(), name='join-team'),
    url(r'^leave_team/$', views.LeaveTeamView.as_view(), name='leave-team'),

    url(r'^create_team/$', views.TeamCreationView.as_view(), name='create-team'),
    url(r'^manage_team/$', views.CaptainHomeView.as_view(), name='manage-team'),
    url(r'^approve_member/(?P<participant_id>[0-9-_:]+)/$', views.ApproveMemberView.as_view(), name='approve-member'),
    url(r'^approve_captain/(?P<participant_id>[0-9-_:]+)/$', views.ApproveCaptainView.as_view(), name='approve-captain'),

)
