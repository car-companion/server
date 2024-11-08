from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from ...models import VehicleModel, Manufacturer
from ...admin import VehicleModelAdmin


class VehicleModelAdminTests(TestCase):
    def setUp(self):
        """
        Set up the test environment.
        Creates a superuser, manufacturer, and a test vehicle model.
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
        """Helper method to generate admin URLs."""
        return reverse(f'admin:vehicle_vehiclemodel_{action}', args=args)

    def test_admin_list_view_access(self):
        """Accessing the list view in the admin."""
        url = self.get_admin_url('changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Corolla')

    def test_search_vehicle_model_by_name(self):
        """Searching for a vehicle model by name."""
        VehicleModel.objects.create(name='Camry', manufacturer=self.manufacturer)
        url = self.get_admin_url('changelist')
        response = self.client.get(url, {'q': 'Camry'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camry')
        self.assertNotContains(response, 'Corolla')

    def test_create_vehicle_model_with_valid_data(self):
        """Creating a new vehicle model with valid data."""
        url = self.get_admin_url('add')
        response = self.client.post(url, {
            'name': 'RAV4',
            'manufacturer': self.manufacturer.id
        }, follow=True)
        self.assertTrue(VehicleModel.objects.filter(name='RAV4').exists())
        self.assertEqual(response.status_code, 200)

    def test_create_vehicle_model_with_duplicate_name_and_manufacturer(self):
        """Attempting to create a vehicle model with the same name and manufacturer."""
        url = self.get_admin_url('add')
        response = self.client.post(url, {
            'name': 'Corolla',
            'manufacturer': self.manufacturer.id
        })
        self.assertEqual(VehicleModel.objects.count(), 1)
        self.assertContains(response, 'This combination of name and manufacturer already exists.')

    def test_update_vehicle_model_name(self):
        """Updating an existing vehicle model's name."""
        url = self.get_admin_url('change', self.vehicle_model.id)
        response = self.client.post(url, {
            'name': 'Corolla Updated',
            'manufacturer': self.manufacturer.id
        })
        self.vehicle_model.refresh_from_db()
        self.assertEqual(self.vehicle_model.name, 'Corolla Updated')

    def test_delete_vehicle_model(self):
        """Deleting an existing vehicle model."""
        url = self.get_admin_url('delete', self.vehicle_model.id)
        response = self.client.post(url, {'post': 'yes'})
        self.assertEqual(VehicleModel.objects.filter(id=self.vehicle_model.id).count(), 0)

    def test_invalid_vehicle_model_creation(self):
        """Trying to create a vehicle model with missing or invalid data."""
        url = self.get_admin_url('add')
        response = self.client.post(url, {
            'name': '',  # Invalid name
            'manufacturer': self.manufacturer.id
        })
        self.assertContains(response, 'This field is required.')