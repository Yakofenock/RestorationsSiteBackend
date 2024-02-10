from django.urls import path
from .views import *


app_name = 'Profiles'
urlpatterns = [
    path('csrf/',     get_csrf_token),
    path('register/', SignupView.as_view()),
    path('login/',    LoginView.as_view()),
    path('logout/',   LogoutView.as_view())
]