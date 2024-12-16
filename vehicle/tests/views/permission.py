from datetime import timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from vehicle.models import (
    Vehicle, VehicleModel, Manufacturer, Color,
    ComponentType, VehicleComponent, ComponentPermission
)


class BaseVehiclePermissionTest(APITestCase):
    """Base test class with common setup and helper methods."""

    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(username='owner', password='testpass')
        self.user = User.objects.create_user(username='testuser', password='testpass')

        self.manufacturer = Manufacturer.objects.create(
            name='TestMake',
            country_code='US'
        )
        self.model = VehicleModel.objects.create(
            name='TestModel',
            manufacturer=self.manufacturer
        )
        self.color = Color.objects.create(
            name='TestColor',
            hex_code='#000000'
        )

        self.vehicle = Vehicle.objects.create(
            vin='JH4KA3142KC889327',
            year_built=2020,
            model=self.model,
            outer_color=self.color,
            interior_color=self.color,
            owner=self.owner
        )

        self.engine_type = ComponentType.objects.create(name='Engine')
        self.main_engine = VehicleComponent.objects.create(
            name='Main Engine',
            component_type=self.engine_type,
            vehicle=self.vehicle
        )

        self.client = APIClient()

    def get_list_url(self, vin):
        """Get URL for permission list endpoint."""
        return reverse('vehicle:permissions:vehicle-permissions-overview',
                       kwargs={'vin': vin})

    def get_permission_url(self, vin, username=None, component_type=None, component_name=None):
        """Get URL for permission management endpoint."""
        if component_type and component_name:
            url_name = 'vehicle:permissions:user-permissions-component-type-name'
        elif component_type:
            url_name = 'vehicle:permissions:user-permissions-component-type'
        else:
            url_name = 'vehicle:permissions:user-permissions'

        kwargs = {'vin': vin}
        if username:
            kwargs['username'] = username
        if component_type:
            kwargs['component_type'] = component_type
        if component_name:
            kwargs['component_name'] = component_name

        return reverse(url_name, kwargs=kwargs)


class VehiclePermissionReadOnlyTests(BaseVehiclePermissionTest):
    """Tests for read-only permission endpoints."""

    def test_permission_list_success(self):
        """
        Scenario: Owner requests permission list
        Given an authenticated vehicle owner
        When requesting the permission list
        Then they receive a list of all permissions
        """
        self.client.force_authenticate(user=self.owner)
        ComponentPermission.objects.create(
            component=self.main_engine,
            user=self.user,
            permission_type='read'
        )

        response = self.client.get(self.get_list_url(self.vehicle.vin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], 'testuser')

    def test_permission_list_unauthorized(self):
        """
        Scenario: Non-owner requests permission list
        Given a user who doesn't own the vehicle
        When requesting the permission list
        Then they receive a forbidden response
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_list_url(self.vehicle.vin))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_list_not_found(self):
        """
        Scenario: Request permissions for non-existent vehicle
        Given an authenticated owner
        When requesting permissions for non-existent vehicle
        Then receive not found response
        """
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.get_list_url('NONEXISTENT12345'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_permissions_with_filters(self):
        """
        Scenario: Retrieve permissions with filters
        Given a vehicle with specific component permissions
        When filtering by type and name
        Then return filtered permissions
        """
        self.client.force_authenticate(user=self.owner)
        ComponentPermission.objects.create(
            component=self.main_engine,
            user=self.user,
            permission_type='read'
        )
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username,
            component_type='Engine',
            component_name='Main Engine'
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class VehiclePermissionFilteringTests(BaseVehiclePermissionTest):
    """Tests for permission filtering functionality."""

    def test_filter_components_no_matches(self):
        """
        Scenario: Filter components with non-existent criteria
        Given a vehicle with components
        When filtering with criteria matching no components
        Then receive validation error
        """
        self.client.force_authenticate(user=self.owner)
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username,
            component_type='NonexistentType'
        )
        response = self.client.post(url, {'permission_type': 'read'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No matching components found.", str(response.data))

    def test_filter_no_component_type(self):
        """
        Scenario: Filter components without component_type
        Given a vehicle with components
        When filtering without specifying component_type
        Then return all components
        """
        self.client.force_authenticate(user=self.owner)
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username
        )
        response = self.client.post(url, {'permission_type': 'read'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['granted']), 1)

    def test_filter_with_component_name(self):
        """
        Scenario: Filter components with component name and type
        Given a vehicle with components
        When filtering by component name and type
        Then return matching components
        """
        self.client.force_authenticate(user=self.owner)
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username,
            component_type='Engine',
            component_name='Main Engine'
        )
        response = self.client.post(url, {'permission_type': 'read'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['granted']), 1)

    def test_get_permissions_with_partial_filters(self):
        """
        Scenario: Retrieve permissions with some filters omitted
        Given a vehicle with permissions
        When requesting permissions with partial filters
        Then return filtered permissions matching the provided criteria
        """
        self.client.force_authenticate(user=self.owner)

        # Create permissions for different components
        ComponentPermission.objects.create(
            component=self.main_engine,
            user=self.user,
            permission_type='read'
        )
        another_component = VehicleComponent.objects.create(
            name='Another Engine',
            component_type=self.engine_type,
            vehicle=self.vehicle
        )
        ComponentPermission.objects.create(
            component=another_component,
            user=self.user,
            permission_type='write'
        )

        # Test with username only
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username  # Only username provided
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data[0]['permissions']), 2)  # Should include both components

        # Test with username and component_type only
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username,
            component_type='Engine'  # Only username and type provided
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data[0]['permissions']), 2)  # Both components of type 'Engine'

        # Test with username, component_type, and component_name
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username,
            component_type='Engine',
            component_name='Main Engine'  # All filters provided
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the 'Main Engine' should match


class VehiclePermissionManagementTests(BaseVehiclePermissionTest):
    """Tests for granting and revoking permissions."""

    def test_grant_permission_success(self):
        """
        Scenario: Owner grants component permission
        Given an authenticated vehicle owner
        When granting permission to another user
        Then the permission is created successfully
        """
        self.client.force_authenticate(user=self.owner)
        data = {
            'permission_type': 'read',
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }

        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username,
            component_type='Engine'
        )
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['granted'])

    def test_grant_permission_to_owner(self):
        """
        Scenario: Grant permission to vehicle owner
        Given an authenticated vehicle owner
        When attempting to grant themselves permission
        Then return validation error
        """
        self.client.force_authenticate(user=self.owner)
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.owner.username,
            component_type='Engine'
        )
        response = self.client.post(url, {'permission_type': 'read'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot grant permissions to the vehicle owner.", str(response.data))

    def test_grant_permission_exception_handling(self):
        """
        Scenario: Grant permission with an exception during processing
        Given an authenticated vehicle owner
        When an exception occurs while processing permissions
        Then handle exception gracefully
        """
        self.client.force_authenticate(user=self.owner)
        data = {'permission_type': 'read',
                'valid_until': (timezone.now() - timedelta(days=1)).isoformat()  # Past time
                }

        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username,
            component_type='Engine'
        )

        response = self.client.post(url, data)

        # Assert response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the failure is properly logged in the response
        self.assertEqual(len(response.data['failed']), 1)
        self.assertIn('error', response.data['failed'][0])
        self.assertIn('Expiration date must be in the future', response.data['failed'][0]['error'])

    def test_revoke_permission_success(self):
        """
        Scenario: Owner revokes component permission
        Given an authenticated vehicle owner and existing permissions
        When revoking permission from a user
        Then the permissions are removed successfully
        """
        self.client.force_authenticate(user=self.owner)
        ComponentPermission.objects.create(
            component=self.main_engine,
            user=self.user,
            permission_type='read'
        )

        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.user.username,
            component_type='Engine'
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['revoked'])

    def test_revoke_permission_from_owner(self):
        """
        Scenario: Revoke permission from vehicle owner
        Given an authenticated vehicle owner
        When attempting to revoke permissions from themselves
        Then return validation error
        """
        self.client.force_authenticate(user=self.owner)
        url = self.get_permission_url(
            self.vehicle.vin,
            username=self.owner.username
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot revoke permissions from the vehicle owner.", str(response.data))


class AccessedVehiclesViewTests(BaseVehiclePermissionTest):
    """Tests for accessed vehicles view."""

    def get_accessed_vehicles_url(self):
        """Get URL for accessed vehicles endpoint."""
        return reverse('vehicle:accessed-vehicles')

    def test_list_accessed_vehicles(self):
        """
        Scenario: User lists vehicles they have access to
        Given a user with permissions on some vehicles
        When requesting their accessed vehicles
        Then they receive a list of vehicles they can access
        """
        self.client.force_authenticate(user=self.user)
        ComponentPermission.objects.create(
            component=self.main_engine,
            user=self.user,
            permission_type='read'
        )

        response = self.client.get(self.get_accessed_vehicles_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['vin'], self.vehicle.vin)

    def test_no_accessed_vehicles(self):
        """
        Scenario: User with no permissions lists accessed vehicles
        Given a user with no vehicle permissions
        When requesting their accessed vehicles
        Then they receive an empty list
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_accessed_vehicles_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
