from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from ...models import VehicleModel, Manufacturer


class VehicleModelTests(TestCase):
    def setUp(self):
        """Create a manufacturer and a vehicle model."""
        self.manufacturer = Manufacturer.objects.create(name="Toyota")
        self.vehicle_model = VehicleModel.objects.create(name="Camry", manufacturer=self.manufacturer)

    def test_name_standardization(self):
        """Test that vehicle model names are standardized."""
        model = VehicleModel.objects.create(name="prius", manufacturer=self.manufacturer)
        self.assertEqual(model.name, "PRIUS")

    def test_empty_name_validation(self):
        """Test for empty model name."""
        invalid_model = VehicleModel(name="", manufacturer=self.manufacturer)
        with self.assertRaises(ValidationError) as context:
            invalid_model.full_clean()
        self.assertIn("Model name cannot be blank", str(context.exception))

    def test_unique_constraint(self):
        """Test uniqueness of name and manufacturer."""
        duplicate_model = VehicleModel(name="Camry", manufacturer=self.manufacturer)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                duplicate_model.save()

    def test_special_characters_validation(self):
        """Ensure special characters in names are not allowed."""
        model = VehicleModel(name="Camry!", manufacturer=self.manufacturer)
        with self.assertRaises(ValidationError) as context:
            model.full_clean()
        self.assertIn("Model name contains invalid special characters", str(context.exception))

    def test_manufacturer_is_required(self):
        """Test that a manufacturer is required."""
        model = VehicleModel(name="Model X", manufacturer=None)
        with self.assertRaises(ValidationError) as context:
            model.full_clean()
        self.assertIn("Manufacturer is required", str(context.exception))

    def test_ordering(self):
        """Ensure models are ordered by manufacturer name, then model name."""
        manufacturer_b = Manufacturer.objects.create(name="BMW")
        VehicleModel.objects.create(name="X5", manufacturer=manufacturer_b)
        models = VehicleModel.objects.all()
        self.assertEqual([model.name for model in models], ['Camry', 'X5'])
