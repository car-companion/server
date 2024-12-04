from django.urls import path
from authentication.views import activate_account

urlpatterns = [
    path('users/activate/<uid>/<token>/', activate_account, name='activate_account'),
]
