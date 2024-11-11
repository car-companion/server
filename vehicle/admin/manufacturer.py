from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _

from ..models.manufacturer import Manufacturer


@admin.register(Manufacturer)
class ManufacturerAdmin(ModelAdmin):
    list_display = ('name', 'get_models_count',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 20

    def get_models_count(self, obj):
        """Get the number of models for this manufacturer"""
        return obj.models.count()

    get_models_count.short_description = _("Models Count")
