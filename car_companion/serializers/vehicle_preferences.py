from rest_framework import serializers
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from car_companion.models import VehicleUserPreferences, Color, Vehicle
from car_companion.serializers.vehicle import VehicleModelSerializer


class ColorSerializer(serializers.ModelSerializer):
    """Serializer for color details."""

    class Meta:
        model = Color
        fields = ['name', 'hex_code', 'is_metallic']


class PreferencesSerializer(serializers.ModelSerializer):
    """Serializer for reading preferences."""
    interior_color = ColorSerializer()  # This will now serialize the full color object
    exterior_color = ColorSerializer()  # This will now serialize the full color object

    class Meta:
        model = VehicleUserPreferences
        fields = ['nickname', 'interior_color', 'exterior_color']


class ColorFieldWithCreation(serializers.Serializer):
    """Custom field for handling color with optional creation."""
    name = serializers.CharField(
        max_length=50,
        help_text=_("Name of the color")
    )
    is_metallic = serializers.BooleanField(
        default=False,
        help_text=_("Whether the color has a metallic finish")
    )
    hex_code = serializers.CharField(
        max_length=7,
        help_text=_("Color in hexadecimal format (#RRGGBB)")
    )

    def validate_hex_code(self, value):
        """Validate hex code format."""
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError(
                _('Invalid hex color code. Use format: #RRGGBB')
            )
        return value.upper()

    def validate_name(self, value):
        """Validate and format color name."""
        return value.strip().capitalize()

    def get_or_create_color(self, validated_data):
        """Get existing color or create new one."""
        name = validated_data['name']
        hex_code = validated_data['hex_code']
        is_metallic = validated_data.get('is_metallic', False)

        try:
            color = Color.objects.get(name__iexact=name)
            if color.hex_code != hex_code or color.is_metallic != is_metallic:
                color.hex_code = hex_code
                color.is_metallic = is_metallic
                color.save()
            return color
        except Color.DoesNotExist:
            return Color.objects.create(
                name=name,
                hex_code=hex_code,
                is_metallic=is_metallic
            )


class PreferencesUpdateSerializer(serializers.Serializer):
    """Serializer for updating preferences."""
    nickname = serializers.CharField(
        min_length=2,
        max_length=100,
        required=False,
        allow_null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-]*$',
                message=_('Nickname can only contain letters, numbers, spaces, and hyphens.')
            )
        ]
    )
    interior_color = ColorFieldWithCreation(required=False, allow_null=True)
    exterior_color = ColorFieldWithCreation(required=False, allow_null=True)

    def validate(self, attrs):
        if not any(attrs.values()):
            raise serializers.ValidationError(
                _("At least one preference must be provided.")
            )
        return attrs


class VehiclePreferencesSerializer(serializers.ModelSerializer):
    """Serializer for vehicle details with preferences."""
    model = VehicleModelSerializer()
    default_interior_color = ColorSerializer(source='interior_color')
    default_exterior_color = ColorSerializer(source='outer_color')
    user_preferences = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'vin',
            'model',
            'year_built',
            'default_interior_color',
            'default_exterior_color',
            'user_preferences'
        ]

    def get_user_preferences(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        try:
            prefs = obj.user_preferences.get(user=request.user)
            return PreferencesSerializer(prefs).data  # This will now include full color details
        except VehicleUserPreferences.DoesNotExist:
            return None