from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import Vehicle, VehicleComponent


class VehicleComponentInline(admin.StackedInline):
    model = VehicleComponent
    extra = 1
    classes = ['collapse']

    fields = [
        ('component_type', 'name'),
        'status'
    ]

    autocomplete_fields = ['component_type']

    verbose_name = _("Component")
    verbose_name_plural = _("Components")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_select_related = [
        'model',
        'model__manufacturer',
        'outer_color',
        'interior_color'
    ]

    list_display = [
        'vin',
        'year_built',
        'model',
        'get_manufacturer',
        'get_components_count'
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

    autocomplete_fields = [
        'model',
        'outer_color',
        'interior_color'
    ]

    fieldsets = [
        (_('Vehicle Information'), {
            'fields': (
                'vin',
                'year_built',
                'model',
                'nickname'
            )
        }),
        (_('Appearance'), {
            'fields': (
                'outer_color',
                'interior_color'
            ),
        }),
    ]

    inlines = [VehicleComponentInline]

    def get_manufacturer(self, obj):
        """Display manufacturer through model relationship"""
        return obj.model.manufacturer

    get_manufacturer.short_description = _('Manufacturer')
    get_manufacturer.admin_order_field = 'model__manufacturer__name'

    def get_components_count(self, obj):
        """Display count of components"""
        return obj.components.count()

    get_components_count.short_description = _('Components')
