from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from guardian.shortcuts import assign_perm, remove_perm
from guardian.exceptions import GuardianError

User = get_user_model()


class ComponentPermission(TimeStampedModel):
    """
    Tracks component-level permissions granted to users.
    Complements django-guardian's permission system by adding metadata
    and explicit permission tracking.
    """

    class PermissionType(models.TextChoices):
        READ = 'read', _('Read Only')
        WRITE = 'write', _('Read & Write')

    component = models.ForeignKey(
        'VehicleComponent',
        on_delete=models.CASCADE,
        related_name='access_permissions',
        verbose_name=_('component')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='component_permissions',
        verbose_name=_('user')
    )

    permission_type = models.CharField(
        max_length=5,
        choices=PermissionType.choices,
        verbose_name=_('permission type')
    )

    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions',
        verbose_name=_('granted by')
    )

    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('valid until'),
        help_text=_('If set, the permission will expire at this time')
    )

    class Meta:
        verbose_name = _('Component Permission')
        verbose_name_plural = _('Component Permissions')
        unique_together = ['component', 'user']
        ordering = ['-created']
        indexes = [
            models.Index(fields=['component', 'user']),
            models.Index(fields=['valid_until']),
        ]

    def assign_permissions(self):
        """Assign guardian permissions based on the permission type."""
        try:
            assign_perm('view_status', self.user, self.component)
            if self.permission_type == self.PermissionType.WRITE:
                assign_perm('change_status', self.user, self.component)
        except GuardianError as e:
            # Log or handle errors as needed
            print(f"Error assigning permissions: {e}")

    def revoke_permissions(self, revoke_read=True, revoke_write=True):
        """
        Revoke guardian permissions.

        Parameters:
            revoke_read (bool): Whether to revoke the 'view_status' (read) permission.
            revoke_write (bool): Whether to revoke the 'change_status' (write) permission.
        """
        try:
            # Revoke 'view_status' permission if revoke_read is True.
            if revoke_read:
                remove_perm('view_status', self.user, self.component)

            # Revoke 'change_status' permission if revoke_write is True.
            if revoke_write:
                remove_perm('change_status', self.user, self.component)
        except GuardianError as e:
            # Log or handle errors as needed.
            print(f"Error revoking permissions: {e}")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.assign_permissions()

    def delete(self, *args, **kwargs):
        self.revoke_permissions()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.component} ({self.permission_type})"
