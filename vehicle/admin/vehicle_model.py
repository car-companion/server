from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from ..models.vehicle_model import VehicleModel, ModelComponent
from django.utils.translation import gettext_lazy as _


class ModelComponentInline(TabularInline):
    """
    Inline admin for managing default components of a vehicle model.
    """
    model = ModelComponent
    extra = 4
    classes = ['collapse']

    fields = [
        ('name', 'component_type'),
        'is_required'
    ]

    autocomplete_fields = ['component_type']


@admin.register(VehicleModel)
class VehicleModelAdmin(ModelAdmin):
    """
    Admin interface for managing vehicle models.
    """
    list_display = [
        'name',
        'manufacturer',
        'get_components_count'
    ]

    list_filter = [
        'manufacturer',
    ]

    search_fields = [
        'name',
        'manufacturer__name'
    ]

    inlines = [ModelComponentInline]

    def get_components_count(self, obj):
        """Display count of default components"""
        return obj.default_components.count()

    get_components_count.short_description = _('Default Components')
