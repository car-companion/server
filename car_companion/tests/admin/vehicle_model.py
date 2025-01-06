from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ...admin.vehicle_model import VehicleModelAdmin
from ...models import VehicleModel, Manufacturer, ComponentType, ModelComponent


class VehicleModelAdminTests(TestCase):
    """
    Test suite for the VehicleModelAdmin and ModelComponentInline functionality.
    Tests all admin features including list display, filters, inlines, and custom methods.
    """

    def setUp(self):
        """
        Set up test environment
        Given a superuser exists in the system
        And test models exist in the database
        """
        # Create superuser
        user = get_user_model()
        self.admin_user = user.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create manufacturers
        self.manufacturer = Manufacturer.objects.create(
            name='BMW',
            country_code='DE'
        )
        self.another_manufacturer = Manufacturer.objects.create(
            name='Audi',
            country_code='DE'
        )

        # Create component types
        self.engine_type = ComponentType.objects.create(name='Engine')
        self.transmission_type = ComponentType.objects.create(name='Transmission')

        # Create vehicle model with components
        self.vehicle_model = VehicleModel.objects.create(
            name='X5',
            manufacturer=self.manufacturer
        )

        # Create default components
        self.components = [
            ModelComponent.objects.create(
                model=self.vehicle_model,
                name='V8 Engine',
                component_type=self.engine_type
            ),
            ModelComponent.objects.create(
                model=self.vehicle_model,
                name='8-Speed Auto',
                component_type=self.transmission_type
            )
        ]

        # Set up admin
        self.site = AdminSite()
        self.model_admin = VehicleModelAdmin(VehicleModel, self.site)
        self.client = Client()
        self.client.force_login(self.admin_user)

    @staticmethod
    def get_admin_url(action, *args):
        """Helper method to generate admin URLs"""
        return reverse(f'admin:car_companion_vehiclemodel_{action}', args=args)

    def test_list_display_configuration(self):
        """
        Scenario: Accessing the vehicle model list view in admin
        Given I am logged in as an admin user
        When I access the vehicle model list view
        Then I should see the list with all display fields
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.content, 'data-label="name"><a[^>]*>X5'.encode())
        self.assertContains(response, 'data-label="manufacturer">Bmw')
        self.assertContains(response, 'data-label="Default Components">2')  # Components count

    def test_manufacturer_filter(self):
        """
        Scenario: Testing manufacturer filter
        Given vehicle models from different manufacturers
        When filtering by manufacturer
        Then only models from selected manufacturer should be shown
        """
        # Create additional model for another manufacturer
        VehicleModel.objects.create(
            name='A4',
            manufacturer=self.another_manufacturer
        )

        url = self.get_admin_url('changelist')

        # Test BMW models
        response = self.client.get(url, {'manufacturer__id__exact': self.manufacturer.id})
        self.assertRegex(response.content, 'data-label="name"><a[^>]*>X5'.encode())
        self.assertNotRegex(response.content, 'data-label="name"><a[^>]*>A4'.encode())

        # Test Audi models
        response = self.client.get(url, {'manufacturer__id__exact': self.another_manufacturer.id})
        self.assertRegex(response.content, 'data-label="name"><a[^>]*>A4'.encode())
        self.assertNotRegex(response.content, 'data-label="name"><a[^>]*>X5'.encode())

    def test_search_functionality(self):
        """
        Scenario: Testing search functionality
        Given multiple vehicle models
        When searching using different fields
        Then appropriate results should be shown
        """
        # Create additional test models
        VehicleModel.objects.create(
            name='320i',
            manufacturer=self.manufacturer
        )
        VehicleModel.objects.create(
            name='A4',
            manufacturer=self.another_manufacturer
        )

        test_cases = [
            ('X5', ['X5'], ['320I', 'A4']),  # Search by model name
            ('Bmw', ['X5', '320I'], ['A4']),  # Search by manufacturer name
            ('Audi', ['A4'], ['X5', '320i']),  # Search by another manufacturer
        ]

        for search_term, should_contain, should_not_contain in test_cases:
            with self.subTest(search_term=search_term):
                url = self.get_admin_url('changelist')
                response = self.client.get(url, {'q': search_term})

                self.assertEqual(response.status_code, 200)
                for term in should_contain:
                    self.assertRegex(response.content, f'data-label="name"><a[^>]+>{term}'.encode())
                for term in should_not_contain:
                    self.assertNotRegex(response.content, f'data-label="name"><a[^>]+>{term}'.encode())

    def test_inline_components(self):
        """
        Scenario: Testing inline components functionality
        Given a vehicle model with components
        When accessing the change form
        Then component inline should be properly displayed
        """
        url = self.get_admin_url('change', self.vehicle_model.pk)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check if both existing components are displayed
        self.assertContains(response, 'V8 engine')
        self.assertContains(response, '8-speed auto')

    def test_components_count_display(self):
        """
        Scenario: Testing components count display
        Given a model with components
        When viewing the admin list
        Then the correct component count should be displayed
        """
        # Add another component to test count update
        ModelComponent.objects.create(
            model=self.vehicle_model,
            name='Brake System',
            component_type=self.engine_type
        )

        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertContains(response, 'data-label="Default Components">3')  # Updated count

    def test_inline_validation(self):
        """
        Scenario: Testing inline component validation
        Given I am adding/editing components
        When submitting invalid data
        Then appropriate validation errors should be shown
        """
        url = self.get_admin_url('change', self.vehicle_model.pk)

        # Try to submit with invalid component data
        invalid_data = {
            'name': 'X5 Updated',
            'manufacturer': self.manufacturer.id,
            'default_components-TOTAL_FORMS': '1',
            'default_components-INITIAL_FORMS': '0',
            'default_components-MIN_NUM_FORMS': '0',
            'default_components-MAX_NUM_FORMS': '1000',
            'default_components-0-name': '',  # Empty name should fail
            'default_components-0-component_type': self.engine_type.id,
            'default_components-0-model': self.vehicle_model.id,
        }

        response = self.client.post(url, invalid_data)
        self.assertContains(response, 'Component name cannot be blank')

    def test_autocomplete_fields(self):
        """
        Scenario: Testing autocomplete fields in inline
        Given I am on the model change form
        Then component_type should have autocomplete widget
        """
        url = self.get_admin_url('change', self.vehicle_model.pk)
        response = self.client.get(url)

        self.assertContains(response, 'autocomplete')
