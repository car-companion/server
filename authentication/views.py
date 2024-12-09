from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.shortcuts import render

User = get_user_model()

@api_view(['GET'])
def activate_account(request, uid, token):
    try:
        # Decode the UID
        uid = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise Http404("Invalid activation link.")

    # Check if the user is already active
    if user.is_active:
        return render(request, 'emails/activation_status.html', {'message': "User already activated."})

    # Check the token validity
    if default_token_generator.check_token(user, token):
        # Activate the user
        user.is_active = True
        user.save()
        return render(request, 'emails/activation_status.html', {'message': "Account activated successfully!"})
    else:
        raise Http404("Invalid or expired token.")
