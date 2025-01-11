from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Schema patterns
schema_patterns = [
    path('', SpectacularAPIView.as_view(), name='schema'),
    path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema:schema'), name='redoc'),
]

# Auth patterns
auth_patterns = [
    path('', include('djoser.urls')),  # Includes user-related endpoints
    path('', include('djoser.urls.jwt')),  # Includes JWT-related endpoints
]

# Main URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', include('health_check.urls')),
    path('api/schema/', include((schema_patterns, 'schema'))),
    path('api/auth/', include((auth_patterns, 'auth'), namespace='auth')),
    path('api/car_companion/', include('car_companion.urls')),
    path('', include('authentication.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
]
