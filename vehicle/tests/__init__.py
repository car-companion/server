from .admin.color import ColorAdminTests
from .admin.manufacturer import ManufacturerAdminTests
from .admin.vehicle_model import VehicleModelAdminTests
from .admin.vehicle import VehicleAdminTests
from .models.color import ColorModelTests
from .models.manufacturer import ManufacturerModelTests
from .models.vehicle_model import VehicleModelTests, ModelComponentTests
from .models.component_type import ComponentTypeModelTests
from .models.vehicle import VehicleTests, VehicleComponentTests
from .models.permissions import ComponentPermissionModelTests

__all__ = ['ColorAdminTests',
           'ColorModelTests',
           'ManufacturerAdminTests',
           'ManufacturerModelTests',
           'VehicleModelAdminTests',
           'VehicleAdminTests',
           'VehicleModelTests',
           'ModelComponentTests',
           'ComponentTypeModelTests',
           'VehicleTests',
           'VehicleComponentTests',
           'ComponentPermissionModelTests'
           ]
