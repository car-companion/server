from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class VehicleUserPreferences(models.Model):
    """
    Stores user-specific preferences for vehicles.
    Each user can have their own nickname and color preferences for a vehicle.
    """
    vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.CASCADE,
        related_name='user_preferences',
        verbose_name=_('vehicle'),
        help_text=_('Vehicle these preferences belong to')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicle_preferences',
        verbose_name=_('user'),
        help_text=_('User who set these preferences')
    )

    nickname = models.CharField(
        _('nickname'),
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-]*$',
                message=_('Nickname can only contain letters, numbers, spaces, and hyphens.')
            )
        ],
        help_text=_('Personal nickname for the vehicle'),
        error_messages={
            'max_length': _('Nickname cannot be longer than 100 characters.')
        }
    )

    interior_color = models.ForeignKey(
        'Color',
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_('personal interior color'),
        help_text=_('User-specific interior color preference'),
        null=True,
        blank=True
    )

    exterior_color = models.ForeignKey(
        'Color',
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_('personal exterior color'),
        help_text=_('User-specific exterior color preference'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Vehicle User Preferences')
        verbose_name_plural = _('Vehicle User Preferences')
        unique_together = ['vehicle', 'user']
        ordering = ['vehicle', 'user']
        db_table = 'vehicle_user_preferences'

    def clean(self):
        if self.nickname:
            self.nickname = self.nickname.strip()
            if len(self.nickname) < 2:
                raise ValidationError(_('Nickname must be at least 2 characters long.'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle} - {self.user.username}'s preferences"
