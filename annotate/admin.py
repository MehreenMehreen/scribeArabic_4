from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .user_model import ScribeUser  # or from .models if it's in models.py

@admin.register(ScribeUser)
class CustomUserAdmin(UserAdmin):
    model = ScribeUser
    list_display = ('email', 'name', 'fullname', 'is_staff', 'is_superuser', 'is_public')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_public')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'fullname', 'is_public')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'fullname', 'password1', 'password2', 'is_public', 'is_staff', 'is_superuser'),
        }),
    )
    search_fields = ('email', 'name', 'fullname')
    ordering = ('email',)
