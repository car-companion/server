from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ...admin.component_type import ComponentTypeAdmin
from ...models import ComponentType


class ComponentTypeAdminTests(TestCase):
    def setUp(self):
        """
        Set up test environment
        Given a superuser exists in the system
        And a test component type exists in the database
        """
        # Create superuser
        user = get_user_model()
        self.admin_user = user.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create test component type
        self.component_type = ComponentType.objects.create(
            name='Engine',
            description='Main engine of the vehicle'
        )

        # Set up admin
        self.site = AdminSite()
        self.component_type_admin = ComponentTypeAdmin(ComponentType, self.site)
        self.client = Client()
        self.client.force_login(self.admin_user)

    @staticmethod
    def get_admin_url(action, *args):
        """
        Helper method to generate admin URLs
        """
        return reverse(f'admin:vehicle_componenttype_{action}', args=args)

    def test_admin_list_view_access(self):
        """
        Scenario: Accessing the component type list view in admin
        Given I am logged in as an admin user
        When I access the component type list view
        Then I should see the list of component types with all display fields
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Engine')
        self.assertContains(response, 'Main engine of the vehicle')

    def test_search_component_type_functionality(self):
        """
        Scenario: Testing search functionality in admin
        Given multiple component types exist in the database
        When searching using different fields
        Then appropriate results should be shown
        """
        # Create test component types
        ComponentType.objects.create(
            name='Window',
            description='Vehicle window component'
        )
        ComponentType.objects.create(
            name='Door',
            description='Vehicle door component'
        )

        test_cases = [
            ('Window', ['Window'], ['Door', 'Engine']),  # Search by name
            ('door', ['Door'], ['Window', 'Engine']),  # Search by name case-insensitive
            ('vehicle', ['Window', 'Door', 'Engine'], []),  # Search by description
            ('engine', ['Engine'], ['Window', 'Door']),  # Search by name
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

    def test_create_component_type_with_all_fields(self):
        """
        Scenario: Creating a new component type with all fields
        Given I am on the add component type page
        When I submit valid component type data
        Then a new component type should be created with all fields
        """
        url = self.get_admin_url('add')
        data = {
            'name': 'Brake',
            'description': 'Brake system component'
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        created_component_type = ComponentType.objects.get(name='Brake')
        self.assertEqual(created_component_type.description, 'Brake system component')

    def test_update_component_type_all_fields(self):
        """
        Scenario: Updating all fields of an existing component type
        Given an existing component type
        When I update all its fields
        Then the changes should be saved correctly
        """
        url = self.get_admin_url('change', self.component_type.id)
        data = {
            'name': 'Engine Updated',
            'description': 'Updated description of the engine'
        }

        response = self.client.post(url, data)

        self.component_type.refresh_from_db()
        self.assertEqual(self.component_type.name, 'Engine updated')  # Assuming capitalization
        self.assertEqual(self.component_type.description, 'Updated description of the engine')

    def test_invalid_name_validation(self):
        """
        Scenario: Testing name validation in admin form
        Given invalid name input
        When submitting the form
        Then appropriate validation errors should be shown
        """
        url = self.get_admin_url('add')
        data = {
            'name': '',  # Invalid: blank name
            'description': 'Component with invalid name'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ComponentType.objects.filter(description='Component with invalid name').exists())
        self.assertContains(response, 'Component type name cannot be blank.')

    def test_unique_name_validation(self):
        """
        Scenario: Testing uniqueness validation in admin form
        Given a component type with a name that already exists
        When submitting the form
        Then appropriate validation errors should be shown
        """
        url = self.get_admin_url('add')
        data = {
            'name': 'Engine',  # Already exists
            'description': 'Duplicate component type'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ComponentType.objects.filter(description='Duplicate component type').exists())
        self.assertContains(response, 'A component type with this name already exists.')

    def test_admin_list_ordering(self):
        """
        Scenario: Testing ordering in the admin list view
        Given multiple component types
        When accessing the list view
        Then they should be ordered by name
        """
        ComponentType.objects.create(name='Zebra', description='Zebra component')
        ComponentType.objects.create(name='Apple', description='Apple component')

        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Extract the names in the order they appear in the response
        content = response.content.decode('utf-8')
        apple_index = content.find('Apple')
        engine_index = content.find('Engine')
        zebra_index = content.find('Zebra')

        self.assertTrue(apple_index < engine_index < zebra_index)

    def test_field_display_in_list_view(self):
        """
        Scenario: Testing that all specified fields are displayed in the list view
        Given the component type admin configuration
        When accessing the list view
        Then all fields in list_display should be visible
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertContains(response, 'data-label="name"')
        self.assertContains(response, 'data-label="description"')

    def test_form_field_rendering(self):
        """
        Scenario: Testing form field rendering in the add/change page
        Given I am on the component type add/change page
        When the form is rendered
        Then all fields should be properly displayed
        """
        url = self.get_admin_url('add')
        response = self.client.get(url)

        self.assertContains(response, 'id="id_name"')
        self.assertContains(response, 'id="id_description"')

    def test_fieldset_organization(self):
        """
        Scenario: Testing admin fieldset organization
        Given I am on the component type add/change page
        When the form is rendered
        Then fields should be organized in correct fieldsets if any
        """
        url = self.get_admin_url('add')
        response = self.client.get(url)

        self.assertContains(response, '<form', msg_prefix="Form tag not found in response")
        self.assertContains(response, 'id="id_name"', msg_prefix="Name field not found in form")
        self.assertContains(response, 'id="id_description"', msg_prefix="Description field not found in form")

    def test_delete_component_type(self):
        """
        Scenario: Deleting a component type via admin
        Given an existing component type
        When I delete it via the admin
        Then it should be removed from the database
        """
        url = self.get_admin_url('delete', self.component_type.id)
        response = self.client.post(url, {'post': 'yes'}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ComponentType.objects.filter(id=self.component_type.id).exists())
        self.assertContains(response, 'Engine')
        self.assertContains(response, 'was deleted successfully.')

    def test_ordering_attribute_in_admin(self):
        """
        Scenario: Testing that the ordering in the admin matches the model's Meta ordering
        Given the ComponentTypeAdmin configuration
        When checking the ordering attribute
        Then it should match the model's Meta ordering
        """
        self.assertEqual(self.component_type_admin.ordering, ['name'])
