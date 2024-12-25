from django.urls import path
from authentication.views import ActivateAccountView

urlpatterns = [
    path(
        'api/auth/users/activation/<str:uid>/<str:token>/',
        ActivateAccountView.as_view(),
        name='activate-account'
    ),
]
