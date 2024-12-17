from django.test import TestCase
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from car_companion.models import Color, Vehicle, VehicleModel, Manufacturer
from car_companion.serializers.color import ColorSerializer, ColorCreateSerializer


class ColorSerializerTests(TestCase):
    """Test suite for the ColorSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        self.color_data = {
            'name': 'Metallic blue',
            'hex_code': '#0000FF',
            'is_metallic': True,
            'description': 'Deep metallic blue color'
        }
        self.color = Color.objects.create(**self.color_data)
        self.serializer = ColorSerializer(self.color)

    def test_color_serialization_contains_expected_fields(self):
        """
        Scenario: Serializing a color object
        Given a color object with complete data
        When the color is serialized
        Then all expected fields should be present
        And no unexpected fields should be included
        """
        data = self.serializer.data
        expected_fields = {'name', 'hex_code', 'is_metallic', 'description'}

        self.assertEqual(set(data.keys()), expected_fields)
        self.assertEqual(data['name'], 'Metallic blue')  # Verify capitalization
        self.assertEqual(data['hex_code'], '#0000FF')
        self.assertTrue(data['is_metallic'])
        self.assertEqual(data['description'], 'Deep metallic blue color')

    def test_color_list_serialization(self):
        """
        Scenario: Serializing multiple colors
        Given multiple color objects
        When serializing as a list
        Then all colors should be properly serialized
        """
        Color.objects.create(
            name='Matte Black',
            hex_code='#000000',
            is_metallic=False
        )
        Color.objects.create(
            name='Pearl White',
            hex_code='#FFFFFF',
            is_metallic=True
        )

        colors = Color.objects.all()
        serializer = ColorSerializer(colors, many=True)

        self.assertEqual(len(serializer.data), 3)  # Including the one from setUp
        self.assertTrue(all(set(color.keys()) == {'name', 'hex_code', 'is_metallic', 'description'}
                            for color in serializer.data))

    def test_color_relationships(self):
        """
        Scenario: Serializing a color used in vehicles
        Given a color used by multiple vehicles
        When serializing the color
        Then the serialization should still be correct
        And should not include relationship data
        """
        # Create related objects
        manufacturer = Manufacturer.objects.create(
            name='Test Brand',
            country_code='US'
        )
        model = VehicleModel.objects.create(
            name='Test Model',
            manufacturer=manufacturer
        )

        # Create vehicles using the color
        Vehicle.objects.create(
            vin='1HGCM82633A123456',
            year_built=2023,
            model=model,
            outer_color=self.color,
            interior_color=self.color
        )
        Vehicle.objects.create(
            vin='1HGCM82633A789012',
            year_built=2023,
            model=model,
            outer_color=self.color,
            interior_color=self.color
        )

        serializer = ColorSerializer(self.color)
        self.assertEqual(
            set(serializer.data.keys()),
            {'name', 'hex_code', 'is_metallic', 'description'}
        )


class ColorCreateSerializerTests(TestCase):
    """Test suite for the ColorCreateSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        self.valid_color_data = {
            'name': 'Metallic Blue',
            'hex_code': '#0000FF',
            'is_metallic': True,
            'description': 'Deep metallic blue color'
        }

    def test_hex_code_validation(self):
        """
        Scenario Outline: Validating hex code format
        Given various hex code formats
        When validating through the serializer
        Then appropriate validation results should be returned

        Examples:
        | Hex Code  | Valid | Description          |
        | #000000   | Yes   | Valid lowercase      |
        | #FFFFFF   | Yes   | Valid uppercase      |
        | #123ABC   | Yes   | Valid mixed case     |
        | 123456    | No    | Missing hash         |
        | #1234     | No    | Too short           |
        | #GGGGGG   | No    | Invalid characters  |
        | #12345H   | No    | Invalid character   |
        """
        serializer = ColorCreateSerializer()

        valid_codes = ['#000000', '#FFFFFF', '#123ABC', '#abcdef']
        invalid_codes = [
            '123456',  # Missing hash
            '#1234',  # Too short
            '#GGGGGG',  # Invalid characters
            '#12345H',  # Invalid character
            'invalid',  # Completely invalid
            '#1234567',  # Too long
        ]

        # Test valid codes
        for code in valid_codes:
            with self.subTest(code=code):
                result = serializer.validate_hex_code(code)
                self.assertEqual(result, code.upper())

        # Test invalid codes
        for code in invalid_codes:
            with self.subTest(code=code):
                with self.assertRaises(serializers.ValidationError) as context:
                    serializer.validate_hex_code(code)
                self.assertEqual(
                    str(context.exception.args[0]),
                    'Invalid hex color code. Use format: #RRGGBB'
                )

    def test_name_validation(self):
        """
        Scenario Outline: Validating color name format
        Given various color names
        When validating through the serializer
        Then appropriate validation results should be returned

        Examples:
        | Name          | Valid | Result        | Description         |
        | blue          | Yes   | Blue          | Basic capitalization|
        | deep blue     | Yes   | Deep blue     | Multiple words     |
        | NAVY BLUE     | Yes   | Navy blue     | All caps           |
        | a             | No    | -             | Too short          |
        | " blue "      | Yes   | Blue          | Extra spaces       |
        """
        serializer = ColorCreateSerializer()

        test_cases = [
            ('blue', 'Blue', True),
            ('deep blue', 'Deep blue', True),
            ('NAVY BLUE', 'Navy blue', True),
            ('  blue  ', 'Blue', True),
            ('a', None, False),
            ('', None, False),
            ('   ', None, False),
        ]

        for input_name, expected_output, should_pass in test_cases:
            with self.subTest(input_name=input_name):
                if should_pass:
                    result = serializer.validate_name(input_name)
                    self.assertEqual(result, expected_output)
                else:
                    with self.assertRaises(serializers.ValidationError) as context:
                        serializer.validate_name(input_name)
                    self.assertEqual(
                        str(context.exception.args[0]),
                        'Color name must be at least 2 characters long.'
                    )

    def test_create_color_with_valid_data(self):
        """
        Scenario: Creating a new color with valid data
        Given valid color data
        When creating through the serializer
        Then the color should be created successfully
        And all fields should be properly formatted
        """
        serializer = ColorCreateSerializer(data=self.valid_color_data)
        self.assertTrue(serializer.is_valid())

        color = serializer.save()
        self.assertEqual(color.name, 'Metallic blue')
        self.assertEqual(color.hex_code, '#0000FF')
        self.assertTrue(color.is_metallic)
        self.assertEqual(color.description, 'Deep metallic blue color')

    def test_create_color_with_minimum_data(self):
        """
        Scenario: Creating a new color with minimum required data
        Given only required color data
        When creating through the serializer
        Then the color should be created successfully
        """
        min_data = {
            'name': 'Blue',
            'hex_code': '#0000FF',
            'is_metallic': False
        }

        serializer = ColorCreateSerializer(data=min_data)
        self.assertTrue(serializer.is_valid())

        color = serializer.save()
        self.assertEqual(color.name, 'Blue')
        self.assertEqual(color.hex_code, '#0000FF')
        self.assertFalse(color.is_metallic)
        self.assertIsNone(color.description)

    def test_color_validation_scenarios(self):
        """
        Scenario Outline: Validating invalid color data
        Given various invalid color data
        When attempting to validate the serializer
        Then appropriate validation errors should be raised

        Examples:
        | Field    | Value    | Expected Error                |
        | name     | ""       | This field may not be blank   |
        | hex_code | "invalid"| Invalid hex color code        |
        | hex_code | ""       | This field may not be blank   |
        """
        invalid_cases = [
            (
                {'name': '', 'hex_code': '#FFFFFF', 'is_metallic': False},
                'name',
                'This field may not be blank.'
            ),
            (
                {'name': 'Test', 'hex_code': 'invalid', 'is_metallic': False},
                'hex_code',
                'Enter a valid hex color, eg. #000000'
            ),
            (
                {'name': 'Test', 'hex_code': '', 'is_metallic': False},
                'hex_code',
                'This field may not be blank.'
            ),
        ]

        for invalid_data, invalid_field, expected_error in invalid_cases:
            with self.subTest(invalid_data=invalid_data):
                serializer = ColorCreateSerializer(data=invalid_data)
                self.assertFalse(serializer.is_valid())
                self.assertIn(invalid_field, serializer.errors)
                self.assertEqual(str(serializer.errors[invalid_field][0]), expected_error)

    def test_name_uniqueness_validation(self):
        """
        Scenario: Creating a color with a duplicate name (case-insensitive)
        Given an existing color name in the database
        When trying to create a color with the same name but different case
        Then the serializer should raise a validation error
        """
        # Pre-create a color with a specific name
        Color.objects.create(
            name='Metallic Blue',
            hex_code='#0000FF',
            is_metallic=True
        )

        # Attempt to create a color with the same name but different case
        duplicate_data = {
            'name': 'metallic blue',  # Same name, lowercase
            'hex_code': '#123456',
            'is_metallic': False
        }

        serializer = ColorCreateSerializer(data=duplicate_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertEqual(
            str(serializer.errors['name'][0]),
            'Color name already exists.'
        )
