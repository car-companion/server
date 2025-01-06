import re
from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


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
