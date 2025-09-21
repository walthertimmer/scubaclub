"""
Main views for the Scuba Club website.
"""
import logging
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.utils.translation import get_language
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
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from .models import DiveClub, DiveEvent, DiveLocation, Language
from .forms import CustomUserCreationForm, DiveClubForm, DiveEventForm


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
    """
    Handle user registration with email verification.\
    """
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


def dive_clubs(request):
    """Render the dive clubs page."""
    clubs = DiveClub.get_for_current_language()
    return render(request, "website/dive_clubs.html", {"clubs": clubs})


def upcoming_dives(request):
    """Render the upcoming dives page."""
    dives = DiveEvent.get_for_current_language().filter(date__gte=timezone.now())
    return render(request, "website/upcoming_dives.html", {"dives": dives})


def dive_locations(request):
    """Render the dive locations page."""
    locations = DiveLocation.get_for_current_language()
    return render(request, "website/dive_locations.html", {"locations": locations})


# @login_required
def club_detail(request, club_slug):
    """Render the detail page for a specific dive club."""
    club = get_object_or_404(DiveClub, slug=club_slug)
    # Optional: Add logic to restrict access (e.g., only members or admins can view)
    # if request.user not in club.members.all() and request.user not in club.admins.all():
    #     return HttpResponseForbidden("You do not have permission to view this club.")
    context = {
        'club': club,
        'members': club.members.all(),
        'admins': club.admins.all(),
        'pending_members': club.pending_members.all(),
        'club_events': club.events.filter(date__gte=timezone.now()),
    }
    return render(request, "website/club_detail.html", context)


@login_required
def request_join_club(request, club_id):
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.method == 'POST':
        club.pending_members.add(request.user)
        # Optionally, send notification to admins
    return redirect('website:club_detail', club_slug=club.slug)


@login_required
def approve_member(request, club_id, user_id):
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")
    user = get_object_or_404(User, pk=user_id)
    if user in club.pending_members.all():
        club.pending_members.remove(user)
        club.members.add(user)
    return redirect('website:club_detail', club_slug=club.slug)


@login_required
def remove_member(request, club_id, user_id):
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")
    user = get_object_or_404(User, pk=user_id)
    if user in club.members.all():
        club.members.remove(user)
    return redirect('website:club_detail', club_slug=club.slug)


@login_required
def create_dive_club(request):
    if request.method == 'POST':
        form = DiveClubForm(request.POST)
        if form.is_valid():
            club = form.save(commit=False)
            club.created_by = request.user
            club.save()
            return redirect('website:club_detail', club_slug=club.slug)
    else:
        form = DiveClubForm()
    return render(request, 'website/create_dive_club.html', {'form': form})


@login_required
def create_dive(request, club_id):
    """Create a new dive event for a specific club."""
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")
    if request.method == 'POST':
        form = DiveEventForm(request.POST)
        if form.is_valid():
            dive = form.save(commit=False)
            dive.organizer = request.user
            dive.club = club  # Associate with the club
            dive.language = club.language  # Inherit club's language
            dive.save()
            return redirect('website:club_detail', club_slug=club.slug)
    else:
        form = DiveEventForm()
    return render(request, 'website/create_dive.html', {'form': form, 'club': club})


@login_required
def create_open_dive(request):
    if request.method == 'POST':
        form = DiveEventForm(request.POST)
        if form.is_valid():
            dive = form.save(commit=False)
            dive.organizer = request.user
            dive.club = None  # No club association
            dive.language = Language.objects.get(code=get_language())  # Set to current language
            dive.save()
            return redirect('website:upcoming_dives')
    else:
        form = DiveEventForm()
    return render(request, 'website/create_dive.html', {'form': form, 'club': None})  # Reuse template, pass club=None


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(DiveEvent, pk=event_id)
    # Optional: Add join/leave logic here (e.g., if POST and not full, add/remove user from participants)
    return render(request, 'website/event_detail.html', {'event': event})
