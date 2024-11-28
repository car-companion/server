from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from ...models import VehicleModel, ModelComponent, Manufacturer, ComponentType, Vehicle, Color
from django.utils.translation import gettext_lazy as _


class VehicleModelTests(TestCase):
    """
    Test suite for the VehicleModel model.
    Covers name standardization, manufacturer relationships, and model constraints.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        cls.manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE",
            website_url="https://www.bmw.com"
        )

        cls.base_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=cls.manufacturer
        )

        cls.valid_model_data = {
            'name': '330i',
            'manufacturer': cls.manufacturer
        }

    def test_name_standardization_and_validation(self):
        """
        Scenario: Testing name standardization and validation
        Given vehicle model names with different formats
        When saving them
        Then they should be properly standardized and validated
        """
        test_cases = [
            ('  m3  ', 'M3'),  # Whitespace and case
            ('x5 series', 'X5 SERIES'),  # Multiple words
            ('330i   sport', '330I SPORT'),  # Multiple spaces
        ]

        for input_name, expected_name in test_cases:
            with self.subTest(input_name=input_name):
                model = VehicleModel.objects.create(
                    name=input_name,
                    manufacturer=self.manufacturer
                )
                self.assertEqual(model.name, expected_name)

    def test_manufacturer_required(self):
        """
        Scenario: Testing manufacturer requirement
        Given a vehicle model without a manufacturer
        When attempting to save
        Then it should raise ValidationError
        """
        model = VehicleModel(name="X6")  # No manufacturer specified
        with self.assertRaises(ValidationError) as context:
            model.full_clean()
        self.assertIn('Manufacturer is required.', str(context.exception))

    def test_invalid_names(self):
        """
        Scenario: Testing invalid model names
        Given invalid model names
        When attempting to save
        Then appropriate validation errors should be raised
        """
        invalid_cases = [
            (None, 'Model name cannot be null.'),
            ('', 'Model name cannot be blank.'),
            ('M@3', 'Model name contains invalid special characters.'),
            ('X5!', 'Model name contains invalid special characters.'),
        ]

        for invalid_name, expected_error in invalid_cases:
            with self.subTest(invalid_name=invalid_name):
                model = VehicleModel(
                    name=invalid_name,
                    manufacturer=self.manufacturer
                )
                with self.assertRaises(ValidationError) as context:
                    model.full_clean()
                self.assertIn(expected_error, str(context.exception))

    def test_unique_together_constraint(self):
        """
        Scenario: Testing unique together constraint
        Given an existing model name and manufacturer combination
        When creating another model with the same combination
        Then it should raise an IntegrityError
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VehicleModel.objects.create(
                    name=self.base_model.name,
                    manufacturer=self.manufacturer
                )

    def test_string_representation(self):
        """
        Scenario: Testing string representation
        Given a vehicle model with name and manufacturer
        When converting to string
        Then it should show manufacturer name and model name
        """
        model = VehicleModel.objects.create(
            name="M5",
            manufacturer=self.manufacturer
        )

        self.assertEqual(str(model), "M5")

    def test_create_vehicle_method(self):
        """
        Scenario: Testing create_vehicle method
        Given a vehicle model with default components
        When calling create_vehicle
        Then it should create a vehicle with all default components
        """
        # Create necessary related objects
        outer_color = Color.objects.create(name="Black", hex_code="#000000")
        interior_color = Color.objects.create(name="Beige", hex_code="#F5F5DC")
        component_type = ComponentType.objects.create(name="Engine")

        # Create a default component for the model
        ModelComponent.objects.create(
            model=self.base_model,
            name="V8 Engine",
            component_type=component_type
        )

        # Create a vehicle using the method
        vehicle = self.base_model.create_vehicle(
            vin="WBA12345678901234",
            year_built=2024,
            outer_color=outer_color,
            interior_color=interior_color,
            nickname="My BMW"
        )

        # Verify the vehicle was created correctly
        self.assertEqual(vehicle.model, self.base_model)
        self.assertEqual(vehicle.nickname, "My BMW")

        # Verify components were created
        self.assertEqual(vehicle.components.count(), 1)
        component = vehicle.components.first()
        self.assertEqual(component.name, "V8 engine")
        self.assertEqual(component.status, 0.0)

    def test_model_meta_configuration(self):
        """
        Scenario: Testing model metadata configuration
        Given the VehicleModel model
        When checking metadata
        Then it should match defined settings
        """
        self.assertEqual(VehicleModel._meta.db_table, 'vehicle_models')
        self.assertEqual(
            VehicleModel._meta.ordering,
            ['manufacturer__name', 'name']
        )

        # Check indexes
        indexes = [index.name for index in VehicleModel._meta.indexes]
        self.assertIn('model_name_idx', indexes)
        self.assertIn('model_manufacturer_idx', indexes)

        # Check verbose names
        self.assertEqual(
            VehicleModel._meta.verbose_name,
            _('Vehicle Model')
        )
        self.assertEqual(
            VehicleModel._meta.verbose_name_plural,
            _('Vehicle Models')
        )


class ModelComponentTests(TestCase):
    """
    Test suite for the ModelComponent model.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the entire test suite."""
        cls.manufacturer = Manufacturer.objects.create(
            name="BMW",
            country_code="DE"
        )
        cls.vehicle_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=cls.manufacturer
        )
        cls.component_type = ComponentType.objects.create(
            name="Engine"
        )
        cls.base_component = ModelComponent.objects.create(
            model=cls.vehicle_model,
            name="V8 Engine",
            component_type=cls.component_type
        )

    def test_name_standardization_and_validation(self):
        """
        Scenario: Testing name standardization and validation
        Given component names with different formats
        When saving them
        Then they should be properly standardized and validated
        """
        test_cases = [
            ('  v9 engine  ', 'V9 engine'),  # Whitespace and case
            ('TURBO CHARGER', 'Turbo charger'),  # All caps
            ('dual   exhaust', 'Dual exhaust'),  # Multiple spaces
        ]

        for input_name, expected_name in test_cases:
            with self.subTest(input_name=input_name):
                component = ModelComponent.objects.create(
                    model=self.vehicle_model,
                    name=input_name,
                    component_type=self.component_type
                )
                self.assertEqual(component.name, expected_name)

    def test_invalid_names(self):
        """
        Scenario: Testing invalid component names
        Given invalid component names
        When attempting to save
        Then appropriate validation errors should be raised
        """
        invalid_cases = [
            (None, 'Component name cannot be null.'),
            ('', 'Component name cannot be blank.'),
            ('A', 'Component name must be at least 2 characters long.'),
            ('Engine@V8', 'Component name contains invalid special characters.'),
            ('Turbo!', 'Component name contains invalid special characters.'),
        ]

        for invalid_name, expected_error in invalid_cases:
            with self.subTest(invalid_name=invalid_name):
                component = ModelComponent(
                    model=self.vehicle_model,
                    name=invalid_name,
                    component_type=self.component_type
                )
                with self.assertRaises(ValidationError) as context:
                    component.full_clean()
                self.assertIn(expected_error, str(context.exception))

    def test_unique_together_constraint(self):
        """
        Scenario: Testing unique together constraint
        Given an existing component
        When creating another with same model, name, and type
        Then it should raise an IntegrityError
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ModelComponent.objects.create(
                    model=self.base_component.model,
                    name=self.base_component.name,
                    component_type=self.base_component.component_type
                )

    def test_string_representation(self):
        """
        Scenario: Testing string representation
        Given a model component
        When converting to string
        Then it should show proper string format
        """
        self.assertEqual(
            str(self.base_component),
            f"V8 engine (Engine) - X5"
        )

    def test_model_meta_configuration(self):
        """
        Scenario: Testing model metadata configuration
        Given the ModelComponent model
        When checking metadata
        Then it should match defined settings
        """
        self.assertEqual(ModelComponent._meta.db_table, 'model_components')
        self.assertEqual(
            ModelComponent._meta.ordering,
            ['model', 'component_type__name']
        )

        # Check verbose names
        self.assertEqual(
            ModelComponent._meta.verbose_name,
            _('Model Component')
        )
        self.assertEqual(
            ModelComponent._meta.verbose_name_plural,
            _('Model Components')
        )
