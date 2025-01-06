from .color import ColorModelTests
from .manufacturer import ManufacturerModelTests
from .vehicle_model import VehicleModelTests, ModelComponentTests
from .component_type import ComponentTypeModelTests
from .vehicle import VehicleTests, VehicleComponentTests
from .permission import ComponentPermissionModelTests
from .vehicle_preferences import VehicleUserPreferencesTests

__all__ = [
    'ColorModelTests',
    'ManufacturerModelTests',
    'VehicleModelTests',
    'ModelComponentTests',
    'ComponentTypeModelTests',
    'VehicleTests',
    'VehicleComponentTests',
    'ComponentPermissionModelTests',
    'VehicleUserPreferencesTests',
]
