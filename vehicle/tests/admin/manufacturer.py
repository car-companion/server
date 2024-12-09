from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext as _
from ...models import Manufacturer, VehicleModel
from ...admin import ManufacturerAdmin


class ManufacturerAdminTests(TestCase):
    """
    Test suite for the ManufacturerAdmin functionality.
    Tests all admin features including list display, filters, and custom methods.
    """

    def setUp(self):
        """
        Set up test environment
        Given a superuser exists in the system
        And test manufacturers exist in the database
        """
        # Create superuser
        user = get_user_model()
        self.admin_user = user.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create test manufacturer
        self.manufacturer = Manufacturer.objects.create(
            name='Bmw',
            country_code='DE',
            website_url='https://www.bmw.com',
            description='Bavarian Motor Works'
        )

        # Create some vehicle models for testing count
        VehicleModel.objects.create(name='X5', manufacturer=self.manufacturer)
        VehicleModel.objects.create(name='X3', manufacturer=self.manufacturer)

        # Set up admin
        self.site = AdminSite()
        self.manufacturer_admin = ManufacturerAdmin(Manufacturer, self.site)
        self.client = Client()
        self.client.force_login(self.admin_user)

    @staticmethod
    def get_admin_url(action, *args):
        """Helper method to generate admin URLs"""
        return reverse(f'admin:vehicle_manufacturer_{action}', args=args)

    def test_admin_list_view_access(self):
        """
        Scenario: Accessing the manufacturer list view in admin
        Given I am logged in as an admin user
        When I access the manufacturer list view
        Then I should see the list of manufacturers with all display fields
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.content, 'data-label="name"><a[^>]*>Bmw'.encode())
        self.assertContains(response, 'data-label="country code">DE')
        self.assertContains(response, 'Visit Website')
        self.assertContains(response, 'data-label="Models Count"><span title="2 models">2')

    def test_models_count_display(self):
        """
        Scenario: Testing models count display
        Given a manufacturer with associated models
        When viewing the admin list
        Then the correct model count should be displayed
        """
        # Add another model to test count update
        VehicleModel.objects.create(name='X7', manufacturer=self.manufacturer)

        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertContains(response, 'data-label="Models Count"><span title="3 models">3')  # Title and count attributes

    def test_website_display_with_and_without_url(self):
        """
        Scenario: Testing website display in admin
        Given manufacturers with and without website URLs
        When viewing the admin list
        Then website links should be properly displayed
        """
        # Create manufacturer without website
        no_website_manufacturer = Manufacturer.objects.create(
            name='Test Brand',
            country_code='US'
        )

        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        # Check manufacturer with website
        self.assertContains(response, 'href="https://www.bmw.com"')
        self.assertContains(response, 'Visit Website')

        # Check manufacturer without website
        self.assertContains(response, 'No website')

    def test_search_functionality(self):
        """
        Scenario: Testing search functionality
        Given multiple manufacturers
        When searching using different fields
        Then appropriate results should be shown
        """
        # Create additional test manufacturers
        Manufacturer.objects.create(
            name='Mercedes',
            country_code='DE',
            description='German luxury vehicles'
        )
        Manufacturer.objects.create(
            name='Toyota',
            country_code='JP',
            description='Japanese manufacturer'
        )

        test_cases = [
            ('Bmw', ['Bmw'], ['Mercedes', 'Toyota']),  # Search by name
            ('DE', ['Bmw', 'Mercedes'], ['Toyota']),  # Search by country
            ('luxury', ['Mercedes'], ['Bmw', 'Toyota']),  # Search by description
        ]

        for search_term, should_contain, should_not_contain in test_cases:
            with self.subTest(search_term=search_term):
                url = self.get_admin_url('changelist')
                response = self.client.get(url, {'q': search_term})

                self.assertEqual(response.status_code, 200)
                for term in should_contain:
                    self.assertContains(response, term)
                for term in should_not_contain:
                    self.assertNotContains(response, term)

    def test_country_filter(self):
        """
        Scenario: Testing country code filter
        Given manufacturers from different countries
        When filtering by country
        Then only manufacturers from selected country should be shown
        """
        # Create manufacturers from different countries
        Manufacturer.objects.create(
            name='Toyota',
            country_code='JP'
        )
        Manufacturer.objects.create(
            name='Mercedes',
            country_code='DE'
        )

        url = self.get_admin_url('changelist')

        # Test German manufacturers
        response = self.client.get(url, {'country_code__exact': 'DE'})
        self.assertContains(response, 'Bmw')
        self.assertContains(response, 'Mercedes')
        self.assertNotContains(response, 'Toyota')

        # Test Japanese manufacturers
        response = self.client.get(url, {'country_code__exact': 'JP'})
        self.assertContains(response, 'Toyota')
        self.assertNotContains(response, 'Bmw')
        self.assertNotContains(response, 'Mercedes')

    def test_fieldset_organization(self):
        """
        Scenario: Testing fieldset organization
        Given I am on the manufacturer add/change page
        When the form is rendered
        Then fields should be organized in correct fieldsets
        """
        url = self.get_admin_url('add')
        response = self.client.get(url)

        self.assertContains(response, _('Basic Information'))
        self.assertContains(response, _('Additional Information'))

        # # Check fields are in correct fieldsets
        # content = response.content.decode()
        # basic_info_pos = content.find('Basic Information')
        # additional_info_pos = content.find('Additional Information')
        #
        # # Basic Information fields
        # name_pos = content.find('name')
        # country_code_pos = content.find('country_code')
        #
        # # Additional Information fields
        # website_pos = content.find('website_url')
        # description_pos = content.find('description')

        # # Verify field positions relative to fieldset positions
        # self.assertTrue(name_pos > basic_info_pos)
        # self.assertTrue(country_code_pos > basic_info_pos)
        # self.assertTrue(website_pos > additional_info_pos)
        # self.assertTrue(description_pos > additional_info_pos)

    def test_readonly_fields(self):
        """
        Scenario: Testing readonly fields
        Given I am viewing a manufacturer
        When accessing the change form
        Then models count should be readonly
        """
        url = self.get_admin_url('change', self.manufacturer.pk)
        self.assertEqual(self.manufacturer.models.count(), 2)

        # Try to submit form with models_count
        response = self.client.post(url, {
            'name': 'Bmw Updated',
            'country_code': 'DE',
            'models_count': 10  # This should be ignored
        })

        self.manufacturer.refresh_from_db()
        self.assertEqual(self.manufacturer.models.count(), 2)  # Count shouldn't change
