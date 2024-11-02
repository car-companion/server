"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

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
                 ], 'auth')

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
