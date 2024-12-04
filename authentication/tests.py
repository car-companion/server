from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from jwt.utils import force_bytes


class ActivationTests(TestCase):
    def test_activation_success(self):
        user = User.objects.create_user(email='test@example.com', password='password', is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = self.client.get(f'/api/auth/users/activate/{uid}/{token}/')
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
