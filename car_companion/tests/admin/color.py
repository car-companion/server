from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.translation import gettext as _

from ...admin.color import ColorAdmin, UnfoldColorWidget
from ...models import Color


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
        self.color = Color.objects.create(
            name='Red',
            hex_code='#FF0000',
            is_metallic=False,
            description='Basic red color'
        )

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
        Then I should see the list of colors with all display fields
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Red')
        self.assertContains(response, '#FF0000')
        self.assertContains(response, 'background-color: #FF0000')

    def test_search_color_functionality(self):
        """
        Scenario: Testing search functionality in admin
        Given multiple colors exist in the database
        When searching using different fields
        Then appropriate results should be shown
        """
        # Create test colors
        Color.objects.create(
            name='Blue',
            hex_code='#0000FF',
            description='Royal blue color'
        )
        Color.objects.create(
            name='Green',
            hex_code='#00FF00',
            description='Forest green'
        )

        test_cases = [
            ('Blue', ['Blue'], ['Green', 'Red']),  # Search by name
            ('#00FF00', ['Green'], ['Blue', 'Red']),  # Search by hex code
            ('Forest', ['Green'], ['Blue', 'Red']),  # Search by description
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

    def test_create_color_with_all_fields(self):
        """
        Scenario: Creating a new color with all fields
        Given I am on the add color page
        When I submit valid color data
        Then a new color should be created with all fields
        """
        url = self.get_admin_url('add')
        data = {
            'name': 'Metallic blue',
            'hex_code': '#0000FF',
            'is_metallic': 'on',
            'description': 'Shiny metallic blue'
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        created_color = Color.objects.get(name='Metallic blue')
        self.assertEqual(created_color.hex_code, '#0000FF')
        self.assertTrue(created_color.is_metallic)
        self.assertEqual(created_color.description, 'Shiny metallic blue')

    def test_update_color_all_fields(self):
        """
        Scenario: Updating all fields of an existing color
        Given an existing color
        When I update all its fields
        Then the changes should be saved correctly
        """
        url = self.get_admin_url('change', self.color.id)
        data = {
            'name': 'Dark red',
            'hex_code': '#8B0000',
            'is_metallic': 'on',
            'description': 'Updated description'
        }

        response = self.client.post(url, data)

        self.color.refresh_from_db()
        self.assertEqual(self.color.name, 'Dark red')
        self.assertEqual(self.color.hex_code, '#8B0000')
        self.assertTrue(self.color.is_metallic)
        self.assertEqual(self.color.description, 'Updated description')

    def test_color_preview_rendering(self):
        """
        Scenario: Testing color preview in admin list view
        Given a color with a specific hex code
        When viewing the color list
        Then the color preview should be correctly rendered
        """
        url = self.get_admin_url('changelist')
        response = self.client.get(url)

        self.assertContains(response, 'style="background-color: #FF0000')
        self.assertContains(response, 'class="w-8 h-8 rounded border"')

    def test_metallic_filter(self):
        """
        Scenario: Testing metallic filter in admin
        Given colors with different metallic states
        When filtering by metallic status
        Then appropriate results should be shown
        """
        Color.objects.create(
            name='Metallic Silver',
            hex_code='#C0C0C0',
            is_metallic=True
        )

        url = self.get_admin_url('changelist')

        # Test metallic filter
        response = self.client.get(url, {'is_metallic__exact': '1'})
        self.assertContains(response, 'Metallic silver')
        self.assertNotContains(response, 'Red')

        # Test non-metallic filter
        response = self.client.get(url, {'is_metallic__exact': '0'})
        self.assertContains(response, 'Red')
        self.assertNotContains(response, 'Metallic silver')

    def test_invalid_hex_code_validation(self):
        """
        Scenario: Testing hex code validation in admin form
        Given invalid hex code input
        When submitting the form
        Then appropriate validation errors should be shown
        """
        url = self.get_admin_url('add')
        data = {
            'name': 'Invalid Color',
            'hex_code': 'invalid',
            'is_metallic': False
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Color.objects.filter(name='Invalid Color').exists())
        self.assertContains(response, 'Invalid hex color code format')

    def test_form_widget_rendering(self):
        """
        Scenario: Testing custom color widget rendering
        Given I am on the color add/change page
        When the form is rendered
        Then the custom color widget should be properly displayed
        """
        # Test default widget rendering
        url = self.get_admin_url('add')
        response = self.client.get(url)

        self.assertContains(response, 'data-jscolor')
        self.assertContains(response, 'Color in hexadecimal format')

        # Test widget with custom attributes
        custom_attrs = {
            'class': 'custom-class',
        }
        widget = UnfoldColorWidget(attrs=custom_attrs)

        rendered = widget.render('color', '#000000')

        # Verify custom attributes are present
        self.assertIn('custom-class', rendered)

        # Verify default attributes are preserved
        self.assertIn('data-jscolor', rendered)
        self.assertIn('dark:text-gray-400', rendered)

        # Test widget without custom attributes
        default_widget = UnfoldColorWidget()
        default_rendered = default_widget.render('color', '#000000')
        self.assertIn('data-jscolor', default_rendered)
        self.assertIn('dark:text-gray-400', default_rendered)

    def test_fieldset_organization(self):
        """
        Scenario: Testing admin fieldset organization
        Given I am on the color add/change page
        When the form is rendered
        Then fields should be organized in correct fieldsets
        """
        url = self.get_admin_url('add')
        response = self.client.get(url)

        self.assertContains(response, _('Basic Information'))
        self.assertContains(response, _('Properties'))
        self.assertContains(response, _('Additional Information'))
