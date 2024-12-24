from django.test import TestCase
from car_companion.models import Vehicle, VehicleModel, Manufacturer, Color
from car_companion.serializers.vehicle import (
    VehicleSerializer,
    ColorSerializer,
    VehicleModelSerializer
)


class ColorSerializerTests(TestCase):
    """Test suite for the ColorSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        self.color_data = {
            'name': 'Midnight black',
            'hex_code': '#000000'
        }
        self.color = Color.objects.create(**self.color_data)
        self.serializer = ColorSerializer(self.color)

    def test_color_serialization_should_only_include_name(self):
        """
        Scenario: Serializing a color object
        Given a color object with name and hex_code
        When the color is serialized
        Then only the name field should be included in the output
        And the hex_code should not be present
        """
        self.assertEqual(self.serializer.data, {'name': 'Midnight black'})
        self.assertNotIn('hex_code', self.serializer.data)


class VehicleModelSerializerTests(TestCase):
    """Test suite for the VehicleModelSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        self.manufacturer = Manufacturer.objects.create(
            name="Bmw",
            country_code="DE"
        )
        self.model = VehicleModel.objects.create(
            name="X5",
            manufacturer=self.manufacturer
        )
        self.serializer = VehicleModelSerializer(self.model)

    def test_vehicle_model_serialization_should_include_manufacturer_name(self):
        """
        Scenario: Serializing a vehicle model
        Given a vehicle model with an associated manufacturer
        When the model is serialized
        Then the output should include the model name
        And the manufacturer should be represented as a string
        """
        expected_data = {
            'name': 'X5',
            'manufacturer': str(self.manufacturer)
        }
        self.assertEqual(self.serializer.data, expected_data)


class VehicleSerializerTests(TestCase):
    """Test suite for the VehicleSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        self.manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE"
        )
        self.vehicle_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=self.manufacturer
        )
        self.outer_color = Color.objects.create(
            name="Midnight Black",
            hex_code="#000000"
        )
        self.interior_color = Color.objects.create(
            name="Cream White",
            hex_code="#FFFFFF"
        )
        self.vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.outer_color,
            interior_color=self.interior_color,
        )

    def test_vehicle_serialization_should_include_nested_relationships(self):
        """
        Scenario: Serializing a complete vehicle object
        Given a vehicle with model, colors, and other attributes
        When the vehicle is serialized
        Then all nested relationships should be properly represented
        And sensitive fields should be excluded
        """
        serializer = VehicleSerializer(self.vehicle)
        expected_data = {
            'vin': 'WBA12345678901234',
            'year_built': 2023,
            'model': {
                'name': 'X5',
                'manufacturer': str(self.manufacturer)
            },
            'default_exterior_color': {
                'name': 'Midnight black'
            },
            'default_interior_color': {
                'name': 'Cream white'
            }
        }

        self.assertEqual(serializer.data, expected_data)

    def test_vehicle_vin_validation(self):
        """
        Scenario Outline: Validating vehicle VIN format
        Given a vehicle data with an invalid VIN
        When attempting to validate the serializer
        Then validation should fail
        And appropriate error messages should be returned

        Examples:
        | VIN               | Description              |
        | WBA123456        | Too short                |
        | WBA1234567890I234| Contains invalid char    |
        | <empty>          | Empty string             |
        """
        invalid_vin_cases = [
            ('WBA123456', 'too short'),
            ('WBA1234567890I234', 'contains invalid character'),
            ('', 'empty string')
        ]

        base_data = {
            'year_built': 2024,
            'model': self.vehicle_model.id,
            'outer_color': self.outer_color.id,
            'interior_color': self.interior_color.id,
        }

        for invalid_vin, case_desc in invalid_vin_cases:
            with self.subTest(f"VIN validation - {case_desc}"):
                data = {**base_data, 'vin': invalid_vin}
                serializer = VehicleSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('vin', serializer.errors)
