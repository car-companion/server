from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.vehicle import (
    VehicleViewSet,
)

from .views.vehicle_component import (
    ComponentList,
    ComponentDetail,
    ComponentByType
)

from .views.permission import (
    VehiclePermissionView,
    VehiclePermissionReadOnlyView,
    AccessedVehiclesView,
)

# URL pattern collections
permission_patterns = [
    path(
        'overview/',
        VehiclePermissionReadOnlyView.as_view(),
        name='vehicle-permissions-overview'
    ),
    path(
        '<str:username>/',
        VehiclePermissionView.as_view(),
        name='user-permissions'
    ),
    path(
        '<str:username>/component/<str:component_type>/',
        VehiclePermissionView.as_view(),
        name='user-permissions-component-type'
    ),
    path(
        '<str:username>/component/<str:component_type>/<str:component_name>/',
        VehiclePermissionView.as_view(),
        name='user-permissions-component-type-name'
    ),
]

component_patterns = [
    path('', ComponentList.as_view(), name='component-list'),
    path(
        '<str:type_name>/',
        ComponentByType.as_view(),
        name='component-by-type'
    ),
    path(
        '<str:type_name>/<str:name>/',
        ComponentDetail.as_view(),
        name='component-detail'
    ),
]

# Router configuration
router = DefaultRouter()
router.register('vehicles', VehicleViewSet, basename='vehicle')

# Main URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path(
        'vehicles/accessed/',
        AccessedVehiclesView.as_view(),
        name='accessed-vehicles'
    ),
    path(
        'vehicles/<str:vin>/permissions/',
        include((permission_patterns, 'permissions'))
    ),
    path(
        'vehicles/<str:vin>/components/',
        include((component_patterns, 'components'))
    ),
]
