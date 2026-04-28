from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import MainUser   # make sure model is consistently named MainUser
from  django.contrib.auth import get_user_model

MainUser = get_user_model()

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=[choice for choice in MainUser.ROLE_CHOICES if choice[0] != "admin"], required=True)

    class Meta:
        model = MainUser
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'role',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

        # Add Bootstrap class for form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'placeholder': f'Enter {field.replace("_", " ")}'})
        self.fields['role'].widget.attrs.update({'class': 'form-select'})


class LoginForm(forms.Form):
    email_or_username = forms.CharField(
        label="Email or Username",
        widget= forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': "Enter username or email",
            'autocomplete': 'username'
        })
    )

    password = forms.CharField(
        widget= forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password', 'autocomplete': 'current-password'})
    )


# create a main user form::
class MainUserForm(forms.ModelForm):
    # role = forms.ChoiceField(choices= MainUser.ROLE_CHOICES, required=True)
    class Meta:
        model = MainUser
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'is_student',
            'is_teacher',
            'is_admin',
        ]

