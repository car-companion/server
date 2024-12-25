from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from authentication.models import CustomUser
import logging

# Set up logging
logger = logging.getLogger(__name__)


class UserRegistrationSerializer(BaseUserCreateSerializer):
    """
    Custom user registration serializer for debugging and customization.
    """

    class Meta(BaseUserCreateSerializer.Meta):
        model = CustomUser
        fields = ("id", "email", "username", "first_name", "last_name", "password")
