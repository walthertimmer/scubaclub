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
    path('club/<int:club_id>/remove/<int:user_id>/', views.remove_member, 
         name='remove_member'),
    path('create-club/', views.create_dive_club, name='create_dive_club'),
]
