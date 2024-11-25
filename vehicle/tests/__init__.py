from .admin.color import ColorAdminTests
from .admin.manufacturer import ManufacturerAdminTests
from .models.color import ColorModelTests
from .models.manufacturer import ManufacturerModelTests

# from .views.vehicle_ownership import VehicleOwnershipTests

__all__ = ['ColorAdminTests',
           'ColorModelTests',
           'ManufacturerModelTests',
           'ManufacturerAdminTests',
           # 'VehicleOwnershipTests'
           ]
