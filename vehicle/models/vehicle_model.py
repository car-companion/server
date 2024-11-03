import re
from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from .manufacturer import Manufacturer


class VehicleModel(models.Model):
    """
    Model representing a specific vehicle model belonging to a manufacturer.
    """
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('The name of the vehicle model'),
        error_messages={
            'blank': _('Model name cannot be blank.'),
        }
    )

    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        related_name='models',
        help_text=_("Manufacturer this model belongs to"),
        error_messages={
            'null': _('Manufacturer is required.'),
        }
    )

    class Meta:
        ordering = ['manufacturer__name', 'name']
        verbose_name = _('Vehicle Model')
        verbose_name_plural = _('Vehicle Models')
        unique_together = ['name', 'manufacturer']
        db_table = 'vehicle_models'
        indexes = [
            models.Index(fields=['name'], name='vehicle_model_name_idx'),
            models.Index(fields=['manufacturer'], name='vehicle_model_manufacturer_idx'),
        ]

    def clean(self):
        """
        Custom validation for the VehicleModel.
        Ensures that the name is properly formatted and standardized.
        """
        if self.name is None:
            raise ValidationError(_('Model name cannot be null.'))
        elif not self.name.strip():
            raise ValidationError(_('Model name cannot be blank.'))

        # Standardize the name format
        self.name = re.sub(r'\s+', ' ', self.name.strip()).upper()

        # Check for minimum length after stripping
        if len(self.name) < 1:
            raise ValidationError(_('Model name must be at least 1 character long.'))

        # Validate against common special characters
        if re.search(r'[!@#$%^&*()+=\[\]{};\':"\\|,.<>/?]', self.name):
            raise ValidationError(_('Model name contains invalid special characters.'))

        # Validate manufacturer is set
        if not self.manufacturer_id:
            raise ValidationError(_('Manufacturer is required.'))

    def save(self, *args: Any, **kwargs: Any):
        """
        Custom save method with additional validation.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.manufacturer.name} {self.name}"
