from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from guardian.shortcuts import assign_perm, remove_perm

from .models.vehicle import Vehicle
from .serializers import VinSerializer

User = get_user_model()


@extend_schema(
    methods=['POST'],
    request=VinSerializer,
    responses={
        '200': inline_serializer('take_ownership_200', fields={}),
        '204': inline_serializer('take_ownership_204', fields={'message': serializers.CharField()}),
        '400': inline_serializer('take_ownership_400', fields={'message': serializers.CharField()}),
        '403': inline_serializer('take_ownership_403', fields={'message': serializers.CharField()}),
        '404': inline_serializer('take_ownership_404', fields={'message': serializers.CharField()}),
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
            return Response({'message': 'You already own this vehicle'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Vehicle already has an owner'}, status=status.HTTP_403_FORBIDDEN)

    vehicle.owner = user
    assign_perm('is_owner', user, vehicle)

    vehicle.save()
    return Response({'msg': 'takeown'}, status=status.HTTP_200_OK)


@extend_schema(
    methods=['POST'],
    request=VinSerializer,
    responses={
        '204': inline_serializer('disown_204', fields={}),
        '400': inline_serializer('disown_400', fields={'message': serializers.CharField()}),
        '403': inline_serializer('disown_403', fields={'message': serializers.CharField()}),
        '404': inline_serializer('disown_404', fields={'message': serializers.CharField()}),
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
    methods=['POST'],
    request=None,
    responses={
        '200': inline_serializer('my_vehicles_200', fields={'vins': serializers.ListSerializer(child=serializers.CharField())}),
})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def my_vehicles(request):
    """ Get all vehicles owned by the current user """
    user = request.user
    vehicles = Vehicle.objects.filter(owner=user).values_list('vin', flat=True)
    return Response({'vins': vehicles}, status=status.HTTP_200_OK)
