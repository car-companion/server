from .color import ColorAdmin
from .manufacturer import ManufacturerAdmin
from .vehicle_model import VehicleModelAdmin
from .vehicle import VehicleAdmin
from .component_type import ComponentTypeAdmin
from .user import UserAdmin
from .group import GroupAdmin

__all__ = [
    'UserAdmin',
    'GroupAdmin',
    'ColorAdmin',
    'ManufacturerAdmin',
    'VehicleModelAdmin',
    'VehicleAdmin',
    'ComponentTypeAdmin',
]
