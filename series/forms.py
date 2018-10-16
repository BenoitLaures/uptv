from django import forms
from django.contrib.auth.forms import UserCreationForm

from users.models import User


class SearchSeriesForm(forms.Form):
    """Form to search for series."""

    search_term = forms.CharField(label='Search shows…', max_length=200)


class SignUpForm(UserCreationForm):
    """Form for new user to sign up."""

    class Meta(UserCreationForm.Meta):
        model = User
