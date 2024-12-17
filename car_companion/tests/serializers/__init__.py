from .vehicle import ColorSerializerTests, VehicleModelSerializerTests, VehicleSerializerTests
from .vehicle_component import ComponentTypeSerializerTests, ComponentSerializerTests, \
    ComponentStatusUpdateSerializerTests
from .permission import (GrantPermissionSerializerTests, PermissionResultSerializerTests,
                         RevokeRequestSerializerTests, RevokeResultSerializerTests,
                         AccessedVehicleSerializerTests)
from .color import ColorSerializerTests, ColorCreateSerializerTests
from .vehicle_preferences import (PreferencesSerializerTests, PreferencesUpdateSerializerTests,
                                  ColorFieldWithCreationTests, VehiclePreferencesSerializerTests)

__all__ = [
    'ColorSerializerTests',
    'VehicleModelSerializerTests',
    'VehicleSerializerTests',
    'ComponentTypeSerializerTests',
    'ComponentSerializerTests',
    'ComponentStatusUpdateSerializerTests',
    'GrantPermissionSerializerTests',
    'PermissionResultSerializerTests',
    'RevokeRequestSerializerTests',
    'RevokeResultSerializerTests',
    'AccessedVehicleSerializerTests',
    'ColorCreateSerializerTests',
    'PreferencesSerializerTests',
    'PreferencesUpdateSerializerTests',
    'VehiclePreferencesSerializerTests',
    'ColorFieldWithCreationTests',
]
