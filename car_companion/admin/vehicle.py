from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, StackedInline
from guardian.admin import GuardedModelAdmin

from ..models.vehicle import Vehicle, VehicleComponent


class VehicleComponentInline(StackedInline):
    """
    Inline admin for managing components of a specific vehicle.
    """
    model = VehicleComponent
    extra = 1
    classes = ['collapse']

    fields = [
        ('component_type', 'name'),
        'status'
    ]

    autocomplete_fields = ['component_type']


@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin, GuardedModelAdmin):
    """
    Admin interface for managing vehicles.
    """
    list_select_related = [
        'model',
        'model__manufacturer',
        'outer_color',
        'interior_color',
        'owner'
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
                'owner'
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

    def save_related(self, request, form, formsets, change):
        """
        Override save_related to create default components after saving the vehicle
        but before saving inline formsets.
        """
        super().save_related(request, form, formsets, change)

        # If this is a new vehicle, create components from model defaults
        if not change:
            model = form.instance.model
            for model_component in model.default_components.all():
                VehicleComponent.objects.get_or_create(
                    name=model_component.name,
                    component_type=model_component.component_type,
                    vehicle=form.instance,
                    defaults={
                        'status': 0.0  # Default initial status
                    }
                )
