"""
Main views for the Scuba Club website.
"""
import logging
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from django.utils import translation
from django.http import HttpResponse, HttpResponseForbidden, Http404
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
from .models import DiveClub, DiveClubTranslation, DiveEvent, DiveLocation, Language, DiveLocationSuggestion
from .forms import CustomUserCreationForm, DiveClubForm, DiveEventForm, DiveLocationForm, DiveLocationSuggestionForm


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
    """Render the registration complete page."""
    return render(request, "website/registration_complete.html")


class CustomLoginView(LoginView):
    authentication_form = AuthenticationForm
    template_name = "registration/login.html"


class CustomLogoutView(LogoutView):
    next_page = '/'


def dive_clubs(request):
    """Render the dive clubs page."""
    current_lang = get_language()
    logger.info("Current language detected as: %s", current_lang)

    clubs = DiveClub.get_for_current_language()
    logger.info("views.dive_clubs Found %d clubs for current language %s", clubs.count(), current_lang)

    # Filter to only include clubs with valid slugs and prepare context
    clubs_with_slugs = []
    for club in clubs:
        slug = club.get_slug_for_language(current_lang)
        if slug:
            club.club_slug = slug
            club.name = club.get_name_for_language(current_lang)
            club.description = club.get_description_for_language(current_lang)
            clubs_with_slugs.append(club)
        else:
            logger.warning("Club ID %d has no slug for language %s", club.id, current_lang)
    return render(request, "website/dive_clubs.html", {"clubs": clubs_with_slugs})


def upcoming_dives(request):
    """Render the upcoming dives page."""
    dives = DiveEvent.get_for_current_language().filter(date__gte=timezone.now())
    current_lang = get_language()
    for dive in dives:
        if dive.club:
            dive.club_slug = dive.club.get_slug_for_language(current_lang)
            dive.club_name = dive.club.get_name_for_language(current_lang)
    return render(request, "website/upcoming_dives.html", {"dives": dives})


def dive_locations(request):
    """Render the dive locations page."""
    locations = DiveLocation.get_for_current_language()
    return render(request, "website/dive_locations.html", {"locations": locations})


def club_detail(request, club_slug):
    """Render the detail page for a specific dive club."""
    current_lang = get_language()
    try:
        translation = DiveClubTranslation.objects.get(
            slug=club_slug, language__code=current_lang)
        club = translation.dive_club
    except DiveClubTranslation.DoesNotExist:
        # Instead of raising Http404, redirect to the club overview page
        # This handles cases where the club doesn't exist in the current language
        return redirect('website:dive_clubs')

    # Populate translated name and description for the template
    club.name = club.get_name_for_language(current_lang)
    club.description = club.get_description_for_language(current_lang)

    context = {
        'club': club,
        'members': club.members.all(),
        'admins': club.admins.all(),
        'pending_members': club.pending_members.all(),
        'club_events': club.events.filter(date__gte=timezone.now()),
        'club_slug': club.get_slug_for_language(current_lang),
    }
    return render(request, "website/club_detail.html", context)


@login_required
def edit_dive_club(request, club_slug):
    """Edit an existing dive club, with permission checks."""
    current_lang = get_language()
    try:
        translation = DiveClubTranslation.objects.get(
            slug=club_slug, language__code=current_lang)
        club = translation.dive_club
        club_name = translation.name
    except DiveClubTranslation.DoesNotExist:
        raise Http404("Club not found")

    # Permission check: Only club admins can edit
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")

    if request.method == 'POST':
        form = DiveClubForm(request.POST, instance=club)
        if form.is_valid():
            form.save()
            # Redirect using the (possibly updated) slug for current language
            updated_slug = club.get_slug_for_language(current_lang)
            if updated_slug:
                return redirect('website:club_detail', club_slug=updated_slug)
            else:
                return redirect('website:dive_clubs')
    else:
        form = DiveClubForm(instance=club)

    return render(request,
                  'website/edit_dive_club.html',
                  {'form': form,
                   'club': club,
                   'club_slug': club_slug,
                   'club_name': club_name})


@login_required
def request_join_club(request, club_id):
    """Request to join a dive club."""
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.method == 'POST':
        club.pending_members.add(request.user)
        # Optionally, send notification to admins
    current_lang = get_language()
    club_slug = club.get_slug_for_language(current_lang)
    if club_slug:
        return redirect('website:club_detail', club_slug=club_slug)
    else:
        return redirect('website:dive_clubs')


@login_required
def approve_member(request, club_id, user_id):
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")
    user = get_object_or_404(User, pk=user_id)
    if user in club.pending_members.all():
        club.pending_members.remove(user)
        club.members.add(user)
    current_lang = get_language()
    club_slug = club.get_slug_for_language(current_lang)
    if club_slug:
        return redirect('website:club_detail', club_slug=club_slug)
    else:
        return redirect('website:dive_clubs')


@login_required
def reject_member(request, club_id, user_id):
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")
    user = get_object_or_404(User, pk=user_id)
    if user in club.pending_members.all():
        club.pending_members.remove(user)
    current_lang = get_language()
    club_slug = club.get_slug_for_language(current_lang)
    if club_slug:
        return redirect('website:club_detail', club_slug=club_slug)
    else:
        return redirect('website:dive_clubs')


@login_required
def remove_member(request, club_id, user_id):
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")
    user = get_object_or_404(User, pk=user_id)
    if user in club.members.all():
        club.members.remove(user)
    current_lang = get_language()
    club_slug = club.get_slug_for_language(current_lang)
    if club_slug:
        return redirect('website:club_detail', club_slug=club_slug)
    else:
        return redirect('website:dive_clubs')


@login_required
def promote_to_admin(request, club_id, user_id):
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")
    user = get_object_or_404(User, pk=user_id)
    if user in club.members.all() and user not in club.admins.all():
        club.admins.add(user)
        # Optional: Ensure they are still a member (though they should be)
        if user not in club.members.all():
            club.members.add(user)
    current_lang = get_language()
    club_slug = club.get_slug_for_language(current_lang)
    if club_slug:
        return redirect('website:club_detail', club_slug=club_slug)
    else:
        return redirect('website:dive_clubs')


@login_required
def remove_admin(request, club_id, user_id):
    club = get_object_or_404(DiveClub, pk=club_id)
    if request.user not in club.admins.all():
        return HttpResponseForbidden("You are not an admin of this club.")
    user = get_object_or_404(User, pk=user_id)
    if user in club.admins.all():
        # Check if this would leave no admins
        if club.admins.count() <= 1:
            # You could return an error message or redirect with a warning
            # For simplicity, prevent the action and redirect back
            current_lang = get_language()
            club_slug = club.get_slug_for_language(current_lang)
            if club_slug:
                return redirect('website:club_detail', club_slug=club_slug)
            else:
                return redirect('website:dive_clubs')
        club.admins.remove(user)
        # Optional: Remove from members as well (demote fully)
        # If you want to keep them as a member, comment out the next line
        # club.members.remove(user)
    current_lang = get_language()
    club_slug = club.get_slug_for_language(current_lang)
    if club_slug:
        return redirect('website:club_detail', club_slug=club_slug)
    else:
        return redirect('website:dive_clubs')


@login_required
def create_dive_club(request):
    """Create a new dive club."""
    if request.method == 'POST':
        form = DiveClubForm(request.POST)
        if form.is_valid():
            club = form.save(commit=False)
            club.created_by = request.user
            club.save()
            # Manually save translations since commit=False skipped it
            form._save_translations(club)
            current_lang = get_language()
            club_slug = club.get_slug_for_language(current_lang)
            if club_slug:
                return redirect('website:club_detail', club_slug=club_slug)
            else:
                # Fallback if no slug (shouldn't happen with required names)
                logger.warning("No slug found for newly created club ID %s in language %s", club.id, current_lang)
                return redirect('website:dive_clubs')
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
def create_dive_event(request, club_id=None):
    """Create a new dive event (club or open)."""
    initial = {}
    if club_id:
        club = get_object_or_404(DiveClub, pk=club_id)
        # Check if user is a member or admin of the club
        if request.user not in club.members.all() and request.user not in club.admins.all():
            return HttpResponseForbidden("You are not a member or admin of this club.")
        initial['club'] = club  # Pre-select the club

    if request.method == 'POST':
        form = DiveEventForm(request.POST, user=request.user)
        if form.is_valid():
            dive = form.save(commit=False)
            dive.organizer = request.user
            selected_club = form.cleaned_data.get('club')
            if selected_club:
                # Check if user is a member or admin of the selected club
                if request.user not in selected_club.members.all() and request.user not in selected_club.admins.all():
                    form.add_error('club', "You must be a member or admin of the selected club to create a club dive.")
                    return render(request, 'website/create_dive.html', {'form': form})
                dive.club = selected_club
                dive.language = selected_club.language  # Inherit club's language
                redirect_url = 'website:club_detail'  # Redirect to club page
                redirect_kwargs = {'club_slug': selected_club.slug}
            else:
                # Open dive: no club
                dive.club = None
                dive.language = Language.objects.get(code=get_language())
                redirect_url = 'website:upcoming_dives'  # Redirect to upcoming dives
                redirect_kwargs = {}
            dive.save()
            return redirect(redirect_url, **redirect_kwargs)
    else:
        form = DiveEventForm(user=request.user, initial=initial)
    return render(request, 'website/create_dive.html', {'form': form})


@login_required
def edit_dive(request, event_id):
    """Edit an existing dive event, with permission checks."""
    event = get_object_or_404(DiveEvent, pk=event_id)

    # Permission check
    if event.club:
        # Club dive: Only club admins can edit
        if request.user not in event.club.admins.all():
            return HttpResponseForbidden("You do not have permission to edit this dive.")
    else:
        # Open dive: Only the organizer can edit
        if request.user != event.organizer:
            return HttpResponseForbidden("You do not have permission to edit this dive.")

    if request.method == 'POST':
        form = DiveEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('website:event_detail', event_id=event.id)
    else:
        form = DiveEventForm(instance=event)

    return render(request, 'website/edit_dive.html', {'form': form, 'event': event})


@login_required
def cancel_dive(request, event_id):
    """Cancel a dive event, with permission checks."""
    event = get_object_or_404(DiveEvent, pk=event_id)

    # Permission check
    if event.club:
        # Club dive: Only club admins can cancel
        if request.user not in event.club.admins.all():
            return HttpResponseForbidden("You do not have permission to cancel this dive.")
    else:
        # Open dive: Only the organizer can cancel
        if request.user != event.organizer:
            return HttpResponseForbidden("You do not have permission to cancel this dive.")

    if request.method == 'POST':
        event.is_cancelled = True
        event.save()
        # Optional: Add email notifications to participants here
        return redirect('website:event_detail', event_id=event.id)

    return render(request, 'website/confirm_dive_cancel.html', {'event': event})


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(DiveEvent, pk=event_id)
    # Optional: Add join/leave logic here (e.g., if POST and not full, add/remove user from participants)
    return render(request, 'website/event_detail.html', {'event': event})


@login_required
def create_dive_location(request):
    if request.method == 'POST':
        form = DiveLocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.created_by = request.user
            location.language = Language.objects.get(code=get_language())
            location.save()
            return redirect('website:dive_locations')
    else:
        form = DiveLocationForm()
    return render(request, 'website/create_dive_location.html', {'form': form})


@login_required
def suggest_location_edit(request, location_id):
    location = get_object_or_404(DiveLocation, pk=location_id)
    if request.method == 'POST':
        form = DiveLocationSuggestionForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.original_location = location
            suggestion.suggested_by = request.user
            suggestion.save()
            return redirect('website:location_detail', location_id=location.id)
    else:
        # Pre-fill the form with current location values
        form = DiveLocationSuggestionForm(initial={
            'suggested_name': location.name,
            'suggested_description': location.description,
            'suggested_country': location.country,
            'suggested_latitude': location.latitude,
            'suggested_longitude': location.longitude,
        })
    return render(request, 'website/suggest_location_edit.html', {'form': form, 'location': location})


@login_required
def review_location_suggestions(request):
    if not request.user.is_superuser:  # Or check for admin role
        return HttpResponseForbidden("Only admins can review suggestions.")
    suggestions = DiveLocationSuggestion.objects.filter(status='pending')
    return render(request, 'website/review_location_suggestions.html', {'suggestions': suggestions})


@login_required
def approve_location_suggestion(request, suggestion_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only admins can approve suggestions.")
    suggestion = get_object_or_404(DiveLocationSuggestion, pk=suggestion_id)
    suggestion.status = 'approved'
    suggestion.apply_changes()
    suggestion.delete()  # Remove after applying
    return redirect('website:review_location_suggestions')


@login_required
def reject_location_suggestion(request, suggestion_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only admins can reject suggestions.")
    suggestion = get_object_or_404(DiveLocationSuggestion, pk=suggestion_id)
    suggestion.status = 'rejected'
    suggestion.save()
    return redirect('website:review_location_suggestions')


def location_detail(request, location_id):
    location = get_object_or_404(DiveLocation, pk=location_id)
    suggestions = location.suggestions.filter(status='pending') if request.user.is_superuser else None
    return render(request, 'website/location_detail.html', {'location': location, 'suggestions': suggestions})


def privacy(request):
    """Render the privacy policy page."""
    return render(request, "website/privacy.html")


def contact(request):
    """Render the contact page."""
    return render(request, "website/contact.html")
