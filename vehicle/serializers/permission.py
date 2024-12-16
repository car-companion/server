from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from vehicle.models import ComponentPermission, Vehicle

User = get_user_model()


class BasePermissionSerializer(serializers.Serializer):
    """Base serializer for permission-related operations."""

    class Meta:
        abstract = True


class GrantPermissionSerializer(BasePermissionSerializer):
    """Serializer for granting component permissions to users."""

    permission_type = serializers.ChoiceField(
        choices=ComponentPermission.PermissionType.choices,
        default=ComponentPermission.PermissionType.READ,
        help_text="Type of permission to grant"
    )
    valid_until = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Optional expiration date for the permission"
    )


class PermissionResultSerializer(BasePermissionSerializer):
    """Serializer for permission operation results."""

    granted = serializers.ListField(
        child=serializers.DictField(),
        help_text="Successfully granted permissions"
    )
    failed = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Failed permission operations"
    )


class RevokeRequestSerializer(BasePermissionSerializer):
    """Serializer for permission revocation requests."""

    username = serializers.CharField(
        help_text="Username of the user whose permissions will be revoked"
    )


class RevokeResultSerializer(BasePermissionSerializer):
    """Serializer for permission revocation results."""

    revoked = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="List of revoked permissions"
    )
    message = serializers.CharField(
        help_text="Summary of the revocation operation"
    )


class AccessedVehicleSerializer(serializers.ModelSerializer):
    """Serializer for vehicles a user has access to."""

    permissions = serializers.SerializerMethodField(
        help_text="Component permissions for this vehicle"
    )

    class Meta:
        model = Vehicle
        fields = ['vin', 'nickname', 'permissions']

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_permissions(self, obj: Vehicle) -> list:
        """Get component permissions for the current user."""
        permissions = (ComponentPermission.objects
                       .filter(
            component__vehicle=obj,
            user=self.context['request'].user
        )
                       .select_related('component', 'component__component_type')
                       )

        return [
            {
                'component_type': perm.component.component_type.name,
                'component_name': perm.component.name,
                'permission_type': perm.permission_type
            }
            for perm in permissions
        ]
