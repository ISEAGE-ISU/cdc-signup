from crispy_forms.bootstrap import PrependedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Div, ButtonHolder, Submit, Fieldset
from django import forms

from base import models, widgets, actions
from base.utils import AUDIENCE_CHOICES


class BaseFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(BaseFormHelper, self).__init__(*args, **kwargs)
        self.form_class = 'form-horizontal'
        self.label_class = 'col-lg-2'
        self.field_class = 'col-lg-8'

    def add_control_box(self):
        """
        Adds a control box to the layout.

        Mutually  exclusive with add_widget_box.
        """
        new_layout = Layout(
            Div(
                *self.layout,
                css_class='fieldset-container'
            ),
            ButtonHolder(
                Submit('Submit', 'Submit', style=""),
                css_class='form-actions'
            ),
        )
        self.layout = new_layout

    def add_widget_box(self, title, icon, extra_buttons=None):
        """
        Adds a widget box to the layout.
        """
        if not extra_buttons or not isinstance(extra_buttons, list):
            extra_buttons = []

        new_layout = Layout(
            Div(
                Div(
                    HTML(
                        '<span class="icon"><i class="' + icon + '"></i></span><h5>' + title + '</h5>'
                    ),
                    css_class='widget-title'
                ),
                Div(
                    Div(
                        *self.layout,
                        css_class='fieldset-container'
                    ),
                    ButtonHolder(
                        Submit('Submit', 'Submit', style=""),
                        *extra_buttons,
                        css_class='form-actions'
                    ),
                    css_class='widget-content nopadding'
                ),
                css_class='widget-box'
            )
        )
        self.layout = new_layout


class SignupForm(forms.Form):
    email = forms.EmailField(label="Email", required=True)
    email_again = forms.EmailField(label="Email (again)", required=True)
    first_name = forms.CharField(label="First name", required=True)
    last_name = forms.CharField(label="Last name", required=True)
    username = forms.CharField(label="Desired username", max_length=40, required=True)

    class Meta:
        fieldsets = [{
            'id': 'signup',
            'legend': 'Create an account',
            'title': 'Enter your information and you will receive an email with further instructions.'
        }]

    def clean(self):
        cleaned_data = super(SignupForm, self).clean()
        if cleaned_data.get('email') != cleaned_data.get('email_again'):
            raise forms.ValidationError("The email addresses you inputted do not match.")
        if " " in cleaned_data.get('username').strip():
            raise forms.ValidationError("Please choose a username without spaces. Note: trailing and leading spaces are automatically ignored.")


class RedGreenSignupForm(SignupForm):
    acct_type = forms.ChoiceField(choices=actions.get_type_choices,
                                  widget=forms.RadioSelect())


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    new_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    new_password_again = forms.CharField(widget=forms.PasswordInput(), required=True)

    class Meta:
        fieldsets = [{
            'id': 'update-password',
            'legend': 'Change Password',
            'title': 'Your password should be at least 8 characters long.<br>' +
                     'Passwords must contain a lowercase letter, an uppercase letter, and a number or symbol.'
        }]

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        if cleaned_data.get('new_password') != cleaned_data.get('new_password_again'):
            raise forms.ValidationError("The passwords you inputted do not match.")


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(required=True)

    class Meta:
        fieldsets = [{
            'id': 'forgot-password',
            'legend': 'Reset Password',
            'title': 'Enter your email and you will receive an email with a new password.'
        }]


class CreateTeamForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)

    class Meta:
        fieldsets = [{
            'id': 'create-team',
            'legend': 'New Team',
            'title': "Enter a name for your team. Don't worry, you can change it later."
        }]


class ModifyTeamForm(forms.ModelForm):
    class Meta:
        model = models.Team
        fields = ['name', 'looking_for_members']
        fieldsets = [{
            'id': 'modify-team',
            'legend': 'Modify Team',
            'title': "You can modify your team here. If your team is full, uncheck \"Looking for members\".",
        }]

    def clean(self):
        cleaned_data = super(ModifyTeamForm, self).clean()
        if cleaned_data.get('looking_for_members') and self.instance.is_full():
            raise forms.ValidationError("Your team is already full, please uncheck \"Looking for members\".")


class GlobalSettingsForm(forms.ModelForm):
    class Meta:
        model = models.GlobalSettings
        fields = [
            'number_of_teams', 'max_team_size', 'administrator_bind_dn', 'administrator_bind_pw', 'competition_name',
            'competition_date', 'competition_prefix', 'check_in_date', 'documentation_url', 'green_docs_url',
            'red_docs_url', 'rules_version', 'enable_account_creation', 'enable_red', 'enable_green',
            'certificate_template',
        ]
        fieldsets = [{
            'id': 'settings',
            'legend': 'Global Settings',
            'title': 'You will need to set the LDAP Admin credentials before any LDAP operations can be performed.'
        }]

    number_of_teams = forms.IntegerField(required=True, label="Number of Teams")
    administrator_bind_dn = forms.CharField(required=True, label="LDAP administrator account")
    administrator_bind_pw = forms.CharField(required=False, label="LDAP administrator password",
                                            widget=forms.PasswordInput(
                                                attrs={'placeholder': 'Leave blank to keep same password'}))
    check_in_date = forms.SplitDateTimeField(widget=widgets.DateTimeInput(), required=False, label="Check-in start date")
    enable_account_creation = forms.BooleanField(required=False, label="Enable account creation")
    documentation_url = forms.URLField(required=False, label="Blue Documentation URL")
    green_docs_url = forms.URLField(required=False, label="Green Documentation URL")
    red_docs_url = forms.URLField(required=False, label="Red Documentation URL")
    competition_date = forms.SplitDateTimeField(widget=widgets.DateTimeInput(), required=False, label="Competition date")


class AdminEmailForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(AdminEmailForm, self).__init__(*args, **kwargs)

        competition_prefix = actions.get_global_setting('competition_prefix')
        if competition_prefix:
            subject = PrependedText('subject', '<span title="Will be prepended to the subject line">[{}]</span>'.format(
                competition_prefix))
        else:
            subject = 'subject'

        self.helper = BaseFormHelper()
        self.helper.layout = [
            HTML(
                '<p class="title">Below, you can send an email to all participants from the cdc support email address.'),
            subject, 'content', 'send_to',
        ]
        self.helper.add_widget_box('Email', 'fa fa-paper-plane-o')
        self.helper.form_id = 'simple-form'

    subject = forms.CharField(required=True, label="Subject")
    content = forms.CharField(required=True, widget=forms.Textarea, label="Body")
    send_to = forms.ChoiceField(choices=AUDIENCE_CHOICES, widget=forms.RadioSelect(), required=True)
