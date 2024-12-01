from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from guardian.shortcuts import assign_perm, remove_perm

User = get_user_model()


class ComponentPermission(TimeStampedModel):
    """
    Manages fine-grained permissions for vehicle components.

    This model extends django-guardian's permission system by adding:
    - Metadata tracking (who granted, when expires)
    - Explicit permission level tracking (read/write)
    - Automatic permission assignment/revocation

    Attributes:
        component (VehicleComponent): The component this permission applies to
        user (User): The user receiving the permission
        permission_type (str): Level of access (read/write)
        granted_by (User): User who granted this permission
        valid_until (datetime): Optional expiration timestamp
    """

    class PermissionType(models.TextChoices):
        """
        Available permission levels for component access.
        """
        READ = 'read', _('Read Only')
        WRITE = 'write', _('Read & Write')

    component = models.ForeignKey(
        'VehicleComponent',
        on_delete=models.CASCADE,
        related_name='access_permissions',
        verbose_name=_('component'),
        help_text=_('Component this permission applies to')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='component_permissions',
        verbose_name=_('user'),
        help_text=_('User receiving the permission')
    )

    permission_type = models.CharField(
        max_length=5,
        choices=PermissionType.choices,
        verbose_name=_('permission type'),
        help_text=_('Level of access granted')
    )

    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions',
        verbose_name=_('granted by'),
        help_text=_('User who granted this permission')
    )

    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('valid until'),
        help_text=_('When this permission expires (optional)')
    )

    class Meta:
        verbose_name = _('Component Permission')
        verbose_name_plural = _('Component Permissions')
        unique_together = ['component', 'user']
        ordering = ['-created']
        indexes = [
            models.Index(fields=['component', 'user'],
                         name='component_perm_comp_user_idx'),
            models.Index(fields=['valid_until'],
                         name='component_perm_valid_until_idx'),
        ]
        permissions = (
            ('can_grant_access', 'Can grant component access'),
            ('can_revoke_access', 'Can revoke component access'),
        )

    def clean(self):
        """
        Validate the model instance.

        Raises:
            ValidationError: If validation fails
        """
        errors = {}

        # Validate valid_until is in future if set
        if self.valid_until and self.valid_until <= timezone.now():
            errors['valid_until'] = _(
                'Expiration date must be in the future.'
            )

        # Prevent self-granting
        if self.granted_by == self.user:
            errors['granted_by'] = _(
                'Users cannot grant permissions to themselves.'
            )

        if errors:
            raise ValidationError(errors)

    def assign_permissions(self):
        """
        Assign the appropriate django-guardian permissions based on permission_type.
        """
        assign_perm('view_status', self.user, self.component)

        if self.permission_type == self.PermissionType.WRITE:
            assign_perm('change_status', self.user, self.component)

    def revoke_permissions(self, revoke_read=True, revoke_write=True):
        """
        Revoke the specified django-guardian permissions.

        Args:
            revoke_read: Whether to revoke view permission
            revoke_write: Whether to revoke change permission
        """
        if revoke_read:
            remove_perm('view_status', self.user, self.component)
        if revoke_write:
            remove_perm('change_status', self.user, self.component)

    def save(self, *args, **kwargs):
        """
        Save the model instance and manage permissions.

        Overrides TimeStampedModel.save() to handle permission assignment
        on creation.
        """
        # Validate the instance
        self.clean()

        # Track if this is a new instance
        is_new = self.pk is None

        # Save the instance
        super().save(*args, **kwargs)

        # Assign permissions on creation
        if is_new:
            self.assign_permissions()

    def delete(self, *args, **kwargs):
        """
        Delete the model instance and revoke permissions.

        Overrides Model.delete() to handle permission cleanup.
        """
        # Revoke all permissions
        self.revoke_permissions()

        # Delete the instance
        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the permission."""
        return f"{self.user} - {self.component} ({self.get_permission_type_display()})"
