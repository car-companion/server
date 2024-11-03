from django.db import models
from django.utils.translation import gettext_lazy as _


class Manufacturer(models.Model):
    """
    Model representing a vehicle manufacturer/brand.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("The name of the vehicle brand")
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')

    def __str__(self):
        return self.name
