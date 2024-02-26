from django.urls import path
from Restorations.views import *


app_name = 'Restorations'
urlpatterns = [
    path('<int:restore_id>/', restoration, name='card'),
    path('info/',             info,        name='info'),
    path('',                  catalog,     name='catalog'),
]

