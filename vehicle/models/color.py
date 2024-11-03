from django.db import models
from django.utils.translation import gettext_lazy as _


class Color(models.Model):
    """
    Represents a color option for vehicles.

    This model serves as a reference table for available vehicle colors,
    used for both interior and exterior color options.

    Attributes:
        name (str): The name of the color. Must be unique and properly formatted.
    """
    name = models.CharField(
        _('color name'),  # Translatable field label
        max_length=50,
        unique=True,
        help_text=_('The name of the color - must be unique'),
        error_messages={
            'unique': _('A color with this name already exists.'),
            'blank': _('Color name cannot be blank.'),
        }
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Color')
        verbose_name_plural = _('Colors')
        db_table = 'vehicle_colors'

        # Add indexes for frequently queried fields
        indexes = [
            models.Index(fields=['name'], name='color_name_idx'),
        ]

    def __str__(self):
        """
        Returns a string representation of the color.
        """
        return self.name
