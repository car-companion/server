from rest_framework import serializers
from vehicle.models import VehicleComponent, ComponentType


class ComponentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponentType
        fields = ['name']


class ComponentSerializer(serializers.ModelSerializer):
    type = ComponentTypeSerializer(source='component_type', read_only=True)

    class Meta:
        model = VehicleComponent
        fields = ['name', 'type', 'status']


class ComponentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.FloatField(min_value=0.0, max_value=1.0, required=True)
