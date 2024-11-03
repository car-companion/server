from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction, DataError
from ...models import Color
from django.utils.translation import gettext_lazy as _


class ColorModelTests(TestCase):
    """
    Test suite for the Color model.
    Covers name standardization, constraints, and translations.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        cls.base_color = Color.objects.create(name="red")

    def test_name_standardization_on_create_and_update(self):
        """
        Scenario: Standardizing color names on creation and update
        Given color names with different formats
        When saving them as new colors or updating existing ones
        Then the names should be correctly standardized
        """
        # Test creation
        creation_cases = [
            ("blue", "Blue"),
            ("  green  ", "Green"),
            ("YELLOW", "Yellow"),
            ("dArK gReY  ", "Dark grey"),
            ("   light blue   ", "Light blue"),
        ]
        for input_name, expected_name in creation_cases:
            with self.subTest(input_name=input_name):
                color = Color.objects.create(name=input_name)
                self.assertEqual(color.name, expected_name)

        # Test updates
        color = Color.objects.create(name="purple")
        update_cases = [
            ("  NEW PURPLE  ", "New purple"),
            ("royal PURPLE", "Royal purple"),
            ("   deep    purple   ", "Deep purple")
        ]
        for input_name, expected_name in update_cases:
            with self.subTest(input_name=input_name):
                color.name = input_name
                color.save()
                self.assertEqual(color.name, expected_name)

    def test_empty_null_and_whitespace_only_names(self):
        """
        Scenario: Handling empty, null, and whitespace-only names
        Given invalid color names (empty, null, whitespace-only)
        When attempting to save them
        Then validation errors should be raised with correct messages
        """
        invalid_names = [
            ("", "Color name cannot be blank."),
            (None, "Color name cannot be null."),
            ("   ", "Color name cannot be blank."),
        ]
        for name, expected_error in invalid_names:
            with self.subTest(name=name):
                color = Color(name=name)
                with self.assertRaises(ValidationError) as context:
                    color.full_clean()
                self.assertIn(expected_error, str(context.exception))

    def test_unique_constraint_with_standardization(self):
        """
        Scenario: Enforcing unique constraint after standardization
        Given an existing color with a specific name
        When creating similar colors with different formats
        Then uniqueness should be enforced, and IntegrityError should be raised
        """
        Color.objects.create(name="ruby red")
        duplicate_names = ["Ruby Red", "  RUBY RED  ", "ruby    red"]
        for name in duplicate_names:
            with self.subTest(name=name):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        Color.objects.create(name=name)

    def test_max_length_validation(self):
        """
        Scenario: Enforcing maximum length for color names
        Given color names of exactly and over the maximum length
        When attempting to save them
        Then names over the maximum length should raise a DataError
        """
        valid_name = "x" * 48 + "ed"
        valid_color = Color.objects.create(name=valid_name)
        self.assertEqual(len(valid_color.name), 50)

        invalid_name = "x" * 51
        with self.assertRaises(DataError):
            Color.objects.create(name=invalid_name)

    def test_whitespace_handling_and_edge_cases(self):
        """
        Scenario: Standardizing various whitespace and edge-case patterns
        Given color names with mixed whitespace and special characters
        When saving them
        Then the names should be properly standardized
        """
        test_cases = [
            ("multiple    spaces", "Multiple spaces"),
            ("tabs\t\tand    spaces", "Tabs and spaces"),
            ("new\nline  breaks", "New line breaks"),
            ("múltiple    ACCÉNTS    éé", "Múltiple accénts éé"),
        ]
        for input_name, expected_name in test_cases:
            with self.subTest(input_name=input_name):
                color = Color(name=input_name)
                color.save()
                self.assertEqual(color.name, expected_name)

    def test_model_meta_configuration(self):
        """
        Scenario: Verifying model metadata configurations
        Given the Color model
        When checking its metadata
        Then it should match the defined settings, including verbose names and indexes
        """
        self.assertEqual(Color._meta.db_table, 'vehicle_colors')
        self.assertEqual(Color._meta.ordering, ['name'])

        indexes = [index.name for index in Color._meta.indexes]
        self.assertIn('color_name_idx', indexes)

    def test_str_method(self):
        """
        Scenario: Testing string representation of Color
        Given a color instance with a specific name
        When converting it to a string
        Then it should return the standardized name
        """
        color = Color.objects.create(name="sunset RED")
        self.assertEqual(str(color), "Sunset red")

    def test_bulk_create_standardization_limitation(self):
        """
        Scenario: Verifying bulk create standardization limitation
        Given multiple colors to be created in bulk
        When using bulk_create
        Then names should remain unstandardized due to bulk_create bypassing save()
        """
        colors = [
            Color(name="sky BLUE"),
            Color(name="  forest GREEN"),
            Color(name="sunset RED  ")
        ]
        created_colors = Color.objects.bulk_create(colors)
        saved_colors = Color.objects.filter(
            name__in=['sky BLUE', '  forest GREEN', 'sunset RED  ']
        )
        self.assertEqual(saved_colors.count(), len(created_colors))

    def test_validation_error_messages(self):
        """
        Scenario: Ensuring appropriate validation error messages
        Given various invalid names for color instances
        When attempting to save them
        Then specific validation errors should be raised with the correct messages
        """
        error_cases = [
            (None, str(_("['Color name cannot be null.']"))),
            ("", str(_('Color name cannot be blank.'))),
            ("   ", str(_('Color name cannot be blank.'))),
            (self.base_color.name, str(_('A color with this name already exists.'))),
        ]
        for input_name, expected_error in error_cases:
            with self.subTest(input_name=input_name):
                color = Color(name=input_name)

                if input_name is None:
                    # Null name: Trigger validation via save
                    with self.assertRaises(ValidationError) as context:
                        color.save()
                    self.assertEqual(str(context.exception), expected_error)

                elif input_name == self.base_color.name:
                    # Duplicate name: Trigger uniqueness validation via save
                    with self.assertRaises(IntegrityError) as context:
                        color.save()
                    self.assertIn("duplicate key", str(context.exception).lower())

                else:
                    # Blank or whitespace-only names: Use full_clean() for field validation
                    with self.assertRaises(ValidationError) as context:
                        color.full_clean()
                    self.assertIn(expected_error, str(context.exception))

    def test_ordering(self):
        """
        Scenario: Testing ordering of colors
        Given multiple colors with names in random order
        When retrieving them from the database
        Then they should be ordered alphabetically by name
        """
        Color.objects.create(name="zebra white")
        Color.objects.create(name="apple red")
        Color.objects.create(name="midnight blue")

        colors = Color.objects.all()
        expected_order = ['Apple red', 'Midnight blue', 'Red', 'Zebra white']
        actual_order = list(colors.values_list('name', flat=True))
        self.assertEqual(actual_order, expected_order)

    def test_update_to_null_name(self):
        """
        Scenario: Updating an existing color name to null
        Given an existing color with a valid name
        When updating the name to null
        Then it should raise a ValidationError with the correct message
        """
        color = Color.objects.create(name="Valid Color")
        color.name = None
        with self.assertRaises(ValidationError) as context:
            color.save()
        self.assertEqual(
            str(context.exception),
            str(_("['Color name cannot be null.']"))
        )
