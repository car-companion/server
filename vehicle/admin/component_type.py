from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models.component_type import ComponentType


@admin.register(ComponentType)
class ComponentTypeAdmin(ModelAdmin):
    list_display = ['name', 'description', ]

    search_fields = ['name', 'description', ]

    ordering = ['name']
