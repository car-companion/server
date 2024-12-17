from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from car_companion.models import Color

User = get_user_model()


class ColorListCreateViewTests(TestCase):
    """Test suite for the ColorListCreateView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        # Create some test colors
        self.colors = [
            Color.objects.create(
                name='Metallic Blue',
                hex_code='#0000FF',
                is_metallic=True,
                description='Deep metallic blue color'
            ),
            Color.objects.create(
                name='Pearl White',
                hex_code='#FFFFFF',
                is_metallic=True,
                description='Pearly white finish'
            ),
            Color.objects.create(
                name='Matte Black',
                hex_code='#000000',
                is_metallic=False,
                description='Classic matte black'
            )
        ]

        # URL for the view
        self.url = reverse('color-list-create')

    def test_authentication_required(self):
        """
        Scenario: Accessing endpoints without authentication
        Given an unauthenticated user
        When accessing the endpoints
        Then authentication should be required
        """
        # Test GET
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test POST
        color_data = {
            'name': 'Test Red',
            'hex_code': '#FF0000',
            'is_metallic': False
        }
        response = self.client.post(self.url, color_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_colors(self):
        """
        Scenario: Listing colors
        Given an authenticated user
        When requesting the color list
        Then all colors should be returned in correct format
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Three test colors

        # Verify serialization format
        expected_fields = {'name', 'hex_code', 'is_metallic', 'description'}
        self.assertEqual(set(response.data[0].keys()), expected_fields)

        # Verify some content
        color_names = {color['name'].lower() for color in response.data}
        self.assertEqual(
            color_names,
            {'metallic blue', 'pearl white', 'matte black'}
        )

    def test_create_color_success(self):
        """
        Scenario: Creating a color successfully
        Given an authenticated user
        When creating a color with valid data
        Then the color should be created
        And a 201 status code should be returned
        """
        self.client.force_authenticate(user=self.user)
        color_data = {
            'name': 'Forest Green',
            'hex_code': '#228B22',
            'is_metallic': False,
            'description': 'Deep forest green color'
        }

        response = self.client.post(self.url, color_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Forest green')  # Verify capitalization
        self.assertEqual(response.data['hex_code'], '#228B22')
        self.assertFalse(response.data['is_metallic'])

        # Verify color was actually created in database
        self.assertTrue(
            Color.objects.filter(name__iexact='Forest green').exists()
        )

    def test_create_color_validation_errors(self):
        """
        Scenario Outline: Creating colors with invalid data
        Given various invalid color data
        When attempting to validate through the endpoint
        Then appropriate validation errors should be returned
        """
        self.client.force_authenticate(user=self.user)

        # Ensure pre-existing color (case insensitive)
        existing_color_name = 'Metallic Blue'
        if not Color.objects.filter(name__iexact=existing_color_name).exists():
            Color.objects.create(
                name=existing_color_name,
                hex_code='#0000FF',
                is_metallic=True
            )

        invalid_cases = [
            # Missing name
            (
                {'name': '', 'hex_code': '#FFFFFF', 'is_metallic': False},
                'name',
                'This field may not be blank.'
            ),
            # Invalid hex code
            (
                {'name': 'Invalid Hex', 'hex_code': '123456', 'is_metallic': False},
                'hex_code',
                'Enter a valid hex color, eg. #000000'
            ),
            # Duplicate name (case insensitive)
            (
                {'name': 'METALLIC BLUE', 'hex_code': '#123456', 'is_metallic': False},
                'name',
                'Color name already exists.'
            ),
        ]

        for invalid_data, error_field, expected_error in invalid_cases:
            with self.subTest(invalid_data=invalid_data):
                response = self.client.post(self.url, invalid_data)

                # Expect 400 Bad Request
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(error_field, response.data)
                self.assertEqual(
                    str(response.data[error_field][0]),
                    expected_error
                )

    def test_create_duplicate_color(self):
        """
        Scenario: Creating a duplicate color
        Given an authenticated user
        When creating a color with a name that already exists
        Then appropriate error should be returned
        """
        self.client.force_authenticate(user=self.user)
        existing_name = self.colors[0].name

        color_data = {
            'name': existing_name,
            'hex_code': '#FF0000',  # Different hex code
            'is_metallic': False
        }

        response = self.client.post(self.url, color_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('already exists', str(response.data['name'][0]).lower())

    def test_create_color_case_insensitive(self):
        """
        Scenario: Creating a color with different case
        Given an authenticated user
        When creating a color with same name but different case
        Then appropriate error should be returned
        """
        self.client.force_authenticate(user=self.user)
        existing_name = self.colors[0].name.upper()  # Use uppercase version

        color_data = {
            'name': existing_name,
            'hex_code': '#FF0000',
            'is_metallic': False
        }

        response = self.client.post(self.url, color_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_serializer_class_selection(self):
        """
        Scenario: Testing serializer class selection
        Given different HTTP methods
        When accessing the view
        Then appropriate serializer should be used
        """
        self.client.force_authenticate(user=self.user)

        # Test GET request - should use ColorSerializer
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(
            response.data[0].get('description', None),
            str
        ))

        # Test POST request - should use ColorCreateSerializer
        color_data = {
            'name': 'New Color',
            'hex_code': '#123456',
            'is_metallic': False
        }
        response = self.client.post(self.url, color_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_color_with_whitespace(self):
        """
        Scenario: Creating a color with whitespace in name
        Given an authenticated user
        When creating a color with whitespace in name
        Then the name should be properly cleaned
        """
        self.client.force_authenticate(user=self.user)
        color_data = {
            'name': '  Racing  Red  ',
            'hex_code': '#FF0000',
            'is_metallic': False
        }

        response = self.client.post(self.url, color_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Racing red')  # Proper capitalization and spacing

    def test_create_color_with_minimum_data(self):
        """
        Scenario: Creating a color with minimum required data
        Given an authenticated user
        When creating a color with only required fields
        Then the color should be created successfully
        """
        self.client.force_authenticate(user=self.user)
        color_data = {
            'name': 'Minimal Red',
            'hex_code': '#FF0000'
        }

        response = self.client.post(self.url, color_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Minimal red')
        self.assertEqual(response.data['hex_code'], '#FF0000')
        self.assertFalse(response.data['is_metallic'])  # Should use default value
