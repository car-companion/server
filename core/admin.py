from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from unfold.admin import ModelAdmin

User = get_user_model()

admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(User)
class CoreUserAdmin(BaseUserAdmin, ModelAdmin):
    superuser_fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined')
    staff_fields = ('username', 'email', 'first_name', 'last_name', 'is_active')
    staff_readonly = ('is_superuser', 'is_staff')

    def get_fields(self, request, obj=None):
        """ Defines which fields admin can view and edit depending on their type """
        if request.user.is_superuser:
            return self.superuser_fields
        elif request.user.is_staff:
            return self.staff_fields
        else:
            return super().get_fields(request, obj)

    def get_readonly_fields(self, request, obj=None):
        """ Specify which fields are read-only for staff users """
        if request.user.is_staff and not request.user.is_superuser:
            return self.staff_readonly
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request):
        """ Define which users get shown depending on admin type """
        query = super().get_queryset(request)
        if request.user.is_superuser:
            return query
        return query.filter(is_staff=True, is_superuser=False)

@admin.register(Group)
class CoreGroupAdmin(BaseGroupAdmin, ModelAdmin):
    def get_model_perms(self, request):
        """ Only superusers may see groups """
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}
