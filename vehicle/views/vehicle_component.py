from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import re

from vehicle.models import Vehicle, VehicleComponent
from vehicle.serializers.vehicle_component import (
    ComponentSerializer,
    ComponentStatusUpdateSerializer
)


class ComponentBaseView(generics.GenericAPIView):
    """Base view for component-related operations."""

    permission_classes = [IsAuthenticated]
    serializer_class = ComponentSerializer

    VIN_PATTERN = r'^[A-HJ-NPR-Z0-9]{17}$'

    def validate_vin(self, vin):
        """
        Validate VIN format and return uppercase VIN if valid.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Uppercase VIN if valid

        Raises:
            ValidationError: If VIN format is invalid
        """
        vin = vin.upper()
        if not re.match(self.VIN_PATTERN, vin):
            raise ValidationError('VIN is invalid')
        return vin

    def get_vehicle(self, vin):
        """
        Get vehicle by VIN with validation.

        Args:
            vin: Vehicle Identification Number

        Returns:
            The requested vehicle instance

        Raises:
            ValidationError: If VIN format is invalid
            Http404: If vehicle not found
        """
        validated_vin = self.validate_vin(vin)
        return get_object_or_404(Vehicle, vin=validated_vin)

    def check_access(self, vehicle, user):
        """Check if user has access to vehicle."""
        return vehicle.owner == user

    def handle_validation_error(self, exc):
        """Convert ValidationError to Response."""
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )


class ComponentList(ComponentBaseView):
    """View for listing all components of a vehicle."""

    @extend_schema(
        operation_id="list_vehicle_components",
        responses={
            200: ComponentSerializer(many=True),
            400: OpenApiResponse(description="VIN is invalid"),
            403: OpenApiResponse(description='Access denied'),
            404: OpenApiResponse(description='Vehicle not found')
        },
        description='List all components for a vehicle'
    )
    def get(self, request, vin):
        try:
            vehicle = self.get_vehicle(vin)
            if not self.check_access(vehicle, request.user):
                return Response(
                    {'detail': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            queryset = VehicleComponent.objects.filter(vehicle=vehicle)
            return Response(self.serializer_class(queryset, many=True).data)
        except ValidationError as e:
            return self.handle_validation_error(e)


class ComponentByType(ComponentBaseView):
    """View for managing components by type."""

    @extend_schema(
        operation_id="list_components_by_type",
        responses={
            200: ComponentSerializer(many=True),
            400: OpenApiResponse(description="VIN is invalid"),
            403: OpenApiResponse(description='Access denied'),
            404: OpenApiResponse(description='Vehicle or components not found')
        },
        description='Get all components of a specific type for a vehicle',
        tags=['Vehicle Component']
    )
    def get(self, request, vin, type_name):
        try:
            vehicle = self.get_vehicle(vin)
            if not self.check_access(vehicle, request.user):
                return Response(
                    {'detail': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            components = VehicleComponent.objects.filter(
                vehicle=vehicle,
                component_type__name=type_name
            )

            if not components.exists():
                return Response(
                    {'detail': 'No components found of this type'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(self.serializer_class(components, many=True).data)
        except ValidationError as e:
            return self.handle_validation_error(e)

    @extend_schema(
        operation_id="update_components_by_type",
        request=ComponentStatusUpdateSerializer,
        responses={
            200: ComponentSerializer(many=True),
            400: OpenApiResponse(description='VIN is invalid or Invalid status value'),
            403: OpenApiResponse(description='Access denied'),
            404: OpenApiResponse(description='Vehicle or components not found')
        },
        description='Update status of all components of a specific type',
        tags=['Vehicle Component']
    )
    def patch(self, request, vin, type_name):
        try:
            vehicle = self.get_vehicle(vin)
            if not self.check_access(vehicle, request.user):
                return Response(
                    {'detail': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            components = VehicleComponent.objects.filter(
                vehicle=vehicle,
                component_type__name=type_name
            )

            if not components.exists():
                return Response(
                    {'detail': 'No components found of this type'},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ComponentStatusUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            new_status = serializer.validated_data['status']
            components.update(status=new_status)
            return Response(self.serializer_class(components, many=True).data)
        except ValidationError as e:
            return self.handle_validation_error(e)


class ComponentDetail(ComponentBaseView):
    """View for managing individual components."""

    @extend_schema(
        operation_id="get_component_detail",  # Unique operationId
        responses={
            200: ComponentSerializer,
            400: OpenApiResponse(description="VIN is invalid"),
            403: OpenApiResponse(description='Access denied'),
            404: OpenApiResponse(description='Vehicle or component not found')
        },
        description='Get details of a specific component',
        tags=['Vehicle Component']
    )
    def get(self, request, vin, type_name, name):
        try:
            vehicle = self.get_vehicle(vin)
            if not self.check_access(vehicle, request.user):
                return Response(
                    {'detail': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            component = get_object_or_404(
                VehicleComponent,
                vehicle=vehicle,
                component_type__name=type_name,
                name=name
            )
            return Response(self.serializer_class(component).data)
        except ValidationError as e:
            return self.handle_validation_error(e)

    @extend_schema(
        operation_id="update_component_detail",
        request=ComponentStatusUpdateSerializer,
        responses={
            200: ComponentSerializer,
            400: OpenApiResponse(description='Invalid status value or Invalid VIN'),
            403: OpenApiResponse(description='Access denied'),
            404: OpenApiResponse(description='Vehicle or component not found')
        },
        description='Update status of a specific component',
        tags=['Vehicle Component']
    )
    def patch(self, request, vin, type_name, name):
        try:
            vehicle = self.get_vehicle(vin)
            if not self.check_access(vehicle, request.user):
                return Response(
                    {'detail': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            component = get_object_or_404(
                VehicleComponent,
                vehicle=vehicle,
                component_type__name=type_name,
                name=name
            )

            serializer = ComponentStatusUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            component.status = serializer.validated_data['status']
            component.save()
            return Response(self.serializer_class(component).data)
        except ValidationError as e:
            return self.handle_validation_error(e)
