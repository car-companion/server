from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import re
from typing import Optional, Union

from car_companion.models import Vehicle, VehicleComponent, ComponentPermission
from car_companion.serializers.vehicle_component import (
    ComponentSerializer,
    ComponentStatusUpdateSerializer
)


class ComponentBaseView(generics.GenericAPIView):
    """Base view for component-related operations."""

    permission_classes = [IsAuthenticated]
    serializer_class = ComponentSerializer

    VIN_PATTERN = r'^[A-HJ-NPR-Z0-9]{17}$'

    def validate_vin(self, vin: str) -> str:
        """Validate VIN format and return uppercase VIN if valid."""
        vin = vin.upper()
        if not re.match(self.VIN_PATTERN, vin):
            raise ValidationError('Invalid Vehicle Identification Number (VIN) format')
        return vin

    def get_vehicle(self, vin: str) -> Vehicle:
        """Get vehicle by VIN with validation."""
        validated_vin = self.validate_vin(vin)
        return get_object_or_404(Vehicle, vin=validated_vin)

    def check_access(self, vehicle: Vehicle, user, required_permission: str = 'read') -> bool:
        """Check if user has access to vehicle components."""
        # Vehicle owner has full access
        if vehicle.owner == user:
            return True

        permissions = ComponentPermission.objects.filter(
            component__vehicle=vehicle,
            user=user
        )

        return (
            permissions.filter(permission_type='write').exists()
            if required_permission == 'write'
            else permissions.exists()
        )

    def check_component_permission(self, component, user, required_permission='read'):
        """
        Check if user has permission for specific component.

        Args:
            component: VehicleComponent instance
            user: User instance
            required_permission: 'read' or 'write' permission required

        Returns:
            bool: True if user has permission, False otherwise
        """
        # If user is the vehicle owner, they have full access
        if component.vehicle.owner == user:
            return True

        # Check if there's any permission record for this user and component
        permission = ComponentPermission.objects.filter(
            component=component,
            user=user
        ).first()

        # If no permission found, deny access
        if not permission:
            return False

        # For write permission, need explicit write permission
        if required_permission == 'write':
            return permission.permission_type == 'write'

        # For read permission, any permission type is sufficient
        return True

    def get_accessible_components(self, vehicle: Vehicle, user, type_name: Optional[str] = None,
                                  required_permission: str = 'read') -> 'QuerySet[VehicleComponent]':
        """Get components that the user has permission to access."""
        base_query = VehicleComponent.objects.filter(vehicle=vehicle)
        if type_name:
            base_query = base_query.filter(component_type__name=type_name)

        if vehicle.owner == user:
            return base_query

        permission_filter = {
            'access_permissions__user': user,
        }
        if required_permission == 'write':
            permission_filter['access_permissions__permission_type'] = 'write'

        return base_query.filter(**permission_filter).distinct()

    def handle_validation_error(self, exc: ValidationError) -> Response:
        """Convert ValidationError to Response."""
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )


class ComponentList(ComponentBaseView):
    """API endpoints for listing all components of a vehicle."""

    @extend_schema(
        operation_id="list_vehicle_components",
        summary="List Vehicle Components",
        parameters=[
            OpenApiParameter(
                name="vin",
                description="Vehicle Identification Number",
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ],
        responses={
            200: ComponentSerializer(many=True),
            400: OpenApiResponse(description="Invalid VIN format"),
            403: OpenApiResponse(description="User does not have permission to access vehicle components"),
            404: OpenApiResponse(description="Vehicle not found")
        },
        description='List all components for a vehicle that the user has permission to access',
        tags=['Vehicle Components']
    )
    def get(self, request, vin: str) -> Response:
        """Get all components for a vehicle that the user has permission to access."""
        try:
            vehicle = self.get_vehicle(vin)
            if not self.check_access(vehicle, request.user, 'read'):
                return Response(
                    {'detail': 'Access denied - insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN
                )

            components = self.get_accessible_components(vehicle, request.user)
            return Response(self.serializer_class(components, many=True).data)

        except ValidationError as e:
            return self.handle_validation_error(e)


class ComponentByType(ComponentBaseView):
    """API endpoints for managing components by type."""

    @extend_schema(
        operation_id="list_components_by_type",
        summary="List Components by Type",
        parameters=[
            OpenApiParameter(name="vin", description="Vehicle Identification Number", required=True, type=str,
                             location=OpenApiParameter.PATH),
            OpenApiParameter(name="type_name", description="Component type name", required=True, type=str,
                             location=OpenApiParameter.PATH)
        ],
        responses={
            200: ComponentSerializer(many=True),
            400: OpenApiResponse(description="Invalid VIN format"),
            403: OpenApiResponse(description="Insufficient permissions"),
            404: OpenApiResponse(description="Vehicle or components not found")
        },
        description='Get all components of a specific type that the user has permission to access',
        tags=['Vehicle Components']
    )
    def get(self, request, vin: str, type_name: str) -> Response:
        """Get all components of a specific type that the user has permission to access."""
        try:
            vehicle = self.get_vehicle(vin)
            if not self.check_access(vehicle, request.user, 'read'):
                return Response(
                    {'detail': f'Access denied - insufficient permissions for {type_name} components'},
                    status=status.HTTP_403_FORBIDDEN
                )

            components = self.get_accessible_components(vehicle, request.user, type_name)
            if not components.exists():
                return Response(
                    {'detail': f'No accessible components found of type {type_name}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(self.serializer_class(components, many=True).data)

        except ValidationError as e:
            return self.handle_validation_error(e)

    @extend_schema(
        operation_id="update_components_by_type",
        summary="Update Components by Type",
        parameters=[
            OpenApiParameter(name="vin", description="Vehicle Identification Number", required=True, type=str,
                             location=OpenApiParameter.PATH),
            OpenApiParameter(name="type_name", description="Component type name", required=True, type=str,
                             location=OpenApiParameter.PATH)
        ],
        request=ComponentStatusUpdateSerializer,
        responses={
            200: ComponentSerializer(many=True),
            400: OpenApiResponse(description="Invalid VIN format or status value"),
            403: OpenApiResponse(description="Insufficient write permissions"),
            404: OpenApiResponse(description="Vehicle or components not found")
        },
        description='Update status of all components of a specific type (requires write permission)',
        tags=['Vehicle Components']
    )
    def patch(self, request, vin: str, type_name: str) -> Response:
        """Update status of all components of a specific type (requires write permission)."""
        try:
            vehicle = self.get_vehicle(vin)
            if not self.check_access(vehicle, request.user, 'write'):
                return Response(
                    {'detail': f'Access denied - insufficient write permissions for {type_name} components'},
                    status=status.HTTP_403_FORBIDDEN
                )

            components = self.get_accessible_components(vehicle, request.user, type_name, 'write')
            if not components.exists():
                return Response(
                    {'detail': f'No components found of type {type_name} with write permission'},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ComponentStatusUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            components.update(status=serializer.validated_data['status'])
            return Response(self.serializer_class(components, many=True).data)

        except ValidationError as e:
            return self.handle_validation_error(e)


class ComponentDetail(ComponentBaseView):
    """API endpoints for managing individual components."""

    @extend_schema(
        operation_id="get_component_detail",
        summary="Get Component Details",
        parameters=[
            OpenApiParameter(name="vin", description="Vehicle Identification Number", required=True, type=str,
                             location=OpenApiParameter.PATH),
            OpenApiParameter(name="type_name", description="Component type name", required=True, type=str,
                             location=OpenApiParameter.PATH),
            OpenApiParameter(name="name", description="Component name", required=True, type=str,
                             location=OpenApiParameter.PATH)
        ],
        responses={
            200: ComponentSerializer,
            400: OpenApiResponse(description="Invalid VIN format"),
            403: OpenApiResponse(description="Insufficient permissions"),
            404: OpenApiResponse(description="Vehicle or component not found")
        },
        description='Get details of a specific component',
        tags=['Vehicle Components']
    )
    def get(self, request, vin: str, type_name: str, name: str) -> Response:
        """Get details of a specific component."""
        try:
            vehicle = self.get_vehicle(vin)
            component = get_object_or_404(
                VehicleComponent,
                vehicle=vehicle,
                component_type__name=type_name,
                name=name
            )

            if not self.check_component_permission(component, request.user, 'read'):
                return Response(
                    {'detail': f'Access denied - insufficient permissions for component {name}'},
                    status=status.HTTP_403_FORBIDDEN
                )

            return Response(self.serializer_class(component).data)

        except ValidationError as e:
            return self.handle_validation_error(e)

    @extend_schema(
        operation_id="update_component_status",
        summary="Update Component Status",
        parameters=[
            OpenApiParameter(name="vin", description="Vehicle Identification Number", required=True, type=str,
                             location=OpenApiParameter.PATH),
            OpenApiParameter(name="type_name", description="Component type name", required=True, type=str,
                             location=OpenApiParameter.PATH),
            OpenApiParameter(name="name", description="Component name", required=True, type=str,
                             location=OpenApiParameter.PATH)
        ],
        request=ComponentStatusUpdateSerializer,
        responses={
            200: ComponentSerializer,
            400: OpenApiResponse(description="Invalid VIN format or status value"),
            403: OpenApiResponse(description="Insufficient write permissions"),
            404: OpenApiResponse(description="Vehicle or component not found")
        },
        description='Update status of a specific component (requires write permission)',
        tags=['Vehicle Components']
    )
    def patch(self, request, vin: str, type_name: str, name: str) -> Response:
        """Update status of a specific component (requires write permission)."""
        try:
            vehicle = self.get_vehicle(vin)
            component = get_object_or_404(
                VehicleComponent,
                vehicle=vehicle,
                component_type__name=type_name,
                name=name
            )

            if not self.check_component_permission(component, request.user, 'write'):
                return Response(
                    {'detail': f'Access denied - insufficient write permissions for component {name}'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = ComponentStatusUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            component.status = serializer.validated_data['status']
            component.save()
            return Response(self.serializer_class(component).data)

        except ValidationError as e:
            return self.handle_validation_error(e)
