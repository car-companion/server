from django.urls import path
from .views import activate_account

urlpatterns = [
    path('activate/<uid>/<token>/', activate_account, name='activate_account'),
]
