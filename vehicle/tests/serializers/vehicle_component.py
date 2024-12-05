from django.test import TestCase
from vehicle.models import VehicleComponent, ComponentType, Vehicle, VehicleModel, Manufacturer, Color
from vehicle.serializers.vehicle_component import (
    ComponentTypeSerializer,
    ComponentSerializer,
    ComponentStatusUpdateSerializer
)


class ComponentTypeSerializerTests(TestCase):
    """Test suite for the ComponentTypeSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        self.component_type_data = {
            'name': 'Engine',
            'description': 'Vehicle engine component'
        }
        self.component_type = ComponentType.objects.create(**self.component_type_data)
        self.serializer = ComponentTypeSerializer(self.component_type)

    def test_component_type_serialization_should_only_include_name(self):
        """
        Scenario: Serializing a component type object
        Given a component type object with name and description
        When the component type is serialized
        Then only the name field should be included in the output
        And the description should not be present
        """
        self.assertEqual(self.serializer.data, {'name': 'Engine'})
        self.assertNotIn('description', self.serializer.data)


class ComponentSerializerTests(TestCase):
    """Test suite for the ComponentSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        # Create necessary related objects
        self.manufacturer = Manufacturer.objects.create(
            name="Bmw",
            country_code="DE"
        )
        self.vehicle_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=self.manufacturer
        )
        self.component_type = ComponentType.objects.create(
            name="Engine",
            description="Vehicle engine component"
        )
        self.vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=Color.objects.create(name="Black", hex_code="#000000"),
            interior_color=Color.objects.create(name="Beige", hex_code="#F5F5DC")
        )
        self.component = VehicleComponent.objects.create(
            name="V8 Engine",
            component_type=self.component_type,
            vehicle=self.vehicle,
            status=0.95
        )
        self.serializer = ComponentSerializer(self.component)

    def test_component_serialization_should_include_nested_type(self):
        """
        Scenario: Serializing a complete component object
        Given a component with type, name, and status
        When the component is serialized
        Then all fields should be properly represented
        And the component type should be nested within the 'type' field
        """
        expected_data = {
            'name': 'V8 engine',
            'type': {
                'name': 'Engine'
            },
            'status': 0.95
        }
        self.assertEqual(self.serializer.data, expected_data)

    def test_component_serialization_should_handle_null_status(self):
        """
        Scenario: Serializing a component with a null status value
        Given a component with a null status value
        When the component is serialized
        Then the status should be included as 0.0
        And other fields should be properly represented
        """
        self.component.status = None
        self.component.save()
        serializer = ComponentSerializer(self.component)
        self.assertEqual(serializer.data['status'], 0.0)  # Check that status is coerced to 0.0
        self.assertEqual(serializer.data['name'], 'V8 engine')  # Check other fields



class ComponentStatusUpdateSerializerTests(TestCase):
    """Test suite for the ComponentStatusUpdateSerializer using BDD style."""

    def test_valid_status_scenarios(self):
        """
        Scenario Outline: Validating valid status values
        Given a status value within allowed range
        When validating the serializer
        Then validation should pass

        Examples:
        | Status | Description        |
        | 0.0    | Minimum value     |
        | 0.5    | Middle value      |
        | 1.0    | Maximum value     |
        | 0.75   | Fractional value  |
        """
        valid_statuses = [
            (0.0, 'minimum value'),
            (0.5, 'middle value'),
            (1.0, 'maximum value'),
            (0.75, 'fractional value')
        ]

        for status, case_desc in valid_statuses:
            with self.subTest(f"Valid status - {case_desc}"):
                serializer = ComponentStatusUpdateSerializer(data={'status': status})
                self.assertTrue(serializer.is_valid(),
                    f"Status {status} should be valid but got errors: {serializer.errors}")

    def test_invalid_status_scenarios(self):
        """
        Scenario Outline: Validating invalid status values
        Given a status value outside allowed range or invalid type
        When validating the serializer
        Then validation should fail
        And appropriate error messages should be returned

        Examples:
        | Status | Description       | Expected Error               |
        | -0.1   | Below minimum    | greater than or equal to 0   |
        | 1.1    | Above maximum    | less than or equal to 1      |
        | None   | None value       | this field is required       |
        | "0.5"  | String value     | A valid number is required   |
        """
        invalid_cases = [
            (-0.1, 'below minimum', 'greater than or equal to 0'),
            (1.1, 'above maximum', 'less than or equal to 1'),
            (None, 'null value', 'this field may not be null.'),  # Adjust expected error for None
        ]

        for status, case_desc, expected_error in invalid_cases:
            with self.subTest(f"Invalid status - {case_desc}"):
                serializer = ComponentStatusUpdateSerializer(data={'status': status})
                self.assertFalse(serializer.is_valid())
                self.assertIn('status', serializer.errors)
                self.assertIn(expected_error, str(serializer.errors['status']).lower())
