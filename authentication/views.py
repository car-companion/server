import requests
import json
from django.http import HttpResponse, HttpResponseNotAllowed
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

        try:
            response = requests.post(
                activation_url,
                json={'uid': uid, 'token': token},
                headers={'Content-Type': 'application/json'},
                timeout=(12, 50),
                allow_redirects=True
            )

            try:
                response_data = response.json()

            except ValueError:
                response_data = response.text

            if response.status_code == 204:
                return Response(
                    {'detail': 'Account activated successfully'},
                    status=status.HTTP_200_OK
                )

            return Response(
                {'detail': response_data},
                status=response.status_code
            )

        except requests.Timeout:
            return Response(
                {'detail': 'Activation request timed out'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.RequestException as e:
            return Response(
                {'detail': f'Activation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResetPasswordView(APIView):
    """
    Handle password reset confirmation through POST requests.
    - GET: (Optional if needed, for example, serving a form template)
    - POST: Forward reset password request to the Djoser endpoint.
    """

    def get(self, request, uid, token):
        """
        Serve a placeholder response or render a template for reset password.
        """
        return Response(
            {
                'detail': 'This endpoint is for password reset confirmation. Please send a POST request with the required data.'},
            status=status.HTTP_200_OK
        )

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

        try:
            # Forward the POST request to Djoser
            response = requests.post(
                reset_password_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=(12, 50),
                allow_redirects=True
            )

            if response.status_code == 204:
                # Success
                return Response(
                    {'detail': 'Password reset successfully. You can now log in.'},
                    status=status.HTTP_200_OK
                )

            # Handle errors from Djoser
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text

            return Response(
                {'detail': response_data},
                status=response.status_code
            )

        except requests.Timeout:
            return Response(
                {'detail': 'Password reset request timed out'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.RequestException as e:
            return Response(
                {'detail': f'Password reset failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
