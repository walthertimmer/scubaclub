"""Models for ScubaClub application."""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import get_language, gettext_lazy as _
from django.utils.text import slugify


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


class DiveClub(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True,
                              help_text="Enter the full URL, including 'http://' or 'https://', e.g., https://example.com")
    email = models.EmailField(blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_DEFAULT, default=1)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name='dive_clubs', blank=True)
    admins = models.ManyToManyField(User, related_name='administered_clubs', blank=True)
    pending_members = models.ManyToManyField(User, related_name='pending_club_requests', blank=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.language})"
    
    def save(self, *args, **kwargs):        
        if not self.slug:
            self.slug = slugify(self.name)
            # Optional: Handle uniqueness conflicts (e.g., append ID if slug exists)
            original_slug = self.slug
            counter = 1
            while DiveClub.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
        # Automatically add creator as an admin if not already
        if not self.admins.filter(pk=self.created_by.pk).exists():
            self.admins.add(self.created_by)

    @classmethod
    def get_for_current_language(cls):
        """Get dive clubs for the current language"""
        current_lang = get_language()
        return cls.objects.filter(language__code=current_lang)
    

class DiveEvent(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dive_location = models.ForeignKey(DiveLocation, on_delete=models.CASCADE)
    date = models.DateTimeField()
    max_participants = models.PositiveIntegerField(default=10)
    language = models.ForeignKey(Language, on_delete=models.SET_DEFAULT, default=1)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_dives')
    participants = models.ManyToManyField(User, related_name='dive_events', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} ({self.language}) - {self.date.strftime('%Y-%m-%d')}"

    @classmethod
    def get_for_current_language(cls):
        """Get dive events for the current language"""
        current_lang = get_language()
        return cls.objects.filter(language__code=current_lang)
