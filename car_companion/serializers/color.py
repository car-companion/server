from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from car_companion.models import Color

class ColorSerializer(serializers.ModelSerializer):
    """Serializer for reading color information."""
    class Meta:
        model = Color
        fields = ['name', 'hex_code', 'is_metallic', 'description']


class ColorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new colors."""
    class Meta:
        model = Color
        fields = ['name', 'hex_code', 'is_metallic', 'description']

    def validate_hex_code(self, value):
        """Validate hex code format."""
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError(
                _('Invalid hex color code. Use format: #RRGGBB')
            )
        return value.upper()

    def validate_name(self, value):
        """Validate color name for uniqueness and formatting."""
        # Strip and capitalize name
        value = value.strip().capitalize()

        # Check for uniqueness (case-insensitive)
        if Color.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(
                _('Color name already exists.')
            )
        if len(value) < 2:
            raise serializers.ValidationError(
                _('Color name must be at least 2 characters long.')
            )
        return value
