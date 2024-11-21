import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class VehicleModel(models.Model):
    """
    Model representing a specific vehicle model that can be used to create vehicles.
    Includes functionality to define default components for each model.
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
        'Manufacturer',
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
            models.Index(fields=['name'], name='model_name_idx'),
            models.Index(fields=['manufacturer'], name='model_manufacturer_idx'),
        ]

    def clean(self):
        """Custom validation for the VehicleModel."""
        if self.name is None:
            raise ValidationError(_('Model name cannot be null.'))
        elif not self.name.strip():
            raise ValidationError(_('Model name cannot be blank.'))

        # Standardize the name format
        self.name = re.sub(r'\s+', ' ', self.name.strip()).upper()

        if len(self.name) < 1:
            raise ValidationError(_('Model name must be at least 1 character long.'))

        if re.search(r'[!@#$%^&*()+=\[\]{};\':"\\|,.<>/?]', self.name):
            raise ValidationError(_('Model name contains invalid special characters.'))

        if not self.manufacturer_id:
            raise ValidationError(_('Manufacturer is required.'))

    def __str__(self):
        return f"{self.manufacturer.name} {self.name}"

    def create_vehicle(self, vin, year_built, outer_color, interior_color, nickname=None):
        """
        Creates a new vehicle instance based on this model,
        including all default components.
        """
        from .vehicle import Vehicle, VehicleComponent

        # Create the vehicle
        vehicle = Vehicle.objects.create(
            vin=vin,
            year_built=year_built,
            model=self,
            outer_color=outer_color,
            interior_color=interior_color,
            nickname=nickname
        )

        # Clone all model default components for this vehicle
        for model_component in self.default_components.all():
            VehicleComponent.objects.create(
                name=model_component.name,
                component_type=model_component.component_type,
                vehicle=vehicle,
                status=0.0  # Default initial status
            )

        return vehicle


class ModelComponent(models.Model):
    """
    Represents default components that should be created for vehicles
    of a specific model.
    """
    model = models.ForeignKey(
        VehicleModel,
        on_delete=models.CASCADE,
        related_name='default_components',
        verbose_name=_('vehicle model'),
        help_text=_('Model this component belongs to')
    )

    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Name of the default component'),
        error_messages={
            'blank': _('Component name cannot be blank.'),
        }
    )

    component_type = models.ForeignKey(
        'ComponentType',
        on_delete=models.PROTECT,
        related_name='model_components',
        verbose_name=_('component type'),
        help_text=_('Type of this component')
    )

    class Meta:
        ordering = ['model', 'component_type__name']
        verbose_name = _('Model Component')
        verbose_name_plural = _('Model Components')
        unique_together = ['model', 'name', 'component_type']
        db_table = 'model_components'

    def clean(self):
        if self.name is None:
            raise ValidationError(_('Component name cannot be null.'))
        elif not self.name.strip():
            raise ValidationError(_('Component name cannot be blank.'))

        self.name = re.sub(r'\s+', ' ', self.name.strip()).capitalize()

        if len(self.name) < 2:
            raise ValidationError(_('Component name must be at least 2 characters long.'))

        if re.search(r'[!@#$%^&*()+=\[\]{};\':"\\|,.<>/?]', self.name):
            raise ValidationError(_('Component name contains invalid special characters.'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.component_type}) - {self.model}"
