from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers

from vehicle.models import Vehicle, VehicleComponent
from vehicle.serializers.vehicle_component import VehicleComponentSerializer


class BaseVehicleAccess:
    """Mixin for vehicle access validation."""

    def validate_vehicle_access(self, vin):
        """
        Validate VIN format and vehicle access.
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

        if vehicle.owner != self.request.user:
            return None, Response(
                {'message': 'Access denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return vehicle, None


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
        """List all components for a vehicle."""
        vehicle, error = self.validate_vehicle_access(vin)
        if error:
            return error

        components = VehicleComponent.objects.filter(vehicle=vehicle)
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
