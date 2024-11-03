import re
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel


class ComponentType(models.Model):
    """
    Reference table for types of components that can be added to vehicles.
    """
    name = models.CharField(
        _('name'),
        max_length=100,
        unique=True,
        help_text=_('Name of the component type (e.g., engine, window)'),
        error_messages={
            'unique': _('A component type with this name already exists.'),
            'blank': _('Component type name cannot be blank.'),
        }
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description of this component type')
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Component Type')
        verbose_name_plural = _('Component Types')
        db_table = 'component_types'
        indexes = [
            models.Index(fields=['name'], name='component_type_name_idx'),
        ]

    def clean(self):
        """
        Custom validation for the ComponentType model.
        Ensures that the name is properly formatted and standardized.
        """
        if self.name is None:
            raise ValidationError(_('Component type name cannot be null.'))
        elif not self.name.strip():
            raise ValidationError(_('Component type name cannot be blank.'))

        # Standardize the name format
        self.name = re.sub(r'\s+', ' ', self.name.strip()).capitalize()

        # Check for minimum length after stripping
        if len(self.name) < 2:
            raise ValidationError(_('Component type name must be at least 2 characters long.'))

        # Validate against common special characters
        if re.search(r'[!@#$%^&*()+=\[\]{};\':"\\|,.<>/?]', self.name):
            raise ValidationError(_('Component type name contains invalid special characters.'))

    def save(self, *args: Any, **kwargs: Any):
        """
        Custom save method with additional validation.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class VehicleComponent(TimeStampedModel):
    """
    Represents a specific component instance in a vehicle with its status.
    """
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
        unique_together = ['vehicle', 'name']
        db_table = 'vehicle_components'
        indexes = [
            models.Index(fields=['name'], name='vehicle_component_name_idx'),
            models.Index(fields=['component_type'], name='vehicle_component_type_idx'),
            models.Index(fields=['vehicle'], name='vehicle_component_vehicle_idx'),
            models.Index(fields=['status'], name='vehicle_component_status_idx'),
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
        self.name = re.sub(r'\s+', ' ', self.name.strip())

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

    def save(self, *args: Any, **kwargs: Any):
        """
        Custom save method with additional validation.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.component_type} - {self.vehicle}"
