from django.contrib.auth import get_user_model
from rest_framework import serializers
from vehicle.models import ComponentPermission, Vehicle

User = get_user_model()


class ComponentPermissionRequestSerializer(serializers.Serializer):
    component_type = serializers.CharField(required=False, allow_null=True)
    component_name = serializers.CharField(required=False)
    permission_type = serializers.ChoiceField(choices=ComponentPermission.PermissionType.choices)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, data):
        data['component_type'] = data.get('component_type', '').strip().capitalize()
        if 'component_name' in data:
            data['component_name'] = data['component_name'].strip().capitalize()
        return data


class AccessRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    components = ComponentPermissionRequestSerializer(many=True)


class PermissionResultSerializer(serializers.Serializer):
    granted = serializers.ListField(child=serializers.DictField())
    revoked = serializers.ListField(child=serializers.DictField(), required=False)
    failed = serializers.ListField(child=serializers.DictField())


class AccessedVehicleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ['vin', 'nickname', 'permissions']

    def get_permissions(self, obj):
        permissions = ComponentPermission.objects.filter(
            component__vehicle=obj, user=self.context['request'].user
        ).select_related('component', 'component__component_type')

        return [
            {
                'component_type': perm.component.component_type.name,
                'component_name': perm.component.name,
                'permission_type': perm.permission_type
            }
            for perm in permissions
        ]
