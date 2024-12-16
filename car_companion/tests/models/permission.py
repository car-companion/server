from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from guardian.shortcuts import get_perms

from ...models import VehicleComponent, ComponentType, ComponentPermission, Manufacturer, VehicleModel, Color, Vehicle

User = get_user_model()


class ComponentPermissionModelTests(TestCase):
    """
    Test suite for the ComponentPermission model.
    Tests permission management, validation, and guardian integration.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        # Create users
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        cls.granter = User.objects.create_user(
            username='granter',
            password='testpass123'
        )

        # Create component type
        cls.component_type = ComponentType.objects.create(
            name="Test Component"
        )

        # Create manufacturer
        cls.manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE"
        )

        # Create vehicle model
        cls.vehicle_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=cls.manufacturer
        )

        # Create colors
        cls.exterior_color = Color.objects.create(
            name="Black",
            hex_code="#000000"
        )
        cls.interior_color = Color.objects.create(
            name="Beige",
            hex_code="#F5F5DC"
        )

        # Create base vehicle
        cls.base_vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=cls.vehicle_model,
            outer_color=cls.exterior_color,
            interior_color=cls.interior_color
        )

        # Create vehicle hierarchy
        cls.component = VehicleComponent.objects.create(
            name="Test Component",
            component_type=cls.component_type,
            status=0.5,
            vehicle=cls.base_vehicle
        )

        # Base permission data
        cls.valid_permission_data = {
            'component': cls.component,
            'user': cls.user,
            'permission_type': ComponentPermission.PermissionType.READ,
            'granted_by': cls.granter,
            'valid_until': timezone.now() + timedelta(days=30)
        }

    def test_create_read_permission(self):
        """
        Scenario: Creating a read-only permission
        Given a user and component
        When creating a read permission
        Then appropriate guardian permissions should be assigned
        """
        permission = ComponentPermission.objects.create(**self.valid_permission_data)

        # Check basic attributes
        self.assertEqual(permission.component, self.component)
        self.assertEqual(permission.user, self.user)
        self.assertEqual(permission.permission_type, ComponentPermission.PermissionType.READ)

        # Check guardian permissions
        user_perms = get_perms(self.user, self.component)
        self.assertIn('view_status', user_perms)
        self.assertNotIn('change_status', user_perms)

    def test_create_write_permission(self):
        """
        Scenario: Creating a write permission
        Given a user and component
        When creating a write permission
        Then both read and write guardian permissions should be assigned
        """
        data = self.valid_permission_data.copy()
        data['permission_type'] = ComponentPermission.PermissionType.WRITE

        ComponentPermission.objects.create(**data)

        # Check guardian permissions
        user_perms = get_perms(self.user, self.component)
        self.assertIn('view_status', user_perms)
        self.assertIn('change_status', user_perms)

    def test_expiration_validation(self):
        """
        Scenario: Validating permission expiration
        Given various expiration timestamps
        When creating permissions
        Then validation should enforce future dates
        """
        test_cases = [
            (timezone.now() - timedelta(days=1), False),  # Past
            (timezone.now(), False),  # Present
            (timezone.now() + timedelta(days=1), True),  # Future
        ]

        for expiration_time, should_pass in test_cases:
            data = self.valid_permission_data.copy()
            data['valid_until'] = expiration_time

            if should_pass:
                ComponentPermission.objects.create(**data)
            else:
                with self.assertRaises(ValidationError):
                    permission = ComponentPermission(**data)
                    permission.full_clean()

    def test_save_assigns_permissions(self):
        """
        Scenario: Permission assignment on save
        Given a new permission instance
        When saving it
        Then permissions should be assigned
        And subsequent saves should not reassign permissions
        """
        # Test initial save
        permission = ComponentPermission(**self.valid_permission_data)
        with patch.object(ComponentPermission, 'assign_permissions') as mock_assign:
            permission.save()
            mock_assign.assert_called_once()

        # Test subsequent save
        with patch.object(ComponentPermission, 'assign_permissions') as mock_assign:
            permission.save()
            mock_assign.assert_not_called()

    def test_prevent_self_granting(self):
        """
        Scenario: Preventing self-granted permissions
        Given a user attempting to grant themselves permission
        When creating the permission
        Then validation should prevent it
        """
        data = self.valid_permission_data.copy()
        data['granted_by'] = self.user  # Same as permission recipient

        with self.assertRaises(ValidationError):
            permission = ComponentPermission(**data)
            permission.full_clean()

    def test_unique_constraint(self):
        """
        Scenario: Enforcing unique user-component pairs
        Given an existing permission
        When creating a duplicate permission
        Then it should be prevented
        """
        # Create initial permission
        ComponentPermission.objects.create(**self.valid_permission_data)

        # Attempt to create duplicate
        with self.assertRaises(Exception):  # Could be IntegrityError or ValidationError
            ComponentPermission.objects.create(**self.valid_permission_data)

    def test_permission_revocation(self):
        """
        Scenario: Revoking permissions
        Given an existing permission
        When deleting it
        Then guardian permissions should be removed
        """
        # Create permission
        permission = ComponentPermission.objects.create(**self.valid_permission_data)

        # Verify initial permissions
        self.assertIn('view_status', get_perms(self.user, self.component))

        # Delete permission
        permission.delete()

        # Verify permissions are removed
        self.assertNotIn('view_status', get_perms(self.user, self.component))

    def test_partial_permission_revocation(self):
        """
        Scenario: Selective permission revocation
        Given a permission with both read and write access
        When revoking only read or only write permission
        Then only the specified permission should be revoked
        """
        # Create permission with write access (includes read)
        data = self.valid_permission_data.copy()
        data['permission_type'] = ComponentPermission.PermissionType.WRITE
        permission = ComponentPermission.objects.create(**data)

        # Test revoking only write permission
        permission.revoke_permissions(revoke_read=False, revoke_write=True)
        user_perms = get_perms(self.user, self.component)
        self.assertIn('view_status', user_perms)
        self.assertNotIn('change_status', user_perms)

        # Test revoking only read permission
        permission.revoke_permissions(revoke_read=True, revoke_write=False)
        user_perms = get_perms(self.user, self.component)
        self.assertNotIn('view_status', user_perms)

    def test_str_representation(self):
        """
        Scenario: String representation
        Given a permission
        When converting to string
        Then it should include user, component, and permission type
        """
        permission = ComponentPermission.objects.create(**self.valid_permission_data)
        expected = f"{self.user} - {self.component} (Read Only)"
        self.assertEqual(str(permission), expected)

    def test_ordering(self):
        """
        Scenario: Permission ordering
        Given multiple permissions
        When retrieving them
        Then they should be ordered by creation date descending
        """
        # Create permissions with different timestamps
        permission1 = ComponentPermission.objects.create(
            component=self.component,
            user=self.user,
            permission_type=ComponentPermission.PermissionType.READ,
            granted_by=self.granter
        )

        permission2 = ComponentPermission.objects.create(
            component=self.component,
            user=User.objects.create_user(username='user2'),
            permission_type=ComponentPermission.PermissionType.READ,
            granted_by=self.granter
        )

        permissions = ComponentPermission.objects.all()
        self.assertEqual(list(permissions), [permission2, permission1])

    def test_meta_configuration(self):
        """
        Scenario: Model metadata configuration
        Given the ComponentPermission model
        When checking its metadata
        Then it should match defined settings
        """
        meta = ComponentPermission._meta
        self.assertEqual(meta.verbose_name, 'Component Permission')
        self.assertEqual(meta.verbose_name_plural, 'Component Permissions')
        self.assertEqual(meta.ordering, ['-created'])

        # Check indexes
        index_names = [index.name for index in meta.indexes]
        self.assertIn('component_perm_comp_user_idx', index_names)
        self.assertIn('component_perm_valid_until_idx', index_names)

        # Check permissions
        self.assertTrue(
            any(perm[0] == 'can_grant_access' for perm in meta.permissions)
        )
        self.assertTrue(
            any(perm[0] == 'can_revoke_access' for perm in meta.permissions)
        )
