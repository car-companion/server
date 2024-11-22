from django.core.validators import MinLengthValidator, MaxLengthValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import status, serializers


class VinSerializer(serializers.Serializer):
    VIN_PATTERN = r'^[A-HJ-NPR-Z0-9]{17}$'

    vin = serializers.CharField(
        validators=[
            MinLengthValidator(17),
            MaxLengthValidator(17),
            RegexValidator(
                regex=VIN_PATTERN,
                message=_("Enter a valid 17-character VIN. Letters I, O, and Q are not allowed.")
            )
        ],
    )