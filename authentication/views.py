import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class ActivateAccountView(APIView):
    """Handle account activation through GET requests."""

    def get(self, request, uid, token):
        """
        Activate user account by forwarding activation request to Djoser endpoint.
        """
        activation_url = f"{request.build_absolute_uri('/')[:-1]}/api/auth/users/activation/"

        try:
            response = requests.post(
                activation_url,
                json={'uid': uid, 'token': token},
                headers={'Content-Type': 'application/json'}
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

        except requests.RequestException as e:
            return Response(
                {'detail': f'Activation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
