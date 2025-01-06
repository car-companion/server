from unittest.mock import Mock
from unittest.mock import patch

import requests
import json
from django.core import mail
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from authentication.emails import ActivationEmail, PasswordResetEmail, ConfirmationEmail
from authentication.models import CustomUser
from authentication.serializers import UserRegistrationSerializer


# --- emails Tests ---
class CustomEmailTests(TestCase):
    """
    Test suite for custom email classes.
    """

    def setUp(self):
        # Create a real user for testing emails
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@mail.com",
            password="testpassword123"
        )

        # Common context for email templates
        self.context = {
            "user": self.user,  # Use a real Django user instance
            "domain": "example.com",
            "site_name": "CarCompanion",
            "uid": "dummy-uid",
            "token": "dummy-token",
            "url": f"http://example.com/activate/dummy-uid/dummy-token/"
        }

        # Mock request
        self.request = Mock()
        self.request.user = self.user  # Attach the real user to the mock request
        self.request.get_host.return_value = "example.com"
        self.request.is_secure.return_value = False

    def test_confirmation_email_template(self):
        """
        Scenario: Confirmation email is sent
        Given the ConfirmationEmail class
        When the email is generated
        Then the correct template is used and the email is sent successfully
        """
        email = ConfirmationEmail(self.context)
        email.request = self.request  # Set the mock request
        email.send(to=["testuser@mail.com"])

        # Verify email sending
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        # Check email details
        self.assertEqual(sent_email.subject, "Account Activated - CarCompanion")  # Match actual subject
        self.assertIn("Congratulations! Your CarCompanion account has been successfully activated.", sent_email.body)

        # Verify correct template usage
        self.assertEqual(email.template_name, "emails/confirmation.html")

    def test_activation_email_template(self):
        """
        Scenario: Activation email is sent
        Given the ActivationEmail class
        When the email is generated
        Then the correct template is used and the email is sent successfully
        """
        email = ActivationEmail(self.context)
        email.request = self.request  # Set the mock request
        email.send(to=["testuser@mail.com"])

        # Verify email sending
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        # Check email details
        self.assertEqual(sent_email.subject, "Account Activation - CarCompanion")  # Match actual subject
        self.assertIn("activate your account", sent_email.body)

        # Verify correct template usage
        self.assertEqual(email.template_name, "emails/activation.html")

    def test_password_reset_email_template(self):
        """
        Scenario: Password reset email is sent
        Given the PasswordResetEmail class
        When the email is generated
        Then the correct template is used and the email is sent successfully
        """
        email = PasswordResetEmail(self.context)
        email.request = self.request  # Set the mock request
        email.send(to=["testuser@mail.com"])

        # Verify email sending
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        # Check email details
        self.assertEqual(sent_email.subject, "Password Reset - CarCompanion")
        self.assertIn("password reset", sent_email.body)

        # Verify correct template usage
        self.assertEqual(email.template_name, "emails/password_reset.html")


# --- Serializer Tests ---
class UserRegistrationSerializerTests(APITestCase):
    """Test suite for the UserRegistrationSerializer."""

    def setUp(self):
        # Common setup for valid and invalid data
        self.valid_data = {
            "email": "testuser@mail.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpassword123",
        }
        self.invalid_data = {
            "email": "invalid-email",  # Invalid email format
            "username": "",  # Username cannot be empty
            "first_name": "Test",
            "last_name": "User",
            "password": "testpassword123",
        }

    def test_valid_registration(self):
        """
        Scenario: User provides valid registration data
        Given valid registration data
        When the serializer is validated
        Then the user is successfully created without errors
        """
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.email, self.valid_data["email"])
        self.assertTrue(user.check_password(self.valid_data["password"]))

    def test_invalid_registration(self):
        """
        Scenario: User provides invalid registration data
        Given invalid registration data
        When the serializer is validated
        Then validation errors are returned, and no user is created
        """
        serializer = UserRegistrationSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn("username", serializer.errors)

    def test_duplicate_registration(self):
        """
        Scenario: User attempts to register with an existing email
        Given an email already registered in the system
        When the serializer is validated
        Then duplicate email errors are returned
        """
        CustomUser.objects.create_user(
            email=self.valid_data["email"], username="existinguser", password="somepassword"
        )
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


# --- Activate Account Tests ---
class ActivateAccountTests(TestCase):
    """Tests for the ActivateAccountView."""

    def setUp(self):
        self.client = APIClient()

    @patch('requests.post')
    def test_activation_success(self, mock_post):
        """
        Scenario: User successfully activates their account
        Given valid UID and token
        When the activation endpoint is called
        Then the user account is activated successfully
        """
        mock_post.return_value.status_code = 204
        response = self.client.get(reverse('activate-account', kwargs={'uid': 'test-uid', 'token': 'test-token'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Account activated successfully', response.data['detail'])

    @patch('requests.post')
    def test_activation_invalid_token(self, mock_post):
        """
        Scenario: User activation fails due to invalid token
        Given an invalid token
        When the activation endpoint is called
        Then the activation fails with an appropriate error message
        """
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {'token': ['Invalid or expired token.']}
        response = self.client.get(reverse('activate-account', kwargs={'uid': 'test-uid', 'token': 'invalid-token'}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid or expired token.', response.data['detail']['token'][0])

    @patch('requests.post')
    def test_activation_request_exception(self, mock_post):
        """
        Scenario: Activation fails due to a request exception
        Given a request failure during activation
        When the activation endpoint is called
        Then a server error is returned
        """
        mock_post.side_effect = requests.RequestException('Request failed')
        response = self.client.get(reverse('activate-account', kwargs={'uid': 'test-uid', 'token': 'test-token'}))
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Activation failed: Request failed', response.data['detail'])

    @patch('requests.post')
    def test_activation_value_error_fallback(self, mock_post):
        """
        Scenario: The activation response contains invalid JSON
        Given the activation endpoint returns non-JSON data
        When the response is processed
        Then it should fall back to the response text
        """
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.side_effect = ValueError()  # Simulate a ValueError during JSON parsing
        mock_post.return_value.text = "Non-JSON error response"

        response = self.client.get(reverse('activate-account', kwargs={'uid': 'test-uid', 'token': 'test-token'}))
        self.assertEqual(response.status_code, 400)
        self.assertIn("Non-JSON error response", response.data['detail'])


# --- Password Reset Tests ---
class PasswordResetTests(TestCase):
    """Tests for the password reset functionality."""

    def setUp(self):
        self.factory = RequestFactory()
        self.client = APIClient()

    @patch('requests.post')
    def test_password_reset_page_get(self, mock_post):
        """
        Scenario: User accesses the password reset page
        Given a valid UID and token
        When the GET request is made
        Then the password reset form is rendered
        """
        response = self.client.get(reverse('reset-password-page', kwargs={'uid': 'test-uid', 'token': 'test-token'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reset_password_form.html')

    @patch('requests.post')
    def test_password_reset_valid_post(self, mock_post):
        """
        Scenario: User successfully resets their password
        Given valid UID, token, and new password
        When the POST request is made
        Then the password reset is processed successfully
        """
        mock_post.return_value.status_code = 204

        response = self.client.post(
            reverse('reset-password-page', kwargs={'uid': 'test-uid', 'token': 'test-token'}),
            data={'new_password': 'newpassword123'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Password reset successfully", response.content.decode())

    def test_password_reset_missing_password(self):
        """
        Scenario: Password reset fails due to missing new password
        Given a POST request without a new password
        When the request is made
        Then a 400 error is returned indicating the missing password
        """
        response = self.client.post(
            reverse('reset-password-page', kwargs={'uid': 'test-uid', 'token': 'test-token'}),
            data={}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("New password is required", response.content.decode())

    @patch('requests.post')
    def test_password_reset_invalid_token(self, mock_post):
        """
        Scenario: Password reset fails due to invalid token
        Given a POST request with an invalid token
        When the Djoser endpoint returns a 400 error with token-specific details
        Then an appropriate error message is displayed
        """
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {'token': ['This token is invalid or expired.']}

        response = self.client.post(
            reverse('reset-password-page', kwargs={'uid': 'test-uid', 'token': 'invalid-token'}),
            data={'new_password': 'newpassword123'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("This token is invalid or expired.", response.content.decode())

    @patch('requests.post')
    def test_password_reset_generic_error(self, mock_post):
        """
        Scenario: Password reset fails with a generic 400 error
        Given the Djoser endpoint returns a 400 error without specific details
        When the POST request is made
        Then a generic error message is returned
        """
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {}

        response = self.client.post(
            reverse('reset-password-page', kwargs={'uid': 'test-uid', 'token': 'test-token'}),
            data={'new_password': 'newpassword123'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("An error occurred while resetting your password.", response.content.decode())

    @patch('requests.post')
    def test_password_reset_unexpected_status_code(self, mock_post):
        """
        Scenario: Password reset fails with an unexpected status code
        Given the Djoser endpoint returns an unexpected status code
        When the POST request is made
        Then the raw response body and status code are returned
        """
        mock_post.return_value.status_code = 500
        mock_post.return_value.json.return_value = {'detail': 'Internal server error'}

        response = self.client.post(
            reverse('reset-password-page', kwargs={'uid': 'test-uid', 'token': 'test-token'}),
            data={'new_password': 'newpassword123'}
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn("Internal server error", json.loads(response.content.decode())['detail'])

    @patch('requests.post')
    def test_password_reset_network_error(self, mock_post):
        """
        Scenario: Password reset fails due to a network error
        Given the Djoser endpoint is unreachable
        When the POST request is made
        Then a 500 error is returned with a descriptive message
        """
        mock_post.side_effect = requests.RequestException('Network error')

        response = self.client.post(
            reverse('reset-password-page', kwargs={'uid': 'test-uid', 'token': 'test-token'}),
            data={'new_password': 'newpassword123'}
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("Password reset failed: Network error", response.content.decode())

    def test_reset_password_page_invalid_method(self):
        """
        Scenario: User makes an invalid HTTP request to the password reset page
        Given a request method other than GET or POST
        When the request is processed
        Then a 405 Method Not Allowed error is returned
        """
        response = self.client.put(reverse('reset-password-page', kwargs={'uid': 'test-uid', 'token': 'test-token'}))
        self.assertEqual(response.status_code, 405)
        self.assertIn("", response.content.decode())
