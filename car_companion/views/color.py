from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from car_companion.models import Color
from car_companion.serializers.color import ColorSerializer, ColorCreateSerializer


class ColorListCreateView(generics.ListCreateAPIView):
    """View for listing and creating colors."""
    permission_classes = [IsAuthenticated]
    queryset = Color.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ColorCreateSerializer
        return ColorSerializer

    @extend_schema(
        summary="List colors",
        description="Get a list of all available colors",
        responses={200: ColorSerializer(many=True)},
        tags=['Colors']
    )
    def get(self, request, *args, **kwargs):
        """List all available colors."""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create color",
        description="Create a new color",
        request=ColorCreateSerializer,
        responses={
            201: ColorSerializer,
            400: OpenApiResponse(description="Invalid color data"),
        },
        tags=['Colors']
    )
    def post(self, request, *args, **kwargs):
        """Create a new color."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            ColorSerializer(instance=serializer.instance).data,
            status=status.HTTP_201_CREATED
        )
