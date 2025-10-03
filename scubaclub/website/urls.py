"""
Urls for website app
"""
from django.urls import path, include
from django.utils.translation import gettext_lazy as _
from . import views

app_name = "website"

urlpatterns = [
    path('', views.home, name='home'),
    path('health/', views.health, name='health'),
    path(_('privacy/'), views.privacy, name='privacy'),
    path(_('contact/'), views.contact, name='contact'),

    path(_('register/'), views.register, name='register'),
    path(_('activate/<uidb64>/<token>/'), views.activate, name='activate'),
    path(_('login/'), views.CustomLoginView.as_view(), name='login'),
    path(_('logout/'), views.CustomLogoutView.as_view(), name='logout'),
    path(_('registration_complete/'), views.registration_complete,
         name='registration_complete'),
    path('accounts/', include('django.contrib.auth.urls')),
    path(_('dive_clubs/'), views.dive_clubs, name='dive_clubs'),
    path(_('upcoming_dives/'), views.upcoming_dives, name='upcoming_dives'),
    path(_('dive_locations/'), views.dive_locations, name='dive_locations'),

    path(_('club/<slug:club_slug>/'), views.club_detail, name='club_detail'),
    path('club/<int:club_id>/request_join/', views.request_join_club,
         name='request_join_club'),
    path('club/<int:club_id>/approve/<int:user_id>/', views.approve_member,
         name='approve_member'),
    path('club/<int:club_id>/reject/<int:user_id>/', views.reject_member,
         name='reject_member'),
    path('club/<int:club_id>/remove/<int:user_id>/', views.remove_member,
         name='remove_member'),
    path('club/<int:club_id>/promote/<int:user_id>/', views.promote_to_admin,
         name='promote_to_admin'),
    path('club/<int:club_id>/remove_admin/<int:user_id>/', views.remove_admin,
         name='remove_admin'),
    path('create-club/', views.create_dive_club, name='create_dive_club'),
    path('club/<slug:club_slug>/edit/',
         views.edit_dive_club, name='edit_dive_club'),

    path(_('create_dive_event/'),
         views.create_dive_event, name='create_dive_event'),
    path(_('create_dive_event/<int:club_id>/'),
         views.create_dive_event,
         name='create_dive_event_with_club'),
    path('dive/<int:dive_id>/',
         views.dive_detail, name='dive_detail'),
    path('dive/<int:dive_id>/edit/',
         views.edit_dive, name='edit_dive'),
    path('dive/<int:dive_id>/cancel/',
         views.cancel_dive, name='cancel_dive'),

    path('create_dive_location/',
         views.create_dive_location,
         name='create_dive_location'),
    path('location/<slug:location_slug>/',
         views.location_detail,
         name='location_detail'),
    path('location/<slug:location_slug>/suggest_edit/',
         views.suggest_location_edit,
         name='suggest_location_edit'),
    path('review_location_suggestions/',
         views.review_location_suggestions,
         name='review_location_suggestions'),
    path('approve_suggestion/<int:suggestion_id>/',
         views.approve_location_suggestion,
         name='approve_location_suggestion'),
    path('reject_suggestion/<int:suggestion_id>/',
         views.reject_location_suggestion,
         name='reject_location_suggestion'),
]
