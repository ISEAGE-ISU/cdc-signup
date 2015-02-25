from django import forms
from base import models, widgets


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


class UpdateTeamNameForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)

    class Meta:
        fieldsets = [{
            'id': 'rename-team',
            'legend': 'Rename Team',
            'title': "You can rename your team here."
        }]


class GlobalSettingsForm(forms.ModelForm):
    class Meta:
        model = models.GlobalSettings
        fields = '__all__'
        fieldsets = [{
            'id': 'settings',
            'legend': 'Global Settings',
            'title': 'You will need to set the LDAP Admin credentials before any LDAP operations can be performed.'
        }]

    number_of_teams = forms.IntegerField(required=True, label="Number of Teams")
    administrator_bind_dn = forms.CharField(required=True, label="LDAP administrator account")
    administrator_bind_pw = forms.CharField(required=False, label="LDAP administrator password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep same password'}))
    check_in_date = forms.DateTimeField(widget=widgets.DateTimeInput(), required=False, label="Check-in start date")
    enable_account_creation = forms.BooleanField(required=False, label="Enable account creation")
    documentation_url = forms.CharField(required=False, label="Shared Documentation URL")
