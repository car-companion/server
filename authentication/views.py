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
        print(activation_url)

        try:
            response = requests.post(
                activation_url,
                json={'uid': uid, 'token': token},
                headers={'Content-Type': 'application/json'},
                timeout=(30, 120),
                allow_redirects=True
            )
            print('response is ready')

            try:
                response_data = response.json()

            except ValueError:
                response_data = response.text

            print(response.status_code)
            if response.status_code == 204:
                print('Account activated successfully')
                return Response(
                    {'detail': 'Account activated successfully'},
                    status=status.HTTP_200_OK
                )

            return Response(
                {'detail': response_data},
                status=response.status_code
            )

        except requests.Timeout:
            print("****************************")
            print()
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

        try:
            # Forward the POST request to Djoser
            response = requests.post(
                reset_password_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=(2, 8),
                allow_redirects=True
            )

            if response.status_code == 204:
                # Success
                return HttpResponse('Password reset successfully. You can now log in.', status=200)

            elif response.status_code == 400:
                # Handle specific error messages
                try:
                    response_data = response.json()
                    error_message = response_data.get('token', ['An error occurred while resetting your password.'])[0]
                except (ValueError, KeyError):
                    error_message = 'An error occurred while resetting your password.'
                return HttpResponse(error_message, status=400)

            # Generic error
            try:
                response_data = response.json()
            except ValueError:
                response_data = {}
            return HttpResponse(
                json.dumps(response_data),
                content_type='application/json',
                status=response.status_code
            )

        except requests.RequestException as e:
            return HttpResponse(f'Password reset failed: {str(e)}', status=500)