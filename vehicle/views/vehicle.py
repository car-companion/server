import re

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from vehicle.models.vehicle import Vehicle
from vehicle.serializers.vehicle import VehicleSerializer, NicknameSerializer


class VehicleViewSet(ViewSet):
    """
    ViewSet for managing vehicle ownership and details.

    This ViewSet provides endpoints for:
    - Taking ownership of vehicles
    - Disowning vehicles
    - Listing owned vehicles
    - Managing vehicle nicknames

    All actions require authentication.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    lookup_field = "vin"

    def get_vehicle(self, vin: str, user, require_owner: bool = True) -> Vehicle:
        """
        Get a vehicle by VIN and optionally verify ownership.

        Args:
            vin: Vehicle Identification Number
            user: User making the request
            require_owner: If True, raises PermissionDenied if user is not the owner

        Returns:
            Vehicle: The requested vehicle instance

        Raises:
            Http404: If vehicle not found
            PermissionDenied: If require_owner is True and user is not the owner
        """
        vehicle = get_object_or_404(self.queryset, vin=vin)
        if require_owner and vehicle.owner != user:
            raise PermissionDenied("You are not the owner of this vehicle")
        return vehicle

    def vin_is_valid(self, vin: str) -> bool:
        """
        Checks in the VIN provided is in valid format

        Args:
            vin: Vehicle Identification Number

        Returns:
            Bool: Whether VIN is valid
        """
        return re.match(Vehicle.VIN_PATTERN, vin.upper()) is not None
        
    @extend_schema(
        request=None,
        summary="Take ownership of a vehicle",
        description="Claim ownership of an unowned vehicle",
        responses={
            200: VehicleSerializer,
            208: OpenApiResponse(description="Already the owner"),
            400: OpenApiResponse(description="VIN is invalid"),
            403: OpenApiResponse(description="Vehicle has another owner"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Vehicle']
    )
    @action(detail=True, methods=["post"])
    def take_ownership(self, request: Request, vin: str) -> Response:
        """
        Take ownership of an unowned vehicle.

        If successful, assigns ownership and 'is_owner' permission to the user.
        """
        if not(re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin.upper())):
            return Response(
                {"detail": "VIN is invalid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        vehicle = get_object_or_404(self.queryset, vin=vin)

        if vehicle.owner:
            if vehicle.owner == request.user:
                return Response(
                    {"detail": "You already own this vehicle"},
                    status=status.HTTP_208_ALREADY_REPORTED
                )
            return Response(
                {"detail": "Vehicle already has an owner"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Assign ownership and permissions
        vehicle.owner = request.user
        vehicle.save()
        assign_perm("is_owner", request.user, vehicle)

        return Response(
            self.serializer_class(vehicle).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Disown a vehicle",
        description="Release ownership of a vehicle you own",
        responses={
            204: OpenApiResponse(description="Successfully disowned"),
            400: OpenApiResponse(description="VIN is invalid"),
            403: OpenApiResponse(description="Not the owner"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Vehicle']
    )
    @action(detail=True, methods=["delete"])
    def disown(self, request: Request, vin: str) -> Response:
        """
        Release ownership of a vehicle.

        Removes both ownership and 'is_owner' permission from the user.
        """
        if not(re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin.upper())):
            return Response(
                {"detail": "VIN is invalid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        vehicle = self.get_vehicle(vin, request.user)

        # Remove ownership and permissions
        vehicle.owner = None
        vehicle.save()
        remove_perm("is_owner", request.user, vehicle)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="List owned vehicles",
        description="Get a list of all vehicles owned by the current user",
        responses={200: VehicleSerializer(many=True)},
        tags=['Vehicle']
    )
    @action(detail=False, methods=["get"])
    def my_vehicles(self, request: Request) -> Response:
        """List all vehicles owned by the current user."""
        vehicles = self.queryset.filter(owner=request.user)
        return Response(
            self.serializer_class(vehicles, many=True).data
        )

    @extend_schema(
        summary="Update vehicle nickname",
        description="Set a new nickname for a vehicle you own",
        request=NicknameSerializer,
        responses={
            200: VehicleSerializer,
            400: OpenApiResponse(description="Invalid nickname"),
            403: OpenApiResponse(description="Not the owner"),
            404: OpenApiResponse(description="Vehicle not found"),
        },
        tags=['Vehicle']
    )
    @action(detail=True, methods=["put"])
    def nickname(self, request: Request, vin: str) -> Response:
        """
        Update the nickname of a vehicle.

        Requires vehicle ownership. Nickname must pass model validation.
        """
        vehicle = self.get_vehicle(vin, request.user)

        serializer = NicknameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update and save nickname
        vehicle.nickname = serializer.validated_data['nickname']
        vehicle.save()

        return Response(
            self.serializer_class(vehicle).data,
            status=status.HTTP_200_OK
        )
