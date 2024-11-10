from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from ...models import VehicleModel, Manufacturer


class VehicleModelTests(TestCase):
    def setUp(self):
        """
        Scenario: Setting up initial data for vehicle model tests
        Given a manufacturer and a vehicle model
        When the tests run
        Then these objects are available for testing
        """
        self.manufacturer = Manufacturer.objects.create(name="Toyota")
        self.vehicle_model = VehicleModel.objects.create(name="Camry", manufacturer=self.manufacturer)

    def test_name_standardization(self):
        """
        Scenario: Standardizing vehicle model names
        Given a new vehicle model with a lowercase name
        When it is saved to the database
        Then the model name should be standardized to uppercase
        """
        model = VehicleModel.objects.create(name="prius", manufacturer=self.manufacturer)
        self.assertEqual(model.name, "PRIUS")

    def test_empty_name_validation(self):
        """
        Scenario: Validating empty vehicle model names
        Given an empty vehicle model name
        When attempting to save the model
        Then a ValidationError should be raised with a message indicating the name cannot be blank
        """
        invalid_model = VehicleModel(name="", manufacturer=self.manufacturer)
        with self.assertRaises(ValidationError) as context:
            invalid_model.full_clean()
        self.assertIn("Model name cannot be blank", str(context.exception))

    def test_unique_constraint(self):
        """
        Scenario: Enforcing unique constraint on vehicle models
        Given a vehicle model name that already exists for a manufacturer
        When attempting to create a duplicate model with the same name and manufacturer
        Then an IntegrityError should be raised
        """
        duplicate_model = VehicleModel(name="Camry", manufacturer=self.manufacturer)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                duplicate_model.save()

    def test_special_characters_validation(self):
        """
        Scenario: Validating model names for special characters
        Given a vehicle model name with special characters
        When attempting to save the model
        Then a ValidationError should be raised with a message indicating invalid characters
        """
        model = VehicleModel(name="Camry!", manufacturer=self.manufacturer)
        with self.assertRaises(ValidationError) as context:
            model.full_clean()
        self.assertIn("Model name contains invalid special characters", str(context.exception))

    def test_manufacturer_is_required(self):
        """
        Scenario: Validating manufacturer requirement
        Given a vehicle model without a manufacturer
        When attempting to save the model
        Then a ValidationError should be raised with a message indicating a manufacturer is required
        """
        model = VehicleModel(name="Model X", manufacturer=None)
        with self.assertRaises(ValidationError) as context:
            model.full_clean()
        self.assertIn("Manufacturer is required", str(context.exception))

    def test_ordering(self):
        """
        Scenario: Ensuring ordering of vehicle models
        Given multiple vehicle models from different manufacturers
        When retrieving models from the database
        Then they should be ordered by manufacturer name, then model name
        """
        manufacturer_b = Manufacturer.objects.create(name="BMW")
        VehicleModel.objects.create(name="X5", manufacturer=manufacturer_b)
        models = VehicleModel.objects.all()
        self.assertEqual([model.name for model in models], ['Camry', 'X5'])