from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from car_companion.models import Vehicle, VehicleUserPreferences
from car_companion.serializers.vehicle_preferences import (
    PreferencesSerializer,
    PreferencesUpdateSerializer,
    VehiclePreferencesSerializer, ColorFieldWithCreation
)


class PreferencesBaseView(APIView):
    """Base view for preferences operations."""
    permission_classes = [IsAuthenticated]

    def get_vehicle(self, vin: str):
        return get_object_or_404(Vehicle, vin=vin)

    def check_access(self, vehicle, user):
        """Check if user has access to the vehicle."""
        return (
                vehicle.owner == user or
                vehicle.components.filter(
                    access_permissions__user=user
                ).exists()
        )


class VehiclePreferencesView(PreferencesBaseView):
    """View for managing vehicle preferences."""

    @extend_schema(
        summary="Get vehicle preferences",
        description="Get user's preferences for a specific vehicle",
        responses={
            200: VehiclePreferencesSerializer,
            403: OpenApiResponse(description="No access to vehicle"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Vehicle Preferences']
    )
    def get(self, request, vin):
        """Get user preferences for a vehicle."""
        vehicle = self.get_vehicle(vin)

        if not self.check_access(vehicle, request.user):
            return Response(
                {"detail": "You don't have access to this vehicle"},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            VehiclePreferencesSerializer(
                vehicle,
                context={'request': request}
            ).data
        )

    @extend_schema(
        summary="Update preferences",
        description="Update or create user preferences for a vehicle",
        request=PreferencesUpdateSerializer,
        responses={
            200: PreferencesSerializer,
            400: OpenApiResponse(description="Invalid preferences data"),
            403: OpenApiResponse(description="No access to vehicle"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Vehicle Preferences']
    )
    # car_companion/views/vehicle_preferences.py

    @extend_schema(
        summary="Update preferences",
        description="Update or create user preferences for a vehicle",
        request=PreferencesUpdateSerializer,
        responses={
            200: PreferencesSerializer,
            400: OpenApiResponse(description="Invalid preferences data"),
            403: OpenApiResponse(description="No access to vehicle"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Vehicle Preferences']
    )
    def put(self, request, vin):
        """Update preferences for a vehicle."""
        vehicle = self.get_vehicle(vin)

        if not self.check_access(vehicle, request.user):
            return Response(
                {"detail": "You don't have access to this vehicle"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PreferencesUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process colors if provided
        interior_color_data = serializer.validated_data.pop('interior_color', None)
        exterior_color_data = serializer.validated_data.pop('exterior_color', None)

        defaults = {}

        # Handle interior color
        if interior_color_data is not None:
            interior_color = ColorFieldWithCreation().get_or_create_color(
                interior_color_data) if interior_color_data else None
            defaults['interior_color'] = interior_color

        # Handle exterior color
        if exterior_color_data is not None:
            exterior_color = ColorFieldWithCreation().get_or_create_color(
                exterior_color_data) if exterior_color_data else None
            defaults['exterior_color'] = exterior_color

        # Add remaining data to defaults
        defaults.update(serializer.validated_data)

        # Update or create preferences
        prefs, _ = VehicleUserPreferences.objects.update_or_create(
            vehicle=vehicle,
            user=request.user,
            defaults=defaults
        )

        return Response(
            PreferencesSerializer(prefs).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Delete preferences",
        description="Remove user preferences for a vehicle",
        responses={
            204: OpenApiResponse(description="Preferences deleted successfully"),
            403: OpenApiResponse(description="No access to vehicle"),
            404: OpenApiResponse(description="Vehicle or preferences not found"),
        },
        tags=['Vehicle Preferences']
    )
    def delete(self, request, vin):
        """Remove preferences for a vehicle."""
        vehicle = self.get_vehicle(vin)

        if not self.check_access(vehicle, request.user):
            return Response(
                {"detail": "You don't have access to this vehicle"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            prefs = VehicleUserPreferences.objects.get(
                vehicle=vehicle,
                user=request.user
            )
            prefs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except VehicleUserPreferences.DoesNotExist:
            return Response(
                {"detail": "No preferences found"},
                status=status.HTTP_404_NOT_FOUND
            )