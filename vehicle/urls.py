from django.urls import path

from .views.vehicle import take_ownership, disown, my_vehicles
from .views.vehicle_component import VehicleComponentDetailView, \
    VehicleComponentsListView  # Add this import

urlpatterns = [
    path('take-ownership/', take_ownership, name='take-ownership'),
    path('disown/', disown, name='disown'),
    path('my-vehicles/', my_vehicles, name='my-vehicles'),
    # Add new URL patterns for components
    path('vehicles/<str:vin>/components/', VehicleComponentsListView.as_view(), name='vehicle-components-list'),
    path('vehicles/<str:vin>/components/<str:component_type>/<str:component_name>/',
         VehicleComponentDetailView.as_view(), name='vehicle-component-detail'),

]
