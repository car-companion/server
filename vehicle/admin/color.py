from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models import Color


@admin.register(Color)
class ColorAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 20
