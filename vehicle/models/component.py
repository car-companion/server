from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from model_utils.models import TimeStampedModel
from .vehicle import Vehicle


class ComponentType(models.Model):
    """
    Reference table for types of components that can be added to vehicles.
    For example: Engine, Window, Door, etc.
    """
    name = models.CharField(
        _('name'),
        max_length=100,
        unique=True,
        help_text=_('Name of the component type (e.g., engine, window)')
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

    def __str__(self):
        return self.name


class VehicleComponent(TimeStampedModel):
    """
    Represents a specific component instance in a vehicle with its status.
    """
    name = models.CharField(
        _('name'),
        max_length=200,
        unique=True,
        help_text=_('Name of the component (e.g., front left window, engine, rear right door, etc.)')
    )
    component_type = models.ForeignKey(
        ComponentType,
        on_delete=models.PROTECT,
        related_name='vehicle_components',
        verbose_name=_('component type'),
        help_text=_('Type of this component')
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name=_('vehicle'),
        help_text=_('Vehicle this component belongs to')
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
        unique_together = ['vehicle', 'name']  # Each component type can only be once per vehicle

    def __str__(self):
        return f"{self.component_type} - {self.vehicle}"
