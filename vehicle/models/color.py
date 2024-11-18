from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
import re


class Color(models.Model):
    """
    Represents a color option for vehicles.
    This model serves as a reference table for available vehicle colors,
    used for both interior and exterior color options.
    """
    name = models.CharField(
        _('color name'),
        max_length=50,
        unique=True,
        help_text=_('The name of the color - must be unique'),
        error_messages={
            'unique': _('A color with this name already exists.'),
            'blank': _('Color name cannot be blank.'),
        }
    )

    hex_code = ColorField(
        _('color code'),
        help_text=_('Color in hexadecimal format'),
        format='hex',
        samples=[
            '#1E40AF',  # Primary blue
            '#047857',  # Green
            '#B91C1C',  # Red
            '#FFFFFF',  # White
            '#000000',  # Black
            '#6B7280',  # Gray
            '#92400E',  # Brown
        ]
    )

    is_metallic = models.BooleanField(
        _('metallic finish'),
        default=False,
        help_text=_('Indicates if the color has a metallic finish')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Additional details about the color')
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Color')
        verbose_name_plural = _('Colors')
        db_table = 'vehicle_colors'
        indexes = [
            models.Index(fields=['name'], name='color_name_idx'),
        ]

    def clean(self):
        """
        Custom validation for the Color model.
        """
        errors = {}

        # Name validation
        if self.name is None:
            errors['name'] = _('Color name cannot be null.')
        elif not self.name.strip():
            errors['name'] = _('Color name cannot be blank.')
        else:
            self.name = re.sub(r'\s+', ' ', self.name.strip()).capitalize()

        # Hex code validation
        if self.hex_code:
            hex_pattern = r'^#[0-9A-Fa-f]{6}$'
            self.hex_code = self.hex_code.upper()
            if not re.match(hex_pattern, self.hex_code):
                errors['hex_code'] = _('Invalid hex color code format. Use format: #RRGGBB')

        # Description validation (optional)
        if self.description:
            self.description = self.description.strip()

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Custom save method with additional validation.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.hex_code})"
