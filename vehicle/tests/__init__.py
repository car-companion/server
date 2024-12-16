from .admin.color import ColorAdminTests
from .admin.manufacturer import ManufacturerAdminTests
from .admin.vehicle_model import VehicleModelAdminTests
from .admin.vehicle import VehicleAdminTests
from .models.color import ColorModelTests
from .models.manufacturer import ManufacturerModelTests
from .models.vehicle_model import VehicleModelTests, ModelComponentTests
from .models.component_type import ComponentTypeModelTests
from .models.vehicle import VehicleTests, VehicleComponentTests
from .models.permission import ComponentPermissionModelTests
from .serializers.vehicle import ColorSerializerTests, VehicleModelSerializerTests, VehicleSerializerTests, \
    NicknameSerializerTests
from .serializers.vehicle_component import ComponentTypeSerializerTests, ComponentSerializerTests, \
    ComponentStatusUpdateSerializerTests
from .serializers.permission import (GrantPermissionSerializerTests, PermissionResultSerializerTests,
                                     RevokeRequestSerializerTests, RevokeResultSerializerTests,
                                     AccessedVehicleSerializerTests)
from .views.vehicle import VehicleViewSetTests
from .views.vehicle_component import ComponentViewsTests
from .views.permission import (VehiclePermissionReadOnlyTests, VehiclePermissionFilteringTests,
                               VehiclePermissionManagementTests, AccessedVehiclesViewTests)
from .views.permission import AccessedVehiclesViewTests

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
           'ComponentPermissionModelTests',
           'ColorSerializerTests',
           'VehicleModelSerializerTests',
           'VehicleSerializerTests',
           'NicknameSerializerTests',
           'VehicleViewSetTests',
           'ComponentTypeSerializerTests',
           'ComponentSerializerTests',
           'ComponentStatusUpdateSerializerTests',
           'ComponentViewsTests',
           'VehiclePermissionReadOnlyTests',
           'VehiclePermissionFilteringTests',
           'VehiclePermissionManagementTests',
           'AccessedVehiclesViewTests'
           ]
