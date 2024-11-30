import re
from django.db import models
from django.contrib.auth import get_user_model
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
from model_utils.models import TimeStampedModel
from typing import Any
from .color import Color
from .vehicle_model import VehicleModel

User = get_user_model()


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
                get_max_year(),  # DRF-Spectacular doesn't like functions here so we will just call it now
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

    owner = models.ForeignKey(
        User,
        verbose_name=_("Owner"),
        on_delete=models.SET_NULL,
        related_name='vehicle_owner',
        help_text=_("Owner of the vehicle"),
        blank=True,
        null=True,
        error_messages={
            'invalid': _("Select a valid vehicle model."),
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
        permissions = (
            ('is_owner', 'Can control everything'),
        )

    def clean(self) -> None:
        """
        Perform model-wide validation.
        Validates:
        - Year built is valid
        - VIN format is correct
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
        If owner is set, append it: YYYY Manufacturer Model "Nickname" (VIN) [Owned by: "Username"]
        """
        base = f"{self.year_built} {self.model.manufacturer} {self.model}"
        if self.nickname:
            base += f' "{self.nickname}"'
        base += f' {self.vin}'
        if self.owner:
            base += f' [Owned by: {self.owner.username}]'
        return base

    @property
    def manufacturer(self):
        """
        Get the manufacturer through the model relationship.
        """
        return self.model.manufacturer


class VehicleComponent(TimeStampedModel):
    """
    Represents a specific component instance in a vehicle with its status.
    """
    from .component_type import ComponentType
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Name of the component'),
        error_messages={
            'blank': _('Component name cannot be blank.'),
        }
    )

    component_type = models.ForeignKey(
        ComponentType,
        on_delete=models.PROTECT,
        related_name='vehicle_components',
        verbose_name=_('component type'),
        help_text=_('Type of this component'),
        error_messages={
            'null': _('Component type is required.'),
        }
    )

    vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name=_('vehicle'),
        help_text=_('Vehicle this component belongs to'),
        error_messages={
            'null': _('Vehicle is required.'),
        }
    )

    status = models.FloatField(
        _('status'),
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0.0, _('Status cannot be less than 0')),
            MaxValueValidator(1.0, _('Status cannot be greater than 1'))
        ],
        default=0.0,
        help_text=_('Current status of the component (0.0-1.0)')
    )

    class Meta:
        ordering = ['vehicle', 'component_type__name']
        verbose_name = _('Vehicle Component')
        verbose_name_plural = _('Vehicle Components')
        unique_together = ['vehicle', 'component_type', 'name']
        db_table = 'vehicle_components'
        indexes = [
            models.Index(fields=['name'], name='vehicle_component_name_idx'),
            models.Index(fields=['component_type'], name='vehicle_component_type_idx'),
            models.Index(fields=['vehicle'], name='vehicle_component_vehicle_idx'),
            models.Index(fields=['status'], name='vehicle_component_status_idx'),
        ]
        permissions = [
            ('view_status', 'Can view component status'),
            ('change_status', 'Can change component status'),
        ]

    def clean(self):
        """
        Custom validation for the VehicleComponent model.
        """
        if self.name is None:
            raise ValidationError(_('Component name cannot be null.'))
        elif not self.name.strip():
            raise ValidationError(_('Component name cannot be blank.'))

        # Standardize the name format
        self.name = re.sub(r'\s+', ' ', self.name.strip()).capitalize()

        # Check for minimum length after stripping
        if len(self.name) < 2:
            raise ValidationError(_('Component name must be at least 2 characters long.'))

        # Validate against common special characters
        if re.search(r'[!@#$%^&*()+=\[\]{};\':"\\|,.<>/?]', self.name):
            raise ValidationError(_('Component name contains invalid special characters.'))

        # Validate required relationships
        if not self.component_type_id:
            raise ValidationError(_('Component type is required.'))
        if not self.vehicle_id:
            raise ValidationError(_('Vehicle is required.'))

        # Validate status range if provided
        if self.status is not None:
            if self.status < 0.0 or self.status > 1.0:
                raise ValidationError(_('Status must be between 0.0 and 1.0.'))
        else:
            self.status = 0.0

    def save(self, *args: Any, **kwargs: Any):
        """
        Custom save method with additional validation.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.component_type} - {self.vehicle}"
