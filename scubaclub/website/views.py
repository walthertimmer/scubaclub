from django.shortcuts import render
from django.utils.translation import gettext as _
from django.utils import translation
from django.http import HttpResponse


def home(request):
    return render(request, "website/home.html")


def health(request):
    return HttpResponse("OK", content_type="text/plain")
