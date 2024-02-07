from django.urls import path
from django.urls import include
from Site.views import index


urlpatterns = [
    path('restorations/',        include('Restorations.urls')),
    path('', index)
]
