from django.db import models
from django.core.validators import (
    MinLengthValidator,
    MaxLengthValidator,
    MinValueValidator,
    MaxValueValidator,
    RegexValidator
)
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
            'invalid': _("Enter a valid VIN.")
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
    )

    model = models.ForeignKey(
        VehicleModel,
        verbose_name=_("Model"),
        on_delete=models.PROTECT,
        related_name='vehicles',
        help_text=_("Vehicle model")
    )

    outer_color = models.ForeignKey(
        Color,
        verbose_name=_("Exterior Color"),
        on_delete=models.PROTECT,
        related_name='vehicle_outer_color',
        help_text=_("Vehicle exterior color")
    )

    interior_color = models.ForeignKey(
        Color,
        verbose_name=_("Interior Color"),
        on_delete=models.PROTECT,
        related_name='vehicle_interior_color',
        help_text=_("Vehicle interior color")
    )

    nickname = models.CharField(
        _("Nickname"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Optional nickname for the vehicle")
    )

    class Meta:
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        db_table = 'vehicles'
        ordering = ['-year_built', 'model']
        indexes = [
            models.Index(fields=['year_built'], name='vehicle_year_idx'),
            models.Index(fields=['model'], name='vehicle_model_idx'),
        ]

    def __str__(self):
        """
        Returns a string representation of the vehicle.
        Format: YYYY Manufacturer Model (VIN)
        """
        return f"{self.year_built} {self.model.manufacturer} {self.model} ({self.vin})"

    def clean(self) -> None:
        """
        Perform model-wide validation.
        """
        from django.core.exceptions import ValidationError

        # Ensure year_built is not greater than the current year + 1
        if self.year_built and self.year_built > get_max_year():
            raise ValidationError({
                'year_built': _("Year cannot be in the future.")
            })

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Custom save method with additional validation.
        """
        self.clean()
        # Convert VIN to uppercase
        if self.vin:
            self.vin = self.vin.upper()
        super().save(*args, **kwargs)

    @property
    def manufacturer(self):
        """
        Get the manufacturer through the model relationship.
        """
        return self.model.manufacturer
