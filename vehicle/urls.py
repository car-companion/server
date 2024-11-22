from django.urls import include, path

from .views import take_ownership, disown, my_vehicles

urlpatterns = [
    path('take-ownership/', take_ownership),
    path('disown/', disown),
    path('my-vehicles/', my_vehicles),
]