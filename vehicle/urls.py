from django.urls import path

from .views.permissions import BulkComponentAccessView
from .views.vehicle import take_ownership, disown, my_vehicles
from .views.vehicle_component import VehicleComponentDetailView, VehicleComponentsListView

urlpatterns = [
    # Vehicle management
    path('take-ownership/', take_ownership, name='take-ownership'),
    path('disown/', disown, name='disown'),
    path('my-vehicles/', my_vehicles, name='my-vehicles'),

    # Vehicle components
    path('vehicles/<str:vin>/components/', VehicleComponentsListView.as_view(), name='vehicle-components-list'),
    path('vehicles/<str:vin>/components/<str:component_type>/<str:component_name>/',
         VehicleComponentDetailView.as_view(), name='vehicle-component-detail'),

    # Permissions
    path('vehicles/<str:vin>/grant-access/',
         BulkComponentAccessView.as_view(),
         name='bulk-component-access')
]
