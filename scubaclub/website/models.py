"""Models for ScubaClub application."""
import logging
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import get_language, gettext_lazy as _
from django.utils.text import slugify


logger = logging.getLogger("scubaclub.models")


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Language(models.Model):
    code = models.CharField(max_length=2, unique=True, choices=[
        ('en', _('English')),
        ('nl', _('Dutch'))
    ])

    def __str__(self):
        return self.code


class Country(models.Model):
    """Model for countries, with translatable names."""
    iso_code = models.CharField(max_length=3, unique=True, help_text="ISO 3166-1 alpha-3 country code (e.g., 'NLD' for Netherlands)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['iso_code']

    def __str__(self):
        # Default name if available, else ISO code
        translation = self.translations.filter(language__code='nl').first()
        return translation.name if translation else self.iso_code

    def get_name_for_language(self, lang_code):
        """Get the translated name for a specific language"""
        translation = self.translations.filter(language__code=lang_code).first()
        if translation:
            return translation.name
        # Fallback
        fallback = self.translations.filter(language__code='nl').first()
        return fallback.name if fallback else self.iso_code


class CountryTranslation(models.Model):
    """Translatable fields for Country."""
    country = models.ForeignKey(Country,
                                on_delete=models.CASCADE,
                                related_name='translations')
    language = models.ForeignKey(Language,
                                 on_delete=models.CASCADE)
    name = models.CharField(max_length=255,
                            help_text="Translated name of the country")

    class Meta:
        # One translation per country per language
        unique_together = ('country', 'language')

    def __str__(self):
        return f"{self.name} ({self.language.code})"


class DiveLocation(models.Model):
    """A dive location"""
    country = models.ForeignKey(Country,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                help_text="Country where the location is based")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    language = models.ForeignKey(Language, on_delete=models.SET_DEFAULT, default=1)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        # Use the default language (Dutch) for display
        translation = self.translations.filter(language__code='nl').first()
        name = translation.name if translation else f"Location {self.id}"
        return f"{name} (Location ID: {self.id})"

    def get_name_for_language(self, lang_code):
        """Get the translated name for a specific language, fallback to default (nl)."""
        translation = self.translations.filter(language__code=lang_code).first()
        if translation:
            return translation.name
        # Fallback to Dutch
        fallback = self.translations.filter(language__code='nl').first()
        return fallback.name if fallback else f"Location {self.id}"

    def get_description_for_language(self, lang_code):
        """Get the translated description for a specific language, fallback to default (nl)."""
        translation = self.translations.filter(language__code=lang_code).first()
        if translation:
            return translation.description
        # Fallback to Dutch
        fallback = self.translations.filter(language__code='nl').first()
        return fallback.description if fallback else ""

    def get_dangers_for_language(self, lang_code):
        try:
            return self.translations.get(language__code=lang_code).dangers or ''
        except DiveLocationTranslation.DoesNotExist:
            return ''

    def get_nicknames_for_language(self, lang_code):
        try:
            return self.translations.get(language__code=lang_code).nicknames or ''
        except DiveLocationTranslation.DoesNotExist:
            return ''

    def get_address_for_language(self, lang_code):
        try:
            return self.translations.get(language__code=lang_code).address or ''
        except DiveLocationTranslation.DoesNotExist:
            return ''

    def get_parking_for_language(self, lang_code):
        try:
            return self.translations.get(language__code=lang_code).parking or ''
        except DiveLocationTranslation.DoesNotExist:
            return ''

    def get_sight_for_language(self, lang_code):
        try:
            return self.translations.get(language__code=lang_code).sight or ''
        except DiveLocationTranslation.DoesNotExist:
            return ''

    def get_max_depth_for_language(self, lang_code):
        try:
            return self.translations.get(language__code=lang_code).max_depth or ''
        except DiveLocationTranslation.DoesNotExist:
            return ''

    def get_bottom_type_for_language(self, lang_code):
        try:
            return self.translations.get(language__code=lang_code).bottom_type or ''
        except DiveLocationTranslation.DoesNotExist:
            return ''

    def get_type_of_water_for_language(self, lang_code):
        try:
            return self.translations.get(language__code=lang_code).type_of_water or ''
        except DiveLocationTranslation.DoesNotExist:
            return ''

    def get_slug_for_language(self, lang_code):
        """Get the slug for a specific language."""
        translation = self.translations.filter(
            language__code=lang_code,
            slug__isnull=False
        ).first()
        if translation and translation.slug:
            return translation.slug
        return None

    @classmethod
    def get_for_current_language(cls):
        """Get dive locations for the current language"""
        current_lang = get_language()
        return cls.objects.filter(
            translations__language__code=current_lang,
            translations__name__isnull=False,
        ).exclude(
            translations__language__code=current_lang,
            translations__name=''
        ).distinct()


class DiveLocationTranslation(models.Model):
    """Translatable fields for DiveLocation."""
    dive_location = models.ForeignKey(DiveLocation,
                                      on_delete=models.CASCADE,
                                      related_name='translations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    name = models.CharField(max_length=255,
                            help_text="Translated name of the location")
    description = models.TextField(blank=True,
                                   help_text="Translated description of the location")
    dangers = models.TextField(blank=True,
                               help_text="Translated dangers or warnings for the location")
    nicknames = models.TextField(blank=True,
                                 help_text="Translated nicknames or alternative names for the location")
    address = models.TextField(blank=True,
                               help_text="Translated address details for the location")
    parking = models.TextField(blank=True,
                               help_text="Translated parking information for the location")
    sight = models.TextField(blank=True,
                             help_text="Translated sight or visibility details for the location")
    max_depth = models.TextField(blank=True,
                                 help_text="Translated max depth information for the location")
    bottom_type = models.TextField(blank=True,
                                   help_text="Translated bottom type description for the location")
    type_of_water = models.TextField(blank=True,
                                     help_text="Translated type of water description for the location")
    slug = models.SlugField(blank=True,
                            help_text="URL slug for this translation")

    class Meta:
        # One translation per location per language
        unique_together = ('dive_location', 'language')

    def __str__(self):
        return f"{self.name} ({self.language.code})"


class DiveLocationSuggestion(models.Model):
    """A suggestion to change a dive location's details or translation."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    original_location = models.ForeignKey(DiveLocation,
                                          on_delete=models.CASCADE,
                                          related_name='suggestions')
    target_language = models.ForeignKey(Language,
                                        on_delete=models.CASCADE,
                                        help_text="Language for this suggestion")
    suggested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    suggested_name = models.CharField(max_length=255, blank=True)
    suggested_description = models.TextField(blank=True)
    suggested_dangers = models.TextField(blank=True)
    suggested_nicknames = models.TextField(blank=True)
    suggested_address = models.TextField(blank=True)
    suggested_parking = models.TextField(blank=True)
    suggested_sight = models.TextField(blank=True)
    suggested_max_depth = models.TextField(blank=True)
    suggested_bottom_type = models.TextField(blank=True)
    suggested_type_of_water = models.TextField(blank=True)
    suggested_country = models.ForeignKey(Country,
                                          on_delete=models.SET_NULL,
                                          null=True,
                                          blank=True)
    suggested_latitude = models.DecimalField(max_digits=9,
                                             decimal_places=6,
                                             blank=True,
                                             null=True)
    suggested_longitude = models.DecimalField(max_digits=9,
                                              decimal_places=6,
                                              blank=True,
                                              null=True)
    status = models.CharField(max_length=10,
                              choices=STATUS_CHOICES,
                              default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"""Suggestion for {self.original_location}
                    ({self.target_language.code}) by {self.suggested_by.username}"""

    def apply_changes(self):
        """Apply approved changes to the original location."""
        if self.status == 'approved':
            # Update non-translatable fields
            if self.suggested_country:
                self.original_location.country = self.suggested_country
            if self.suggested_latitude is not None:
                self.original_location.latitude = self.suggested_latitude
            if self.suggested_longitude is not None:
                self.original_location.longitude = self.suggested_longitude
            self.original_location.save()

            # Update or create translation
            translation, created = DiveLocationTranslation.objects.get_or_create(
                dive_location=self.original_location,
                language=self.target_language,
                defaults={
                    'name': self.suggested_name or f"Location {self.original_location.id}",
                    'description': self.suggested_description or '',
                    'dangers': self.suggested_dangers or '',
                    'nicknames': self.suggested_nicknames or '',
                    'address': self.suggested_address or '',
                    'parking': self.suggested_parking or '',
                    'sight': self.suggested_sight or '',
                    'max_depth': self.suggested_max_depth or '',
                    'bottom_type': self.suggested_bottom_type or '',
                    'type_of_water': self.suggested_type_of_water or '',
                    'slug': ''
                }
            )

            if not created:
                if self.suggested_name:
                    translation.name = self.suggested_name
                if self.suggested_description:
                    translation.description = self.suggested_description
                if self.suggested_dangers:
                    translation.dangers = self.suggested_dangers
                if self.suggested_nicknames:
                    translation.nicknames = self.suggested_nicknames
                if self.suggested_address:
                    translation.address = self.suggested_address
                if self.suggested_parking:
                    translation.parking = self.suggested_parking
                if self.suggested_sight:
                    translation.sight = self.suggested_sight
                if self.suggested_max_depth:
                    translation.max_depth = self.suggested_max_depth
                if self.suggested_bottom_type:
                    translation.bottom_type = self.suggested_bottom_type
                if self.suggested_type_of_water:
                    translation.type_of_water = self.suggested_type_of_water

            # Generate slug
            if translation.name:
                translation.slug = slugify(translation.name)

                # Handle uniqueness conflicts
                original_slug = translation.slug
                counter = 1
                while DiveLocationTranslation.objects.filter(
                    language=self.target_language,
                    slug=translation.slug
                ).exclude(dive_location=self.original_location).exists():
                    translation.slug = f"{original_slug}-{counter}"
                    counter += 1

            translation.save()


class DiveClub(models.Model):
    """A dive club"""
    # Non-translatable fields (shared across languages)
    address = models.CharField(max_length=255, blank=True)
    municipality = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True,
                              help_text="Enter the full URL, including 'http://' or 'https://', e.g., https://scubaclub.org")
    email = models.EmailField(blank=True)
    country = models.ForeignKey(Country,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                help_text="Country where the club is based")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name='dive_clubs', blank=True)
    admins = models.ManyToManyField(User, related_name='administered_clubs', blank=True)
    pending_members = models.ManyToManyField(User, related_name='pending_club_requests', blank=True)

    class Meta:
        """Meta class for DiveClub"""
        ordering = ['-created_at']

    def __str__(self):
        # Use the default language (Dutch) for display if no translation exists
        translation = self.translations.filter(language__code='nl').first()
        name = translation.name if translation else "Unnamed club"
        return f"{name} (Club ID: {self.id})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically add creator as an admin if not already
        if not self.admins.filter(pk=self.created_by.pk).exists():
            self.admins.add(self.created_by)

    def get_name_for_language(self, lang_code):
        """Get the translated name for a specific language, fallback to default (nl)."""
        translation = self.translations.filter(language__code=lang_code).first()
        if translation:
            return translation.name
        # Fallback to Dutch
        fallback = self.translations.filter(language__code='nl').first()
        return fallback.name if fallback else "Unnamed Club"

    def get_description_for_language(self, lang_code):
        """Get the translated description for a specific language, fallback to default (nl)."""
        translation = self.translations.filter(language__code=lang_code).first()
        if translation:
            return translation.description
        # Fallback to Dutch
        fallback = self.translations.filter(language__code='nl').first()
        return fallback.description if fallback else ""

    def get_slug_for_language(self, lang_code):
        """Get the slug for a specific language."""
        logger.info("Getting slug for language %s", lang_code)
        translation = self.translations.filter(
            language__code=lang_code,
            slug__isnull=False
        ).first()
        if translation and translation.slug:
            return translation.slug
        return None

    @classmethod
    def get_for_current_language(cls):
        """Get dive clubs for the current language"""
        current_lang = get_language()
        logger.info("models.diveclub fetching clubs for current language %s", current_lang)

        # First, let's see all clubs with translations
        all_clubs_with_translations = cls.objects.filter(
            translations__language__code=current_lang
        )
        logger.info("models.diveclub Found %d clubs with translations for language %s", all_clubs_with_translations.count(), current_lang)

        # Now filter for non-null and non-empty names
        filtered_clubs = cls.objects.filter(
            translations__language__code=current_lang,
            translations__name__isnull=False,
        ).exclude(
            translations__language__code=current_lang,
            translations__name=''
        ).distinct()

        logger.info("After filtering for non-empty names: %d clubs", filtered_clubs.count())

        # log the actual clubs found
        for club in filtered_clubs:
            translation = club.translations.filter(language__code=current_lang).first()
            logger.info("Club ID %d: name='%s', slug='%s'", club.id, translation.name if translation else 'None', translation.slug if translation else 'None')

        return filtered_clubs


class DiveClubTranslation(models.Model):
    """Translatable fields for DiveClub."""
    dive_club = models.ForeignKey(DiveClub, on_delete=models.CASCADE, related_name='translations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, help_text="Translated name of the club")
    description = models.TextField(blank=True, help_text="Translated description of the club")
    slug = models.SlugField(blank=True, help_text="URL slug for this translation")

    class Meta:
        unique_together = ('dive_club', 'language')  # Ensure one translation per club per language

    def __str__(self):
        return f"{self.name} ({self.language.code})"


class DiveEvent(models.Model):
    """
    A group dive
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dive_location = models.ForeignKey(DiveLocation, on_delete=models.CASCADE)
    date = models.DateTimeField()
    max_participants = models.PositiveIntegerField(default=30)
    language = models.ForeignKey(
        Language, on_delete=models.SET_DEFAULT, default=1)
    organizer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='organized_dives')
    participants = models.ManyToManyField(
        User, related_name='dives', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    club = models.ForeignKey(
        DiveClub, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='dives')
    is_cancelled = models.BooleanField(
        default=False, help_text="Mark if the dive has been cancelled.")

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} ({self.language}) - {self.date.strftime('%Y-%m-%d')}"

    @classmethod
    def get_for_current_language(cls):
        """Get dive events for the current language"""
        current_lang = get_language()
        return cls.objects.filter(language__code=current_lang)
