from django.urls import include, path

from .views.vehicle import take_ownership, disown, my_vehicles

urlpatterns = [
    path('take-ownership/', take_ownership, name='take-ownership'),
    path('disown/', disown, name='disown'),
    path('my-vehicles/', my_vehicles, name='my-vehicles'),
]