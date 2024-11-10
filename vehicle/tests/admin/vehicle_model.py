from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from ...models import VehicleModel, Manufacturer
from ...admin import VehicleModelAdmin


class VehicleModelAdminTests(TestCase):
    def setUp(self):
        """
        Scenario: Setting up the admin test environment
        Given an admin user, a manufacturer, and a test vehicle model
        When the tests are run
        Then these objects are available for testing, and the admin user is logged in
        """
        user = get_user_model()
        self.admin_user = user.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create manufacturer and a test vehicle model
        self.manufacturer = Manufacturer.objects.create(name='Toyota')
        self.vehicle_model = VehicleModel.objects.create(
            name='Corolla',
            manufacturer=self.manufacturer
        )

        # Set up admin site
        self.site = AdminSite()
        self.vehicle_model_admin = VehicleModelAdmin(VehicleModel, self.site)
        self.client = Client()
        self.client.force_login(self.admin_user)

    @staticmethod
    def get_admin_url(action, *args):
        """
        Scenario: Generating admin URLs for vehicle models
        Given an action and optional arguments
        When this method is called
        Then it returns the corresponding admin URL
        """
        return reverse(f'admin:vehicle_vehiclemodel_{action}', args=args)

    def test_admin_list_view_access(self):
        """
        Scenario: Accessing the vehicle model list view in the admin
        Given a logged-in admin user
        When accessing the vehicle model list page
        Then the response should be successful and display the model name 'Corolla'
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Corolla')

    def test_search_vehicle_model_by_name(self):
        """
        Scenario: Searching for a vehicle model by name in the admin
        Given multiple vehicle models in the system
        When searching for a specific model name
        Then only models matching the search term should be displayed
        """
        VehicleModel.objects.create(name='Camry', manufacturer=self.manufacturer)
        url = self.get_admin_url('changelist')
        response = self.client.get(url, {'q': 'Camry'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camry')
        self.assertNotContains(response, 'Corolla')

    def test_create_vehicle_model_with_valid_data(self):
        """
        Scenario: Creating a new vehicle model with valid data in the admin
        Given a logged-in admin user and valid vehicle model data
        When submitting a form to create the model
        Then the new model should be created successfully
        """
        url = self.get_admin_url('add')
        response = self.client.post(url, {
            'name': 'RAV4',
            'manufacturer': self.manufacturer.id
        }, follow=True)
        self.assertTrue(VehicleModel.objects.filter(name='RAV4').exists())
        self.assertEqual(response.status_code, 200)

    def test_create_vehicle_model_with_duplicate_name_and_manufacturer(self):
        """
        Scenario: Attempting to create a duplicate vehicle model in the admin
        Given an existing vehicle model with a specific name and manufacturer
        When trying to create another model with the same name and manufacturer
        Then the system should prevent the duplicate and show an appropriate error message
        """
        url = self.get_admin_url('add')
        response = self.client.post(url, {
            'name': 'Corolla',
            'manufacturer': self.manufacturer.id
        })
        self.assertEqual(VehicleModel.objects.count(), 1)
        self.assertContains(response, 'This combination of name and manufacturer already exists.')

    def test_update_vehicle_model_name(self):
        """
        Scenario: Updating a vehicle model's name in the admin
        Given an existing vehicle model
        When changing the model's name and saving
        Then the new name should be saved and reflected in the database
        """
        url = self.get_admin_url('change', self.vehicle_model.id)
        response = self.client.post(url, {
            'name': 'Corolla Updated',
            'manufacturer': self.manufacturer.id
        })
        self.vehicle_model.refresh_from_db()
        self.assertEqual(self.vehicle_model.name, 'Corolla Updated')

    def test_delete_vehicle_model(self):
        """
        Scenario: Deleting a vehicle model in the admin
        Given an existing vehicle model
        When confirming the delete action
        Then the model should be removed from the database
        """
        url = self.get_admin_url('delete', self.vehicle_model.id)
        response = self.client.post(url, {'post': 'yes'})
        self.assertEqual(VehicleModel.objects.filter(id=self.vehicle_model.id).count(), 0)

    def test_invalid_vehicle_model_creation(self):
        """
        Scenario: Attempting to create a vehicle model with missing or invalid data in the admin
        Given a form submission with an empty name field
        When trying to save the form
        Then the system should raise an error indicating that the name field is required
        """
        url = self.get_admin_url('add')
        response = self.client.post(url, {
            'name': '',  # Invalid name
            'manufacturer': self.manufacturer.id
        })
        self.assertContains(response, 'This field is required.')