from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from ...models import Vehicle, VehicleModel, Manufacturer, Color, ComponentType, VehicleComponent
from django.utils.translation import gettext_lazy as _


class VehicleTests(TestCase):
    """
    Test suite for the Vehicle model.
    Covers VIN validation, year validation, relationships,
    nickname handling, and all model constraints.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        # Create manufacturer
        cls.manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE"
        )

        # Create vehicle model
        cls.vehicle_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=cls.manufacturer
        )

        # Create colors
        cls.exterior_color = Color.objects.create(
            name="Black",
            hex_code="#000000"
        )
        cls.interior_color = Color.objects.create(
            name="Beige",
            hex_code="#F5F5DC"
        )

        # Create base vehicle
        cls.base_vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=cls.vehicle_model,
            outer_color=cls.exterior_color,
            interior_color=cls.interior_color
        )

        cls.valid_vehicle_data = {
            'vin': "WBA98765432109876",
            'year_built': 2023,
            'model': cls.vehicle_model,
            'outer_color': cls.exterior_color,
            'interior_color': cls.interior_color
        }

    def test_vin_validation_and_standardization(self):
        """
        Scenario: Testing VIN validation and standardization
        Given VINs with different formats
        When saving them
        Then they should be properly standardized and validated
        """
        test_cases = [
            ('wba12345678901235', 'WBA12345678901235'),  # Lowercase to uppercase
            ('WBA12345678901237', 'WBA12345678901237'),  # Already uppercase
            ('NBA98765432109876', 'NBA98765432109876'),  # Valid different VIN
        ]

        for input_vin, expected_vin in test_cases:
            with self.subTest(input_vin=input_vin):
                vehicle = Vehicle.objects.create(
                    vin=input_vin,
                    year_built=2023,
                    model=self.vehicle_model,
                    outer_color=self.exterior_color,
                    interior_color=self.interior_color
                )
                self.assertEqual(vehicle.vin, expected_vin)

    def test_invalid_vins(self):
        """
        Scenario: Testing invalid VINs
        Given invalid VINs
        When attempting to save
        Then appropriate validation errors should be raised
        """
        invalid_cases = [
            (None, 'VIN is required.'),
            ('', 'VIN is required.'),
            ('ABC123', 'VIN must be exactly 17 characters.'),
            ('WBA123456789IOQXX', 'VIN cannot contain letters I, O, or Q.'),
            ('WBA123456789@#$%&', 'Enter a valid VIN.'),
        ]

        for invalid_vin, expected_error in invalid_cases:
            with self.subTest(invalid_vin=invalid_vin):
                vehicle = Vehicle(
                    vin=invalid_vin,
                    year_built=2023,
                    model=self.vehicle_model,
                    outer_color=self.exterior_color,
                    interior_color=self.interior_color
                )
                with self.assertRaises(ValidationError) as context:
                    vehicle.full_clean()
                self.assertIn(expected_error, str(context.exception))

    def test_year_validation(self):
        """
        Scenario: Testing year validation
        Given various years
        When saving vehicles
        Then validation should enforce valid years
        """
        current_year = timezone.now().year
        test_cases = [
            (1886, True),  # Minimum valid year
            (current_year, True),  # Current year
            (current_year + 1, True),  # Next year (maximum allowed)
            (1885, False),  # Too old
            (current_year + 2, False),  # Too far in future
        ]

        for year, should_pass in test_cases:
            with self.subTest(year=year):
                vehicle = Vehicle(
                    vin=f"WBA{year}5678901234",
                    year_built=year,
                    model=self.vehicle_model,
                    outer_color=self.exterior_color,
                    interior_color=self.interior_color
                )

                if should_pass:
                    vehicle.full_clean()  # Should not raise error
                else:
                    with self.assertRaises(ValidationError):
                        vehicle.full_clean()

    def test_nickname_validation(self):
        """
        Scenario: Testing nickname validation
        Given various nickname formats
        When saving vehicles
        Then they should be properly validated and standardized
        """
        valid_cases = [
            ('  My Car  ', 'My Car'),  # Whitespace stripping
            ('Family-Car-2023', 'Family-Car-2023'),  # Valid with hyphen
            ('My    Cool    Car', 'My Cool Car'),  # Multiple spaces
            (None, None),  # No nickname
        ]

        invalid_cases = [
            ('A', 'Nickname must be at least 2 characters long if provided.'),
            ('Car@Home', 'Nickname can only contain letters, numbers, spaces, and hyphens.'),
            ('My#Car', 'Nickname can only contain letters, numbers, spaces, and hyphens.'),
        ]

        # Test valid cases
        for input_nickname, expected_nickname in valid_cases:
            with self.subTest(input_nickname=input_nickname):
                vehicle = Vehicle.objects.create(
                    vin=f"NBA{self.valid_vehicle_data['year_built']}567890{len(input_nickname) if input_nickname else 0}",
                    nickname=input_nickname,
                    **{k: v for k, v in self.valid_vehicle_data.items() if k != 'vin'}
                )
                self.assertEqual(vehicle.nickname, expected_nickname)

        # Test invalid cases
        for invalid_nickname, expected_error in invalid_cases:
            with self.subTest(invalid_nickname=invalid_nickname):
                vehicle = Vehicle(
                    nickname=invalid_nickname,
                    **self.valid_vehicle_data
                )
                with self.assertRaises(ValidationError) as context:
                    vehicle.full_clean()
                self.assertIn(expected_error, str(context.exception))

    def test_required_relationships(self):
        """
        Scenario: Testing required relationship validation
        Given missing required relationships
        When attempting to save
        Then appropriate validation errors should be raised
        """
        required_fields = [
            ('model', None, 'Vehicle model is required.'),
            ('outer_color', None, 'Exterior color is required.'),
            ('interior_color', None, 'Interior color is required.'),
        ]

        for field, value, expected_error in required_fields:
            with self.subTest(field=field):
                data = self.valid_vehicle_data.copy()
                data[field] = value
                vehicle = Vehicle(
                    **data
                )
                with self.assertRaises(ValidationError) as context:
                    vehicle.full_clean()
                self.assertIn(expected_error, str(context.exception))

    def test_string_representation(self):
        """
        Scenario: Testing string representation
        Given vehicles with and without nicknames
        When converting to string
        Then it should show the correct format
        """
        # Test without nickname
        self.assertEqual(
            str(self.base_vehicle),
            f"2023 Bmw (DE) X5 {self.base_vehicle.vin}"
        )

        # Test with nickname
        vehicle_with_nickname = Vehicle.objects.create(
            vin="NBA99999999999999",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color,
            nickname="Family Car"
        )
        self.assertEqual(
            str(vehicle_with_nickname),
            f'2023 Bmw (DE) X5 "Family Car" NBA99999999999999'
        )

    def test_manufacturer_property(self):
        """
        Scenario: Testing manufacturer property
        Given a vehicle
        When accessing manufacturer property
        Then it should return the correct manufacturer
        """
        self.assertEqual(self.base_vehicle.manufacturer, self.manufacturer)

    def test_model_meta_configuration(self):
        """
        Scenario: Testing model metadata configuration
        Given the Vehicle model
        When checking metadata
        Then it should match defined settings
        """
        self.assertEqual(Vehicle._meta.db_table, 'vehicles')
        self.assertEqual(Vehicle._meta.ordering, ['-year_built', 'model'])

        # Check indexes
        indexes = [index.name for index in Vehicle._meta.indexes]
        self.assertIn('vehicle_year_idx', indexes)
        self.assertIn('vehicle_model_idx', indexes)
        self.assertIn('vehicle_outer_color_idx', indexes)
        self.assertIn('vehicle_interior_color_idx', indexes)

        # Check verbose names
        self.assertEqual(Vehicle._meta.verbose_name, _('Vehicle'))
        self.assertEqual(Vehicle._meta.verbose_name_plural, _('Vehicles'))

    def test_unique_vin_constraint(self):
        """
        Scenario: Testing unique VIN constraint
        Given an existing VIN
        When creating another vehicle with the same VIN
        Then it should raise an IntegrityError
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vehicle.objects.create(
                    vin=self.base_vehicle.vin,
                    year_built=2023,
                    model=self.vehicle_model,
                    outer_color=self.exterior_color,
                    interior_color=self.interior_color
                )


class VehicleComponentTests(TestCase):
    """
    Test suite for the VehicleComponent model.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        # Create basic vehicle
        cls.manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE"
        )
        cls.vehicle_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=cls.manufacturer
        )
        cls.exterior_color = Color.objects.create(
            name="Black",
            hex_code="#000000"
        )
        cls.interior_color = Color.objects.create(
            name="Beige",
            hex_code="#F5F5DC"
        )
        cls.vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=cls.vehicle_model,
            outer_color=cls.exterior_color,
            interior_color=cls.interior_color
        )

        # Create component type
        cls.component_type = ComponentType.objects.create(
            name="Engine"
        )

        # Create base component
        cls.base_component = VehicleComponent.objects.create(
            name="V8 Engine",
            component_type=cls.component_type,
            vehicle=cls.vehicle,
            status=0.8
        )

        cls.valid_component_data = {
            'name': 'Turbocharger',
            'component_type': cls.component_type,
            'vehicle': cls.vehicle,
            'status': 0.9
        }

    def test_name_validation_and_standardization(self):
        """
        Scenario: Testing name validation and standardization
        Given various component names
        When saving components
        Then they should be properly validated and standardized
        """
        valid_cases = [
            ('  v9 engine  ', 'V9 engine'),  # Whitespace stripping and capitalization
            ('TURBO CHARGER', 'Turbo charger'),  # All caps to proper case
            ('air-intake   filter', 'Air-intake filter'),  # Hyphen and spacing
        ]

        invalid_cases = [
            (None, 'Component name cannot be null.'),
            ('', 'Component name cannot be blank.'),
            ('A', 'Component name must be at least 2 characters long.'),
            ('Part@123', 'Component name contains invalid special characters.'),
            ('C' * 201, 'Ensure this value has at most 200 characters'),
        ]

        # Test valid cases
        for input_name, expected_name in valid_cases:
            with self.subTest(input_name=input_name):
                component = VehicleComponent.objects.create(
                    name=input_name,
                    component_type=self.component_type,
                    vehicle=self.vehicle
                )
                self.assertEqual(component.name, expected_name)

        # Test invalid cases
        for invalid_name, expected_error in invalid_cases:
            with self.subTest(invalid_name=invalid_name):
                component = VehicleComponent(
                    name=invalid_name,
                    component_type=self.component_type,
                    vehicle=self.vehicle
                )
                with self.assertRaises(ValidationError) as context:
                    component.full_clean()
                self.assertIn(expected_error, str(context.exception))

    def test_status_validation(self):
        """
        Scenario: Testing status validation and defaults
        Given various status values
        When saving components
        Then they should be properly validated and defaults applied
        """
        valid_values = [
            (1, 0.0, 0.0),
            (2, 0.5, 0.5),
            (3, 1.0, 1.0),
            (4, None, 0.0),  # Tests default value
        ]
        invalid_values = [-0.1, 1.1, 2.0]

        # Test valid values
        for count, input_status, expected_status in valid_values:
            with self.subTest(status=input_status):
                component = VehicleComponent.objects.create(
                    name=f"Test Component{count}",
                    component_type=self.component_type,
                    vehicle=self.vehicle,
                    status=input_status
                )
                self.assertEqual(component.status, expected_status)

        # Test invalid values
        for invalid_status in invalid_values:
            with self.subTest(status=invalid_status):
                component = VehicleComponent(
                    name="Test Component",
                    component_type=self.component_type,
                    vehicle=self.vehicle,
                    status=invalid_status
                )
                with self.assertRaises(ValidationError) as context:
                    component.full_clean()
                self.assertIn('Status must be between 0.0 and 1.0.', str(context.exception))

    def test_model_relationships(self):
        """
        Scenario: Testing model relationships and constraints
        Given a component with relationships
        When performing relationship operations
        Then they should behave as expected
        """
        # Test required relationships
        required_fields = [
            ('component_type', None, 'Component type is required.'),
            ('vehicle', None, 'Vehicle is required.'),
        ]

        for field, value, expected_error in required_fields:
            with self.subTest(field=field):
                data = self.valid_component_data.copy()
                data[field] = value
                component = VehicleComponent(**data)
                with self.assertRaises(ValidationError) as context:
                    component.full_clean()
                self.assertIn(expected_error, str(context.exception))

        # Test unique together constraint
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VehicleComponent.objects.create(
                    name=self.base_component.name,
                    component_type=self.base_component.component_type,
                    vehicle=self.base_component.vehicle
                )

        # Test deletion behaviors
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.component_type.delete()  # Should be protected

        vehicle_id = self.vehicle.vin
        self.vehicle.delete()  # Should cascade
        self.assertEqual(
            VehicleComponent.objects.filter(vehicle__vin=vehicle_id).count(),
            0
        )

    def test_model_metadata(self):
        """
        Scenario: Testing model metadata and behaviors
        Given the VehicleComponent model
        When checking model configuration
        Then it should match specifications
        """
        # Test string representation
        expected_str = f"Engine - {self.vehicle}"
        self.assertEqual(str(self.base_component), expected_str)

        # Test metadata configuration
        self.assertEqual(VehicleComponent._meta.db_table, 'vehicle_components')
        self.assertEqual(
            VehicleComponent._meta.ordering,
            ['vehicle', 'component_type__name']
        )

        # Check indexes
        indexes = [index.name for index in VehicleComponent._meta.indexes]
        expected_indexes = [
            'vehicle_component_name_idx',
            'vehicle_component_type_idx',
            'vehicle_component_vehicle_idx',
            'vehicle_component_status_idx'
        ]
        for index in expected_indexes:
            self.assertIn(index, indexes)

        # Check verbose names
        self.assertEqual(
            VehicleComponent._meta.verbose_name,
            _('Vehicle Component')
        )
        self.assertEqual(
            VehicleComponent._meta.verbose_name_plural,
            _('Vehicle Components')
        )

    def test_timestamped_behavior(self):
        """
        Scenario: Testing TimeStampedModel functionality
        Given a vehicle component
        When performing operations
        Then timestamps should be properly managed
        """
        # Test creation timestamp exists
        self.assertIsNotNone(self.base_component.created)

        # Test modification timestamp updates
        original_modified = self.base_component.modified
        self.base_component.status = 0.7
        self.base_component.save()
        self.assertGreater(self.base_component.modified, original_modified)

    def test_queryset_operations(self):
        """
        Scenario: Testing queryset operations
        Given multiple components
        When performing database operations
        Then they should work as expected
        """
        # Create test components with different statuses
        components = [
            VehicleComponent.objects.create(
                name=f"Test Component {i}",
                component_type=self.component_type,
                vehicle=self.vehicle,
                status=i * 0.2
            ) for i in range(1, 4)
        ]

        # Test basic filtering
        low_status = VehicleComponent.objects.filter(status__lt=0.5)
        high_status = VehicleComponent.objects.filter(status__gte=0.5)
        self.assertTrue(low_status.exists())
        self.assertTrue(high_status.exists())

        # Test ordering
        ordered = VehicleComponent.objects.order_by('status')
        self.assertLess(ordered.first().status, ordered.last().status)

        # Test aggregation
        from django.db.models import Avg
        avg_status = VehicleComponent.objects.aggregate(
            avg_status=Avg('status')
        )['avg_status']
        self.assertIsNotNone(avg_status)

    def test_year_validation_with_none(self):
        """
        Scenario: Testing year validation with None value
        Given a vehicle with year_built set to None
        When validating the vehicle
        Then it should raise ValidationError
        """
        vehicle = Vehicle(
            vin="WBA12345678901234",
            year_built=None,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color
        )

        with self.assertRaises(ValidationError) as context:
            vehicle.clean()
        self.assertIn('Year built is required.', str(context.exception))

    def test_vin_validation_with_none(self):
        """
        Scenario: Testing VIN validation with None value
        Given a vehicle with VIN set to None
        When validating the vehicle
        Then it should raise ValidationError
        """
        vehicle = Vehicle(
            vin=None,
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color
        )

        with self.assertRaises(ValidationError) as context:
            vehicle.clean()
        self.assertIn('VIN is required.', str(context.exception))

    def test_string_representation_with_owner(self):
        """
        Scenario: Testing string representation with owner
        Given a vehicle with an owner
        When converting to string
        Then it should include owner information
        """
        from django.contrib.auth.models import User
        owner = User.objects.create(username='testuser')
        vehicle = Vehicle.objects.create(
            vin="NBA88888888888888",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color,
            owner=owner
        )

        expected_str = f'2023 Bmw (DE) X5 NBA88888888888888 [Owned by: testuser]'
        self.assertEqual(str(vehicle), expected_str)

    def test_vin_validation_with_empty_string(self):
        """
        Scenario: Testing VIN validation with empty string
        Given a vehicle with VIN as empty string
        When validating the vehicle
        Then it should raise ValidationError
        """
        vehicle = Vehicle(
            vin='',  # Empty string will make self.vin falsy
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.exterior_color,
            interior_color=self.interior_color
        )

        with self.assertRaises(ValidationError) as context:
            vehicle.clean()
        self.assertIn('VIN is required.', str(context.exception))
