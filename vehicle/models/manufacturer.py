import re
from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator, RegexValidator


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

    country_code = models.CharField(
        _('country code'),
        max_length=2,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z]{2}$',
                message=_('Country code must be exactly 2 uppercase letters.')
            )
        ],
        help_text=_("ISO 3166-1 alpha-2 country code (e.g., 'DE' for Germany)"),
        error_messages={
            'blank': _('Country code cannot be blank.'),
            'invalid': _('Enter a valid country code (2 uppercase letters).'),
        }
    )

    website_url = models.URLField(
        _('website URL'),
        max_length=255,
        blank=True,
        null=True,
        validators=[URLValidator()],
        help_text=_("Official manufacturer website URL"),
        error_messages={
            'invalid': _('Enter a valid URL.'),
        }
    )

    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_("Description of the manufacturer"),
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')
        db_table = 'manufacturers'
        indexes = [
            models.Index(fields=['name'], name='manufacturer_name_idx'),
            models.Index(fields=['country_code'], name='manufacturer_country_idx'),
        ]

    def clean(self):
        """
        Custom validation for the Manufacturer model.
        Ensures that the name and other fields are properly formatted and standardized.
        """
        errors = {}

        # Name validation
        if self.name is None:
            errors['name'] = _('Manufacturer name cannot be null.')
        elif not self.name.strip():
            errors['name'] = _('Manufacturer name cannot be blank.')
        else:
            self.name = re.sub(r'\s+', ' ', self.name.strip()).capitalize()
            if len(self.name) < 2:
                errors['name'] = _('Manufacturer name must be at least 2 characters long.')
            if re.search(r'[!@#$%^&*()_+=\[\]{};\':"\\|,.<>/?]', self.name):
                errors['name'] = _('Manufacturer name contains invalid special characters.')

        # Country code validation
        if self.country_code:
            self.country_code = self.country_code.upper()
        else:
            errors['country_code'] = _('Country code is required.')

        # Website URL validation (optional)
        if self.website_url:
            self.website_url = self.website_url.strip()
            url_validator = URLValidator()
            try:
                url_validator(self.website_url)
            except ValidationError:
                errors['website_url'] = _('Enter a valid URL.')

        # Description validation (optional)
        if self.description:
            self.description = self.description.strip()

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any):
        """
        Custom save method with additional validation.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.country_code})"
