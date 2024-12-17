from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from car_companion.models import (
    VehicleUserPreferences, Color, Vehicle, VehicleModel,
    Manufacturer
)
from car_companion.serializers.vehicle_preferences import (
    ColorSerializer, PreferencesSerializer, ColorFieldWithCreation,
    PreferencesUpdateSerializer, VehiclePreferencesSerializer
)

User = get_user_model()


class BasePreferencesTestCase(TestCase):
    """Base test case with common setup for preferences testing."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        # Create manufacturer and model
        self.manufacturer = Manufacturer.objects.create(
            name='BMW',
            country_code='DE'
        )
        self.vehicle_model = VehicleModel.objects.create(
            name='X5',
            manufacturer=self.manufacturer
        )

        # Create colors
        self.interior_color = Color.objects.create(
            name='Beige',
            hex_code='#F5F5DC',
            is_metallic=False
        )
        self.exterior_color = Color.objects.create(
            name='Metallic Blue',
            hex_code='#0000FF',
            is_metallic=True
        )

        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            vin='WBA12345678901234',
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color
        )

        # Create preferences
        self.preferences = VehicleUserPreferences.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            nickname='My Ride',
            interior_color=self.interior_color,
            exterior_color=self.exterior_color
        )


class PreferencesSerializerTests(BasePreferencesTestCase):
    """Test cases for the PreferencesSerializer."""

    def test_preferences_serialization(self):
        """
        Scenario: Serializing user preferences
        Given preferences with color relationships
        When serializing the preferences
        Then all nested relationships should be properly serialized
        """
        serializer = PreferencesSerializer(self.preferences)
        data = serializer.data

        self.assertEqual(data['nickname'], 'My Ride')
        self.assertEqual(data['interior_color']['name'], 'Beige')
        self.assertEqual(data['exterior_color']['name'], 'Metallic blue')

    def test_preferences_without_colors(self):
        """
        Scenario: Serializing preferences without colors
        Given preferences without color selections
        When serializing the preferences
        Then color fields should be null
        """
        prefs = VehicleUserPreferences.objects.create(
            vehicle=self.vehicle,
            user=self.other_user,
            nickname='Test Car'
        )
        serializer = PreferencesSerializer(prefs)
        data = serializer.data

        self.assertEqual(data['nickname'], 'Test Car')
        self.assertIsNone(data['interior_color'])
        self.assertIsNone(data['exterior_color'])


class ColorFieldWithCreationTests(BasePreferencesTestCase):
    """Test cases for the ColorFieldWithCreation custom field."""

    def test_hex_code_validation(self):
        """
        Scenario Outline: Validating hex code format
        Given various hex code inputs
        When validating through the field
        Then appropriate validation results should occur
        """
        field = ColorFieldWithCreation()

        valid_codes = ['#000000', '#FFFFFF', '#123ABC']
        invalid_codes = ['123456', '#1234', '#GGGGGG', '#12345H']

        # Test valid codes
        for code in valid_codes:
            with self.subTest(code=code):
                result = field.validate_hex_code(code)
                self.assertEqual(result, code.upper())

        # Test invalid codes
        for code in invalid_codes:
            with self.subTest(code=code):
                with self.assertRaises(serializers.ValidationError):
                    field.validate_hex_code(code)

    def test_get_or_create_color(self):
        """
        Scenario: Testing color creation or retrieval
        Given color data
        When getting or creating a color
        Then existing colors should be updated and new ones created
        """
        field = ColorFieldWithCreation()

        # Test creating new color
        new_color_data = {
            'name': 'New Red',
            'hex_code': '#FF0000',
            'is_metallic': True
        }
        new_color = field.get_or_create_color(new_color_data)
        self.assertEqual(new_color.name, 'New red')
        self.assertEqual(new_color.hex_code, '#FF0000')
        self.assertTrue(new_color.is_metallic)

        # Test updating existing color
        updated_data = {
            'name': 'New Red',  # Same name
            'hex_code': '#FF1111',  # Different hex
            'is_metallic': False  # Different metallic
        }
        updated_color = field.get_or_create_color(updated_data)
        self.assertEqual(updated_color.id, new_color.id)  # Same color
        self.assertEqual(updated_color.hex_code, '#FF1111')  # Updated
        self.assertFalse(updated_color.is_metallic)  # Updated

    def test_get_or_create_color_no_update(self):
        """
        Scenario: Testing get_or_create_color when no update is needed
        Given a color already exists with the same data
        When get_or_create_color is called
        Then the existing color is returned without updates
        """
        field = ColorFieldWithCreation()

        # Existing color in database
        existing_color = Color.objects.create(
            name="Test Color",
            hex_code="#ABCDEF",
            is_metallic=True
        )

        # Data that matches the existing color
        color_data = {
            'name': 'Test Color',
            'hex_code': '#ABCDEF',
            'is_metallic': True
        }

        # Call get_or_create_color
        with self.assertNumQueries(1):  # Expect a single query to check existence, no update
            retrieved_color = field.get_or_create_color(color_data)

        # Assert no updates occurred
        self.assertEqual(retrieved_color.id, existing_color.id)
        self.assertEqual(retrieved_color.hex_code, existing_color.hex_code)
        self.assertTrue(retrieved_color.is_metallic)


class PreferencesUpdateSerializerTests(BasePreferencesTestCase):
    """Test cases for the PreferencesUpdateSerializer."""

    def test_nickname_validation(self):
        """
        Scenario: Testing nickname validation
        Given various nickname formats
        When validating through the serializer
        Then appropriate validation results should occur
        """
        valid_data = [
            {'nickname': 'Valid Name'},
            {'nickname': 'Valid-Name-123'},
        ]
        invalid_data = [
            {'nickname': 'Invalid@Name'},
            {'nickname': 'Invalid!'},
            {'nickname': 'a'},  # Too short
            {'nickname': None}
        ]

        for data in valid_data:
            serializer = PreferencesUpdateSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for {data}")

        for data in invalid_data:
            serializer = PreferencesUpdateSerializer(data=data)
            self.assertFalse(serializer.is_valid(), f"Should fail for {data}")

    def test_empty_update_validation(self):
        """
        Scenario: Testing empty update validation
        Given no fields to update
        When validating the serializer
        Then it should raise validation error
        """
        serializer = PreferencesUpdateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_color_update(self):
        """
        Scenario: Testing color update
        Given new color data
        When updating preferences
        Then colors should be created or updated appropriately
        """
        data = {
            'interior_color': {
                'name': 'New Interior',
                'hex_code': '#112233',
                'is_metallic': False
            }
        }
        serializer = PreferencesUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class VehiclePreferencesSerializerTests(BasePreferencesTestCase):
    """Test cases for the VehiclePreferencesSerializer."""

    def test_vehicle_preferences_serialization(self):
        """
        Scenario: Testing full vehicle preferences serialization
        Given a vehicle with user preferences
        When serializing with authenticated user
        Then all nested data should be properly serialized
        """
        request = type('Request', (), {'user': self.user})
        serializer = VehiclePreferencesSerializer(
            self.vehicle,
            context={'request': request}
        )
        data = serializer.data

        self.assertEqual(data['vin'], 'WBA12345678901234')
        self.assertEqual(data['year_built'], 2023)
        self.assertEqual(data['model']['name'], 'X5')
        self.assertEqual(data['default_interior_color']['name'], 'Beige')
        self.assertIsNotNone(data['user_preferences'])

    def test_preferences_without_user(self):
        """
        Scenario: Testing preferences serialization without user
        Given a vehicle
        When serializing without authenticated user
        Then user preferences should be null
        """
        serializer = VehiclePreferencesSerializer(self.vehicle)
        self.assertIsNone(serializer.data['user_preferences'])

    def test_preferences_for_different_user(self):
        """
        Scenario: Testing preferences for different user
        Given a vehicle with preferences
        When serializing for a different user
        Then that user's preferences should be null
        """
        request = type('Request', (), {'user': self.other_user})
        serializer = VehiclePreferencesSerializer(
            self.vehicle,
            context={'request': request}
        )
        self.assertIsNone(serializer.data['user_preferences'])
