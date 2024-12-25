from django.urls import path
from authentication.views import ActivateAccountView, reset_password_page


urlpatterns = [
    path(
        'api/auth/users/activation/<str:uid>/<str:token>/',
        ActivateAccountView.as_view(),
        name='activate-account'
    ),
    path('api/auth/users/reset_password_confirm/<str:uid>/<str:token>/', reset_password_page,
         name='reset-password-page'),

]
