from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import status, generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from vehicle.models import Vehicle, VehicleComponent
from vehicle.serializers.vehicle_component import VehicleComponentSerializer


class VehicleComponentsView(generics.GenericAPIView):
    """
    API endpoints for vehicle components:
    - List all components for a vehicle
    - Get details of a specific component
    Only accessible by the vehicle owner.
    """
    serializer_class = VehicleComponentSerializer
    permission_classes = [IsAuthenticated]

    def _validate_vehicle_access(self, vin):
        """
        Validate VIN format and vehicle access.
        Returns (vehicle, error_response) tuple.
        """
        # Validate VIN length
        if len(vin) != 17:
            return None, Response(
                {'message': 'Invalid VIN format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve vehicle or return 404
        try:
            vehicle = Vehicle.objects.get(vin=vin)
        except Vehicle.DoesNotExist:
            return None, Response(
                {'message': 'Vehicle with given VIN does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check ownership
        if vehicle.owner != self.request.user:
            return None, Response(
                {'message': 'You do not have permission to access this vehicle\'s components.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return vehicle, None

    @extend_schema(
        methods=['GET'],
        request=None,
        responses={
            '200': OpenApiResponse(
                response=VehicleComponentSerializer(many=True),
                description='List of components and their status for the requested vehicle.',
            ),
            '403': OpenApiResponse(
                response=inline_serializer(
                    'VehicleNotOwned',
                    fields={'message': serializers.CharField(
                        default='You do not have permission to access this vehicle\'s components.')}
                ),
                description='User is not the owner of the vehicle.',
            ),
            '404': OpenApiResponse(
                response=inline_serializer(
                    'VehicleNotFound',
                    fields={'message': serializers.CharField(default='Vehicle with given VIN does not exist.')}
                ),
                description='The vehicle with the provided VIN does not exist.',
            ),
            '400': OpenApiResponse(
                response=inline_serializer(
                    'InvalidVIN',
                    fields={'message': serializers.CharField(default='Invalid VIN format.')}
                ),
                description='Invalid VIN provided in the request.',
            ),
        },
    )
    def get(self, request, vin):
        """List all components for a vehicle."""
        vehicle, error = self._validate_vehicle_access(vin)
        if error:
            return error

        components = VehicleComponent.objects.filter(vehicle=vehicle)
        serializer = self.serializer_class(components, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        methods=['GET'],
        request=None,
        responses={
            '200': OpenApiResponse(
                response=inline_serializer(
                    'VehicleComponentDetail',
                    fields={
                        'name': serializers.CharField(),
                        'status': serializers.CharField(),
                        'component_type': serializers.CharField(),
                        'updated_at': serializers.DateTimeField()
                    }
                ),
                description='Details of the requested component, including its type.',
            ),
            '403': OpenApiResponse(
                response=inline_serializer(
                    'VehicleNotOwned',
                    fields={'message': serializers.CharField(
                        default='You do not have permission to access this vehicle\'s components.')}
                ),
                description='User is not the owner of the vehicle.',
            ),
            '404': OpenApiResponse(
                response=inline_serializer(
                    'NotFound',
                    fields={'message': serializers.CharField(
                        default='Vehicle or component not found.')}
                ),
                description='The vehicle or component does not exist.',
            ),
            '400': OpenApiResponse(
                response=inline_serializer(
                    'InvalidRequest',
                    fields={'message': serializers.CharField(default='Invalid request parameters.')}
                ),
                description='Invalid parameters provided in the request.',
            ),
        },
    )
    def get(self, request, vin, component_type=None, component_name=None):
        """
        Get component details or list all components.
        If component_type and component_name are provided, returns specific component details.
        Otherwise, returns list of all components.
        """
        vehicle, error = self._validate_vehicle_access(vin)
        if error:
            return error

        # If component details are requested
        if component_type and component_name:
            try:
                component = (VehicleComponent.objects
                .select_related('component_type')
                .get(
                    vehicle=vehicle,
                    name=component_name,
                    component_type__name=component_type
                ))

                response_data = {
                    'name': component.name,
                    'status': component.status,
                    'component_type': component.component_type.name,
                    'modified': component.modified
                }
                return Response(response_data, status=status.HTTP_200_OK)

            except VehicleComponent.DoesNotExist:
                return Response(
                    {'message': f'Component "{component_name}" of type "{component_type}" not found for this vehicle.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Otherwise, list all components
        components = VehicleComponent.objects.filter(vehicle=vehicle)
        serializer = self.serializer_class(components, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
