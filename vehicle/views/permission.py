from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from vehicle.models import ComponentPermission, VehicleComponent, Vehicle
from vehicle.serializers.permission import (
    AccessRequestSerializer,
    PermissionResultSerializer,
    AccessedVehicleSerializer
)

User = get_user_model()


class VehiclePermissionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AccessRequestSerializer

    def _check_vehicle_ownership(self, vehicle, user):
        if vehicle.owner != user:
            raise PermissionDenied("Not authorized")

    def _get_vehicle(self, vin):
        return get_object_or_404(
            Vehicle.objects.select_related('owner'),
            vin=vin
        )

    @extend_schema(
        summary="Retrieve permissions for a vehicle",
        description="Fetch permissions for vehicle components, including owner and shared access.",
        request=None,
        responses={
            200: OpenApiResponse(description="List of permissions"),
            403: OpenApiResponse(description="Not authorized"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Access Management']
    )
    @action(detail=False, methods=["get"])
    def get(self, request, vin):
        vehicle = self._get_vehicle(vin)
        self._check_vehicle_ownership(vehicle, request.user)

        components = (VehicleComponent.objects
                      .filter(vehicle=vehicle)
                      .select_related('component_type'))

        permissions = (ComponentPermission.objects
        .filter(component__vehicle=vehicle)
        .select_related(
            'component',
            'component__component_type',
            'user'
        ))

        return Response({
            'owner_access': [
                {
                    'component_type': comp.component_type.name,
                    'component_name': comp.name,
                    'permission_type': ComponentPermission.PermissionType.WRITE
                }
                for comp in components
            ],
            'shared_access': [
                {
                    'component_type': perm.component.component_type.name,
                    'component_name': perm.component.name,
                    'user': perm.user.username,
                    'permission_type': perm.permission_type,
                    'valid_until': perm.valid_until
                }
                for perm in permissions
            ]
        })

    @extend_schema(
        summary="Grant permissions for vehicle components",
        description="Grant specific permissions for vehicle components to another user.",
        request=AccessRequestSerializer,
        responses={
            200: PermissionResultSerializer,
            400: OpenApiResponse(description="Invalid request data"),
            403: OpenApiResponse(description="Not authorized"),
            404: OpenApiResponse(description="Vehicle or user not found"),
        },
        tags=['Access Management']
    )
    @action(detail=True, methods=["post"])
    def post(self, request, vin):
        vehicle = self._get_vehicle(vin)
        self._check_vehicle_ownership(vehicle, request.user)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target_user = get_object_or_404(User, username=data['username'])
        if target_user == vehicle.owner:
            raise ValidationError("Cannot grant access to vehicle owner")

        results = {"granted": [], "failed": []}

        for comp_data in data['components']:
            self._process_component_permission(
                vehicle, target_user, comp_data, results, request.user
            )

        return Response(results)

    def _process_component_permission(self, vehicle, target_user, comp_data, results, granting_user):
        components = self._get_components_query(vehicle, comp_data)

        for component in components:
            try:
                permission, created = self._update_or_create_permission(
                    component, target_user, comp_data, granting_user
                )
                results["granted"].append({
                    'component_type': component.component_type.name,
                    'component_name': component.name,
                    'status': 'created' if created else 'updated'
                })
            except Exception as e:
                results["failed"].append({
                    'component_type': component.component_type.name,
                    'component_name': component.name,
                    'error': str(e)
                })

    def _get_components_query(self, vehicle, comp_data):
        query = VehicleComponent.objects.filter(vehicle=vehicle)

        # If component_type is provided, filter by it
        if comp_data.get('component_type'):
            query = query.filter(component_type__name=comp_data['component_type'])

        # If component_name is provided, filter by it
        if comp_data.get('component_name'):
            query = query.filter(name=comp_data['component_name'])

        return query

    @action(detail=True, methods=["post"])
    def _update_or_create_permission(self, component, target_user, comp_data, granting_user):
        return ComponentPermission.objects.update_or_create(
            component=component,
            user=target_user,
            defaults={
                'permission_type': comp_data['permission_type'],
                'granted_by': granting_user,
                'valid_until': comp_data.get('valid_until')
            }
        )


@extend_schema(
    summary="List vehicles accessed by the user",
    description="Retrieve a list of vehicles for which the authenticated user has access permissions.",
    request=None,
    responses={
        200: AccessedVehicleSerializer(many=True),
    },
    tags=['Access Management']
)
@action(detail=False, methods=["get"])
class AccessedVehiclesView(generics.ListAPIView):
    serializer_class = AccessedVehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (Vehicle.objects
                .filter(components__access_permissions__user=self.request.user)
                .distinct()
                .select_related('owner'))
