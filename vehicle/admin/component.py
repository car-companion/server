from django.contrib import admin
from ..models.component import ComponentType, VehicleComponent


@admin.register(ComponentType)
class ComponentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', ]

    search_fields = ['name', 'description', ]

    ordering = ['name']
