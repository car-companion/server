from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from car_companion.models import (
    Vehicle, VehicleModel, Manufacturer, Color,
    VehicleUserPreferences, VehicleComponent, ComponentType,
    ComponentPermission
)

User = get_user_model()


class VehiclePreferencesViewTests(TestCase):
    """Test suite for VehiclePreferencesView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create users
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@mail.com',
            password='testpass123'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@mail.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@mail.com',
            password='testpass123'
        )

        # Create manufacturer and model
        self.manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE"
        )
        self.vehicle_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=self.manufacturer
        )

        # Create colors
        self.interior_color = Color.objects.create(
            name="Beige",
            hex_code="#F5F5DC",
            is_metallic=False
        )
        self.exterior_color = Color.objects.create(
            name="Metallic Blue",
            hex_code="#0000FF",
            is_metallic=True
        )

        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color,
            owner=self.owner
        )

        # Create component and permission for access testing
        self.component_type = ComponentType.objects.create(name="Engine")
        self.component = VehicleComponent.objects.create(
            name="Main Engine",
            component_type=self.component_type,
            vehicle=self.vehicle
        )
        self.permission = ComponentPermission.objects.create(
            component=self.component,
            user=self.user,
            permission_type='read'
        )

        # Create preferences
        self.preferences = VehicleUserPreferences.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            nickname="My BMW",
            interior_color=self.interior_color,
            exterior_color=self.exterior_color
        )

        # URL for the view
        self.url = reverse('vehicle-preferences', kwargs={'vin': self.vehicle.vin})

    def test_authentication_required(self):
        """
        Scenario: Accessing endpoints without authentication
        Given an unauthenticated user
        When accessing any endpoint
        Then authentication should be required
        """
        # Test GET
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test PUT
        response = self.client.put(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test DELETE
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_preferences_success(self):
        """
        Scenario: Getting preferences successfully
        Given an authenticated user with access
        When requesting preferences
        Then preferences should be returned
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_preferences']['nickname'], 'My BMW')
        self.assertEqual(response.data['vin'], self.vehicle.vin)
        self.assertIn('model', response.data)
        self.assertIn('default_interior_color', response.data)
        self.assertIn('default_exterior_color', response.data)

    def test_get_preferences_access_denied(self):
        """
        Scenario: Getting preferences without access
        Given an authenticated user without access
        When requesting preferences
        Then access should be denied
        """
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('access', response.data['detail'].lower())

    def test_update_preferences_success(self):
        """
        Scenario: Updating preferences successfully
        Given an authenticated user with access
        When updating preferences with valid data
        Then preferences should be updated
        """
        self.client.force_authenticate(user=self.user)
        new_preferences = {
            'nickname': 'Updated BMW',
            'interior_color': {
                'name': 'New Interior',
                'hex_code': '#112233',
                'is_metallic': False
            }
        }

        response = self.client.put(self.url, new_preferences, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nickname'], 'Updated BMW')
        self.assertEqual(response.data['interior_color']['hex_code'], '#112233')

    def test_update_preferences_validation(self):
        """
        Scenario: Updating preferences with invalid data
        Given an authenticated user with access
        When updating preferences with invalid data
        Then appropriate validation errors should be returned
        """
        self.client.force_authenticate(user=self.user)

        invalid_cases = [
            # Invalid nickname
            (
                {'nickname': '@invalid@'},
                'nickname',
                'can only contain letters'
            ),
            # Invalid hex code
            (
                {
                    'interior_color': {
                        'name': 'Test',
                        'hex_code': 'invalid',
                        'is_metallic': False
                    }
                },
                'interior_color',
                'Invalid hex color code'
            ),
            # Empty update
            (
                {},
                'non_field_errors',
                'at least one preference'
            )
        ]

        for invalid_data, error_field, error_message in invalid_cases:
            with self.subTest(invalid_data=invalid_data):
                response = self.client.put(self.url, invalid_data, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertTrue(
                    any(error_message.lower() in str(error).lower()
                        for error in response.data.values())
                )

    def test_create_preferences(self):
        """
        Scenario: Creating new preferences
        Given an authenticated user with access
        When creating preferences for the first time
        Then preferences should be created
        """
        # Delete existing preferences
        self.preferences.delete()

        self.client.force_authenticate(user=self.user)
        new_preferences = {
            'nickname': 'My New BMW',
            'interior_color': {
                'name': 'Custom Interior',
                'hex_code': '#112233',
                'is_metallic': False
            }
        }

        response = self.client.put(self.url, new_preferences, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nickname'], 'My New BMW')
        self.assertTrue(
            VehicleUserPreferences.objects.filter(
                vehicle=self.vehicle,
                user=self.user
            ).exists()
        )

    def test_delete_preferences_success(self):
        """
        Scenario: Deleting preferences successfully
        Given an authenticated user with access
        When deleting preferences
        Then preferences should be removed
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            VehicleUserPreferences.objects.filter(
                vehicle=self.vehicle,
                user=self.user
            ).exists()
        )

    def test_delete_nonexistent_preferences(self):
        """
        Scenario: Deleting nonexistent preferences
        Given an authenticated user with access
        When deleting preferences that don't exist
        Then appropriate error should be returned
        """
        self.preferences.delete()

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('no preferences', response.data['detail'].lower())

    def test_access_by_component_permission(self):
        """
        Scenario: Accessing via component permission
        Given a user with component permission
        When accessing preferences
        Then access should be granted
        """
        # Create new vehicle without owner
        vehicle = Vehicle.objects.create(
            vin="WBA98765432109876",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color
        )

        # Create component and permission
        component = VehicleComponent.objects.create(
            name="Test Component",
            component_type=self.component_type,
            vehicle=vehicle
        )
        ComponentPermission.objects.create(
            component=component,
            user=self.user,
            permission_type='read'
        )

        url = reverse('vehicle-preferences', kwargs={'vin': vehicle.vin})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_with_existing_color(self):
        """
        Scenario: Updating preferences with existing color
        Given an authenticated user
        When updating with an existing color name
        Then the existing color should be used
        """
        self.client.force_authenticate(user=self.user)
        update_data = {
            'interior_color': {
                'name': self.interior_color.name,
                'hex_code': '#112233',  # Different hex code
                'is_metallic': True
            }
        }

        response = self.client.put(self.url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the color was updated
        self.interior_color.refresh_from_db()
        self.assertEqual(self.interior_color.hex_code, '#112233')
        self.assertTrue(self.interior_color.is_metallic)

    def test_update_preferences_no_access(self):
        """
        Scenario: User tries to update preferences without access
        Given an authenticated user without vehicle access
        When updating preferences
        Then access should be denied
        """
        self.client.force_authenticate(user=self.other_user)  # User without access
        update_data = {'nickname': 'No Access Test'}

        response = self.client.put(self.url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You don't have access", response.data['detail'])

    def test_update_preferences_with_exterior_color(self):
        """
        Scenario: Updating preferences with exterior color data
        Given an authenticated user with access
        When providing exterior color data
        Then the exterior color should be updated
        """
        self.client.force_authenticate(user=self.user)
        update_data = {
            'nickname': 'Updated Exterior Color',
            'exterior_color': {
                'name': 'Bright Red',
                'hex_code': '#FF0000',
                'is_metallic': True
            }
        }

        response = self.client.put(self.url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exterior_color']['name'], 'Bright red')
        self.assertEqual(response.data['exterior_color']['hex_code'], '#FF0000')

    def test_delete_preferences_no_access(self):
        """
        Scenario: User tries to delete preferences without access
        Given an authenticated user without vehicle access
        When deleting preferences
        Then access should be denied
        """
        self.client.force_authenticate(user=self.other_user)  # User without access
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You don't have access", response.data['detail'])
