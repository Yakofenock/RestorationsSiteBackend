from django.urls import path
from django.urls import include
from Site.views import index
from django.contrib import admin

from django.conf.urls.static import static
from Site.settings import MEDIA_URL, MEDIA_ROOT


urlpatterns = [
    path('api/restorations_api/v1/', include('Restorations.api_v1.urls')),
    path('restorations/', include('Restorations.urls')),
    path('admin/',        admin.site.urls),
    path('', index)
]


urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
