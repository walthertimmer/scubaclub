"""
Forms for website
"""
import logging
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from django.db import models
from django.utils.text import slugify
import re
from .models import DiveClub, DiveClubTranslation, DiveEvent, DiveLocation, DiveLocationSuggestion, Language


logger = logging.getLogger("scubaclub.forms")


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
    """
    Form for creating/editing a DiveClub
    """
    name_nl = forms.CharField(
        max_length=255,
        required=True,  # Will be overridden dynamically
        label="Name (Dutch)",
        help_text="Translated name of the club in Dutch."
    )
    name_en = forms.CharField(
        max_length=255,
        required=False,  # Will be overridden dynamically
        label="Name (English)",
        help_text="Translated name of the club in English."
    )
    description_nl = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Description (Dutch)",
        help_text="Translated description of the club in Dutch."
    )
    description_en = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Description (English)",
        help_text="Translated description of the club in English."
    )

    class Meta:
        model = DiveClub
        fields = [
            'address',
            'municipality',
            'postal_code',
            'telephone',
            'website',
            'email',
            'country'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically set required based on current language
        current_lang = get_language()
        if current_lang == 'nl':
            self.fields['name_nl'].required = True
            self.fields['name_en'].required = False
        elif current_lang == 'en':
            self.fields['name_nl'].required = False
            self.fields['name_en'].required = True
        # Descriptions remain optional regardless

        # Append * to labels for required fields
        for field_name, field in self.fields.items():
            if field.required:
                field.label = f"{field.label} *"

        # If editing an existing instance, populate translation fields from DiveClubTranslation
        if self.instance and self.instance.pk:
            try:
                nl_translation = self.instance.translations.filter(language__code='nl').first()
                en_translation = self.instance.translations.filter(language__code='en').first()
                if nl_translation:
                    self.fields['name_nl'].initial = nl_translation.name
                    self.fields['description_nl'].initial = nl_translation.description
                if en_translation:
                    self.fields['name_en'].initial = en_translation.name
                    self.fields['description_en'].initial = en_translation.description
            except Exception as e:
                logger.error("Error loading translations for DiveClub ID %s: %s", self.instance.pk, e)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self._save_translations(instance)
        return instance

    def _save_translations(self, dive_club):
        logger.info("Starting _save_translations for dive_club ID: %s", dive_club.id)

        try:
            # Get or create Dutch translation
            nl_lang = Language.objects.get(code='nl')
            nl_name = self.cleaned_data.get('name_nl', '').strip()
            nl_description = self.cleaned_data.get('description_nl', '').strip()

            logger.info("Dutch name: '%s', description length: %d", nl_name, len(nl_description))

            nl_translation, created = DiveClubTranslation.objects.get_or_create(
                dive_club=dive_club,
                language=nl_lang,
                defaults={
                    'name': nl_name,
                    'description': nl_description,
                    'slug': ''
                }
            )
            if not created:
                nl_translation.name = nl_name
                nl_translation.description = nl_description

            # Always generate a unique slug
            if nl_translation.name:
                nl_translation.slug = slugify(nl_translation.name)
            else:
                nl_translation.slug = f"club-{dive_club.id}"

            logger.info("Generated Dutch slug: '%s'", nl_translation.slug)

            # Handle uniqueness conflicts per language
            original_slug = nl_translation.slug
            counter = 1
            while DiveClubTranslation.objects.filter(
                language=nl_lang,
                slug=nl_translation.slug
            ).exclude(dive_club=dive_club).exists():
                nl_translation.slug = f"{original_slug}-{counter}"
                counter += 1

            nl_translation.save()
            logger.info("Saved Dutch translation: name='%s', slug='%s'", nl_translation.name, nl_translation.slug)
        except Exception as e:
            logger.error("Error saving Dutch translation for DiveClub ID %s: %s", dive_club.id, e)

        try:
            # Get or create English translation (always)
            en_lang = Language.objects.get(code='en')
            en_name = self.cleaned_data.get('name_en', '').strip()
            en_description = self.cleaned_data.get('description_en', '').strip()

            logger.info("English name: '%s', description length: %d", en_name, len(en_description))

            if en_name:  # Only create/update English translation if name is provided
                en_translation, created = DiveClubTranslation.objects.get_or_create(
                    dive_club=dive_club,
                    language=en_lang,
                    defaults={
                        'name': en_name,
                        'description': en_description,
                        'slug': ''
                    }
                )

                if not created:
                    en_translation.name = en_name
                    en_translation.description = en_description

                # Generate slug for English
                en_translation.slug = slugify(en_name)
                logger.info("Generated English slug: '%s'", en_translation.slug)

                # Handle uniqueness conflicts per language
                original_slug = en_translation.slug
                counter = 1
                while DiveClubTranslation.objects.filter(
                    language=en_lang,
                    slug=en_translation.slug
                ).exclude(dive_club=dive_club).exists():
                    en_translation.slug = f"{original_slug}-{counter}"
                    counter += 1

                en_translation.save()
                logger.info("Saved English translation: name='%s', slug='%s'", en_translation.name, en_translation.slug)
        except Exception as e:
            logger.error("Error saving English translation for DiveClub ID %s: %s", dive_club.id, e)

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
    """
    Form for creating/editing a DiveLocation
    """
    class Meta:
        model = DiveLocation
        fields = ['name', 'description', 'country', 'latitude', 'longitude']


class DiveLocationSuggestionForm(forms.ModelForm):
    """
    Form for suggesting edits to a DiveLocation
    """
    class Meta:
        model = DiveLocationSuggestion
        fields = [
            'suggested_name',
            'suggested_description',
            'suggested_country',
            'suggested_latitude',
            'suggested_longitude'
        ]
        widgets = {
            'suggested_description': forms.Textarea(attrs={'placeholder': 'Describe the suggested changes.'}),
        }
