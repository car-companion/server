from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

router = DefaultRouter()

# Schema URLs
schema_patterns = ([
                       path('', SpectacularAPIView.as_view(), name='schema'),
                       path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema:schema'), name='swagger-ui'),
                       path('redoc/', SpectacularRedocView.as_view(url_name='schema:schema'), name='redoc'),
                   ], 'schema')

# Auth URLs
auth_patterns = ([
                     path('', include('djoser.urls')),
                     path('', include('djoser.urls.jwt')),
                     path('', include('authentication.urls')),
                 ], 'auth')

# Core URL patterns
urlpatterns = [
    path('api/', include([
        path('', include(router.urls)),
        path('auth/', include(auth_patterns)),
        path('schema/', include(schema_patterns)),
    ])),
    path("admin/", admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
    path('health/', include('health_check.urls')),
]

# Static URL patterns for development
if settings.DEBUG:
    static_patterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns.extend(static_patterns)