from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.vehicle_component import ComponentList, ComponentDetail, ComponentByType
from .views.vehicle import VehicleViewSet

router = DefaultRouter()
router.register('vehicles', VehicleViewSet, basename='vehicle')

component_patterns = [
    path('', ComponentList.as_view(), name='component-list'),
    path('<str:type_name>/', ComponentByType.as_view(), name='component-by-type'),
    path('<str:type_name>/<str:name>/', ComponentDetail.as_view(), name='component-detail'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('vehicles/<str:vin>/components/', include((component_patterns, 'components'))),
]