from django import forms


class SignupForm(forms.Form):
    email = forms.EmailField(label="Email", required=True)
    email_again = forms.EmailField(label="Email (again)", required=True)
    first_name = forms.CharField(label="First name", required=True)
    last_name = forms.CharField(label="Last name", required=True)
    username = forms.CharField(label="Desired username", max_length=40, required=True)

    class Meta:
        fieldsets = [{
                'id':'signup',
                'legend':'Create an account',
                'title':'Enter your information and you will receive an email with further instructions.'
        }]

    def clean(self):
        cleaned_data = super(SignupForm, self).clean()
        if cleaned_data.get('email') != cleaned_data.get('email_again'):
            raise forms.ValidationError("The email addresses you inputted do not match.")


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    new_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    new_password_again = forms.CharField(widget=forms.PasswordInput(), required=True)

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        if cleaned_data.get('new_password') != cleaned_data.get('new_password_again'):
            raise forms.ValidationError("The passwords you inputted do not match.")


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(required=True)

    class Meta:
        fieldsets = [{
                'id':'forgot-password',
                'legend':'Reset Password',
                'title':'Enter your email and you will receive an email with a new password.'
        }]


class CreateTeamForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)

    class Meta:
        fieldsets = [{
                'id':'create-team',
                'legend':'New Team',
                'title':"Enter a name for your team. Don't worry, you can change it later."
        }]


class UpdateTeamNameForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)

    class Meta:
        fieldsets = [{
                'id':'rename-team',
                'legend':'Rename Team',
                'title':"You can rename your team here."
        }]
