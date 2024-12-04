from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction, DataError
from ...models import Color
from django.utils.translation import gettext_lazy as _


class ColorModelTests(TestCase):
    """
    Test suite for the Color model.
    Covers name standardization, hex code validation, metallic finish flag,
    description handling, and all model constraints.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        cls.base_color = Color.objects.create(
            name="red",
            hex_code="#FF0000",
            is_metallic=False,
            description="Basic red color"
        )

        cls.valid_color_data = {
            'name': 'Blue',
            'hex_code': '#0000FF',
            'is_metallic': True,
            'description': 'Deep blue color with metallic finish'
        }

    def test_name_standardization_and_validation(self):
        """
        Scenario: Standardizing and validating color names
        Given color names with different formats
        When saving them as new colors or updating existing ones
        Then the names should be correctly standardized and validated
        """
        # Test creation with different name formats
        creation_cases = [
            ("blue sky", "Blue sky", "#0000FF"),
            ("  forest GREEN  ", "Forest green", "#00FF00"),
            ("SUNSET_RED", "Sunset_red", "#FF0000"),
        ]
        for input_name, expected_name, hex_code in creation_cases:
            with self.subTest(input_name=input_name):
                color = Color.objects.create(
                    name=input_name,
                    hex_code=hex_code
                )
                self.assertEqual(color.name, expected_name)

    def test_validation_error_messages(self):
        """
        Scenario: Testing validation error messages for name and hex code
        Given colors with invalid name or hex code formats
        When validating the color
        Then appropriate error messages should be raised
        """
        test_cases = [
            # Test name validation
            (
                {'name': None, 'hex_code': '#FF0000'},
                'name',
                'This field cannot be null.'
            ),
            (
                {'name': '', 'hex_code': '#FF0000'},
                'name',
                'Color name cannot be blank.'
            ),
            (
                {'name': '   ', 'hex_code': '#FF0000'},
                'name',
                'Color name cannot be blank.'
            ),
            # Test hex_code validation
            (
                {'name': 'Test', 'hex_code': 'FF0000'},  # Missing #
                'hex_code',
                'Enter a valid hex color, eg. #000000'
            ),
            (
                {'name': 'Test', 'hex_code': '#FF00'},  # Too short
                'hex_code',
                'Enter a valid hex color, eg. #000000'
            ),
            (
                {'name': 'Test', 'hex_code': '#FF00000'},  # Too long
                'hex_code',
                'Enter a valid hex color, eg. #000000'
            ),
            (
                {'name': 'Test', 'hex_code': '#GG0000'},  # Invalid characters
                'hex_code',
                'Enter a valid hex color, eg. #000000'
            ),
            (
                {'name': 'Test', 'hex_code': None},  # Invalid characters
                'hex_code',
                'This field cannot be null.'
            ),
        ]

        for data, field, expected_message in test_cases:
            with self.subTest(data=data):
                color = Color(**data)
                with self.assertRaises(ValidationError) as context:
                    color.full_clean()
                errors = context.exception.error_dict
                self.assertIn(field, errors)
                self.assertEqual(
                    str(errors[field][0].message),
                    str(_(expected_message))
                )

    def test_hex_code_uppercase_conversion(self):
        """
        Scenario: Testing hex code uppercase conversion on save
        Given colors with lowercase or mixed case hex codes
        When saving the color
        Then hex codes should be converted to uppercase
        """
        test_cases = [
            ('#ff0000', '#FF0000'),
            ('#00ff00', '#00FF00'),
            ('#FFff00', '#FFFF00'),
            ('#abcdef', '#ABCDEF'),
        ]

        for input_hex, expected_hex in test_cases:
            with self.subTest(input_hex=input_hex):
                color = Color.objects.create(
                    name=f'Color {input_hex}',
                    hex_code=input_hex
                )
                self.assertEqual(color.hex_code, expected_hex)

    def test_color_creation_with_all_fields(self):
        """
        Scenario: Creating colors with all available fields
        Given complete color data including optional fields
        When creating new color instances
        Then all fields should be properly saved
        """
        color = Color.objects.create(**self.valid_color_data)

        self.assertEqual(color.name, 'Blue')
        self.assertEqual(color.hex_code, '#0000FF')
        self.assertTrue(color.is_metallic)
        self.assertEqual(color.description, 'Deep blue color with metallic finish')

    def test_metallic_finish_default(self):
        """
        Scenario: Testing metallic finish default value
        Given a new color without specifying metallic finish
        When creating the color
        Then metallic finish should default to False
        """
        color = Color.objects.create(
            name='Simple Red',
            hex_code='#FF0000'
        )
        self.assertFalse(color.is_metallic)

    def test_description_handling(self):
        """
        Scenario: Testing description field handling
        Given colors with various description formats
        When saving the colors
        Then descriptions should be properly handled
        """
        test_cases = [
            ('blue', '', ''),  # Empty string should become ''
            ('green', '   ', ''),  # Whitespace should become ''
            ('red', ' Some description  ', 'Some description'),  # Should be stripped
            ('black', None, None)  # None should stay None
        ]

        for color_name, input_desc, expected_desc in test_cases:
            with self.subTest(description=input_desc):
                color = Color.objects.create(
                    name=f'Color {color_name}',
                    hex_code='#000000',
                    description=input_desc
                )
                self.assertEqual(color.description, expected_desc)

    def test_unique_constraint_with_standardization(self):
        """
        Scenario: Enforcing unique constraint after standardization
        Given an existing color with a specific name
        When creating similar colors with different formats
        Then uniqueness should be enforced
        """
        Color.objects.create(
            name="ruby red",
            hex_code="#FF0000"
        )
        duplicate_names = ["Ruby Red", "  RUBY RED  ", "ruby    red"]

        for name in duplicate_names:
            with self.subTest(name=name):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        Color.objects.create(
                            name=name,
                            hex_code="#FF0001"
                        )

    def test_str_representation(self):
        """
        Scenario: Testing string representation
        Given a color with name and hex code
        When converting to string
        Then should return formatted string with name and hex code
        """
        color = Color.objects.create(
            name="Forest Green",
            hex_code="#00FF00"
        )
        expected_str = "Forest green (#00FF00)"
        self.assertEqual(str(color), expected_str)

    def test_ordering(self):
        """
        Scenario: Testing color ordering
        Given multiple colors
        When retrieving from database
        Then should be ordered by name
        """
        colors_data = [
            ("Zebra White", "#FFFFFF"),
            ("Apple Red", "#FF0000"),
            ("Midnight Blue", "#000080")
        ]

        for name, hex_code in colors_data:
            Color.objects.create(name=name, hex_code=hex_code)

        colors = Color.objects.all()
        expected_order = ['Apple red', 'Midnight blue',
                          'Red', 'Zebra white']
        actual_order = list(colors.values_list('name', flat=True))
        self.assertEqual(actual_order, expected_order)

    def test_model_meta_configuration(self):
        """
        Scenario: Verifying model metadata configurations
        Given the Color model
        When checking its metadata
        Then it should match the defined settings
        """
        self.assertEqual(Color._meta.db_table, 'vehicle_colors')
        self.assertEqual(Color._meta.ordering, ['name'])

        indexes = [index.name for index in Color._meta.indexes]
        self.assertIn('color_name_idx', indexes)

        self.assertEqual(Color._meta.verbose_name, _('Color'))
        self.assertEqual(Color._meta.verbose_name_plural, _('Colors'))
