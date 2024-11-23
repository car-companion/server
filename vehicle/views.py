from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from guardian.shortcuts import assign_perm, remove_perm

from .models.vehicle import Vehicle
from .serializers import VehicleSerializer, VehicleRequestSerializer

User = get_user_model()


@extend_schema(
    methods=['POST'],
    request=VehicleRequestSerializer,
    responses={
        '200': OpenApiResponse(
            response=inline_serializer('TakeOwnershipOk', fields={'message': serializers.CharField(default='Ok')}),
            description='Ownership successfully taken.',
        ),
        '204': OpenApiResponse(
            response=inline_serializer('TakeOwnershipNop', fields={}),
            description='User is already owner of the vehicle.',
        ),
        '400': OpenApiResponse(
            response=inline_serializer('TakeOwnershipInvalidVin', fields={'message': serializers.CharField(default='VIN not specified')}),
            description='VIN not specified in request.',
        ),
        '403': OpenApiResponse(
            response=inline_serializer('TakeOwnershipHasOwner', fields={'message': serializers.CharField(default='Vehicle already has an owner')}),
            description='Vehicle already has an owner.',
        ),
        '404': OpenApiResponse(
            response=inline_serializer('TakeOwnershipNotFound', fields={'message': serializers.CharField(default='Vehicle with given VIN does not exist')}),
            description='Invalid VIN provided in request.',
        ),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def take_ownership(request):
    """ Handle taking ownership of a vehicle. """
    
    if 'vin' not in request.data:
        return Response({'message': 'VIN not specified!'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        vehicle = Vehicle.objects.get(vin=request.data['vin'])
    except Vehicle.DoesNotExist:
        return Response({'message': 'Vehicle with given VIN does not exist'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user

    if vehicle.owner is not None:
        if vehicle.owner == user:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Vehicle already has an owner'}, status=status.HTTP_403_FORBIDDEN)

    vehicle.owner = user
    assign_perm('is_owner', user, vehicle)

    vehicle.save()
    return Response({'message': 'ok'}, status=status.HTTP_200_OK)


@extend_schema(
    methods=['POST'],
    request=VehicleRequestSerializer,
    responses={
        '204': OpenApiResponse(
            response=inline_serializer('DisownOk', fields={}),
            description='Vehicle sucessfully disowned.',
        ),
        '400': OpenApiResponse(
            response=inline_serializer('DisownInvalidVin', fields={'message': serializers.CharField(default='VIN not specified')}),
            description='VIN not specified in request.',
        ),
        '403': OpenApiResponse(
            response=inline_serializer('DisownNotOwner', fields={'message': serializers.CharField(default='You are not the owner')}),
            description='User is not owner of the vehicle.',
        ),
        '404': OpenApiResponse(
            response=inline_serializer('DisownNotFound', fields={'message': serializers.CharField(default='Vehicle with given VIN does not exist')}),
            description='Invalid VIN provided in request.',
        ),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disown(request):
    """ Handle disowning a vehicle. """

    if 'vin' not in request.data:
        return Response({'message': 'VIN not specified!'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        vehicle = Vehicle.objects.get(vin=request.data['vin'])
    except Vehicle.DoesNotExist:
        return Response({'message': 'Vehicle with given VIN does not exist'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user

    if vehicle.owner != user:
        return Response({'message': 'You are not an owner of this vehicle'}, status=status.HTTP_403_FORBIDDEN)

    vehicle.owner = None
    remove_perm('is_owner', user, vehicle)

    vehicle.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    methods=['GET'],
    request=None,
    responses={
        '200': VehicleSerializer,
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_vehicles(request):
    """ Get all vehicles owned by the current user """
    vehicles = Vehicle.objects.filter(owner=request.user)
    ser = VehicleSerializer(vehicles, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)
