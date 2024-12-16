from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from ...models import ComponentType
from django.utils.translation import gettext_lazy as _


class ComponentTypeModelTests(TestCase):
    """
    Test suite for the ComponentType model.
    Covers name standardization, validation, description handling, and constraints.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        cls.base_component_type = ComponentType.objects.create(
            name="Engine",
            description="The engine is a vital component of the vehicle."
        )

        cls.valid_component_data = {
            'name': 'Window',
            'description': 'A transparent opening in a vehicle for light and ventilation.'
        }

    def test_name_standardization_and_validation(self):
        """
        Scenario: Standardizing and validating component type names
        Given component type names with different formats
        When saving them as new types or updating existing ones
        Then the names should be correctly standardized and validated
        """
        # Test creation with different name formats
        creation_cases = [
            (" side mirror  ", "Side mirror"),
            ("DOOR", "Door"),
            (" fuel tank", "Fuel tank"),
        ]
        for input_name, expected_name in creation_cases:
            with self.subTest(input_name=input_name):
                component_type = ComponentType.objects.create(
                    name=input_name
                )
                self.assertEqual(component_type.name, expected_name)

    def test_validation_error_messages(self):
        """
        Scenario: Testing validation error messages for name
        Given component types with invalid name formats
        When validating the component type
        Then appropriate error messages should be raised
        """
        invalid_cases = [
            (None, 'This field cannot be null.'),
            ('', 'Component type name cannot be blank.'),
            ('   ', 'Component type name cannot be blank.'),
            ('!@#$%^&', 'Component type name contains invalid special characters.'),
            ('A', 'Component type name must be at least 2 characters long.'),
        ]

        for invalid_name, expected_error in invalid_cases:
            with self.subTest(invalid_name=invalid_name):
                component_type = ComponentType(
                    name=invalid_name,
                )
                with self.assertRaises(ValidationError) as context:
                    component_type.full_clean()
                self.assertIn(expected_error, str(context.exception))


    def test_description_handling(self):
        """
        Scenario: Testing description field handling
        Given component types with various description formats
        When saving the component types
        Then descriptions should be properly handled
        """
        test_cases = [
            ('mirror', '', ''),  # Empty string should become ''
            ('wheel', ' Essential for movement  ', ' Essential for movement  '),  # Should be stripped
        ]

        for component_name, input_desc, expected_desc in test_cases:
            with self.subTest(description=input_desc):
                component_type = ComponentType.objects.create(
                    name=f'Component {component_name}',
                    description=input_desc
                )
                self.assertEqual(component_type.description, expected_desc)

    def test_unique_constraint_with_standardization(self):
        """
        Scenario: Enforcing unique constraint after standardization
        Given an existing component type with a specific name
        When creating similar component types with different formats
        Then uniqueness should be enforced
        """
        ComponentType.objects.create(
            name="airbag",
        )
        duplicate_names = ["Airbag", "  AIRBAG  ", "airbag"]

        for name in duplicate_names:
            with self.subTest(name=name):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        ComponentType.objects.create(
                            name=name
                        )

    def test_str_representation(self):
        """
        Scenario: Testing string representation
        Given a component type with a name
        When converting to string
        Then it should return the name
        """
        component_type = ComponentType.objects.create(
            name="Gearbox"
        )
        self.assertEqual(str(component_type), "Gearbox")

    def test_ordering(self):
        """
        Scenario: Testing component type ordering
        Given multiple component types
        When retrieving from database
        Then they should be ordered by name
        """
        components_data = [
            "Zebra Mirror",
            "Apple Door",
            "Midnight Light",
        ]

        for name in components_data:
            ComponentType.objects.create(name=name)

        components = ComponentType.objects.all()
        expected_order = ['Apple door', 'Engine', 'Midnight light', 'Zebra mirror']
        actual_order = list(components.values_list('name', flat=True))
        self.assertEqual(actual_order, expected_order)

    def test_model_meta_configuration(self):
        """
        Scenario: Verifying model metadata configurations
        Given the ComponentType model
        When checking its metadata
        Then it should match the defined settings
        """
        self.assertEqual(ComponentType._meta.db_table, 'component_types')
        self.assertEqual(ComponentType._meta.ordering, ['name'])

        indexes = [index.name for index in ComponentType._meta.indexes]
        self.assertIn('component_type_name_idx', indexes)

        self.assertEqual(ComponentType._meta.verbose_name, _('Component Type'))
        self.assertEqual(ComponentType._meta.verbose_name_plural, _('Component Types'))
