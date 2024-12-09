from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.permission import VehiclePermissionView, AccessedVehiclesView
from .views.vehicle_component import ComponentList, ComponentDetail, ComponentByType
from .views.vehicle import VehicleViewSet

# Create the router for vehicles
router = DefaultRouter()
router.register('vehicles', VehicleViewSet, basename='vehicle')

# Define component URL patterns
component_patterns = [
    path('', ComponentList.as_view(), name='component-list'),
    path('<str:type_name>/', ComponentByType.as_view(), name='component-by-type'),
    path('<str:type_name>/<str:name>/', ComponentDetail.as_view(), name='component-detail'),
]

# Include all URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('vehicles/<str:vin>/components/', include((component_patterns, 'components'), namespace='components')),
    # Vehicle permission management
    path('vehicles/<str:vin>/permissions/', VehiclePermissionView.as_view(), name='vehicle-permissions'),

    # List of accessed vehicles
    path('vehicles/accessed/', AccessedVehiclesView.as_view(), name='accessed-vehicles'),

]
