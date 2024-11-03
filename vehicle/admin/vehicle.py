from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models.vehicle import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_select_related = ['model', 'model__manufacturer', 'outer_color', 'interior_color']
    list_display = [
        'vin',
        'year_built',
        'model',
        'get_manufacturer',
        'outer_color',
        'interior_color',
        'nickname'
    ]

    list_filter = [
        'year_built',
        'model__manufacturer',
        'model',
    ]

    search_fields = [
        'vin',
        'nickname',
        'model__name',
        'model__manufacturer__name'
    ]

    fieldsets = [
        (_('Basic Information'), {
            'fields': (
                'vin',
                'year_built',
                'model',
                'nickname'
            )
        }),
        (_('Colors'), {
            'fields': (
                'outer_color',
                'interior_color'
            )
        })
    ]

    def get_manufacturer(self, obj):
        """Display manufacturer through model relationship"""
        return obj.model.manufacturer

    get_manufacturer.short_description = _('Manufacturer')
    get_manufacturer.admin_order_field = 'model__manufacturer__name'
