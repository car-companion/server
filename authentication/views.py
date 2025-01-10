import requests
import json
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from socket import timeout as SocketTimeout
import logging

logger = logging.getLogger(__name__)



class ActivateAccountView(APIView):
    """Handle account activation through GET requests."""

    def get(self, request, uid, token):
        """
        Activate user account by forwarding activation request to Djoser endpoint.
        """
        # Get the current host
        current_host = request.get_host()
        print(current_host)
        logger.info(f"Activation request started for uid: {uid} from host: {current_host}")

        activation_url = f"{request.scheme}://{current_host}/api/auth/users/activation/"
        logger.info(f"Activation URL: {activation_url}")
        # activation_url = f"{request.build_absolute_uri('/')[:-1]}/api/auth/users/activation/"

        try:
            logger.info("Sending activation request")
            response = requests.post(
                activation_url,
                json={'uid': uid, 'token': token},
                headers={'Content-Type': 'application/json'},
                timeout=(3.05, 27),
                allow_redirects=True
            )
            logger.info(f"Response received: {response.status_code}")
            print(response.status_code)


            try:
                response_data = response.json()
                logger.info(f"Response data: {response_data}")
                print(response.status_code)

            except ValueError:
                response_data = response.text
                logger.info(f"Raw response: {response_data}")


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
            logger.error("Request timed out")

            return Response(
                {'detail': 'Activation request timed out'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except SocketTimeout:
            return Response(
                {'detail': 'Email server connection timed out'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.RequestException as e:
            logger.error(f"Activation failed: {str(e)}")

            return Response(
                {'detail': f'Activation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def reset_password_page(request, uid, token):
    """
    Handle password reset form display and submission.
    - GET: Render the form for the user to input a new password.
    - POST: Use the uid and token from the URL, along with the new password, to send a POST request.
    """
    if request.method == 'GET':
        # Render a page for entering the new password
        return render(request, 'reset_password_form.html', {'uid': uid, 'token': token})

    elif request.method == 'POST':
        # Read the new password from the submitted form
        new_password = request.POST.get('new_password')

        if not new_password:
            return HttpResponse('New password is required', status=400)

        # Construct the payload for the Djoser endpoint
        reset_password_url = f"{request.build_absolute_uri('/')[:-1]}/api/auth/users/reset_password_confirm/"
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
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 204:
                # Success
                return HttpResponse('Password reset successfully. You can now log in.', status=200)

            elif response.status_code == 400:
                # Handle specific error messages
                response_data = response.json()
                error_message = response_data.get('token', ['An error occurred while resetting your password.'])[0]
                return HttpResponse(error_message, status=400)

            # Generic error
            return HttpResponse(
                json.dumps(response.json()),
                content_type='application/json',
                status=response.status_code
            )

        except requests.RequestException as e:
            return HttpResponse(f'Password reset failed: {str(e)}', status=500)

    # Handle unsupported methods
    return HttpResponseNotAllowed(['GET', 'POST'])
