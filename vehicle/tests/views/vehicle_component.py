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

        # Create vehicles
        self.vehicle = Vehicle.objects.create(
            vin='WB10175A14ZL30042',
            year_built=2020,
            model=self.model,
            outer_color=self.color,
            interior_color=self.color,
            owner=self.user
        )

        self.empty_vehicle = Vehicle.objects.create(
            vin='WB10175A14ZL30043',
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

    def test_list_components_authenticated_owner(self):
        """
        Scenario: Owner requests list of all components
        Given an authenticated user who owns the vehicle
        When they request the component list
        Then they receive all components for their vehicle
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-list', kwargs={'vin': self.vehicle.vin})
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)  # 1 engine + 4 tires

    def test_list_components_authenticated_non_owner(self):
        """
        Scenario: Non-owner attempts to list components
        Given an authenticated user who doesn't own the vehicle
        When they request the component list
        Then they receive a forbidden response
        """
        # Given
        self.client.force_authenticate(user=self.other_user)

        # When
        url = reverse('vehicle:components:component-list', kwargs={'vin': self.vehicle.vin})
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_components_unauthenticated(self):
        """
        Scenario: Unauthenticated user attempts to list components
        Given an unauthenticated user
        When they request the component list
        Then they receive an unauthorized response
        """
        # Given
        url = reverse('vehicle:components:component-list', kwargs={'vin': self.vehicle.vin})

        # When
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_components_invalid_vin(self):
        """
        Scenario: Request with invalid VIN format
        Given an authenticated owner
        When they request components with an invalid VIN
        Then they receive a bad request response
        """
        # Given
        self.client.force_authenticate(user=self.user)
        invalid_vin = 'INVALID'

        # When
        url = reverse('vehicle:components:component-list', kwargs={'vin': invalid_vin})
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_components_unowned_vehicle(self):
        """
        Scenario: Request components for unowned vehicle
        Given an authenticated user and a vehicle without an owner
        When they request the component list
        Then they receive a forbidden response
        """
        # Given
        self.client.force_authenticate(user=self.other_user)
        self.vehicle.owner = None
        self.vehicle.save()

        # When
        url = reverse('vehicle:components:component-list', kwargs={'vin': self.vehicle.vin})
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_components_by_type_success(self):
        """
        Scenario: Owner requests components of specific type
        Given an authenticated owner
        When they request components of a specific type
        Then they receive all matching components
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-by-type',
                     kwargs={'vin': self.vehicle.vin, 'type_name': 'Tire'})
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # 4 tires

    def test_components_by_type_not_found(self):
        """
        Scenario: Owner requests non-existent component type
        Given an authenticated owner
        When they request components of a non-existent type
        Then they receive a not found response
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-by-type',
                     kwargs={'vin': self.vehicle.vin, 'type_name': 'NonExistent'})
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_component_type_status(self):
        """
        Scenario: Owner updates status of all components of a type
        Given an authenticated owner
        When they update the status of all components of a type
        Then all matching components are updated
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-by-type',
                     kwargs={'vin': self.vehicle.vin, 'type_name': 'Tire'})
        response = self.client.patch(url, {'status': 0.5})

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(comp['status'] == 0.5 for comp in response.data))

    def test_update_component_type_invalid_status(self):
        """
        Scenario: Owner attempts to update with invalid status
        Given an authenticated owner
        When they attempt to update with an invalid status value
        Then they receive a bad request response
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-by-type',
                     kwargs={'vin': self.vehicle.vin, 'type_name': 'Engine'})
        response = self.client.patch(url, {'status': 'invalid'})

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_vehicle_components(self):
        """
        Scenario: Owner requests components for empty vehicle
        Given an authenticated owner of an empty vehicle
        When they request components by type
        Then they receive a not found response
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-by-type',
                     kwargs={'vin': self.empty_vehicle.vin, 'type_name': 'Engine'})
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_component_detail_success(self):
        """
        Scenario: Owner requests specific component details
        Given an authenticated owner
        When they request details of a specific component
        Then they receive the component details
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-detail',
                     kwargs={
                         'vin': self.vehicle.vin,
                         'type_name': 'Engine',
                         'name': 'Main engine'
                     })
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Main engine')
        self.assertEqual(response.data['status'], 0.8)

    def test_update_component_status_success(self):
        """
        Scenario: Owner updates specific component status
        Given an authenticated owner
        When they update a specific component's status
        Then the component status is updated
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-detail',
                     kwargs={
                         'vin': self.vehicle.vin,
                         'type_name': 'Engine',
                         'name': 'Main engine'
                     })
        response = self.client.patch(url, {'status': 0.6})

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 0.6)

    def test_update_component_status_invalid(self):
        """
        Scenario: Owner attempts to set invalid component status
        Given an authenticated owner
        When they attempt to set an invalid status value
        Then they receive a validation error
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = reverse('vehicle:components:component-detail',
                     kwargs={
                         'vin': self.vehicle.vin,
                         'type_name': 'Engine',
                         'name': 'Main engine'
                     })
        response = self.client.patch(url, {'status': 1.5})  # Invalid value > 1

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)