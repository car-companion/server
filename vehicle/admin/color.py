from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from colorfield.widgets import ColorWidget
from unfold.admin import ModelAdmin
from ..models import Color


class UnfoldColorWidget(ColorWidget):
    """
    Custom ColorWidget that integrates with Unfold admin theme.
    """

    def __init__(self, attrs=None):
        default_attrs = {
            'class': ('border bg-white font-medium min-w-20 rounded-md shadow-sm text-font-default-light '
                      'text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none '
                      'group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 dark:bg-gray-900 '
                      'dark:border-gray-700 dark:text-font-default-dark dark:focus:border-primary-600 '
                      'dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 '
                      'dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full max-w-2xl'),
            'data-jscolor': '{previewPosition: "right", previewSize: 32}',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        """
        Render the widget with Unfold styling.
        """
        html = super().render(name, value, attrs, renderer)
        wrapper_html = format_html(
            '<div class="mb-4">{}'
            '<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Color in hexadecimal format</p></div>',
            html,
        )
        return wrapper_html


class ColorAdminForm(forms.ModelForm):
    """
    Custom form for Color model admin.
    """
    hex_code = forms.CharField(
        label=_('Color code'),
        widget=UnfoldColorWidget,
        help_text=_('Color in hexadecimal format')
    )

    class Meta:
        model = Color
        fields = '__all__'


@admin.register(Color)
class ColorAdmin(ModelAdmin):
    form = ColorAdminForm
    list_display = (
        'name',
        'color_preview',
        'hex_code',
        'is_metallic',
    )

    list_filter = ('is_metallic',)
    search_fields = ('name', 'hex_code', 'description')
    ordering = ('name',)
    list_per_page = 20

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'hex_code'),
            ),
            'classes': ('grid-col-2',)
        }),
        (_('Properties'), {
            'fields': (
                ('is_metallic',),
            ),
            'classes': ('grid-col-2',)
        }),
        (_('Additional Information'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    def color_preview(self, obj):
        return format_html(
            '''
            <div class="flex items-center justify-center">
                <div class="w-8 h-8 rounded border" 
                     style="background-color: {}; border-color: var(--color-black-white);">
                </div>
            </div>
            ''',
            obj.hex_code
        )

    color_preview.short_description = _('Preview')
