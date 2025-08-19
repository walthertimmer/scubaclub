from django.shortcuts import render
from django.utils.translation import gettext as _
from django.utils import translation


def home(request):
    return render(request, "website/home.html")
