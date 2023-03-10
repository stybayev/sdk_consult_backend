from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.i18n import i18n_patterns

schema_view = get_schema_view(
    openapi.Info(
        title="Consult Backend API",
        default_version='v1',
        description="List of API urls of backend application",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    url=settings.SWAGGER_URL,
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('auth/', include('authentication.urls')),
                  path('news/', include('contents.urls')),
                  path('favorites/', include('favorites.urls')),
                  path('services/', include('services.urls')),
                  path('real_estate/', include('real_estate.urls')),
                  path('contacts/', include('contacts.urls')),
                  path('programs/', include('programs.urls')),
                  path('comments/', include('comments.urls')),
                  path('rosetta/', include('rosetta.urls')),
                  path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
                  path('api/api.json/', schema_view.without_ui(cache_timeout=0), name='schema-swagger-ui'),
                  path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
              ] + static(settings.STATIC_URL,
                         document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

handler404 = 'utils.views.error_404'
handler500 = 'utils.views.error_500'

admin.site.site_header = 'ssd.consult.kz'
admin.site.index_title = 'ssd.consult.kz'
admin.site.site_title = 'ssd.consult.kz'
