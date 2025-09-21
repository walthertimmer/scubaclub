"""
Forms for website
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
import re
from .models import DiveClub, DiveEvent, DiveLocation

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text=_("Required. 150 characters or fewer. Only letters and numbers are allowed."),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if not re.match(r'^[A-Za-z0-9]+$', username):
            raise forms.ValidationError(_("Only letters and numbers are allowed in the username."))
        return username

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class DiveClubForm(forms.ModelForm):
    class Meta:
        model = DiveClub
        fields = ['name', 'description', 'location', 'website', 'email', 'language']


class DiveEventForm(forms.ModelForm):
    class Meta:
        model = DiveEvent
        fields = ['title', 'description', 'dive_location', 'date', 'max_participants']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit dive_location choices to current language
        self.fields['dive_location'].queryset = DiveLocation.get_for_current_language()
