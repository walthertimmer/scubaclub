"""
Forms for website
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from django.db import models
import re
from .models import DiveClub, DiveEvent, DiveLocation, DiveLocationSuggestion

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
    """
    Form for creating/editing a DiveEvent
    """
    club = forms.ModelChoiceField(
        queryset=DiveClub.objects.none(),  # Will be set in __init__
        required=False,
        empty_label="Open Dive (no club)",  # Default to open dive
        help_text="Select a club if this is a club dive. Only clubs where you are a member or admin are shown."
    )

    class Meta:
        model = DiveEvent
        fields = ['title', 'description', 'dive_location', 'date', 'max_participants', 'club']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Morning Dive at Reef'}),
            'description': forms.Textarea(attrs={'placeholder': 'e.g., A fun group dive with experienced divers.'}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'max_participants': forms.NumberInput(attrs={'placeholder': 'e.g., 20'}),
        }
        help_texts = {
            'title': 'Enter a catchy title for the dive event.',
            'description': 'Provide details about the dive, location, and requirements.',
            'date': 'Select the date and time in YYYY-MM-DDTHH:MM format (minutes only, no seconds).',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract user from kwargs
        super().__init__(*args, **kwargs)
        # Limit dive_location choices to current language
        self.fields['dive_location'].queryset = DiveLocation.get_for_current_language()
        # Limit club choices to clubs where user is member or admin
        if user:
            self.fields['club'].queryset = DiveClub.objects.filter(
                models.Q(members=user) | models.Q(admins=user)
            ).distinct()


class DiveLocationForm(forms.ModelForm):
    class Meta:
        model = DiveLocation
        fields = ['name', 'description', 'country', 'latitude', 'longitude']


class DiveLocationSuggestionForm(forms.ModelForm):
    class Meta:
        model = DiveLocationSuggestion
        fields = ['suggested_name', 'suggested_description', 'suggested_country', 'suggested_latitude', 'suggested_longitude']
        widgets = {
            'suggested_description': forms.Textarea(attrs={'placeholder': 'Describe the suggested changes.'}),
        }
