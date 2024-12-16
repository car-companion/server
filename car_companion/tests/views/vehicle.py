from django.contrib.auth.models import User
from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from car_companion.models import Vehicle, VehicleModel, Manufacturer, Color
from car_companion.views.vehicle import VehicleViewSet


class VehicleViewSetTests(APITestCase):
    def setUp(self):
        """Set up test data"""
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

        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            vin='JH4KA3142KC889327',
            year_built=2020,
            model=self.model,
            outer_color=self.color,
            interior_color=self.color
        )

        # Set up API client
        self.client = APIClient()

    def get_url(self, route_name, **kwargs):
        return reverse(f'vehicle:{route_name}', kwargs=kwargs)

    def test_take_ownership_success(self):
        """
        Feature: Vehicle Ownership
        Scenario: User takes ownership of an unowned vehicle
        Given an authenticated user
        And an unowned vehicle
        When the user attempts to take ownership
        Then the ownership is granted successfully
        And the user receives owner permissions
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # When
        url = self.get_url('vehicle-take-ownership', vin=self.vehicle.vin)
        response = self.client.post(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.owner, self.user)
        self.assertTrue(self.user.has_perm('is_owner', self.vehicle))

    def test_take_ownership_already_owned(self):
        """
        Scenario: User attempts to take ownership of an already owned vehicle
        Given an authenticated user
        And a vehicle owned by another user
        When the user attempts to take ownership
        Then the request is forbidden
        """
        # Given
        self.client.force_authenticate(user=self.user)
        self.vehicle.owner = self.other_user
        self.vehicle.save()

        # When
        url = self.get_url('vehicle-take-ownership', vin=self.vehicle.vin)
        response = self.client.post(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_take_ownership_already_owner(self):
        """
        Scenario: Owner attempts to take ownership of their own vehicle
        Given an authenticated user
        And a vehicle they already own
        When the user attempts to take ownership
        Then they receive an already owned response
        """
        # Given
        self.client.force_authenticate(user=self.user)
        self.vehicle.owner = self.user
        self.vehicle.save()

        # When
        url = self.get_url('vehicle-take-ownership', vin=self.vehicle.vin)
        response = self.client.post(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_208_ALREADY_REPORTED)

    def test_disown_vehicle_success(self):
        """
        Scenario: Owner successfully disowns their vehicle
        Given an authenticated user
        And a vehicle they own
        When they attempt to disown the vehicle
        Then the ownership is removed
        And their owner permissions are removed
        """
        # Given
        self.client.force_authenticate(user=self.user)
        self.vehicle.owner = self.user
        self.vehicle.save()
        assign_perm('is_owner', self.user, self.vehicle)

        # When
        url = self.get_url('vehicle-disown', vin=self.vehicle.vin)
        response = self.client.delete(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.vehicle.refresh_from_db()
        self.assertIsNone(self.vehicle.owner)
        self.assertFalse(self.user.has_perm('is_owner', self.vehicle))

    def test_disown_not_owner(self):
        """
        Scenario: User attempts to disown a vehicle they don't own
        Given an authenticated user
        And a vehicle owned by another user
        When they attempt to disown the vehicle
        Then the request is forbidden
        """
        # Given
        self.client.force_authenticate(user=self.user)
        self.vehicle.owner = self.other_user
        self.vehicle.save()

        # When
        url = self.get_url('vehicle-disown', vin=self.vehicle.vin)
        response = self.client.delete(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_vehicles_list(self):
        """
        Scenario: User requests list of their owned vehicles
        Given an authenticated user
        And multiple vehicles with different owners
        When they request their vehicle list
        Then they receive only their owned vehicles
        """
        # Given
        self.client.force_authenticate(user=self.user)

        # Create additional test vehicles
        vehicle2 = Vehicle.objects.create(
            vin='22345678901234567',
            year_built=2021,
            model=self.model,
            outer_color=self.color,
            interior_color=self.color,
            owner=self.user
        )

        vehicle3 = Vehicle.objects.create(
            vin='32345678901234567',
            year_built=2022,
            model=self.model,
            outer_color=self.color,
            interior_color=self.color,
            owner=self.other_user
        )

        # When
        url = self.get_url('vehicle-my-vehicles')
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['vin'], vehicle2.vin)

    def test_update_nickname_success(self):
        """
        Scenario: Owner updates their vehicle's nickname
        Given an authenticated user
        And a vehicle they own
        When they update the nickname
        Then the nickname is changed successfully
        """
        # Given
        self.client.force_authenticate(user=self.user)
        self.vehicle.owner = self.user
        self.vehicle.save()

        # When
        url = self.get_url('vehicle-nickname', vin=self.vehicle.vin)
        response = self.client.put(url, {'nickname': 'MyNewNickname'})

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.nickname, 'MyNewNickname')

    def test_update_nickname_invalid(self):
        """
        Scenario: Owner attempts to set an invalid nickname
        Given an authenticated user
        And a vehicle they own
        When they attempt to set an invalid nickname
        Then they receive a validation error
        """
        # Given
        self.client.force_authenticate(user=self.user)
        self.vehicle.owner = self.user
        self.vehicle.save()

        # When
        url = self.get_url('vehicle-nickname', vin=self.vehicle.vin)
        response = self.client.put(url, {'nickname': '@#Invalid'})

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_vin_length(self):
        """
        Scenario: User attempts operations with invalid VIN
        Given an authenticated user
        When they attempt operations with an invalid VIN
        Then they receive a validation error
        """
        # Given
        self.client.force_authenticate(user=self.user)
        invalid_vin = '1' * 18  # Too long

        # Test take_ownership
        url = self.get_url('vehicle-take-ownership', vin=invalid_vin)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test disown
        url = self.get_url('vehicle-disown', vin=invalid_vin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access(self):
        """
        Scenario: Unauthenticated user attempts to access endpoints
        Given an unauthenticated user
        When they attempt to access protected endpoints
        Then they receive authentication errors
        """
        # Given - client not authenticated

        # Test take_ownership
        url = self.get_url('vehicle-take-ownership', vin=self.vehicle.vin)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test disown
        url = self.get_url('vehicle-disown', vin=self.vehicle.vin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test my_vehicles
        url = self.get_url('vehicle-my-vehicles')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test nickname update
        url = reverse('vehicle:vehicle-nickname', kwargs={'vin': self.vehicle.vin})
        response = self.client.put(url, {'nickname': 'NewNick'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vin_is_valid_method(self):
        """
        Scenario: Testing VIN validation method directly
        Given different VIN formats
        When checking their validity using vin_is_valid method
        Then appropriate boolean results should be returned
        """
        viewset = VehicleViewSet()

        # Test valid VINs
        valid_vins = [
            'JH4KA3142KC889327',  # Your test vehicle VIN
            'WBA12345678901234',  # Common format
            'NPA12345678901234'  # Different valid format
        ]
        for vin in valid_vins:
            with self.subTest(vin=vin):
                self.assertTrue(viewset.vin_is_valid(vin))
                self.assertTrue(viewset.vin_is_valid(vin.lower()))  # Test case insensitivity

        # Test invalid VINs
        invalid_vins = [
            'INVALID123',  # Too short
            'IO12345678901234Q',  # Contains invalid characters I, O, Q
            'AB1234567890123##',  # Contains special characters
        ]
        for vin in invalid_vins:
            with self.subTest(vin=vin):
                self.assertFalse(viewset.vin_is_valid(vin))
