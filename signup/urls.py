from django.conf.urls import include, url
from base import views
from signup import settings
from . import admin as custom_admin

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.contrib.auth.models import User, Group
admin.autodiscover()
admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.register(User, custom_admin.CustomUserAdmin)

handler403 = 'signup.errors.error403'
handler404 = 'signup.errors.error404'
handler500 = 'signup.errors.error500'

urlpatterns = (
    # Examples:
    # url(r'^$', 'signup.views.home', name='home'),
    # url(r'^signup/', include('signup.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^django-admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^django-admin/', include(admin.site.urls)),

    url(r'^admin/$', views.AdminDashboard.as_view(), name='admin-dash'),
    url(r'^admin/email/$', views.AdminSendEmailView.as_view(), name='admin-email'),
    url(r'^admin/reset/$', views.AdminCompetitionResetView.as_view(), name='admin-reset'),
    url(r'^admin/approvals/$', views.RedGreenApprovals.as_view(), name='admin-approvals'),
    url(r'^admin/approvals/(?P<participant_id>\d+)/approve', views.RedGreenApprove.as_view(), name='admin-approve'),
    url(r'^admin/approvals/(?P<participant_id>\d+)/unapprove', views.RedGreenUnapprove.as_view(), name='admin-unapprove'),

    url(r'^$', views.IndexView.as_view(), name='site-index'),
    url(r'^login/$', views.LoginView.as_view(), name='site-login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='site-logout'),

    url(r'^signup/$', views.SignupView.as_view(), name='signup'),
    url(r'^signup/red/$', views.RedLanding.as_view(), name="red_signup"),
    url(r'^signup/red/real/$', views.RedSignup.as_view(), name='red_signup_real'),
    url(r'^signup/green/$', views.GreenSignup.as_view(), name="green_signup"),
    url(r'^forgot/$', views.ForgotPasswordView.as_view(), name='forgot-password'),

    url(r'^dashboard/$', views.DashboardView.as_view(), name='dashboard'),

    url(r'^dashboard/check_in/$', views.CheckInView.as_view(), name='check-in'),
    url(r'^dashboard/join_team/$', views.TeamListView.as_view(), name='team-list'),
    url(r'^dashboard/join_team/(?P<team_id>[0-9-_:]+)/$', views.JoinTeamView.as_view(), name='join-team'),
    url(r'^dashboard/leave_team/$', views.LeaveTeamView.as_view(), name='leave-team'),
    url(r'^dashboard/request_captain/$', views.RequestCaptainView.as_view(), name='request-promotion'),
    url(r'^dashboard/step_down/$', views.StepDownView.as_view(), name='step-down'),
    url(r'^dashboard/create_team/$', views.TeamCreationView.as_view(), name='create-team'),
    url(r'^dashboard/toggle_lft/$', views.ToggleLFTView.as_view(), name='toggle-lft'),

    url(r'^dashboard/manage_team/$', views.CaptainHomeView.as_view(), name='manage-team'),
    url(r'^dashboard/manage_team/approve_member/(?P<participant_id>[0-9-_:]+)/$', views.ApproveMemberView.as_view(), name='approve-member'),
    url(r'^dashboard/manage_team/approve_captain/(?P<participant_id>[0-9-_:]+)/$', views.ApproveCaptainView.as_view(), name='approve-captain'),
    url(r'^dashboard/manage_team/disband/$', views.DisbandTeamView.as_view(), name='disband-team'),

    url(r'^archive/(?P<email_id>\d+)/$', views.ArchiveEmailView.as_view(), name='archive-email'),

)

# if settings.DEBUG:
#     urlpatterns += [
#         url(r'^403/$', 'signup.errors.error403', name='403'),
#         url(r'^404/$', 'signup.errors.error404', name='404'),
#         url(r'^500/$', 'signup.errors.error500', name='500'),
#     ]
