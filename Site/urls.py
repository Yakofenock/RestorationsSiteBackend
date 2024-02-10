from django.urls import path
from django.urls import include
from Site.views import index
from django.contrib import admin

from django.conf.urls.static import static
from Site.settings import MEDIA_URL, MEDIA_ROOT

from drf_yasg.views import get_schema_view
from drf_yasg.openapi import Info, Contact, License
from rest_framework.permissions import AllowAny


schema_view = get_schema_view(
   Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_soft="https://www.google.com/policies/terms/",
      contact=Contact(email="contact@snippets.local"),
      license=License(name="BSD License"),
   ),
   public=True,
   permission_classes=[AllowAny]
)


urlpatterns = [
    path('api/restorations_api/v1/', include('Restorations.api_v1.urls')),
    path('api/profiles_api/v1/',     include('Profiles.api_v1.urls')),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    path('restorations/', include('Restorations.urls')),
    path('admin/',        admin.site.urls),
    path('', index),


]

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
