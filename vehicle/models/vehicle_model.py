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
        help_text=_('The name of the vehicle model')
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        related_name='models',
        help_text=_("Manufacturer this model belongs to")
    )

    class Meta:
        ordering = ['manufacturer__name', 'name']
        verbose_name = _('Vehicle Model')
        verbose_name_plural = _('Vehicle Models')
        unique_together = ['name', 'manufacturer']

    def __str__(self):
        return f"{self.manufacturer.name} {self.name}"
