"""Admin configuration for the website app."""
from django.contrib import admin
from .models import (
    UserProfile,
    Language,
    DiveLocation,
    DiveLocationTranslation,
    DiveLocationSuggestion,
    DiveClub,
    DiveEvent,
    DiveClubTranslation,

    Country,
    CountryTranslation
)

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Language)
admin.site.register(DiveLocation)
admin.site.register(DiveLocationTranslation)
admin.site.register(DiveLocationSuggestion)
admin.site.register(DiveClub)
admin.site.register(DiveEvent)
admin.site.register(DiveClubTranslation)
admin.site.register(Country)
admin.site.register(CountryTranslation)
