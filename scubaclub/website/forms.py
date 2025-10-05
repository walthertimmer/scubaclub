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

    # Dutch fields
    name_nl = forms.CharField(
        max_length=255,
        label="Name (Dutch)",
        required=True,  # Will be overridden dynamically
        widget=forms.TextInput(attrs={'placeholder': 'Enter location name in Dutch'})
    )
    description_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter description in Dutch'}),
        label="Description (Dutch)",
        required=False
    )
    dangers_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter dangers in Dutch'}),
        label="Dangers (Dutch)",
        required=False
    )
    nicknames_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter nicknames in Dutch'}),
        label="Nicknames (Dutch)",
        required=False
    )
    address_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter address in Dutch'}),
        label="Address (Dutch)",
        required=False
    )
    parking_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter parking info in Dutch'}),
        label="Parking (Dutch)",
        required=False
    )
    sight_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter sight info in Dutch'}),
        label="Sight (Dutch)",
        required=False
    )
    max_depth_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter current depth in Dutch'}),
        label="Max Depth (Dutch)",
        required=False
    )
    bottom_type_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter bottom type in Dutch'}),
        label="Bottom Type (Dutch)",
        required=False
    )
    type_of_water_nl = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter type of water in Dutch'}),
        label="Type of Water (Dutch)",
        required=False
    )

    # English fields
    name_en = forms.CharField(
        max_length=255,
        label="Name (English)",
        required=False,  # Will be overridden dynamically
        widget=forms.TextInput(attrs={'placeholder': 'Enter location name in English'})
    )
    description_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter description in English'}),
        label="Description (English)",
        required=False
    )
    dangers_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter dangers in English'}),
        label="Dangers (English)",
        required=False
    )
    nicknames_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter nicknames in English'}),
        label="Nicknames (English)",
        required=False
    )
    address_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter address in English'}),
        label="Address (English)",
        required=False
    )
    parking_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter parking info in English'}),
        label="Parking (English)",
        required=False
    )
    sight_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter sight info in English'}),
        label="Sight (English)",
        required=False
    )
    max_depth_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter current depth in English'}),
        label="Max Depth (English)",
        required=False
    )
    bottom_type_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter bottom type in English'}),
        label="Bottom Type (English)",
        required=False
    )
    type_of_water_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter type of water in English'}),
        label="Type of Water (English)",
        required=False
    )

    class Meta:
        model = DiveLocation
        fields = ['country', 'latitude', 'longitude']

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

        # If editing an existing instance, populate translation fields
        if self.instance and self.instance.pk:
            try:
                from .models import DiveLocationTranslation
                nl_translation = self.instance.translations \
                    .filter(language__code='nl').first()
                en_translation = self.instance.translations \
                    .filter(language__code='en').first()

                if nl_translation:
                    self.fields['name_nl'].initial = nl_translation.name
                    self.fields['description_nl'].initial = nl_translation.description
                    self.fields['dangers_nl'].initial = nl_translation.dangers
                    self.fields['nicknames_nl'].initial = nl_translation.nicknames
                    self.fields['address_nl'].initial = nl_translation.address
                    self.fields['parking_nl'].initial = nl_translation.parking
                    self.fields['sight_nl'].initial = nl_translation.sight
                    self.fields['max_depth_nl'].initial = nl_translation.max_depth
                    self.fields['bottom_type_nl'].initial = nl_translation.bottom_type
                    self.fields['type_of_water_nl'].initial = nl_translation.type_of_water
                if en_translation:
                    self.fields['name_en'].initial = en_translation.name
                    self.fields['description_en'].initial = en_translation.description
                    self.fields['dangers_en'].initial = en_translation.dangers
                    self.fields['nicknames_en'].initial = en_translation.nicknames
                    self.fields['address_en'].initial = en_translation.address
                    self.fields['parking_en'].initial = en_translation.parking
                    self.fields['sight_en'].initial = en_translation.sight
                    self.fields['max_depth_en'].initial = en_translation.max_depth
                    self.fields['bottom_type_en'].initial = en_translation.bottom_type
                    self.fields['type_of_water_en'].initial = en_translation.type_of_water
            except Exception as e:
                logger.error("Error loading translations for DiveLocation ID %s: %s",
                             self.instance.pk, e)

    def clean(self):
        cleaned_data = super().clean()
        current_lang = get_language()

        # Ensure at least one name is provided for the current language
        if current_lang == 'nl':
            name_nl = cleaned_data.get('name_nl', '').strip()
            if not name_nl:
                self.add_error('name_nl', 'This field is required for Dutch locations.')
        elif current_lang == 'en':
            name_en = cleaned_data.get('name_en', '').strip()
            if not name_en:
                self.add_error('name_en', 'This field is required for English locations.')

        return cleaned_data

    def save(self, commit=True):
        location = super().save(commit=commit)
        if commit:
            self._save_translations(location)
        return location

    def _save_translations(self, location):
        """Save translations for both languages."""
        from django.utils.text import slugify
        from .models import DiveLocationTranslation

        logger.info("Starting _save_translations for dive_location ID: %s",
                    location.id)

        try:
            # Save Dutch translation
            nl_lang = Language.objects.get(code='nl')
            nl_name = self.cleaned_data.get('name_nl', '').strip()
            nl_description = self.cleaned_data.get('description_nl', '').strip()
            nl_dangers = self.cleaned_data.get('dangers_nl', '').strip()
            nl_nicknames = self.cleaned_data.get('nicknames_nl', '').strip()
            nl_address = self.cleaned_data.get('address_nl', '').strip()
            nl_parking = self.cleaned_data.get('parking_nl', '').strip()
            nl_sight = self.cleaned_data.get('sight_nl', '').strip()
            nl_max_depth = self.cleaned_data.get('max_depth_nl', '').strip()
            nl_bottom_type = self.cleaned_data.get('bottom_type_nl', '').strip()
            nl_type_of_water = self.cleaned_data.get('type_of_water_nl', '').strip()

            logger.info("Dutch name: '%s', description length: %d",
                        nl_name, len(nl_description))

            if nl_name:  # Only save if name is provided
                nl_translation, created = DiveLocationTranslation.objects.get_or_create(
                    dive_location=location,
                    language=nl_lang,
                    defaults={
                        'name': nl_name,
                        'description': nl_description,
                        'dangers': nl_dangers,
                        'nicknames': nl_nicknames,
                        'address': nl_address,
                        'parking': nl_parking,
                        'sight': nl_sight,
                        'max_depth': nl_max_depth,
                        'bottom_type': nl_bottom_type,
                        'type_of_water': nl_type_of_water,
                        'slug': ''
                    }
                )
                if not created:
                    nl_translation.name = nl_name
                    nl_translation.description = nl_description
                    nl_translation.dangers = nl_dangers
                    nl_translation.nicknames = nl_nicknames
                    nl_translation.address = nl_address
                    nl_translation.parking = nl_parking
                    nl_translation.sight = nl_sight
                    nl_translation.max_depth = nl_max_depth
                    nl_translation.bottom_type = nl_bottom_type
                    nl_translation.type_of_water = nl_type_of_water

                # Generate slug
                if nl_translation.name:
                    nl_translation.slug = slugify(nl_translation.name)
                else:
                    nl_translation.slug = f"location-{location.id}"

                logger.info("Generated Dutch slug: '%s'", nl_translation.slug)

                # Handle uniqueness conflicts per language
                original_slug = nl_translation.slug
                counter = 1
                while DiveLocationTranslation.objects.filter(
                    language=nl_lang,
                    slug=nl_translation.slug
                ).exclude(dive_location=location).exists():
                    nl_translation.slug = f"{original_slug}-{counter}"
                    counter += 1

                nl_translation.save()
                logger.info("Saved Dutch translation: name='%s', slug='%s'",
                            nl_translation.name, nl_translation.slug)
        except Exception as e:
            logger.error("Error saving Dutch translation for DiveLocation ID %s: %s",
                         location.id, e)

        try:
            # Save English translation
            en_lang = Language.objects.get(code='en')
            en_name = self.cleaned_data.get('name_en', '').strip()
            en_description = self.cleaned_data.get('description_en', '').strip()
            en_dangers = self.cleaned_data.get('dangers_en', '').strip()
            en_nicknames = self.cleaned_data.get('nicknames_en', '').strip()
            en_address = self.cleaned_data.get('address_en', '').strip()
            en_parking = self.cleaned_data.get('parking_en', '').strip()
            en_sight = self.cleaned_data.get('sight_en', '').strip()
            en_max_depth = self.cleaned_data.get('max_depth_en', '').strip()
            en_bottom_type = self.cleaned_data.get('bottom_type_en', '').strip()
            en_type_of_water = self.cleaned_data.get('type_of_water_en', '').strip()

            logger.info("English name: '%s', description length: %d",
                        en_name, len(en_description))

            if en_name:  # Only create/update English translation if name is provided
                en_translation, created = DiveLocationTranslation.objects.get_or_create(
                    dive_location=location,
                    language=en_lang,
                    defaults={
                        'name': en_name,
                        'description': en_description,
                        'dangers': en_dangers,
                        'nicknames': en_nicknames,
                        'address': en_address,
                        'parking': en_parking,
                        'sight': en_sight,
                        'max_depth': en_max_depth,
                        'bottom_type': en_bottom_type,
                        'type_of_water': en_type_of_water,
                        'slug': ''
                    }
                )

                if not created:
                    en_translation.name = en_name
                    en_translation.description = en_description
                    en_translation.dangers = en_dangers
                    en_translation.nicknames = en_nicknames
                    en_translation.address = en_address
                    en_translation.parking = en_parking
                    en_translation.sight = en_sight
                    en_translation.max_depth = en_max_depth
                    en_translation.bottom_type = en_bottom_type
                    en_translation.type_of_water = en_type_of_water

                # Generate slug for English
                if en_translation.name:
                    en_translation.slug = slugify(en_name)
                else:
                    en_translation.slug = f"location-{location.id}-en"

                logger.info("Generated English slug: '%s'", en_translation.slug)

                # Handle uniqueness conflicts per language
                original_slug = en_translation.slug
                counter = 1
                while DiveLocationTranslation.objects.filter(
                    language=en_lang,
                    slug=en_translation.slug
                ).exclude(dive_location=location).exists():
                    en_translation.slug = f"{original_slug}-{counter}"
                    counter += 1

                en_translation.save()
                logger.info("Saved English translation: name='%s', slug='%s'",
                            en_translation.name, en_translation.slug)
        except Exception as e:
            logger.error("Error saving English translation for DiveLocation ID %s: %s",
                         location.id, e)


class DiveLocationSuggestionForm(forms.ModelForm):
    """
    Form for suggesting edits to a DiveLocation
    """

    target_language = forms.ModelChoiceField(
        queryset=Language.objects.all(),
        label="Language",
        help_text="Select the language for this suggestion"
    )

    class Meta:
        model = DiveLocationSuggestion
        fields = [
            'target_language',
            'suggested_name',
            'suggested_description',
            'suggested_dangers',
            'suggested_nicknames',
            'suggested_address',
            'suggested_parking',
            'suggested_sight',
            'suggested_max_depth',
            'suggested_bottom_type',
            'suggested_type_of_water',
            'suggested_country',
            'suggested_latitude',
            'suggested_longitude'
        ]
        widgets = {
            'suggested_description': forms.Textarea(attrs={'rows': 4}),
            'suggested_dangers': forms.Textarea(attrs={'rows': 4}),
            'suggested_nicknames': forms.Textarea(attrs={'rows': 4}),
            'suggested_address': forms.Textarea(attrs={'rows': 4}),
            'suggested_parking': forms.Textarea(attrs={'rows': 4}),
            'suggested_sight': forms.Textarea(attrs={'rows': 4}),
            'suggested_max_depth': forms.Textarea(attrs={'rows': 4}),
            'suggested_bottom_type': forms.Textarea(attrs={'rows': 4}),
            'suggested_type_of_water': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.location = kwargs.pop('location', None)
        kwargs.pop('language', None)
        super().__init__(*args, **kwargs)

        if self.location:
            # Set current language as default
            current_lang = get_language()
            try:
                default_language = Language.objects.get(code=current_lang)
                self.fields['target_language'].initial = default_language
            except Language.DoesNotExist:
                pass

            # Pre-populate non-translatable fields
            if not self.initial.get('suggested_country'):
                self.fields['suggested_country'].initial = self.location.country
            if not self.initial.get('suggested_latitude'):
                self.fields['suggested_latitude'].initial = self.location.latitude
            if not self.initial.get('suggested_longitude'):
                self.fields['suggested_longitude'].initial = self.location.longitude

        # Add JavaScript to update form fields when language changes
        self.fields['target_language'].widget.attrs['onchange'] = 'updateFormFields(this.value)'

    def clean(self):
        cleaned_data = super().clean()
        target_language = cleaned_data.get('target_language')

        if self.location and target_language:
            # Pre-populate fields based on selected language if form is being rendered
            # This will be handled by JavaScript on the frontend
            pass

        return cleaned_data
