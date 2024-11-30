from django.contrib.auth import get_user_model
from rest_framework import serializers
from vehicle.models import ComponentPermission

User = get_user_model()


class ComponentPermissionRequestSerializer(serializers.Serializer):
    """Serializer for individual component permission request."""
    component_type = serializers.CharField(
        help_text="Type of the component (e.g., 'engine', 'door')"
    )
    component_name = serializers.CharField(
        help_text="Name of the specific component (e.g., 'main engine', 'rear left door')"
    )
    permission_type = serializers.ChoiceField(
        choices=ComponentPermission.PermissionType.choices,
        help_text="Permission type: 'read' or 'write'"
    )
    valid_until = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Optional expiration date for the permission"
    )

    def validate_component_type(self, value):
        """Validate component type name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Component type cannot be empty")
        return value.strip().capitalize()

    def validate_component_name(self, value):
        """Validate component name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Component name cannot be empty")
        return value.strip().capitalize()


class ComponentAccessRequestSerializer(serializers.Serializer):
    """Serializer for granting access to multiple components."""
    username = serializers.CharField(
        help_text="Username to grant access to"
    )
    components = serializers.ListField(
        child=ComponentPermissionRequestSerializer(),
        help_text="List of components and their permission types",
        min_length=1
    )

    def validate_username(self, value):
        """Validate that the target user exists."""
        if not value or not value.strip():
            raise serializers.ValidationError("Username cannot be empty")
        try:
            User.objects.get(username=value.strip())
            return value.strip()
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")


class ComponentPermissionResultSerializer(serializers.Serializer):
    """Serializer for component permission result."""
    component_type = serializers.CharField()
    component_name = serializers.CharField()
    status = serializers.CharField()
    permission_type = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class ComponentAccessResponseSerializer(serializers.Serializer):
    """Serializer for the bulk access response."""
    message = serializers.CharField()
    granted = ComponentPermissionResultSerializer(many=True)
    failed = ComponentPermissionResultSerializer(many=True)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""
    message = serializers.CharField()


class UserPermissionDetailSerializer(serializers.ModelSerializer):
    """Serializer for user details in permission listing."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ComponentPermissionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed component permission information."""
    component_type = serializers.CharField(source='component.component_type.name')
    component_name = serializers.CharField(source='component.name')
    user = UserPermissionDetailSerializer()
    granted_by = UserPermissionDetailSerializer()

    class Meta:
        model = ComponentPermission
        fields = [
            'id',
            'component_type',
            'component_name',
            'user',
            'permission_type',
            'granted_by',
            'valid_until',
            'created',
            'modified'
        ]


class VehiclePermissionsResponseSerializer(serializers.Serializer):
    """Serializer for the vehicle permissions response."""
    vin = serializers.CharField()
    vehicle_name = serializers.CharField()
    owner = UserPermissionDetailSerializer()
    permissions = ComponentPermissionDetailSerializer(many=True)
