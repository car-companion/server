from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers
from django.db.models import Prefetch

from vehicle.models import ComponentPermission, VehicleComponent, Vehicle
from vehicle.serializers.permissions import (
    ComponentAccessRequestSerializer,
    ComponentAccessResponseSerializer,
    ErrorResponseSerializer,
    VehiclePermissionsResponseSerializer
)

User = get_user_model()


class BulkComponentAccessView(generics.GenericAPIView):
    """Grant and view access to vehicle components."""
    permission_classes = [IsAuthenticated]
    serializer_class = ComponentAccessRequestSerializer

    def get_vehicle_and_check_ownership(self, vin, user):
        """Get vehicle and verify ownership."""
        vehicle = get_object_or_404(Vehicle, vin=vin)
        if vehicle.owner != user:
            raise PermissionDenied("You do not own this vehicle")
        return vehicle

    def get_target_user(self, username, vehicle_owner):
        """Get target user and validate."""
        user = get_object_or_404(User, username=username)
        if user == vehicle_owner:
            raise ValidationError("Cannot grant access to vehicle owner")
        return user

    def get_component(self, vehicle, component_type, component_name):
        """Get component by its natural keys."""
        return get_object_or_404(
            VehicleComponent,
            vehicle=vehicle,
            component_type__name=component_type,
            name=component_name
        )

    def process_component_permission(self, component_data, vehicle, target_user, granting_user):
        """Process permission for a single component."""
        try:
            # Get component using natural keys
            component = self.get_component(
                vehicle=vehicle,
                component_type=component_data['component_type'],
                component_name=component_data['component_name']
            )

            # Create or update permission
            permission, created = ComponentPermission.objects.update_or_create(
                component=component,
                user=target_user,
                defaults={
                    'permission_type': component_data['permission_type'],
                    'granted_by': granting_user,
                    'valid_until': component_data.get('valid_until')
                }
            )

            return {
                'component_type': component.component_type.name,
                'component_name': component.name,
                'status': 'created' if created else 'updated',
                'permission_type': permission.permission_type
            }

        except VehicleComponent.DoesNotExist:
            return {
                'component_type': component_data['component_type'],
                'component_name': component_data['component_name'],
                'status': 'failed',
                'error': 'Component not found'
            }

    @extend_schema(
        description="Get all component permissions for a vehicle",
        responses={
            200: VehiclePermissionsResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        },
        tags=['Vehicle Component Permissions']
    )
    def get(self, request, vin):
        """Get all component permissions for a vehicle."""
        try:
            # Get vehicle with prefetched relationships
            vehicle = get_object_or_404(
                Vehicle.objects.select_related('owner')
                .prefetch_related(
                    Prefetch(
                        'components__access_permissions',
                        queryset=ComponentPermission.objects.select_related(
                            'user',
                            'granted_by',
                            'component__component_type'
                        )
                    )
                ),
                vin=vin
            )

            # Check ownership
            if vehicle.owner != request.user:
                raise PermissionDenied("You do not own this vehicle")

            # Collect all permissions
            all_permissions = []
            for component in vehicle.components.all():
                all_permissions.extend(component.access_permissions.all())

            # Prepare response data
            response_data = {
                'vin': vehicle.vin,
                'vehicle_name': str(vehicle),
                'owner': vehicle.owner,
                'permissions': all_permissions
            }

            # Serialize and return
            serializer = VehiclePermissionsResponseSerializer(response_data)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @extend_schema(
        description="Grant access to multiple components for a user",
        request=ComponentAccessRequestSerializer,
        responses={
            200: ComponentAccessResponseSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        },
        tags=['Vehicle Component Permissions']
    )
    def post(self, request, vin):
        """Grant access to multiple components for a user."""
        try:
            # Get and validate vehicle
            vehicle = self.get_vehicle_and_check_ownership(vin, request.user)

            # Validate request data
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Get and validate target user
            target_user = self.get_target_user(
                serializer.validated_data['username'],
                vehicle.owner
            )

            # Process each component
            results = []
            for component_data in serializer.validated_data['components']:
                result = self.process_component_permission(
                    component_data,
                    vehicle,
                    target_user,
                    request.user
                )
                results.append(result)

            # Group results by status
            successful = [r for r in results if r['status'] in ('created', 'updated')]
            failed = [r for r in results if r['status'] == 'failed']

            # Prepare response
            response_data = {
                'message': f'Processed access request for user {target_user.username}',
                'granted': successful,
                'failed': failed
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
