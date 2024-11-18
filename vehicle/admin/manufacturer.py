from django.contrib import admin
from django.db.models import Count
from unfold.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from ..models.manufacturer import Manufacturer


@admin.register(Manufacturer)
class ManufacturerAdmin(ModelAdmin):
    list_display = (
        'name',
        'country_code',
        'display_website',
        'get_models_count',
    )
    list_filter = ('country_code',)
    search_fields = (
        'name',
        'country_code',
        'description',
    )
    ordering = ('name',)
    list_per_page = 20

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'country_code',
            ),
        }),
        (_('Additional Information'), {
            'fields': (
                'website_url',
                'description',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('get_models_count',)

    def get_models_count(self, obj):
        """Get the number of models for this manufacturer"""
        count = obj.models.count()
        return format_html(
            '<span title="{}">{}</span>',
            _("{} models").format(count),
            count
        )

    get_models_count.short_description = _("Models Count")
    get_models_count.admin_order_field = 'models_count'

    def display_website(self, obj):
        """Display website as a clickable link"""
        if obj.website_url:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
                obj.website_url,
                _("Visit Website")
            )
        return _("No website")

    display_website.short_description = _("Website")

    def get_queryset(self, request):
        """Optimize queryset by annotating the models count"""
        return super().get_queryset(request).annotate(
            models_count=Count('models')
        )
