from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction, DataError
from ...models import Manufacturer
from django.utils.translation import gettext_lazy as _


class ManufacturerModelTests(TestCase):
    """
    Test suite for the Manufacturer model.
    Covers name standardization, country code validation, website URL validation,
    and all model constraints.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        cls.base_manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE",
            website_url="https://www.bmw.com",
            description="Bavarian Motor Works"
        )

        cls.valid_manufacturer_data = {
            'name': 'Audi',
            'country_code': 'DE',
            'website_url': 'https://www.audi.com',
            'description': 'German automotive manufacturer'
        }

    def test_name_standardization_and_validation(self):
        """
        Scenario: Testing name standardization and validation
        Given manufacturer names with different formats
        When saving them
        Then they should be properly standardized and validated
        """
        test_cases = [
            ('mercedes benz', 'Mercedes benz'),  # Space handling
            ('  TOYOTA  ', 'Toyota'),  # Whitespace and case
            ('volkswagen    group', 'Volkswagen group'),  # Multiple spaces
        ]

        for input_name, expected_name in test_cases:
            with self.subTest(input_name=input_name):
                manufacturer = Manufacturer.objects.create(
                    name=input_name,
                    country_code='DE'
                )
                self.assertEqual(manufacturer.name, expected_name)

    def test_invalid_names(self):
        """
        Scenario: Testing invalid manufacturer names
        Given invalid manufacturer names
        When attempting to save
        Then appropriate validation errors should be raised
        """
        invalid_cases = [
            (None, 'Manufacturer name cannot be null.'),
            ('', 'Manufacturer name cannot be blank.'),
            ('A', 'Manufacturer name must be at least 2 characters long.'),
            ('Test@Name', 'Manufacturer name contains invalid special characters.'),
            ('Name!', 'Manufacturer name contains invalid special characters.'),
        ]

        for invalid_name, expected_error in invalid_cases:
            with self.subTest(invalid_name=invalid_name):
                manufacturer = Manufacturer(
                    name=invalid_name,
                    country_code='DE'
                )
                with self.assertRaises(ValidationError) as context:
                    manufacturer.full_clean()
                self.assertIn(expected_error, str(context.exception))

    def test_country_code_validation(self):
        """
        Scenario: Testing country code validation
        Given various country code formats
        When saving manufacturers
        Then validation should enforce correct format
        """
        valid_codes = ['DE', 'ir', 'FR', 'GB', 'US']
        invalid_codes = ['DEU', 'D', '12', 'G!', None, '']

        # Test valid codes
        for code in valid_codes:
            with self.subTest(code=code):
                manufacturer = Manufacturer.objects.create(
                    name=f'Manufacturer {code}',
                    country_code=code
                )
                self.assertEqual(manufacturer.country_code, code.upper())

        # Test invalid codes
        for code in invalid_codes:
            with self.subTest(code=code):
                with self.assertRaises(ValidationError):
                    manufacturer = Manufacturer(
                        name='Test Manufacturer',
                        country_code=code
                    )
                    manufacturer.full_clean()

    def test_website_url_validation(self):
        """
        Scenario: Testing website URL validation
        Given various URL formats
        When saving manufacturers
        Then validation should enforce correct URL format
        """
        valid_urls = [
            ('test', 'https://www.test.com'),
            ('test2', 'http://test.com'),
            ('test3', 'https://test.co.uk'),
            ('test4', None)  # URL is optional
        ]

        invalid_urls = [
            'not-a-url',
            'just.text',
            'https://',
        ]

        # Test valid URLs
        for manufacturer, url in valid_urls:
            with self.subTest(url=url):
                manufacturer = Manufacturer.objects.create(
                    name=f'Manufacturer {manufacturer}',
                    country_code='DE',
                    website_url=url
                )
                if url:
                    self.assertEqual(manufacturer.website_url, url)

        # Test invalid URLs
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValidationError):
                    manufacturer = Manufacturer(
                        name='Test Manufacturer',
                        country_code='DE',
                        website_url=url
                    )
                    manufacturer.full_clean()

    def test_description_handling(self):
        """
        Scenario: Testing description field handling
        Given various description formats
        When saving the manufacturer
        Then descriptions should be properly handled
        """
        test_cases = [
            ('  Test description  ', 'Test description'),  # Strips whitespace
            ('', ''),  # Empty string becomes ''
            (None, None),  # None remains None
            ('Valid description', 'Valid description'),  # Valid case
        ]

        for input_desc, expected_desc in test_cases:
            with self.subTest(description=input_desc):
                manufacturer = Manufacturer.objects.create(
                    name=f'Manufacturer {input_desc}',
                    country_code='DE',
                    description=input_desc
                )
                self.assertEqual(manufacturer.description, expected_desc)

    def test_unique_name_constraint(self):
        """
        Scenario: Testing unique name constraint
        Given an existing manufacturer name
        When creating another manufacturer with the same name
        Then it should raise an IntegrityError
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Manufacturer.objects.create(
                    name=self.base_manufacturer.name,
                    country_code='FR'
                )

    def test_string_representation(self):
        """
        Scenario: Testing string representation
        Given a manufacturer with name and country code
        When converting to string
        Then it should show name and country code in parentheses
        """
        manufacturer = Manufacturer.objects.create(
            name='Volvo',
            country_code='SE'
        )
        self.assertEqual(str(manufacturer), 'Volvo (SE)')

    def test_model_meta_configuration(self):
        """
        Scenario: Testing model metadata configuration
        Given the Manufacturer model
        When checking metadata
        Then it should match defined settings
        """
        self.assertEqual(Manufacturer._meta.db_table, 'manufacturers')
        self.assertEqual(Manufacturer._meta.ordering, ['name'])

        # Check indexes
        indexes = [index.name for index in Manufacturer._meta.indexes]
        self.assertIn('manufacturer_name_idx', indexes)
        self.assertIn('manufacturer_country_idx', indexes)

        # Check verbose names
        self.assertEqual(
            Manufacturer._meta.verbose_name,
            _('Manufacturer')
        )
        self.assertEqual(
            Manufacturer._meta.verbose_name_plural,
            _('Manufacturers')
        )

    def test_blank_fields(self):
        """
        Scenario: Testing blank field handling
        Given a manufacturer with blank optional fields
        When saving the manufacturer
        Then it should handle blank fields appropriately
        """
        manufacturer = Manufacturer.objects.create(
            name='Test Brand',
            country_code='US',
            website_url='',
            description=''
        )

        self.assertEqual(manufacturer.website_url, '')
        self.assertEqual(manufacturer.description, '')

    def test_field_max_lengths(self):
        """
        Scenario: Testing field max length constraints
        Given data exceeding max lengths
        When attempting to save
        Then it should raise appropriate validation errors
        """
        too_long_name = 'M' * 101  # Name max_length is 100
        too_long_country = 'USA'  # country_code max_length is 2
        too_long_url = 'https://www.' + 'x' * 250  # URL max_length is 255

        test_cases = [
            ('name', too_long_name),
            ('country_code', too_long_country),
            ('website_url', too_long_url),
        ]

        for field, value in test_cases:
            with self.subTest(field=field):
                data = self.valid_manufacturer_data.copy()
                data[field] = value

                manufacturer = Manufacturer(**data)
                with self.assertRaises((ValidationError, DataError)):
                    manufacturer.full_clean()
                    manufacturer.save()
