from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail, BadHeaderError
from django.utils.encoding import force_bytes
from django.conf import settings

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']

    def create(self, validated_data):
        try:
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                is_active=False  # User is inactive until they activate their account
            )
            # Generate token and send activation email
            self.send_activation_email(user)
            return user
        except Exception as e:
            raise serializers.ValidationError({"error": f"User creation failed: {str(e)}"})

    def send_activation_email(self, user):
        try:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
            subject = "Activate Your Account"
            message = f"Click the link to activate your account: {activation_link}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except BadHeaderError:
            raise serializers.ValidationError({"error": "Invalid header found in email."})
        except Exception as e:
            raise serializers.ValidationError({"error": f"Failed to send activation email: {str(e)}"})

