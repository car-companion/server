from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from vehicle.models.vehicle import Vehicle


class VehicleRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['vin']

class VehicleSerializer(serializers.ModelSerializer):
    manufacturer = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    outer_color = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ['vin', 'nickname', 'manufacturer', 'model_name', 'year_built', 'outer_color']

    @extend_schema_field(OpenApiTypes.STR)
    def get_manufacturer(self, vehicle: Vehicle) -> str:
        return str(vehicle.model.manufacturer.name)

    @extend_schema_field(OpenApiTypes.STR)
    def get_model_name(self, vehicle: Vehicle) -> str:
        return str(vehicle.model.name)
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_outer_color(self, vehicle: Vehicle) -> str:
        return str(vehicle.outer_color)

class VehicleNicknameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['nickname']
        extra_kwargs = {
            'nickname': {
                'required': True,
                'allow_blank': False,
                'min_length': 2,
                'max_length': 100
            }
        }
