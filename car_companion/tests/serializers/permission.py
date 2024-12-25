from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from car_companion.models import (
    Vehicle, VehicleModel, Manufacturer, Color, ComponentType,
    VehicleComponent, ComponentPermission, VehicleUserPreferences
)
from car_companion.serializers.permission import (
    GrantPermissionSerializer,
    PermissionResultSerializer,
    RevokeRequestSerializer,
    RevokeResultSerializer,
    AccessedVehicleSerializer
)

user = get_user_model()


class GrantPermissionSerializerTests(TestCase):
    """Test suite for the GrantPermissionSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        self.permission_data = {
            'permission_type': ComponentPermission.PermissionType.READ,
            'valid_until': timezone.now() + timedelta(days=30)
        }

    def test_valid_permission_type_scenarios(self):
        """
        Scenario Outline: Validating valid permission types
        Given a permission request with valid permission type
        When validating the serializer
        Then validation should pass

        Examples:
        | Type  | Description     |
        | read  | Read access     |
        | write | Write access    |
        """
        valid_types = [
            ('read', 'Read access'),
            ('write', 'Write access')
        ]

        for perm_type, case_desc in valid_types:
            with self.subTest(f"Valid permission type - {case_desc}"):
                data = {'permission_type': perm_type}
                serializer = GrantPermissionSerializer(data=data)
                self.assertTrue(serializer.is_valid())

    def test_invalid_permission_type_scenarios(self):
        """
        Scenario: Validating invalid permission types
        Given a permission request with invalid type
        When validating the serializer
        Then validation should fail
        And appropriate error messages should be returned
        """
        invalid_types = [
            ('admin', 'Invalid type'),
            ('', 'Empty string'),
            (None, 'None value')
        ]

        for invalid_type, case_desc in invalid_types:
            with self.subTest(f"Invalid permission type - {case_desc}"):
                data = {'permission_type': invalid_type}
                serializer = GrantPermissionSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('permission_type', serializer.errors)

    def test_valid_until_validation(self):
        """
        Scenario: Validating expiration date formats
        Given different valid_until date formats
        When validating the serializer
        Then appropriate validation results should be returned
        """
        current_time = timezone.now()
        test_cases = [
            (current_time + timedelta(days=1), True, 'Future date'),
            (None, True, 'None value allowed'),
            (current_time - timedelta(days=1), True, 'Past date allowed')
        ]

        for date_value, should_pass, case_desc in test_cases:
            with self.subTest(f"Valid until validation - {case_desc}"):
                data = {
                    'permission_type': 'read',
                    'valid_until': date_value
                }
                serializer = GrantPermissionSerializer(data=data)
                self.assertEqual(serializer.is_valid(), should_pass)


class PermissionResultSerializerTests(TestCase):
    """Test suite for the PermissionResultSerializer using BDD style."""

    def test_permission_result_serialization(self):
        """
        Scenario: Serializing permission operation results
        Given permission operation results with granted and failed operations
        When serializing the results
        Then all fields should be properly represented
        """
        test_data = {
            'granted': [
                {'component': 'Engine', 'type': 'read'},
                {'component': 'Door', 'type': 'write'}
            ],
            'failed': [
                {'component': 'Window', 'error': 'Permission denied'}
            ]
        }

        serializer = PermissionResultSerializer(data=test_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, test_data)


class RevokeRequestSerializerTests(TestCase):
    """Test suite for the RevokeRequestSerializer using BDD style."""

    def test_username_validation(self):
        """
        Scenario Outline: Validating username field
        Given various username inputs
        When validating the serializer
        Then appropriate validation results should be returned
        """
        test_cases = [
            ('validuser', True, 'Valid username'),
            ('', False, 'Empty username'),
            (None, False, 'None username')
        ]

        for username, should_pass, case_desc in test_cases:
            with self.subTest(f"Username validation - {case_desc}"):
                data = {'username': username}
                serializer = RevokeRequestSerializer(data=data)
                self.assertEqual(serializer.is_valid(), should_pass)


class RevokeResultSerializerTests(TestCase):
    """Test suite for the RevokeResultSerializer using BDD style."""

    def test_revoke_result_serialization(self):
        """
        Scenario: Serializing revocation results
        Given revocation operation results
        When serializing the results
        Then all fields should be properly represented
        """
        test_data = {
            'revoked': [
                {'component': 'Engine', 'type': 'read'},
                {'component': 'Door', 'type': 'write'}
            ],
            'message': 'Successfully revoked 2 permissions'
        }

        serializer = RevokeResultSerializer(data=test_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, test_data)


class AccessedVehicleSerializerTests(TestCase):
    """Test suite for the AccessedVehicleSerializer using BDD style."""

    def setUp(self):
        """Set up test data before each test method."""
        # Create users
        self.user = user.objects.create_user(username='testuser',
                                             email='testuser@mail.com',
                                             password='testpass')

        # Create vehicle hierarchy
        self.manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE"
        )
        self.model = VehicleModel.objects.create(
            name="X5",
            manufacturer=self.manufacturer
        )
        self.color_interior = Color.objects.create(
            name="Beige",
            hex_code="#F5F5DC",
            is_metallic=False
        )
        self.color_exterior = Color.objects.create(
            name="Metallic blue",
            hex_code="#0000FF",
            is_metallic=True
        )
        self.vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=self.model,
            outer_color=self.color_exterior,
            interior_color=self.color_interior,
        )

        # Create user preferences
        self.preferences = VehicleUserPreferences.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            nickname="My Favorite BMW",
            interior_color=self.color_interior,
            exterior_color=self.color_exterior
        )

        # Create component and permission
        self.component_type = ComponentType.objects.create(name="Engine")
        self.component = VehicleComponent.objects.create(
            name="Main engine",
            component_type=self.component_type,
            vehicle=self.vehicle
        )
        self.permission = ComponentPermission.objects.create(
            component=self.component,
            user=self.user,
            permission_type=ComponentPermission.PermissionType.READ
        )

    def test_accessed_vehicle_serialization_with_preferences(self):
        """
        Scenario: Serializing vehicle with user preferences and permissions
        Given a vehicle with component permissions and user preferences
        When serializing the vehicle
        Then all fields, preferences, and permissions should be properly represented
        """
        context = {'request': type('Request', (), {'user': self.user})}
        serializer = AccessedVehicleSerializer(self.vehicle, context=context)

        expected_data = {
            'vin': 'WBA12345678901234',
            'model': 'X5',
            'year_built': 2023,
            'default_interior_color': {
                'name': 'Beige',
                'hex_code': '#F5F5DC',
                'is_metallic': False
            },
            'default_exterior_color': {
                'name': 'Metallic blue',
                'hex_code': '#0000FF',
                'is_metallic': True
            },
            'user_preferences': {
                'nickname': 'My Favorite BMW',
                'interior_color': {
                    'name': 'Beige',
                    'hex_code': '#F5F5DC',
                    'is_metallic': False
                },
                'exterior_color': {
                    'name': 'Metallic blue',
                    'hex_code': '#0000FF',
                    'is_metallic': True
                }
            },
            'permissions': [{
                'component_type': 'Engine',
                'component_name': 'Main engine',
                'permission_type': 'read'
            }]
        }

        self.assertEqual(serializer.data, expected_data)

    def test_accessed_vehicle_serialization_without_preferences(self):
        """
        Scenario: Serializing vehicle without user preferences
        Given a vehicle with no user-specific preferences
        When serializing the vehicle
        Then user_preferences should be null
        """
        # Delete user preferences
        self.preferences.delete()

        context = {'request': type('Request', (), {'user': self.user})}
        serializer = AccessedVehicleSerializer(self.vehicle, context=context)

        expected_data = {
            'vin': 'WBA12345678901234',
            'model': 'X5',
            'year_built': 2023,
            'default_interior_color': {
                'name': 'Beige',
                'hex_code': '#F5F5DC',
                'is_metallic': False
            },
            'default_exterior_color': {
                'name': 'Metallic blue',
                'hex_code': '#0000FF',
                'is_metallic': True
            },
            'user_preferences': None,
            'permissions': [{
                'component_type': 'Engine',
                'component_name': 'Main engine',
                'permission_type': 'read'
            }]
        }

        self.assertEqual(serializer.data, expected_data)

    def test_accessed_vehicle_serialization_without_permissions(self):
        """
        Scenario: Serializing vehicle without component permissions
        Given a vehicle with no component permissions for the user
        When serializing the vehicle
        Then permissions list should be empty
        """
        # Delete the user's permission
        self.permission.delete()

        context = {'request': type('Request', (), {'user': self.user})}
        serializer = AccessedVehicleSerializer(self.vehicle, context=context)

        expected_data = {
            'vin': 'WBA12345678901234',
            'model': 'X5',
            'year_built': 2023,
            'default_interior_color': {
                'name': 'Beige',
                'hex_code': '#F5F5DC',
                'is_metallic': False
            },
            'default_exterior_color': {
                'name': 'Metallic blue',
                'hex_code': '#0000FF',
                'is_metallic': True
            },
            'user_preferences': {
                'nickname': 'My Favorite BMW',
                'interior_color': {
                    'name': 'Beige',
                    'hex_code': '#F5F5DC',
                    'is_metallic': False
                },
                'exterior_color': {
                    'name': 'Metallic blue',
                    'hex_code': '#0000FF',
                    'is_metallic': True
                }
            },
            'permissions': []
        }

        self.assertEqual(serializer.data, expected_data)
