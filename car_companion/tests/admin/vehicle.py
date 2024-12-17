from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext as _
from ...models import (
    Vehicle, VehicleComponent, VehicleModel, Manufacturer,
    Color, ComponentType, ModelComponent
)
from ...admin.vehicle import VehicleAdmin, VehicleComponentInline


class VehicleAdminTests(TestCase):
    """
    Test suite for the VehicleAdmin and VehicleComponentInline functionality.
    """

    def setUp(self):
        """Set up test environment"""
        # Create superuser
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
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
        self.exterior_color = Color.objects.create(
            name='Black',
            hex_code='#000000'
        )
        self.interior_color = Color.objects.create(
            name='Beige',
            hex_code='#F5F5DC'
        )

        # Create component types and model components
        self.engine_type = ComponentType.objects.create(name='Engine')
        self.transmission_type = ComponentType.objects.create(name='Transmission')

        # Create default components for the model
        self.model_components = [
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

        # Create base vehicle
        self.vehicle = Vehicle.objects.create(
            vin='WBA12345678901234',
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color,
        )

        # Set up admin
        self.site = AdminSite()
        self.vehicle_admin = VehicleAdmin(Vehicle, self.site)
        self.client = Client()
        self.client.force_login(self.admin_user)

    @staticmethod
    def get_admin_url(action, *args):
        """Helper method to generate admin URLs"""
        return reverse(f'admin:car_companion_vehicle_{action}', args=args)

    def test_list_display_and_select_related(self):
        """
        Scenario: Testing list display with select_related optimization
        Given a vehicle in the database
        When accessing the list view
        Then all fields should be displayed with minimal queries
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'WBA12345678901234')  # VIN
        self.assertContains(response, 'data-label="Year Built">2023')  # Year
        self.assertContains(response, 'data-label="Model">X5')  # Model
        self.assertContains(response, 'data-label="Manufacturer">Bmw')  # Manufacturer
        self.assertContains(response, 'data-label="Components">0')  # Components count

    def test_filters(self):
        """
        Scenario: Testing list filters
        Given multiple vehicles
        When applying filters
        Then only matching vehicles should be shown
        """
        # Create another manufacturer and model
        another_manufacturer = Manufacturer.objects.create(
            name='Audi',
            country_code='DE'
        )
        another_model = VehicleModel.objects.create(
            name='A4',
            manufacturer=another_manufacturer
        )

        # Create another vehicle
        Vehicle.objects.create(
            vin='WAU12345678901234',
            year_built=2017,
            model=another_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color
        )

        url = self.get_admin_url('changelist')

        # Test year filter
        response = self.client.get(url, {'year_built__exact': '2023'})
        self.assertContains(response, 'WBA12345678901234')
        self.assertNotContains(response, 'WAU12345678901234')

        # Test manufacturer filter
        response = self.client.get(
            url,
            {'model__manufacturer__id__exact': self.manufacturer.id}
        )
        self.assertContains(response, 'data-label="Manufacturer">Bmw')
        self.assertNotContains(response, 'data-label="Manufacturer">Audi')

        # Test model filter
        response = self.client.get(
            url,
            {'model__id__exact': self.vehicle_model.id}
        )
        self.assertContains(response, 'data-label="Model">X5')
        self.assertNotContains(response, 'data-label="Model">A4')

    def test_search_functionality(self):
        """
        Scenario: Testing search functionality
        Given multiple vehicles
        When searching using different fields
        Then appropriate results should be shown
        """
        # Create another vehicle for search testing
        Vehicle.objects.create(
            vin='WAU98765432109876',
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color,
        )

        test_cases = [
            ('WBA123', ['WBA12345678901234'], ['WAU98765432109876']),
            ('X5', ['WBA12345678901234', 'WAU98765432109876'], []),
            ('BMW', ['WBA12345678901234', 'WAU98765432109876'], [])
        ]

        url = self.get_admin_url('changelist')
        for search_term, should_contain, should_not_contain in test_cases:
            with self.subTest(search_term=search_term):
                response = self.client.get(url, {'q': search_term})
                for term in should_contain:
                    self.assertContains(response, term)
                for term in should_not_contain:
                    self.assertNotContains(response, term)

    def test_fieldsets_and_inlines(self):
        """
        Scenario: Testing fieldset organization and inline display
        Given I am on the vehicle add/change form
        When the form is rendered
        Then fields should be organized in correct fieldsets
        And inline components should be displayed
        """
        url = self.get_admin_url('change', self.vehicle.vin)
        response = self.client.get(url)

        # Test fieldsets
        self.assertContains(response, _('Vehicle Information'))
        self.assertContains(response, _('Appearance'))

        # Test fields presence
        form_fields = [
            'vin', 'year_built', 'model',
            'outer_color', 'interior_color'
        ]
        for field in form_fields:
            self.assertContains(response, field)

        # Test inline
        self.assertContains(response, 'component_type')
        self.assertContains(response, 'status')

    def test_default_components_creation(self):
        """
        Scenario: Testing automatic creation of default components
        Given a vehicle model with default components
        When creating a new vehicle
        Then default components should be automatically created
        """
        new_vehicle_data = {
            'vin': 'WBA98765432109876',
            'year_built': 2023,
            'model': self.vehicle_model.id,
            'outer_color': self.exterior_color.id,
            'interior_color': self.interior_color.id,
            'components-TOTAL_FORMS': '0',
            'components-INITIAL_FORMS': '0',
            'components-MIN_NUM_FORMS': '0',
            'components-MAX_NUM_FORMS': '1000',
        }

        url = self.get_admin_url('add')
        response = self.client.post(url, new_vehicle_data)
        self.assertEqual(response.status_code, 302)  # Successful redirect

        # Check if default components were created
        new_vehicle = Vehicle.objects.get(vin='WBA98765432109876')
        self.assertEqual(new_vehicle.components.count(), 2)

        component_names = set(new_vehicle.components.values_list('name', flat=True))
        expected_names = {'V8 engine', '8-speed auto'}
        self.assertEqual(component_names, expected_names)

    def test_inline_component_validation(self):
        """
        Scenario: Testing inline component validation
        Given I am adding/editing vehicle components
        When submitting invalid data
        Then appropriate validation errors should be shown
        """
        url = self.get_admin_url('change', self.vehicle.vin)

        invalid_data = {
            'vin': self.vehicle.vin,
            'year_built': 2023,
            'model': self.vehicle_model.id,
            'outer_color': self.exterior_color.id,
            'interior_color': self.interior_color.id,
            'components-TOTAL_FORMS': '1',
            'components-INITIAL_FORMS': '0',
            'components-MIN_NUM_FORMS': '0',
            'components-MAX_NUM_FORMS': '1000',
            'components-0-name': '',  # Empty name should fail
            'components-0-component_type': self.engine_type.id,
            'components-0-vehicle': self.vehicle.vin,
            'components-0-status': 2.0,  # Invalid status
        }

        response = self.client.post(url, invalid_data)
        self.assertContains(response, 'Component name cannot be blank')
        self.assertContains(response, 'Status cannot be greater than 1')

    def test_autocomplete_fields(self):
        """
        Scenario: Testing autocomplete fields configuration
        Given I am on the vehicle form
        Then autocomplete fields should be properly configured
        """
        url = self.get_admin_url('add')
        response = self.client.get(url)

        autocomplete_fields = ['model', 'outer_color', 'interior_color']
        for field in autocomplete_fields:
            self.assertContains(response, f'field-{field}')

    def test_computed_fields(self):
        """
        Scenario: Testing computed fields in admin
        Given a vehicle with components
        When viewing in admin
        Then computed fields should show correct values
        """
        # Create some components
        VehicleComponent.objects.create(
            vehicle=self.vehicle,
            name='Test Component',
            component_type=self.engine_type,
            status=0.5
        )

        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        # Test manufacturer display
        self.assertEqual(
            self.vehicle_admin.get_manufacturer(self.vehicle),
            self.manufacturer
        )

        # Test components count
        self.assertEqual(
            self.vehicle_admin.get_components_count(self.vehicle),
            1
        )

    def test_create_vehicle_creates_default_components(self):
        """
        Scenario: Testing automatic creation of default components upon vehicle creation
        Given a vehicle model with default components
        When creating a new vehicle
        Then default components should be automatically created
        """
        new_vehicle_data = {
            'vin': 'WBA98765432109876',
            'year_built': 2023,
            'model': self.vehicle_model.id,
            'outer_color': self.exterior_color.id,
            'interior_color': self.interior_color.id,
            'components-TOTAL_FORMS': '0',
            'components-INITIAL_FORMS': '0',
            'components-MIN_NUM_FORMS': '0',
            'components-MAX_NUM_FORMS': '1000',
        }

        url = self.get_admin_url('add')
        response = self.client.post(url, new_vehicle_data)
        self.assertEqual(response.status_code, 302)  # Successful redirect

        # Check if default components were created
        new_vehicle = Vehicle.objects.get(vin='WBA98765432109876')
        self.assertEqual(new_vehicle.components.count(), len(self.model_components))

    def test_update_vehicle_does_not_create_default_components(self):
        """
        Scenario: Testing that updating a vehicle does not create default components
        Given a vehicle with components
        When the vehicle is updated
        Then default components should not be created again
        """
        # Pre-populate components
        for model_component in self.model_components:
            VehicleComponent.objects.create(
                vehicle=self.vehicle,
                name=model_component.name,
                component_type=model_component.component_type,
                status=0.5
            )

        initial_component_count = self.vehicle.components.count()

        # Update the vehicle
        update_data = {
            'vin': self.vehicle.vin,
            'id': self.vehicle.vin,  # Include 'id' to indicate update
            'year_built': 2024,
            'model': self.vehicle.model.id,
            'outer_color': self.vehicle.outer_color.id,
            'interior_color': self.vehicle.interior_color.id,
            'components-TOTAL_FORMS': '0',
            'components-INITIAL_FORMS': '0',
            'components-MIN_NUM_FORMS': '0',
            'components-MAX_NUM_FORMS': '1000',
        }

        url = self.get_admin_url('change', self.vehicle.vin)
        response = self.client.post(url, update_data)
        self.assertEqual(response.status_code, 302)  # Successful redirect

        # Refresh from database
        self.vehicle.refresh_from_db()

        # Ensure components count remains the same
        self.assertEqual(self.vehicle.components.count(), initial_component_count)
