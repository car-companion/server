from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.permissions import BulkComponentAccessView
from .views.vehicle import VehicleViewSet
from .views.vehicle_component import (
    VehicleComponentsListView,
    VehicleComponentDetailView
)

# Initialize Default Router and register ViewSets
router = DefaultRouter()
router.register(r"vehicles", VehicleViewSet, basename="vehicle")

# Define urlpatterns
urlpatterns = [
    # Include routes from the router (CRUD and custom VehicleViewSet actions)
    path("", include(router.urls)),

    # Routes for Vehicle components
    path(
        "vehicles/<str:vin>/components/",
        VehicleComponentsListView.as_view(),
        name="vehicle-components-list"
    ),
    path(
        "vehicles/<str:vin>/components/<str:component_type>/<str:component_name>/",
        VehicleComponentDetailView.as_view(),
        name="vehicle-component-detail"
    ),

    # Routes for Bulk Component Access Permissions
    path(
        "vehicles/<str:vin>/grant-access/",
        BulkComponentAccessView.as_view(),
        name="bulk-component-access"
    ),
]
