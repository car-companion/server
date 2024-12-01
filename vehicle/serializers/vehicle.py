from django.core.validators import RegexValidator
from rest_framework import serializers
from vehicle.models import Color, VehicleModel
from vehicle.models.vehicle import Vehicle


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
    outer_color = ColorSerializer()
    interior_color = ColorSerializer()

    class Meta:
        model = Vehicle
        fields = ['vin', 'nickname', 'model', 'year_built', 'interior_color', 'outer_color']


class NicknameSerializer(serializers.Serializer):
    nickname = serializers.CharField(
        min_length=2,
        max_length=100,
        required=True,
        allow_blank=False,
        validators=[
            RegexValidator(regex=r'^[a-zA-Z0-9\s\-]*$')
        ],
    )
