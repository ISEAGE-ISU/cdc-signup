from django import forms
import models

class SignupForm(forms.Form):
    email = forms.EmailField(label="Email", required=True)
    first_name = forms.CharField(label="First name", required=True)
    last_name = forms.CharField(label="Last name", required=True)
    username = forms.CharField(label="Desired username", required=True)


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    new_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    new_password_again = forms.CharField(widget=forms.PasswordInput(), required=True)

    def clean(self):
        cleaned_data = super(ForgotPasswordForm, self)
        if cleaned_data.new_password != cleaned_data.new_password_again:
            raise forms.ValidationError("The passwords you inputted do not match.")


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(required=True)


class CreateTeamForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)