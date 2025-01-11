import threading

import requests
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class ActivateAccountView(APIView):
    """Handle account activation through GET requests."""

    def get(self, request, uid, token):
        """
        Activate user account by forwarding activation request to Djoser endpoint.
        """
        # Get the current host
        current_host = request.get_host()
        request.scheme = 'https' if request.is_secure() else 'http'
        activation_url = f"{request.scheme}://{current_host}/api/auth/users/activation/"

        def async_activation():
            response = requests.post(
                activation_url,
                json={'uid': uid, 'token': token},
                headers={'Content-Type': 'application/json'},
                timeout=(2, 8),  # Increased timeout for longer processing
                allow_redirects=True
            )

        thread = threading.Thread(target=async_activation)
        thread.start()

        # Return an immediate response
        return Response(
            {'detail': 'Activation request submitted. It will be processed shortly.'},
            status=status.HTTP_202_ACCEPTED
        )


class ResetPasswordView(APIView):
    """
    Handle password reset form display and submission.
    - GET: Render the form for the user to input a new password.
    - POST: Use the uid and token from the URL, along with the new password, to send a POST request.
    """

    def get(self, request, uid, token):
        """
        Render a page for entering the new password.
        """
        return render(request, 'reset_password_form.html', {'uid': uid, 'token': token})

    def post(self, request, uid, token):
        """
        Handle password reset confirmation by forwarding the request to Djoser.
        """
        # Extract the new password from the request data
        new_password = request.data.get('new_password')

        if not new_password:
            return Response(
                {'detail': 'New password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Construct the Djoser reset password endpoint URL
        current_host = request.get_host()
        request.scheme = 'https' if request.is_secure() else 'http'
        reset_password_url = f"{request.scheme}://{current_host}/api/auth/users/reset_password_confirm/"

        # Prepare payload for the Djoser endpoint
        payload = {
            'uid': uid,
            'token': token,
            'new_password': new_password
        }

        def async_reset_password():
            response = requests.post(
                reset_password_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=(2, 8),  # Increased timeout for longer processing
                allow_redirects=True
            )

        # Start the reset process in a background thread
        thread = threading.Thread(target=async_reset_password)
        thread.start()

        # Return an immediate response
        return Response(
            {'detail': 'Password reset request submitted. It will be processed shortly.', },
            status=status.HTTP_202_ACCEPTED
        )
