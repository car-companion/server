import re
from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Manufacturer(models.Model):
    """
    Model representing a vehicle manufacturer/brand.
    """
    name = models.CharField(
        _('name'),
        max_length=100,
        unique=True,
        help_text=_("The name of the vehicle brand"),
        error_messages={
            'unique': _('A manufacturer with this name already exists.'),
            'blank': _('Manufacturer name cannot be blank.'),
        }
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')
        db_table = 'manufacturers'
        indexes = [
            models.Index(fields=['name'], name='manufacturer_name_idx'),
        ]

    def clean(self):
        """
        Custom validation for the Manufacturer model.
        Ensures that the name is properly formatted and standardized.
        """
        if self.name is None:
            raise ValidationError(_('Manufacturer name cannot be null.'))
        elif not self.name.strip():
            raise ValidationError(_('Manufacturer name cannot be blank.'))

        self.name = re.sub(r'\s+', ' ', self.name.strip()).capitalize()

        if len(self.name) < 2:
            raise ValidationError(_('Manufacturer name must be at least 2 characters long.'))

        if re.search(r'[!@#$%^&*()_+=\[\]{};\':"\\|,.<>/?]', self.name):
            raise ValidationError(_('Manufacturer name contains invalid special characters.'))

    def save(self, *args: Any, **kwargs: Any):
        """
        Custom save method with additional validation.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
