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


class DiveLocation(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    country = models.CharField(max_length=128, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    language = models.ForeignKey(Language, on_delete=models.SET_DEFAULT, default=1)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.language})"

    @classmethod
    def get_for_current_language(cls):
        """Get dive locations for the current language"""
        current_lang = get_language()
        return cls.objects.filter(language__code=current_lang)


class DiveLocationSuggestion(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    original_location = models.ForeignKey(DiveLocation, on_delete=models.CASCADE, related_name='suggestions')
    suggested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    suggested_name = models.CharField(max_length=255, blank=True)
    suggested_description = models.TextField(blank=True)
    suggested_country = models.CharField(max_length=128, blank=True)
    suggested_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    suggested_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Suggestion for {self.original_location.name} by {self.suggested_by.username}"

    def apply_changes(self):
        """Apply approved changes to the original location."""
        if self.status == 'approved':
            self.original_location.name = self.suggested_name or self.original_location.name
            self.original_location.description = self.suggested_description or self.original_location.description
            self.original_location.country = self.suggested_country or self.original_location.country
            self.original_location.latitude = self.suggested_latitude if self.suggested_latitude is not None else self.original_location.latitude
            self.original_location.longitude = self.suggested_longitude if self.suggested_longitude is not None else self.original_location.longitude
            self.original_location.save()


class DiveClub(models.Model):
    # Non-translatable fields (shared across languages)
    address = models.CharField(max_length=255, blank=True)
    municipality = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True,
                              help_text="Enter the full URL, including 'http://' or 'https://', e.g., https://scubaclub.org")
    email = models.EmailField(blank=True)
    country = models.CharField(max_length=128,
                               blank=True,
                               help_text="Nation or country where the club is based")
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
    language = models.ForeignKey(Language, on_delete=models.SET_DEFAULT, default=1)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_dives')
    participants = models.ManyToManyField(User, related_name='dive_events', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    club = models.ForeignKey(DiveClub, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    is_cancelled = models.BooleanField(default=False, help_text="Mark if the dive has been cancelled.")

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} ({self.language}) - {self.date.strftime('%Y-%m-%d')}"

    @classmethod
    def get_for_current_language(cls):
        """Get dive events for the current language"""
        current_lang = get_language()
        return cls.objects.filter(language__code=current_lang)
