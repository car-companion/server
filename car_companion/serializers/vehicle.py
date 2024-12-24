from django.core.validators import RegexValidator
from rest_framework import serializers
from car_companion.models import Color, VehicleModel
from car_companion.models.vehicle import Vehicle


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['name']


class VehicleModelSerializer(serializers.ModelSerializer):
    manufacturer = serializers.StringRelatedField()

    class Meta:
        model = VehicleModel
        fields = ['name', 'manufacturer']


class VehicleSerializer(serializers.ModelSerializer):
    model = VehicleModelSerializer()
    default_exterior_color = ColorSerializer(source='outer_color')
    default_interior_color = ColorSerializer(source='interior_color')

    class Meta:
        model = Vehicle
        fields = ['vin',  'model', 'year_built', 'default_interior_color', 'default_exterior_color']
