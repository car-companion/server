from django.contrib import admin
from ..models import VehicleModel


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer')
    list_filter = ('manufacturer',)
    search_fields = ('name', 'manufacturer__name')
    ordering = ('manufacturer__name', 'name')
    autocomplete_fields = ['manufacturer']
    list_per_page = 20
