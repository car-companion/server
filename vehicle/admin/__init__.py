from .color import ColorAdmin
from .manufacturer import ManufacturerAdmin
from .vehicle_model import VehicleModelAdmin
from .vehicle import VehicleAdmin
from .component import ComponentTypeAdmin
from .user_and_groups import UserAdmin, GroupAdmin

__all__ = [
    'UserAdmin',
    'GroupAdmin',
    'ColorAdmin',
    'ManufacturerAdmin',
    'VehicleModelAdmin',
    'VehicleAdmin',
    'ComponentTypeAdmin',
]
