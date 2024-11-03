from django.contrib import admin
from ..models import Color


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 20
