from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from vehicle.models import (
    Vehicle, VehicleModel, Manufacturer, Color, ComponentType,
    VehicleComponent, ComponentPermission
)
from vehicle.serializers.permission import (
    GrantPermissionSerializer,
    PermissionResultSerializer,
    RevokeRequestSerializer,
    RevokeResultSerializer,
    AccessedVehicleSerializer
)

User = get_user_model()


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
        self.user = User.objects.create_user(username='testuser', password='testpass')

        # Create vehicle hierarchy
        self.manufacturer = Manufacturer.objects.create(
            name="Bmw",
            country_code="DE"
        )
        self.model = VehicleModel.objects.create(
            name="X5",
            manufacturer=self.manufacturer
        )
        self.color = Color.objects.create(
            name="Black",
            hex_code="#000000"
        )
        self.vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=self.model,
            outer_color=self.color,
            interior_color=self.color,
            nickname="Test Vehicle"
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

    def test_accessed_vehicle_serialization(self):
        """
        Scenario: Serializing vehicle with user permissions
        Given a vehicle with component permissions
        When serializing the vehicle
        Then all fields and permissions should be properly represented
        """
        context = {'request': type('Request', (), {'user': self.user})}
        serializer = AccessedVehicleSerializer(self.vehicle, context=context)

        expected_data = {
            'vin': 'WBA12345678901234',
            'nickname': 'Test Vehicle',
            'permissions': [{
                'component_type': 'Engine',
                'component_name': 'Main engine',
                'permission_type': 'read'
            }]
        }

        self.assertEqual(serializer.data, expected_data)

    def test_accessed_vehicle_without_permissions(self):
        """
        Scenario: Serializing vehicle without permissions
        Given a vehicle with no component permissions
        When serializing the vehicle
        Then permissions list should be empty
        """
        # Delete existing permission
        self.permission.delete()

        context = {'request': type('Request', (), {'user': self.user})}
        serializer = AccessedVehicleSerializer(self.vehicle, context=context)

        self.assertEqual(serializer.data['permissions'], [])
