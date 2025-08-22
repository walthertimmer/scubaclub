from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    certifications = models.CharField(max_length=512, blank=True, help_text="Comma-separated list of dive certifications")

    def __str__(self):
        return f"{self.user.username}'s profile"


class DiveLocation(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    country = models.CharField(max_length=128, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    def __str__(self):
        return self.name
