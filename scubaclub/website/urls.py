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
]
