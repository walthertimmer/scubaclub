from django.contrib import admin
from .models import UserProfile, Language, DiveLocation, DiveClub, DiveEvent

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Language)
admin.site.register(DiveLocation)
admin.site.register(DiveClub)
admin.site.register(DiveEvent)
