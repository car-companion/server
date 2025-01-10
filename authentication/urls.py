from django.urls import path
from authentication.views import ActivateAccountView, ResetPasswordView

urlpatterns = [
    path(
        'api/auth/users/activation/<str:uid>/<str:token>/',
        ActivateAccountView.as_view(),
        name='activate-account'
    ),
    path('api/auth/users/reset_password_confirm/<str:uid>/<str:token>/',
         ResetPasswordView.as_view(),
         name='reset-password-page'),

]
