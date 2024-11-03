from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from ...models import Color
from ...admin import ColorAdmin


class ColorAdminTests(TestCase):
    def setUp(self):
        """
        Set up test environment
        Given a superuser exists in the system
        And a test color exists in the database
        """
        # Create superuser
        user = get_user_model()
        self.admin_user = user.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create test color
        self.color = Color.objects.create(name='Red')

        # Set up admin
        self.site = AdminSite()
        self.color_admin = ColorAdmin(Color, self.site)
        self.client = Client()
        self.client.force_login(self.admin_user)

    @staticmethod
    def get_admin_url(action, *args):
        """
        Helper method to generate admin URLs
        """
        return reverse(f'admin:vehicle_color_{action}', args=args)

    def test_admin_list_view_access(self):
        """
        Scenario: Accessing the color list view in admin
        Given I am logged in as an admin user
        When I access the color list view
        Then I should see the list of colors
        And the response should include the test color
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Red')

    def test_search_color_by_name(self):
        """
        Scenario: Searching for a color by name
        Given multiple colors exist in the database
        When I search for a specific color name
        Then I should only see the matching colors
        """
        # Given
        Color.objects.create(name='Blue')
        Color.objects.create(name='Green')

        # When
        url = self.get_admin_url('changelist')
        response = self.client.get(url, {'q': 'Blue'})

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blue')
        self.assertNotContains(response, 'Green')

    def test_create_color_with_valid_name(self):
        """
        Scenario: Creating a new color with valid name
        Given I am on the add color page
        When I submit a valid color name
        Then a new color should be created
        And I should be redirected to the color list
        """
        # Given
        url = self.get_admin_url('add')

        # When
        response = self.client.post(url, {
            'name': 'Yellow'
        }, follow=True)

        # Then
        self.assertTrue(Color.objects.filter(name='Yellow').exists())
        self.assertEqual(response.status_code, 200)

    def test_create_color_with_duplicate_name(self):
        """
        Scenario: Attempting to create a color with duplicate name
        Given a color already exists with the name 'Red'
        When I try to create another color with the same name
        Then it should show an error message
        And the new color should not be created
        """
        # Given
        url = self.get_admin_url('add')
        initial_count = Color.objects.count()

        # When
        response = self.client.post(url, {
            'name': 'Red'
        })

        # Then
        self.assertEqual(Color.objects.count(), initial_count)
        self.assertContains(response, 'A color with this name already exists.')

    def test_update_color_name(self):
        """
        Scenario: Updating an existing color name
        Given an existing color
        When I update its name
        Then the color name should be changed
        And the changes should be saved in the database
        """
        # Given
        url = self.get_admin_url('change', self.color.id)

        # When
        response = self.client.post(url, {
            'name': 'Dark red'
        })

        # Then
        self.color.refresh_from_db()
        self.assertEqual(self.color.name, 'Dark red')

    def test_delete_color(self):
        """
        Scenario: Deleting an existing color
        Given an existing color in the database
        When I delete the color through the admin interface
        Then the color should be removed from the database
        """
        # Given
        url = self.get_admin_url('delete', self.color.id)

        # When
        response = self.client.post(url, {'post': 'yes'})

        # Then
        self.assertEqual(Color.objects.filter(id=self.color.id).count(), 0)

    def test_empty_name_validation(self):
        """
        Scenario: Attempting to create a color with empty name
        Given I am on the add color page
        When I submit an empty color name
        Then it should show a validation error
        And no color should be created
        """
        # Given
        url = self.get_admin_url('add')
        initial_count = Color.objects.count()

        # When
        response = self.client.post(url, {
            'name': ''
        })

        # Then
        self.assertEqual(Color.objects.count(), initial_count)
        self.assertContains(response, 'This field is required')

    def test_non_admin_access(self):
        """
        Scenario: Non-admin user attempting to access admin
        Given I am logged in as a non-admin user
        When I try to access the color admin
        Then I should be redirected to the login page
        """
        # Given
        user = get_user_model()
        regular_user = user.objects.create_user(
            username='regular',
            password='regular123'
        )
        client = Client()
        client.force_login(regular_user)

        # When
        url = self.get_admin_url('changelist')
        response = client.get(url)

        # Then
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_update_to_null_name(self):
        """
        Scenario: Updating an existing color name to null
        Given an existing color with a valid name
        When updating the name to null
        Then it should raise a ValidationError with the correct message
        """
        # Given
        color = Color.objects.create(name="Valid Color")

        # When/Then
        color.name = None
        with self.assertRaises(ValidationError) as context:
            color.save()
        self.assertEqual(
            str(context.exception),
            str(_("['Color name cannot be null.']"))
        )
