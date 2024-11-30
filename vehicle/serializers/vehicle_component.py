from rest_framework import serializers
from vehicle.models import VehicleComponent


class VehicleComponentSerializer(serializers.ModelSerializer):
    component_type_name = serializers.CharField(source='component_type.name', read_only=True)

    class Meta:
        model = VehicleComponent
        fields = ['name', 'component_type_name', 'status']
