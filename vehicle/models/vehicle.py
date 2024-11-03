from django.db import models
from django.core.validators import (
    MinLengthValidator,
    MaxLengthValidator,
    MinValueValidator,
    MaxValueValidator,
    RegexValidator
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import Any
from .color import Color
from .vehicle_model import VehicleModel


def get_max_year():
    """Returns the maximum allowed year (current year + 1)"""
    return timezone.now().year + 1


class Vehicle(models.Model):
    """
    Model representing a vehicle in the system.

    This model stores core information about vehicles including their
    identification, manufacturing details, and appearance characteristics.
    """

    # VIN validation pattern
    VIN_PATTERN = r'^[A-HJ-NPR-Z0-9]{17}$'

    # First model year (Karl Benz's first automobile)
    FIRST_MODEL_YEAR = 1886

    vin = models.CharField(
        _("VIN"),
        primary_key=True,
        max_length=17,
        validators=[
            MinLengthValidator(17),
            MaxLengthValidator(17),
            RegexValidator(
                regex=VIN_PATTERN,
                message=_("Enter a valid 17-character VIN. Letters I, O, and Q are not allowed.")
            )
        ],
        help_text=_("17-character Vehicle Identification Number"),
        error_messages={
            'unique': _("A vehicle with this VIN already exists."),
            'invalid': _("Enter a valid VIN."),
            'blank': _("VIN cannot be blank."),
            'null': _("VIN is required."),
            'max_length': _("VIN must be exactly 17 characters."),
            'min_length': _("VIN must be exactly 17 characters.")
        }
    )

    year_built = models.IntegerField(
        _("Year Built"),
        validators=[
            MinValueValidator(
                FIRST_MODEL_YEAR,
                message=_(f"Year must be {FIRST_MODEL_YEAR} or later.")
            ),
            MaxValueValidator(
                get_max_year,
                message=_("Year cannot be in the future.")
            )
        ],
        help_text=_("Year the vehicle was manufactured"),
        error_messages={
            'null': _("Year built is required."),
            'invalid': _("Enter a valid year.")
        }
    )

    model = models.ForeignKey(
        VehicleModel,
        verbose_name=_("Model"),
        on_delete=models.PROTECT,
        related_name='vehicles',
        help_text=_("Vehicle model"),
        error_messages={
            'null': _("Vehicle model is required."),
            'invalid': _("Select a valid vehicle model.")
        }
    )

    outer_color = models.ForeignKey(
        Color,
        verbose_name=_("Exterior Color"),
        on_delete=models.PROTECT,
        related_name='vehicle_outer_color',
        help_text=_("Vehicle exterior color"),
        error_messages={
            'null': _("Exterior color is required."),
            'invalid': _("Select a valid exterior color.")
        }
    )

    interior_color = models.ForeignKey(
        Color,
        verbose_name=_("Interior Color"),
        on_delete=models.PROTECT,
        related_name='vehicle_interior_color',
        help_text=_("Vehicle interior color"),
        error_messages={
            'null': _("Interior color is required."),
            'invalid': _("Select a valid interior color.")
        }
    )

    nickname = models.CharField(
        _("Nickname"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Optional nickname for the vehicle"),
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-]*$',
                message=_("Nickname can only contain letters, numbers, spaces, and hyphens.")
            )
        ],
        error_messages={
            'max_length': _("Nickname cannot be longer than 100 characters.")
        }
    )

    class Meta:
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        db_table = 'vehicles'
        ordering = ['-year_built', 'model']
        indexes = [
            models.Index(fields=['year_built'], name='vehicle_year_idx'),
            models.Index(fields=['model'], name='vehicle_model_idx'),
            models.Index(fields=['outer_color'], name='vehicle_outer_color_idx'),
            models.Index(fields=['interior_color'], name='vehicle_interior_color_idx'),
        ]

    def clean(self) -> None:
        """
        Perform model-wide validation.
        Validates:
        - Year built is valid
        - VIN format is correct
        - Colors are different (optional)
        - Nickname format is valid
        - Required relationships exist
        """
        errors = {}

        # Validate year_built
        if self.year_built:
            if self.year_built > get_max_year():
                errors['year_built'] = _("Year cannot be in the future.")
            elif self.year_built < self.FIRST_MODEL_YEAR:
                errors['year_built'] = _(f"Year must be {self.FIRST_MODEL_YEAR} or later.")

        # Validate VIN format and standardization
        if self.vin:
            # Convert to uppercase for validation
            self.vin = self.vin.upper()
            # Check for invalid characters (I, O, Q)
            if any(c in self.vin for c in 'IOQ'):
                errors['vin'] = _("VIN cannot contain letters I, O, or Q.")
        else:
            errors['vin'] = _("VIN is required.")

        # Optional: Validate that interior and exterior colors are different
        if self.interior_color and self.outer_color and self.interior_color == self.outer_color:
            errors['interior_color'] = _("Interior and exterior colors should be different.")

        # Validate nickname format if provided
        if self.nickname:
            self.nickname = self.nickname.strip()
            if 2 > len(self.nickname) > 0:
                errors['nickname'] = _("Nickname must be at least 2 characters long if provided.")

            # Check for special characters not caught by the validator
            if not self.nickname.replace(' ', '').replace('-', '').isalnum():
                errors['nickname'] = _("Nickname can only contain letters, numbers, spaces, and hyphens.")

        # Validate required relationships
        if not self.model_id:
            errors['model'] = _("Vehicle model is required.")
        if not self.outer_color_id:
            errors['outer_color'] = _("Exterior color is required.")
        if not self.interior_color_id:
            errors['interior_color'] = _("Interior color is required.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Custom save method with additional validation.
        - Performs full model validation
        - Standardizes VIN format
        - Standardizes nickname format
        """
        # Standardize VIN
        if self.vin:
            self.vin = self.vin.upper()

        # Standardize nickname
        if self.nickname:
            self.nickname = self.nickname.strip()
            # Convert multiple spaces to single space
            self.nickname = ' '.join(self.nickname.split())

        # Perform full validation
        self.clean()

        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns a string representation of the vehicle.
        Format: YYYY Manufacturer Model (VIN)
        If nickname is set, append it: YYYY Manufacturer Model "Nickname" (VIN)
        """
        base = f"{self.year_built} {self.model.manufacturer} {self.model}"
        if self.nickname:
            return f'{base} "{self.nickname}" ({self.vin})'
        return f"{base} ({self.vin})"

    @property
    def manufacturer(self):
        """
        Get the manufacturer through the model relationship.
        """
        return self.model.manufacturer
