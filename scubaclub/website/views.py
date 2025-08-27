"""
Main views for the Scuba Club website.
"""
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.utils import translation
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
import logging


logger = logging.getLogger("scubaclub.views")


def home(request):
    """Render the home page."""
    user_display = request.user if request.user.is_authenticated else "Anonymous"
    logger.info("Home view accessed by user: %s", user_display)
    return render(request, "website/home.html")


def health(request):
    """Health check endpoint."""
    return HttpResponse("OK", content_type="text/plain")


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = request.POST.get('email')
            user.is_active = False  # Require activation
            user.save()
            # Send activation email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            activation_link = f"{request.scheme}://{request.get_host()}/activate/{uid}/{token}/"
            send_mail(
                "Activate your account",
                f"Click the link to activate: {activation_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            return redirect("website:registration_complete")
    else:
        form = CustomUserCreationForm()
    return render(request, "website/register.html", {"form": form})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect("website:login")
    else:
        return render(request, "website/activation_invalid.html")


def registration_complete(request):
    return render(request, "website/registration_complete.html")


class CustomLoginView(LoginView):
    authentication_form = AuthenticationForm
    template_name = "registration/login.html"


class CustomLogoutView(LogoutView):
    next_page = '/'
