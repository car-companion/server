from djoser.serializers import UserCreateSerializer as BaseUserRegistrationSerializer
from rest_framework import serializers


class UserRegistrationSerializer(BaseUserRegistrationSerializer):
    class Meta(BaseUserRegistrationSerializer.Meta):
        fields = ("id", "email", "username", "first_name", "last_name", "password")

    def create(self, validated_data):
        try:
            user = super().create(validated_data)
            user.is_active = False  # Make sure the user is inactive initially
            user.save()
            return user
        except Exception as e:
            raise serializers.ValidationError({"error": f"User creation failed: {str(e)}"})
