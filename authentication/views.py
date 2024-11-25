from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(['GET'])
def activate_account(request, uid, token):
    try:
        # Decode the UID
        uid = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid activation link."}, status=400)

    # Check if the user is already active
    if user.is_active:
        return Response({"error": "User is already activated."}, status=400)

    # Check the token validity
    if default_token_generator.check_token(user, token):
        # Activate the user
        user.is_active = True
        user.save()
        return Response({"message": "Account activated successfully!"}, status=200)
    else:
        return Response({"error": "Invalid or expired token."}, status=400)
