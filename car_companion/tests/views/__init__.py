from .vehicle import VehicleViewSetTests
from .vehicle_component import ComponentViewsTests
from .permission import (VehiclePermissionReadOnlyTests, VehiclePermissionFilteringTests,
                         VehiclePermissionManagementTests, AccessedVehiclesViewTests)
from .color import ColorListCreateViewTests
from .vehicle_preferences import VehiclePreferencesViewTests

__all__ = [
    'VehicleViewSetTests',
    'ComponentViewsTests',
    'VehiclePermissionReadOnlyTests',
    'VehiclePermissionFilteringTests',
    'VehiclePermissionManagementTests',
    'AccessedVehiclesViewTests',
    'ColorListCreateViewTests',
    'VehiclePreferencesViewTests',
]
