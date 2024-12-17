from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.utils import DataError
from car_companion.models import (
    VehicleUserPreferences, Vehicle, VehicleModel,
    Manufacturer, Color
)

User = get_user_model()


class VehicleUserPreferencesTests(TestCase):
    """
    Test suite for the VehicleUserPreferences model.
    Tests user-specific preferences, validations, and constraints.
    """

    def setUp(self):
        """Set up test data before each test method."""
        # Create basic objects needed for testing
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        self.manufacturer = Manufacturer.objects.create(
            name="Bmw",
            country_code="DE"
        )
        self.vehicle_model = VehicleModel.objects.create(
            name="X5",
            manufacturer=self.manufacturer
        )
        self.outer_color = Color.objects.create(
            name="Black",
            hex_code="#000000"
        )
        self.interior_color = Color.objects.create(
            name="Beige",
            hex_code="#F5F5DC"
        )
        self.vehicle = Vehicle.objects.create(
            vin="WBA12345678901234",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.outer_color,
            interior_color=self.interior_color
        )

        # Create base preferences
        self.preferences = VehicleUserPreferences.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            nickname="My BMW",
            interior_color=self.interior_color,
            exterior_color=self.outer_color
        )

    def test_create_preferences_success(self):
        """
        Scenario: Creating preferences with valid data
        Given a user and a vehicle
        When creating preferences with valid data
        Then the preferences should be saved successfully
        """
        preferences = VehicleUserPreferences.objects.create(
            vehicle=self.vehicle,
            user=self.other_user,
            nickname="Family Car"
        )

        self.assertEqual(preferences.nickname, "Family Car")
        self.assertEqual(preferences.vehicle, self.vehicle)
        self.assertEqual(preferences.user, self.other_user)

    def test_nickname_validation_scenarios(self):
        """
        Scenario: Testing nickname validation
        Given various nickname formats
        When validating the nicknames
        Then appropriate validation errors should be raised for invalid formats
        """
        test_cases = [
            ("My-BMW-2023", True, None),  # Valid with hyphens
            ("Car 1234", True, None),  # Valid with numbers
            ("A", False, "Nickname must be at least 2 characters long."),  # Too short
            ("Car@Home", False, "Nickname can only contain letters, numbers, spaces, and hyphens."),
            # Invalid chars
            ("A" * 101, False, "Nickname cannot be longer than 100 characters."),  # Too long
        ]

        # Loop through each test case
        for index, (nickname, should_pass, error_message) in enumerate(test_cases):
            with self.subTest(nickname=nickname):
                # Use a unique vehicle for each test case
                unique_vehicle = Vehicle.objects.create(
                    vin=f"WBA2P2C54BC33750{index}",
                    year_built=2023,
                    model=self.vehicle_model,
                    outer_color=self.outer_color,
                    interior_color=self.interior_color
                )

                # Create a preferences instance
                preferences = VehicleUserPreferences(
                    vehicle=unique_vehicle,
                    user=self.other_user,
                    nickname=nickname
                )

                if should_pass:
                    preferences.full_clean()  # Should not raise error
                    preferences.save()
                    self.assertEqual(preferences.nickname, nickname.strip())
                else:
                    with self.assertRaises((ValidationError, DataError)) as context:
                        preferences.full_clean()
                    if error_message:
                        self.assertIn(error_message, str(context.exception))

    def test_unique_together_constraint(self):
        """
        Scenario: Testing unique constraint for vehicle-user combination
        Given existing preferences for a vehicle-user pair
        When creating another preference for the same pair
        Then it should raise an IntegrityError
        """
        with self.assertRaises(IntegrityError):
            VehicleUserPreferences.objects.create(
                vehicle=self.vehicle,
                user=self.user,  # Same user-vehicle combination
                nickname="Another Nickname"
            )

    def test_optional_color_preferences(self):
        """
        Scenario: Testing optional color preferences
        Given a preference without color selections
        When saving the preferences
        Then it should save successfully
        """
        preferences = VehicleUserPreferences.objects.create(
            vehicle=self.vehicle,
            user=self.other_user,
            nickname="No Colors"
        )

        self.assertIsNone(preferences.interior_color)
        self.assertIsNone(preferences.exterior_color)

    def test_on_delete_behavior(self):
        """
        Scenario: Testing cascade deletion behavior
        Given existing preferences
        When related objects are deleted
        Then appropriate actions should be taken
        """
        # Test vehicle deletion (CASCADE)
        vehicle_id = self.vehicle.vin
        self.vehicle.delete()
        self.assertFalse(
            VehicleUserPreferences.objects.filter(vehicle__vin=vehicle_id).exists()
        )

        # Test user deletion (CASCADE)
        new_vehicle = Vehicle.objects.create(
            vin="WBA98765432109876",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.outer_color,
            interior_color=self.interior_color
        )
        preferences = VehicleUserPreferences.objects.create(
            vehicle=new_vehicle,
            user=self.other_user,
            nickname="Test Car"
        )
        user_id = self.other_user.id
        self.other_user.delete()
        self.assertFalse(
            VehicleUserPreferences.objects.filter(user__id=user_id).exists()
        )

        # Test color deletion (PROTECT)
        with self.assertRaises(Exception):  # Should prevent deletion
            self.interior_color.delete()

    def test_string_representation(self):
        """
        Scenario: Testing string representation
        Given preferences with different data
        When converting to string
        Then it should return the expected format
        """
        expected_str = f"{self.vehicle} - {self.user.username}'s preferences"
        self.assertEqual(str(self.preferences), expected_str)

    def test_ordering(self):
        """
        Scenario: Testing ordering of preferences
        Given multiple preferences
        When retrieving them
        Then they should be ordered by vehicle and user
        """
        # Create another vehicle and preferences
        another_vehicle = Vehicle.objects.create(
            vin="WBA98765432109876",
            year_built=2023,
            model=self.vehicle_model,
            outer_color=self.outer_color,
            interior_color=self.interior_color
        )
        VehicleUserPreferences.objects.create(
            vehicle=another_vehicle,
            user=self.other_user,
            nickname="Another Car"
        )

        # Get ordered preferences
        preferences = VehicleUserPreferences.objects.all()
        self.assertEqual(len(preferences), 2)

        # Verify ordering
        for i in range(len(preferences) - 1):
            current = (preferences[i].vehicle.vin, preferences[i].user.username)
            next_pref = (preferences[i + 1].vehicle.vin, preferences[i + 1].user.username)
            self.assertLessEqual(current, next_pref)

    def test_nickname_whitespace_handling(self):
        """
        Scenario: Testing nickname whitespace handling
        Given nicknames with various whitespace patterns
        When saving the preferences
        Then whitespace should be properly handled
        """
        test_cases = [
            ("  My Car  ", "My Car"),
            ("Multiple   Spaces", "Multiple   Spaces"),
            ("\tTabbed\t", "Tabbed"),
            ("\nNew\nLine\n", "New\nLine"),
        ]

        # Loop through each test case
        for index, (input_nickname, expected_nickname) in enumerate(test_cases):
            with self.subTest(input_nickname=input_nickname):
                # Create a unique vehicle for each test iteration
                unique_vehicle = Vehicle.objects.create(
                    vin=f"5UXZV4C54CL53670{index}",
                    year_built=2023,
                    model=self.vehicle_model,
                    outer_color=self.outer_color,
                    interior_color=self.interior_color
                )

                # Use a unique VehicleUserPreferences instance
                preferences = VehicleUserPreferences.objects.create(
                    vehicle=unique_vehicle,
                    user=self.other_user,  # Keep the user the same
                    nickname=input_nickname
                )

                self.assertEqual(preferences.nickname, expected_nickname)

    def test_meta_configuration(self):
        """
        Scenario: Testing model metadata configuration
        Given the VehicleUserPreferences model
        When checking its metadata
        Then it should match the defined settings
        """
        meta = VehicleUserPreferences._meta
        self.assertEqual(meta.db_table, 'vehicle_user_preferences')
        self.assertEqual(meta.ordering, ['vehicle', 'user'])

        # Normalize unique_together to a list of tuples for comparison
        unique_together = list(meta.unique_together)
        self.assertEqual(
            unique_together,
            [('vehicle', 'user')]
        )

        self.assertEqual(meta.verbose_name, 'Vehicle User Preferences')
        self.assertEqual(meta.verbose_name_plural, 'Vehicle User Preferences')

    def test_clean_method_with_empty_nickname(self):
        """
        Scenario: Testing clean method when nickname is None or empty
        Given a VehicleUserPreferences instance with no nickname
        When clean is called
        Then it should not raise any validation error and nickname remains None or empty
        """
        preferences = VehicleUserPreferences(
            vehicle=self.vehicle,
            user=self.user,
            nickname=''  # Empty nickname
        )

        # Call clean method to ensure it handles empty nicknames gracefully
        preferences.clean()

        # Check that nickname is still an empty string after cleaning
        self.assertEqual(preferences.nickname, '')

