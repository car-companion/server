from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth import get_user_model

from vehicle.models.vehicle import Vehicle

User = get_user_model()


class VehicleOwnershipTests(APITestCase):
    """
    Test suite for the vehicle ownership views.
    Covers taking ownership of a vehicle, disowning an owned vehicle
    and listing all vehicles a user owns.
    """
    fixtures = ['fixture_ownership.json']

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite and check initial db state."""

        # Endpoints being tested in this TestCase
        cls.API_TAKE_OWNERSHIP = reverse_lazy('vehicle:take-ownership')
        cls.API_DISOWN         = reverse_lazy('vehicle:disown')
        cls.API_MY_VEHICLES    = reverse_lazy('vehicle:my-vehicles')

        # Other endpoints required
        cls.API_LOGIN = reverse_lazy('auth:jwt-create')
        cls.API_USERNAME_FROM_TOKEN = reverse_lazy('auth:user-me')

        # Users we will be using for testing in this suite
        cls.users = [
            {'username': 'testuser', 'password': 'user1234'},
            {'username': 'testuser2', 'password': 'user1234'},
        ]

        # Check if they exist in the DB
        users_retrieved = User.objects.filter(username__in=[user['username'] for user in cls.users])
        assert len(users_retrieved) == len(cls.users)

        # Vehicle VINs we will be using for testing in this suite
        cls.vins = [
            'YV1MS672482401129',
            '5UXKR2C58F0801672',
        ]
        cls.invalid_vin = 'some invalid vin'
        cls.valid_but_nonexistent_vin = '1G4EZ5770G0011002'

        # Check if they exist in the DB
        vehicles_retrieved = Vehicle.objects.filter(vin__in=cls.vins)
        assert len(vehicles_retrieved) == len(cls.vins)


    def login(self, username, password):
        """Utility function for obtaining and storing an auth token"""
        response = self.client.post(self.API_LOGIN, {'username': username, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {response.data['access']}')


    def logout(self):
        """Utility function for removing the auth token from logged in user"""
        self.client.credentials()


    def get_my_username(self):
        """
        Returns currently logged in user's username from their token
        or None if not logged in.
        """
        return self.client.get(self.API_USERNAME_FROM_TOKEN).data.get('username', None)


    def setUp(self):
        """We will always authenticate as the first user and auth/deauth as others as needed"""
        self.login(**self.users[0])


    def tearDown(self):
        """ """
        self.logout()


    def test_take_ownership(self):
        """
        Scenario: User wants to take ownership of a vehicle that already exists in the system
        Given an authenticated user
        When a POST request is made to API_TAKE_OWNERSHIP with:
            {
                "vin": "VIN_OF_A_VEHICLE",
            }
        Then the user should be given ownership of the vehicle or rejected
        """
        test_cases = [
            (
                {},
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                {'vin': self.invalid_vin},
                status.HTTP_404_NOT_FOUND,
            ),
            (
                {'vin': self.valid_but_nonexistent_vin},
                status.HTTP_404_NOT_FOUND,
            ),
            (
                {'vin': self.vins[0]},
                status.HTTP_200_OK,
            ),
            (
                {'vin': self.vins[0]},
                status.HTTP_204_NO_CONTENT,
            )
        ]
        for data, code in test_cases:
            with self.subTest(data=data, code=code):

                # Try to take ownership of the vehicle
                resp = self.client.post(self.API_TAKE_OWNERSHIP, data=data, format='json')
                self.assertEqual(resp.status_code, code)

                # Check that owner is set in db
                if status.is_success(resp.status_code):
                    user = User.objects.get(username=self.get_my_username())
                    vehicle = Vehicle.objects.get(vin=data['vin'])
                    self.assertEqual(vehicle.owner, user)
                    self.assertTrue(user.has_perm('vehicle.is_owner', vehicle))

        
        # Second user tries to take ownership of the first's vehicle
        # but only succeeds in taking the second one
        self.logout()
        self.login(**self.users[1])

        test_cases = [
            (
                {'vin': self.vins[0]},
                403,
            ),
            (
                {'vin': self.vins[1]},
                200,
            ),
        ]
        for data, code in test_cases:
            with self.subTest(data=data, code=code):

                # Try to take ownership of the vehicle
                resp = self.client.post(self.API_TAKE_OWNERSHIP, data=data, format='json')
                self.assertEqual(resp.status_code, code)

                # Check that owner is set in db
                if status.is_success(resp.status_code):
                    user = User.objects.get(username=self.get_my_username())
                    vehicle = Vehicle.objects.get(vin=data['vin'])
                    self.assertEqual(vehicle.owner, user)
                    self.assertTrue(user.has_perm('vehicle.is_owner', vehicle))


    def test_take_ownership_unauthenticated(self):
        """
        Scenario: User wants to take ownership of a vehicle that already exists in the system
        Given an unauthenticated user
        When a POST request is made to API_TAKE_OWNERSHIP with:
            {
                "vin": "VIN_OF_A_VEHICLE",
            }
        Then the user should always be denied
        """
        # Deauthenticate user
        self.logout()

        test_cases = [
            (
                {'vin': self.vins[1]},
            ),
            (
                {'vin': self.invalid_vin},
            ),
            (
                {'vin': self.valid_but_nonexistent_vin},
            ),
            (
                {},
            ),
        ]
        for data in test_cases:
            with self.subTest(data=data):

                # Try to take ownership of the vehicle
                resp = self.client.post(self.API_TAKE_OWNERSHIP, data=data, format='json')
                self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_disown(self):
        """
        Scenario: User wants to disown a vehicle he already owns
        Given an authenticated user
        When a POST request is made to API_DISOWN with:
            {
                "vin": "VIN_OF_A_VEHICLE",
            }
        Then vehicle should be successfully disowned or the user rejected
        """
        # User is owner of the first vehicle
        resp = self.client.post(self.API_TAKE_OWNERSHIP, data={'vin': self.vins[0]}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        test_cases = [
            (
                {},
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                {'vin': self.invalid_vin},
                status.HTTP_404_NOT_FOUND,
            ),
            (
                {'vin': self.valid_but_nonexistent_vin},
                status.HTTP_404_NOT_FOUND,
            ),
            (
                {'vin': self.vins[1]},
                status.HTTP_403_FORBIDDEN,
            ),
            (
                {'vin': self.vins[0]},
                status.HTTP_204_NO_CONTENT,
            )
        ]
        for data, code in test_cases:
            with self.subTest(data=data, code=code):
                
                # Try to disown the vehicle
                resp = self.client.post(self.API_DISOWN, data=data, format='json')
                self.assertEqual(resp.status_code, code)

                # Ensure that owner is cleared from db
                if status.is_success(resp.status_code):
                    user = User.objects.get(username=self.get_my_username())
                    vehicle = Vehicle.objects.get(vin=data['vin'])
                    self.assertEqual(vehicle.owner, None)
                    self.assertFalse(user.has_perm('vehicle.is_owner', vehicle))



    def test_my_vehicles(self):
        """
        Scenario: User wants to see vehicles he owns
        Given an authenticated user
        When a GET request is made to API_MY_VEHICLES
        Then a list with zero or more VINs should be returned as:
            {
                "vins": [
                    "VIN123",
                    "VIN456"
                ]
            }
        """
        # Check that there are no owned vehicles
        resp = self.client.get(self.API_MY_VEHICLES)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        vehicles = [vehicle['vin'] for vehicle in (resp.data or [])]
        self.assertEqual(set(vehicles), set())

        # Take ownership of some vehicles
        for vin in self.vins[:2]:
            resp = self.client.post(self.API_TAKE_OWNERSHIP, data={'vin': vin}, format='json')
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Retrieve those vehicles
        test_cases = [
            (
                {},
                status.HTTP_200_OK,
            ),
            (
                {"data": "does", "not": "matter", "123": "456"},
                status.HTTP_200_OK,
            )
        ]
        for data, code in test_cases:
            with self.subTest(data=data, code=code):

                resp = self.client.get(self.API_MY_VEHICLES, data)
                self.assertEqual(resp.status_code, code)
                # Extract VINs from response and compare to our list
                vehicles = [vehicle['vin'] for vehicle in (resp.data or [])]
                self.assertEqual(set(vehicles), set(self.vins))
