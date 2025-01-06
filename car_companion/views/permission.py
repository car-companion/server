from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from car_companion.models import ComponentPermission, VehicleComponent, Vehicle
from car_companion.serializers.permission import (
    AccessedVehicleSerializer, GrantPermissionSerializer, PermissionResultSerializer, RevokeResultSerializer
)

User = get_user_model()


class VehiclePermissionBaseView(generics.GenericAPIView):
    """Base view for vehicle-related permissions."""
    permission_classes = [IsAuthenticated]

    def get_vehicle(self, vin):
        """Retrieve a vehicle by VIN."""
        return get_object_or_404(Vehicle.objects.select_related('owner'), vin=vin)

    def check_vehicle_ownership(self, vehicle, user):
        """Ensure the user is the vehicle's owner."""
        if vehicle.owner != user:
            raise PermissionDenied("You are not authorized to manage this vehicle.")

    def get_filtered_components(self, vehicle, component_type=None, component_name=None):
        """Retrieve components based on filters."""
        components = VehicleComponent.objects.filter(vehicle=vehicle)
        if component_type:
            components = components.filter(component_type__name=component_type.capitalize())
        if component_name:
            components = components.filter(name=component_name.capitalize())
        if not components.exists():
            raise ValidationError("No matching components found.")
        return components


class VehiclePermissionReadOnlyView(VehiclePermissionBaseView):
    """View for read-only vehicle permissions."""

    @extend_schema(
        operation_id="list_vehicle_permissions",
        summary="Retrieve permissions for a vehicle",
        description="Fetch permissions grouped by users.",
        responses={
            200: OpenApiResponse(description="Permissions grouped by users"),
            403: OpenApiResponse(description="Not authorized"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Access Management']
    )
    def get(self, request, vin):
        vehicle = self.get_vehicle(vin)
        self.check_vehicle_ownership(vehicle, request.user)

        filters = {"component__vehicle": vehicle}
        permissions = ComponentPermission.objects.filter(**filters).select_related(
            'component', 'component__component_type', 'user'
        )

        grouped_permissions = {}
        for perm in permissions:
            user = perm.user.username
            grouped_permissions.setdefault(user, []).append({
                'component_type': perm.component.component_type.name,
                'component_name': perm.component.name,
                'permission_type': perm.permission_type,
                'valid_until': perm.valid_until,
            })

        return Response([
            {'user': user, 'permissions': perms}
            for user, perms in grouped_permissions.items()
        ], status=status.HTTP_200_OK)


class VehiclePermissionView(VehiclePermissionBaseView):
    @extend_schema(
        operation_id="retrieve_user_permissions",
        summary="Retrieve permissions for a vehicle",
        description="Fetch permissions grouped by users.",
        responses={
            200: OpenApiResponse(description="Permissions grouped by users"),
            403: OpenApiResponse(description="Not authorized"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Access Management']
    )
    def get(self, request, vin, username=None, component_type=None, component_name=None):
        vehicle = self.get_vehicle(vin)
        self.check_vehicle_ownership(vehicle, request.user)

        # Get base components queryset
        components = vehicle.components.select_related('component_type').all()
        if component_type:
            components = components.filter(component_type__name=component_type.capitalize())
        if component_name:
            components = components.filter(name=component_name.capitalize())

        # If it's the owner requesting
        if vehicle.owner and vehicle.owner.username == username:
            # For owners, return all matching components with full access
            permissions_list = [{
                'component_type': comp.component_type.name,
                'component_name': comp.name,
                'permission_type': 'write',  # Owner has full access
                'valid_until': None
            } for comp in components]

            if permissions_list:
                return Response([{
                    'user': username,
                    'permissions': permissions_list
                }], status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "No matching components found."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # For non-owners, get explicit permissions
        filters = {
            "component__in": components,
            "user__username": username
        }
        permissions = ComponentPermission.objects.filter(**filters).select_related(
            'component', 'component__component_type', 'user'
        )

        if not permissions:
            return Response(
                {"detail": "No permissions found for the specified criteria."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Group permissions by user
        grouped_permissions = {}
        for perm in permissions:
            user = perm.user.username
            grouped_permissions.setdefault(user, []).append({
                'component_type': perm.component.component_type.name,
                'component_name': perm.component.name,
                'permission_type': perm.permission_type,
                'valid_until': perm.valid_until,
            })

        return Response([
            {'user': user, 'permissions': perms}
            for user, perms in grouped_permissions.items()
        ], status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="grant_user_permissions",
        summary="Grant permissions for a user",
        description="Grant permissions for a user on components of a vehicle.",
        request=GrantPermissionSerializer,
        responses={
            200: PermissionResultSerializer,
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Not authorized"),
        },
        tags=['Access Management']
    )
    def post(self, request, vin, username=None, component_type=None, component_name=None):
        vehicle = self.get_vehicle(vin)
        self.check_vehicle_ownership(vehicle, request.user)

        serializer = GrantPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target_user = get_object_or_404(User, username=username)
        if target_user == vehicle.owner:
            raise ValidationError("Cannot grant permissions to the vehicle owner.")

        components = self.get_filtered_components(vehicle, component_type, component_name)

        results = {"granted": [], "failed": []}
        for component in components:
            try:
                permission, created = ComponentPermission.objects.update_or_create(
                    component=component,
                    user=target_user,
                    defaults={
                        "permission_type": data["permission_type"],
                        "valid_until": data.get("valid_until"),
                    },
                )
                results["granted"].append({
                    "component_type": component.component_type.name,
                    "component_name": component.name,
                    "status": "created" if created else "updated",
                })
            except Exception as e:
                results["failed"].append({
                    "component_type": component.component_type.name,
                    "component_name": component.name,
                    "error": str(e),
                })

        return Response(results, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Revoke permissions for a user",
        description="Revoke all or specific permissions for a user.",
        responses={
            200: RevokeResultSerializer,
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Not authorized"),
        },
        tags=['Access Management']
    )
    def delete(self, request, vin, username=None, component_type=None, component_name=None):
        vehicle = self.get_vehicle(vin)
        self.check_vehicle_ownership(vehicle, request.user)

        target_user = get_object_or_404(User, username=username)
        if target_user == vehicle.owner:
            raise ValidationError("Cannot revoke permissions from the vehicle owner.")

        components = self.get_filtered_components(vehicle, component_type, component_name)

        permissions = ComponentPermission.objects.filter(
            component__in=components,
            user=target_user
        )

        revoked = [
            {
                "component_type": perm.component.component_type.name,
                "component_name": perm.component.name,
                "permission_type": perm.permission_type,
            }
            for perm in permissions
        ]
        permissions.delete()

        return Response({
            "revoked": revoked,
            "message": f"Permissions revoked for user {username} on vehicle {vin}."
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="List vehicles accessed by the user",
        description="Retrieve a list of vehicles for which the user has permissions.",
        responses={
            200: AccessedVehicleSerializer(many=True),
        },
        tags=['Vehicle']
    )
)
class AccessedVehiclesView(generics.ListAPIView):
    serializer_class = AccessedVehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(
            components__access_permissions__user=self.request.user
        ).distinct().select_related('owner')
