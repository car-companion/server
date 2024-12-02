from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from vehicle.models import (
    Vehicle, VehicleModel, Manufacturer, Color,
    ComponentType, VehicleComponent
)


class ComponentViewsTests(APITestCase):
    """Test suite for component-related views using BDD style."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass')

        # Create base data
        self.manufacturer = Manufacturer.objects.create(
            name='Jeep',
            country_code='US'
        )
        self.model = VehicleModel.objects.create(
            name='Avenger',
            manufacturer=self.manufacturer
        )
        self.color = Color.objects.create(
            name='Black',
            hex_code='#000000'
        )

        # Create vehicles
        self.vehicle = Vehicle.objects.create(
            vin='JH4KA7650NC040097',
            year_built=2020,
            model=self.model,
            outer_color=self.color,
            interior_color=self.color,
            owner=self.user
        )

        self.empty_vehicle = Vehicle.objects.create(
            vin='19UUB3F3XFA811288',
            year_built=2020,
            model=self.model,
            outer_color=self.color,
            interior_color=self.color,
            owner=self.user
        )

        # Create component types
        self.engine_type = ComponentType.objects.create(name='Engine')
        self.tire_type = ComponentType.objects.create(name='Tire')

        # Create components
        self.engine = VehicleComponent.objects.create(
            name='Main engine',
            component_type=self.engine_type,
            vehicle=self.vehicle,
            status=0.8
        )
        self.tires = [
            VehicleComponent.objects.create(
                name=f'Tire {i}',
                component_type=self.tire_type,
                vehicle=self.vehicle,
                status=0.9
            ) for i in range(1, 5)
        ]

        self.client = APIClient()

    # Base Helper Methods
    def _get_component_list_url(self, vin):
        return reverse('vehicle:components:component-list', kwargs={'vin': vin})

    def _get_component_type_url(self, vin, type_name):
        return reverse('vehicle:components:component-by-type',
                       kwargs={'vin': vin, 'type_name': type_name})

    def _get_component_detail_url(self, vin, type_name, name):
        return reverse('vehicle:components:component-detail',
                       kwargs={'vin': vin, 'type_name': type_name, 'name': name})

    # Component List Tests
    def test_list_components_success(self):
        """
        Scenario: Owner requests list of all components
        Given an authenticated vehicle owner
        When they request the component list
        Then they receive all components for their vehicle
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self._get_component_list_url(self.vehicle.vin))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)  # 1 engine + 4 tires

    def test_list_components_access_scenarios(self):
        """
        Scenario: Access control for component listing
        Given different types of users
        When they attempt to access the component list
        Then they receive appropriate responses
        """
        url = self._get_component_list_url(self.vehicle.vin)

        # Test unauthorized
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test non-owner
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test unowned vehicle
        self.vehicle.owner = None
        self.vehicle.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Component Type Tests
    def test_list_components_by_type_success(self):
        """
        Scenario: Owner requests components of specific type
        Given an authenticated owner
        When they request components of a specific type
        Then they receive all matching components
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self._get_component_type_url(self.vehicle.vin, 'Tire'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_components_by_type_not_found_scenarios(self):
        """
        Scenario: Request components that don't exist
        Given an authenticated owner
        When they request non-existent components
        Then they receive appropriate error responses
        """
        self.client.force_authenticate(user=self.user)

        # Test non-existent type
        response = self.client.get(self._get_component_type_url(self.vehicle.vin, 'NonExistent'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test empty type
        empty_type = ComponentType.objects.create(name='EmptyType')
        response = self.client.get(self._get_component_type_url(self.vehicle.vin, 'EmptyType'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Component Type Access Tests
    def test_component_type_access_denied_scenarios(self):
        """
        Scenario: Non-owner attempts to access component type
        Given different unauthorized users
        When they attempt to access components by type
        Then they receive appropriate access denied responses
        """
        url = self._get_component_type_url(self.vehicle.vin, 'Engine')

        # Test non-owner access
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Access denied')

        # Test vehicle with no owner
        self.vehicle.owner = None
        self.vehicle.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Access denied')

    def test_component_type_update_access_denied_scenarios(self):
        """
        Scenario: Non-owner attempts to update component type status
        Given different unauthorized users
        When they attempt to update component type status
        Then they receive appropriate access denied responses
        """
        url = self._get_component_type_url(self.vehicle.vin, 'Engine')
        payload = {'status': 0.5}

        # Test non-owner update
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Access denied')

        # Test vehicle with no owner
        self.vehicle.owner = None
        self.vehicle.save()
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Access denied')

    def test_component_type_not_found_update_scenarios(self):
        """
        Scenario: Update attempts on non-existent components
        Given an authenticated owner
        When they attempt to update non-existent component types
        Then they receive appropriate not found responses
        """
        self.client.force_authenticate(user=self.user)
        payload = {'status': 0.5}

        # Test non-existent type
        url = self._get_component_type_url(self.vehicle.vin, 'NonExistentType')
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'No components found of this type')

        # Test empty type
        empty_type = ComponentType.objects.create(name='EmptyType')
        url = self._get_component_type_url(self.vehicle.vin, 'EmptyType')
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'No components found of this type')

    def test_component_type_validation_scenarios(self):
        """
        Scenario: Invalid update attempts on component types
        Given an authenticated owner
        When they attempt various invalid updates
        Then they receive appropriate validation error responses
        """
        self.client.force_authenticate(user=self.user)
        url = self._get_component_type_url(self.vehicle.vin, 'Engine')

        # Test invalid status values
        invalid_status_cases = [
            ({'status': -0.5}, "Status cannot be negative"),
            ({'status': 1.5}, "Status cannot be greater than 1"),
            ({'status': 'invalid'}, "Status must be a number"),
            ({}, "Status is required"),
            ({'invalid_field': 0.5}, "Status is required"),
        ]

        for payload, error_message in invalid_status_cases:
            response = self.client.patch(url, payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue(
                'status' in response.data or 'detail' in response.data,
                f"Expected 'status' or 'detail' in response, got: {response.data}"
            )

        # Test invalid VIN format with valid status
        invalid_vin_url = self._get_component_type_url('INVALID-VIN', 'Engine')
        response = self.client.patch(invalid_vin_url, {'status': 0.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

        # Test invalid VIN characters with valid status
        invalid_chars_url = self._get_component_type_url('WB1OI75A14ZL3004', 'Engine')
        response = self.client.patch(invalid_chars_url, {'status': 0.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    # Component Detail Tests
    def test_component_detail_success(self):
        """
        Scenario: Owner requests specific component details
        Given an authenticated owner
        When they request details of a specific component
        Then they receive the component details
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            self._get_component_detail_url(self.vehicle.vin, 'Engine', 'Main engine')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Main engine')
        self.assertEqual(response.data['status'], 0.8)

    # Status Update Tests
    def test_update_status_success_scenarios(self):
        """
        Scenario: Valid status updates
        Given an authenticated owner
        When they update component status with valid values
        Then the updates are successful
        """
        self.client.force_authenticate(user=self.user)

        # Individual component update
        response = self.client.patch(
            self._get_component_detail_url(self.vehicle.vin, 'Engine', 'Main engine'),
            {'status': 0.6}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 0.6)

        # Component type update
        response = self.client.patch(
            self._get_component_type_url(self.vehicle.vin, 'Tire'),
            {'status': 0.5}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(comp['status'] == 0.5 for comp in response.data))

    # Validation Tests
    def test_vin_validation_scenarios(self):
        """
        Scenario: VIN validation
        Given various invalid VIN formats
        When making requests with these VINs
        Then appropriate validation errors are returned
        """
        self.client.force_authenticate(user=self.user)
        invalid_vins = ['INVALID', 'WB1OI75A14ZL3004']  # Too short, Invalid chars

        for vin in invalid_vins:
            # Test list endpoint
            response = self.client.get(self._get_component_list_url(vin))
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # Test type endpoint
            response = self.client.get(self._get_component_type_url(vin, 'Engine'))
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # Test detail endpoint
            response = self.client.get(
                self._get_component_detail_url(vin, 'Engine', 'Main engine')
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_validation_scenarios(self):
        """
        Scenario: Status value validation
        Given various invalid status values
        When attempting to update component status
        Then appropriate validation errors are returned
        """
        self.client.force_authenticate(user=self.user)
        invalid_status_values = [
            -0.5,  # Negative
            1.5,  # Above maximum
            'invalid'  # Non-numeric
        ]

        for invalid_status in invalid_status_values:
            # Test individual component update
            response = self.client.patch(
                self._get_component_detail_url(self.vehicle.vin, 'Engine', 'Main engine'),
                {'status': invalid_status}
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # Test component type update
            response = self.client.patch(
                self._get_component_type_url(self.vehicle.vin, 'Engine'),
                {'status': invalid_status}
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_component_detail_access_denied_get_scenarios(self):
        """
        Scenario: Unauthorized users attempt to get component details
        Given different unauthorized users
        When they attempt to get component details
        Then they receive appropriate access denied responses
        """
        url = self._get_component_detail_url(
            self.vehicle.vin,
            'Engine',
            'Main engine'
        )

        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test non-owner access
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Access denied')

        # Test vehicle with no owner
        self.vehicle.owner = None
        self.vehicle.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Access denied')

    def test_component_detail_access_denied_patch_scenarios(self):
        """
        Scenario: Unauthorized users attempt to update component status
        Given different unauthorized users
        When they attempt to update component status
        Then they receive appropriate access denied responses
        """
        url = self._get_component_detail_url(
            self.vehicle.vin,
            'Engine',
            'Main engine'
        )
        payload = {'status': 0.5}

        # Test unauthenticated access
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test non-owner access
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Access denied')

        # Test vehicle with no owner
        self.vehicle.owner = None
        self.vehicle.save()
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Access denied')

    def test_component_detail_validation_patch_scenarios(self):
        """
        Scenario: Invalid update attempts on component details
        Given an authenticated owner
        When they attempt various invalid updates
        Then they receive appropriate validation error responses
        """
        self.client.force_authenticate(user=self.user)
        base_url = self._get_component_detail_url(
            self.vehicle.vin,
            'Engine',
            'Main engine'
        )

        # Test various invalid status values
        invalid_status_cases = [
            ({'status': -0.5}, "Status cannot be negative"),
            ({'status': 1.5}, "Status cannot be greater than 1"),
            ({'status': 'invalid'}, "Status must be a number"),
            ({}, "Status is required"),
            ({'invalid_field': 0.5}, "Status is required"),
        ]

        for payload, error_message in invalid_status_cases:
            response = self.client.patch(base_url, payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue(
                'status' in response.data or 'detail' in response.data,
                f"Expected 'status' or 'detail' in response, got: {response.data}"
            )

        # Test invalid VIN format
        invalid_vin_url = self._get_component_detail_url(
            'INVALID-VIN',
            'Engine',
            'Main engine'
        )
        response = self.client.patch(invalid_vin_url, {'status': 0.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

        # Test invalid VIN characters
        invalid_chars_url = self._get_component_detail_url(
            'WB1OI75A14ZL3004',  # Contains invalid characters I and O
            'Engine',
            'Main engine'
        )
        response = self.client.patch(invalid_chars_url, {'status': 0.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

        # Test non-existent component
        not_found_url = self._get_component_detail_url(
            self.vehicle.vin,
            'Engine',
            'NonExistentComponent'
        )
        response = self.client.patch(not_found_url, {'status': 0.5})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

        # Test non-existent component type
        invalid_type_url = self._get_component_detail_url(
            self.vehicle.vin,
            'NonExistentType',
            'Main engine'
        )
        response = self.client.patch(invalid_type_url, {'status': 0.5})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)
