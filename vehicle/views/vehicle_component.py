from rest_framework import status, generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from guardian.shortcuts import get_perms
from django.shortcuts import get_object_or_404

from vehicle.models import Vehicle, VehicleComponent, ComponentPermission
from vehicle.serializers.vehicle_component import VehicleComponentSerializer


class BaseVehicleAccess:
    """Mixin for vehicle and component access validation."""

    def validate_vehicle_access(self, vin):
        """
        Validate VIN format and basic vehicle access.
        Returns (vehicle, error_response) tuple.
        """
        if len(vin) != 17:
            return None, Response(
                {'message': 'Invalid VIN format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vehicle = Vehicle.objects.get(vin=vin)
        except Vehicle.DoesNotExist:
            return None, Response(
                {'message': 'Vehicle not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return vehicle, None

    def validate_component_access(self, vehicle, component, user, required_permission=None):
        """
        Validate component access based on ownership and permissions.
        Args:
            vehicle: Vehicle instance
            component: VehicleComponent instance
            user: User requesting access
            required_permission: specific permission required (e.g., 'change_status')
        Returns:
            (bool, Response): (True, None) if access granted, (False, error_response) if denied
        """
        # Vehicle owner has full access
        if vehicle.owner == user:
            return True, None

        # Check if user has explicit permission
        user_perms = get_perms(user, component)

        # For read operations, 'view_status' is enough
        if not required_permission and 'view_status' in user_perms:
            return True, None

        # For write operations, check specific permission
        if required_permission and required_permission in user_perms:
            return True, None

        return False, Response(
            {'message': 'Access denied.'},
            status=status.HTTP_403_FORBIDDEN
        )


class VehicleComponentsListView(BaseVehicleAccess, generics.ListAPIView):
    """List all components for a vehicle."""

    serializer_class = VehicleComponentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=VehicleComponentSerializer(many=True),
                description='List of vehicle components'
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    'Error400',
                    fields={'message': serializers.CharField()}
                )
            ),
            403: OpenApiResponse(
                response=inline_serializer(
                    'Error403',
                    fields={'message': serializers.CharField()}
                )
            ),
            404: OpenApiResponse(
                response=inline_serializer(
                    'Error404',
                    fields={'message': serializers.CharField()}
                )
            ),
        }
    )
    def get(self, request, vin):
        """List all components for a vehicle the user has access to."""
        vehicle, error = self.validate_vehicle_access(vin)
        if error:
            return error

        # If user is owner, return all components
        if vehicle.owner == request.user:
            components = VehicleComponent.objects.filter(vehicle=vehicle)
        else:
            # Get only components user has permission to view
            component_ids = []
            for component in VehicleComponent.objects.filter(vehicle=vehicle):
                has_access, _ = self.validate_component_access(
                    vehicle, component, request.user
                )
                if has_access:
                    component_ids.append(component.id)

            components = VehicleComponent.objects.filter(id__in=component_ids)

        serializer = self.serializer_class(components, many=True)
        return Response(serializer.data)


class VehicleComponentDetailView(BaseVehicleAccess, generics.GenericAPIView):
    """Manage a specific vehicle component."""

    serializer_class = VehicleComponentSerializer
    permission_classes = [IsAuthenticated]

    def get_component(self, vehicle, component_type, component_name):
        """Get a specific component or return None."""
        try:
            return VehicleComponent.objects.get(
                vehicle=vehicle,
                component_type__name=component_type,
                name=component_name
            )
        except VehicleComponent.DoesNotExist:
            return None

    @extend_schema(
        responses={
            200: VehicleComponentSerializer,
            400: inline_serializer(
                'Error400',
                fields={'message': serializers.CharField()}
            ),
            403: inline_serializer(
                'Error403',
                fields={'message': serializers.CharField()}
            ),
            404: inline_serializer(
                'Error404',
                fields={'message': serializers.CharField()}
            ),
        }
    )
    def get(self, request, vin, component_type, component_name):
        """Get details of a specific component."""
        vehicle, error = self.validate_vehicle_access(vin)
        if error:
            return error

        component = self.get_component(vehicle, component_type, component_name)
        if not component:
            return Response(
                {'message': 'Component not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check access permission
        has_access, error = self.validate_component_access(
            vehicle, component, request.user
        )
        if not has_access:
            return error

        serializer = self.serializer_class(component)
        return Response(serializer.data)

    @extend_schema(
        request=inline_serializer(
            'ComponentStatusUpdate',
            fields={'status': serializers.FloatField()}
        ),
        responses={
            200: VehicleComponentSerializer,
            400: inline_serializer(
                'Error400',
                fields={'message': serializers.CharField()}
            ),
            403: inline_serializer(
                'Error403',
                fields={'message': serializers.CharField()}
            ),
            404: inline_serializer(
                'Error404',
                fields={'message': serializers.CharField()}
            ),
        }
    )
    def patch(self, request, vin, component_type, component_name):
        """Update the status of a specific component."""
        vehicle, error = self.validate_vehicle_access(vin)
        if error:
            return error

        component = self.get_component(vehicle, component_type, component_name)
        if not component:
            return Response(
                {'message': 'Component not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check write permission
        has_access, error = self.validate_component_access(
            vehicle, component, request.user, 'change_status'
        )
        if not has_access:
            return error

        try:
            status_value = float(request.data.get('status', 0))
            if not 0 <= status_value <= 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {'message': 'Status must be a float between 0 and 1.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        component.status = status_value
        component.save()

        serializer = self.serializer_class(component)
        return Response(serializer.data)
